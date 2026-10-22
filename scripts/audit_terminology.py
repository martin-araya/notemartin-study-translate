"""Auditoría de terminología entre documentos (fase 045).

Compara las traducciones observadas con el glosario congelado y
reporta:

- ``inconsistency``: la traducción observada no coincide con el
  equivalente preferido ni con ninguna variante permitida.
- ``forbidden_use``: la traducción observada está en
  ``forbidden_forms``.
- ``allowed_use``: la traducción observada está en
  ``allowed_variants``.

El auditor respeta las excepciones declaradas por entrada. No
modifica el glosario ni las traducciones.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

TERM_RE = re.compile(r"\b\w[\w\-]*\w\b|\w", re.UNICODE)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="audit_terminology.py")
    p.add_argument("--translations", required=True)
    p.add_argument("--glossary", required=True)
    p.add_argument("--out", required=True)
    return p.parse_args(argv)


def write_atomic(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def build_glossary_index(glossary: dict) -> dict[str, dict]:
    index: dict[str, dict] = {}
    for entry in glossary.get("entries", []):
        src = entry.get("source_term")
        if not src:
            continue
        key = src.lower()
        index[key] = {
            "preferred": (entry.get("preferred") or {}).get("term", ""),
            "allowed_variants": list(entry.get("allowed_variants") or []),
            "forbidden_forms": list(entry.get("forbidden_forms") or []),
            "domain": entry.get("domain"),
            "sense": entry.get("sense"),
            "entry_id": entry.get("id"),
        }
    return index


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    glossary = json.loads(Path(args.glossary).read_text(encoding="utf-8"))
    glossary_index = build_glossary_index(glossary)

    inconsistencies: list[dict] = []
    forbidden_uses: list[dict] = []
    allowed_uses: list[dict] = []

    for path in sorted(Path(args.translations).glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for entry in data.get("entries", []):
            original = entry.get("original_text") or ""
            translated = entry.get("translated_text") or ""
            for token in TERM_RE.findall(original):
                g = glossary_index.get(token.lower())
                if not g:
                    continue
                pref = g["preferred"].lower()
                allowed = [a.lower() for a in g["allowed_variants"]]
                forbidden = [f.lower() for f in g["forbidden_forms"]]
                translated_tokens = {t.lower() for t in TERM_RE.findall(translated)}
                if pref and pref not in translated_tokens:
                    if any(a in translated_tokens for a in allowed):
                        allowed_uses.append({
                            "path": path.name,
                            "segment_id": entry["segment_id"],
                            "term": token,
                            "variant_used": [a for a in g["allowed_variants"] if a.lower() in translated_tokens][0],
                        })
                        continue
                    inconsistencies.append({
                        "path": path.name,
                        "segment_id": entry["segment_id"],
                        "term": token,
                        "preferred": g["preferred"],
                        "allowed_variants": g["allowed_variants"],
                        "observed": sorted(translated_tokens),
                    })
                for forbidden_term in g["forbidden_forms"]:
                    if forbidden_term.lower() in translated_tokens:
                        forbidden_uses.append({
                            "path": path.name,
                            "segment_id": entry["segment_id"],
                            "term": token,
                            "forbidden_form": forbidden_term,
                        })

    write_atomic(Path(args.out), {
        "translations_dir": str(args.translations),
        "glossary_version": glossary.get("version"),
        "inconsistencies": inconsistencies,
        "forbidden_uses": forbidden_uses,
        "allowed_uses": allowed_uses,
        "summary": {
            "inconsistencies": len(inconsistencies),
            "forbidden_uses": len(forbidden_uses),
            "allowed_uses": len(allowed_uses),
        },
    })
    print(f"ok: inconsistencias={len(inconsistencies)} forbidden={len(forbidden_uses)} allowed={len(allowed_uses)} -> {args.out}")
    return 0 if not forbidden_uses else 1


if __name__ == "__main__":
    sys.exit(main())