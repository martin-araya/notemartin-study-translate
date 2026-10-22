"""Construye el mapa de anclas por documento (fase 038).

Genera ``anchors.json`` por documento a partir de ``snapshots.json``.
El algoritmo es github-slug-v1 con normalización de diacríticos vía
``unicodedata.normalize("NFD", x)``.

Campos por anchor:
- ``old_text``: texto original del heading.
- ``old_slug``: slug calculado por el algoritmo.
- ``new_text``: texto esperado tras la traducción.
- ``new_slug``: slug calculado sobre ``new_text``.
- ``source``: ``implicit`` (calculado) o ``explicit`` (de ``<a id="…">``).

Las anclas explícitas se preservan sin transformación. Los duplicados
reciben sufijo ``-1``, ``-2`` según orden de aparición.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from pathlib import Path


def github_slug(text: str) -> str:
    """Calcula el slug github-style con normalización de diacríticos."""
    decomposed = unicodedata.normalize("NFD", text)
    no_diacritics = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    lowered = no_diacritics.lower()
    cleaned = re.sub(r"`+", "", lowered)
    cleaned = re.sub(r"<[^>]+>", "", cleaned)
    cleaned = re.sub(r"[^\w\- ]+", "-", cleaned, flags=re.UNICODE)
    cleaned = re.sub(r"\s+", "-", cleaned)
    cleaned = re.sub(r"-+", "-", cleaned)
    slug = cleaned.strip("-")
    if len(slug) > 256:
        slug = slug[:256].rstrip("-")
    return slug


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="build_anchors.py")
    p.add_argument("--snapshots", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--algorithm", default="github-slug-v1")
    return p.parse_args(argv)


def write_atomic(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def build_anchors_for_doc(doc: dict) -> dict:
    seen_counts: dict[str, int] = {}
    anchors: list[dict] = []
    headings = doc.get("headings") or []
    for h in headings:
        text = h.get("text") or ""
        anchor = h.get("anchor")
        old_slug = anchor or github_slug(text)
        if anchor:
            base_slug = anchor
            source = "explicit"
        else:
            base_slug = github_slug(text)
            source = "implicit"
        count = seen_counts.get(base_slug, 0)
        if count == 0:
            new_slug = base_slug
        else:
            new_slug = f"{base_slug}-{count}"
        seen_counts[base_slug] = count + 1
        anchors.append({
            "old_text": text,
            "old_slug": old_slug,
            "new_text": text,
            "new_slug": new_slug,
            "source": source,
            "level": h.get("level"),
        })
    return {"algorithm": "github-slug-v1", "anchors": anchors}


def detect_cross_doc_collisions(per_doc: dict[str, dict]) -> dict[str, list[dict]]:
    """Detecta anchors que generan el mismo ``new_slug`` en documentos distintos."""
    index: dict[str, list[dict]] = {}
    for doc_id, payload in per_doc.items():
        for anchor in payload.get("anchors", []):
            slug = anchor.get("new_slug")
            if not slug:
                continue
            index.setdefault(slug, []).append({
                "document_id": doc_id,
                "path": payload.get("path"),
                "new_slug": slug,
            })
    return {slug: entries for slug, entries in index.items() if len(entries) > 1}


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    snapshots = json.loads(Path(args.snapshots).read_text(encoding="utf-8"))
    out_dir = Path(args.out)
    written = 0
    per_doc: dict[str, dict] = {}
    for f in snapshots.get("files", []):
        doc_id = f.get("document_id")
        if not doc_id:
            continue
        payload = {
            "document_id": doc_id,
            "path": f.get("path"),
            **build_anchors_for_doc(f),
        }
        per_doc[doc_id] = payload
        write_atomic(out_dir / f"{doc_id}.json", payload)
        written += 1

    collisions = detect_cross_doc_collisions(per_doc)
    if collisions:
        report = {
            "kind": "cross_doc_collision",
            "total": len(collisions),
            "collisions": [
                {"slug": slug, "documents": entries}
                for slug, entries in collisions.items()
            ],
        }
        write_atomic(out_dir / "_collisions.json", report)
        print(f"warning: {len(collisions)} colisiones cross-doc registradas en _collisions.json", file=sys.stderr)
    else:
        existing = out_dir / "_collisions.json"
        if existing.exists():
            existing.unlink()

    print(f"ok: {written} documentos -> {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())