"""Reescribe referencias internas justificadas (fase 039).

Lee ``anchors.json`` por documento y reescribe las referencias
``[texto](#slug_local)`` o ``[texto](./ruta.md)`` cuyo slug cambia.

- Las URLs externas (``http://``, ``https://``, ``mailto:``) no se
  tocan.
- Las referencias ambiguas o sin destino se reportan, no se
  reescriben.
- El archivo reescrito se escribe atómicamente en ``output-dir``.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
EXTERNAL_RE = re.compile(r"^(https?://|mailto:|/[^/])", re.IGNORECASE)
UNSAFE_SCHEMES = ("javascript:", "data:", "file:", "vbscript:", "about:")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="rewrite_references.py")
    p.add_argument("--source", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--anchors", required=True)
    p.add_argument("--report", required=True)
    return p.parse_args(argv)


def write_atomic(target: Path, payload) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    if isinstance(payload, bytes):
        tmp.write_bytes(payload)
    elif isinstance(payload, str):
        tmp.write_text(payload, encoding="utf-8")
    else:
        tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def rewrite_markdown(text: str, anchor_map: dict[str, str], doc_id: str = "") -> tuple[str, list[dict]]:
    findings: list[dict] = []
    rewritten = LINK_RE.sub(
        lambda m: _replace(m, anchor_map, findings, doc_id),
        text,
    )
    return rewritten, findings


def _replace(match: re.Match, anchor_map: dict[str, str], findings: list[dict], doc_id: str = "") -> str:
    text = match.group(1)
    target = match.group(2)
    lower = target.lower()
    for scheme in UNSAFE_SCHEMES:
        if lower.startswith(scheme):
            findings.append({"kind": "unsafe_scheme", "document_id": doc_id, "target": target, "scheme": scheme})
            return match.group(0)
    if EXTERNAL_RE.match(target):
        return match.group(0)
    if target.startswith("#"):
        old_slug = target[1:].split("#", 1)[0]
        if old_slug in anchor_map:
            new_slug = anchor_map[old_slug]
            if new_slug != old_slug:
                return f"[{text}](#{new_slug})"
        else:
            findings.append({"kind": "unresolved", "document_id": doc_id, "target": target})
        return match.group(0)
    return match.group(0)


def collect_anchor_lookup(anchors_dir: Path) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for path in anchors_dir.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for a in data.get("anchors", []):
            old = a.get("old_slug") or a.get("new_slug")
            new = a.get("new_slug")
            if old and new and old != new:
                lookup[old] = new
    return lookup


def collect_per_document(anchors_dir: Path) -> dict[str, dict[str, str]]:
    per_doc: dict[str, dict[str, str]] = {}
    for path in anchors_dir.glob("*.json"):
        if path.name.startswith("_"):
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        doc_id = data.get("document_id") or path.stem
        per_doc[doc_id] = {}
        for a in data.get("anchors", []):
            old = a.get("old_slug") or a.get("new_slug")
            new = a.get("new_slug")
            if old and new:
                per_doc[doc_id][old] = new
    return per_doc


def find_ambiguous(per_doc: dict[str, dict[str, str]]) -> dict[str, list[str]]:
    """Detecta anchors presentes en más de un documento. No reescribe."""
    index: dict[str, list[str]] = {}
    for doc_id, mapping in per_doc.items():
        for old in mapping:
            index.setdefault(old, []).append(doc_id)
    return {old: docs for old, docs in index.items() if len(docs) > 1}


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source_dir = Path(args.source)
    output_dir = Path(args.output_dir)
    anchors_dir = Path(args.anchors)
    report_path = Path(args.report)

    lookup = collect_anchor_lookup(anchors_dir)
    per_doc = collect_per_document(anchors_dir)
    ambiguous = find_ambiguous(per_doc)
    report = {
        "files": [],
        "rewritten_total": 0,
        "unresolved_total": 0,
        "unsafe_scheme_total": 0,
        "ambiguous_total": 0,
        "ambiguous_slugs": ambiguous,
    }

    for source_file in sorted(source_dir.glob("*.md")):
        text = source_file.read_text(encoding="utf-8")
        rewritten, findings = rewrite_markdown(text, lookup, doc_id=source_file.stem)
        write_atomic(output_dir / source_file.name, rewritten.encode("utf-8"))
        report["files"].append({
            "path": source_file.name,
            "unchanged": rewritten == text,
            "unresolved": [f for f in findings if f["kind"] == "unresolved"],
            "unsafe_scheme": [f for f in findings if f["kind"] == "unsafe_scheme"],
        })
        report["rewritten_total"] += sum(1 for _ in LINK_RE.finditer(text)) - sum(
            1 for _ in LINK_RE.finditer(rewritten)
        )
        report["unresolved_total"] += len([f for f in findings if f["kind"] == "unresolved"])
        report["unsafe_scheme_total"] += len([f for f in findings if f["kind"] == "unsafe_scheme"])

    report["ambiguous_total"] = len(ambiguous)
    if ambiguous:
        print(f"warning: {len(ambiguous)} anchors ambiguos no se reescriben", file=sys.stderr)

    write_atomic(report_path, report)
    print(
        f"ok: reescritos={report['rewritten_total']} "
        f"unresolved={report['unresolved_total']} -> {report_path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())