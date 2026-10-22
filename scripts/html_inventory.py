"""Inventario de patrones HTML (fase 071).

Escanea un corpus HTML y cuenta etiquetas, atributos y hallazgos
inseguros. Sin ejecutar nada: solo regex y conteo.

Uso::

    python scripts/html_inventory.py --root tests/fixtures/html \\
        --out /tmp/inventory.json

Devuelve JSON con ``tag_counts``, ``attribute_counts`` y
``unsafe_findings`` (scripts, iframes, eventos on*).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

HTML_TAG_RE = re.compile(r"<([A-Za-z][A-Za-z0-9_-]*)([^>]*)>", re.DOTALL)
ATTR_NAME_RE = re.compile(r"\b([A-Za-z_:][A-Za-z0-9_.:-]*)\s*=")
SCRIPT_RE = re.compile(r"<script\b", re.IGNORECASE)
IFRAME_RE = re.compile(r"<iframe\b", re.IGNORECASE)
STYLE_RE = re.compile(r"<style\b", re.IGNORECASE)
EVENT_RE = re.compile(r"\son[a-z]+\s*=", re.IGNORECASE)
OBJECT_RE = re.compile(r"<(object|embed)\b", re.IGNORECASE)


def scan_text(text: str) -> dict:
    tag_counter: Counter = Counter()
    attr_counter: Counter = Counter()
    findings: list[dict] = []

    for m in HTML_TAG_RE.finditer(text):
        tag = m.group(1).lower()
        tag_counter[tag] += 1
        for a in ATTR_NAME_RE.finditer(m.group(2)):
            attr_counter[a.group(1).lower()] += 1

    for m in SCRIPT_RE.finditer(text):
        findings.append({"kind": "unsafe_script", "start": m.start(), "end": m.end(), "value": m.group(0)})
    for m in IFRAME_RE.finditer(text):
        findings.append({"kind": "unsafe_iframe", "start": m.start(), "end": m.end(), "value": m.group(0)})
    for m in STYLE_RE.finditer(text):
        findings.append({"kind": "unsafe_style", "start": m.start(), "end": m.end(), "value": m.group(0)})
    for m in OBJECT_RE.finditer(text):
        findings.append({"kind": "unsafe_object", "start": m.start(), "end": m.end(), "value": m.group(0)})
    for m in EVENT_RE.finditer(text):
        findings.append({"kind": "unsafe_event_handler", "start": m.start(), "end": m.end(), "value": m.group(0)})

    return {
        "tag_counts": dict(tag_counter),
        "attribute_counts": dict(attr_counter),
        "unsafe_findings": findings,
    }


def write_atomic(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="html_inventory.py")
    p.add_argument("--root", required=True)
    p.add_argument("--out", required=True)
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root)
    out_path = Path(args.out)

    files = sorted(root.rglob("*.md")) if root.is_dir() else [root]
    aggregate = {
        "files": [],
        "tag_counts": {},
        "attribute_counts": {},
        "unsafe_findings": [],
    }
    tag_total: Counter = Counter()
    attr_total: Counter = Counter()

    for f in files:
        text = f.read_text(encoding="utf-8")
        result = scan_text(text)
        aggregate["files"].append({
            "path": str(f.relative_to(root)) if root.is_dir() else str(f),
            "tag_counts": result["tag_counts"],
            "attribute_counts": result["attribute_counts"],
            "unsafe_findings": result["unsafe_findings"],
        })
        for k, v in result["tag_counts"].items():
            tag_total[k] += v
        for k, v in result["attribute_counts"].items():
            attr_total[k] += v
        aggregate["unsafe_findings"].extend(result["unsafe_findings"])

    aggregate["tag_counts"] = dict(tag_total)
    aggregate["attribute_counts"] = dict(attr_total)
    aggregate["summary"] = {
        "files": len(aggregate["files"]),
        "unsafe_total": len(aggregate["unsafe_findings"]),
        "tags_total": sum(tag_total.values()),
        "attributes_total": sum(attr_total.values()),
    }
    write_atomic(out_path, aggregate)
    print(
        f"ok: files={aggregate['summary']['files']} "
        f"tags={aggregate['summary']['tags_total']} "
        f"unsafe={aggregate['summary']['unsafe_total']} -> {out_path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())