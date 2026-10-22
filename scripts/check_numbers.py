"""Detecta cambios numéricos entre originales y traducidos (fase 037).

Compara ``original_text`` y ``translated_text`` por segmento. Marca:

- ``numeric_change``: cuando un número, unidad o intervalo cambia
  entre original y traducción (no por reordenamiento).
- ``safe_reorder``: cuando los tokens están en distinto orden pero son
  los mismos. Coherente con la regla de fidelidad semántica, no léxica.

Salida: JSON con ``{document_id, segment_id, numeric_change, safe_reorder, details}`` por candidato.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

NUM_RE = re.compile(r"\b\d+(?:[.,]\d+)?\b")
UNIT_RE = re.compile(r"\b\d+(?:[.,]\d+)?\s?(?:px|em|rem|ms|s|mb|kb|gb|°c|°f|kg|cm|mm|%)\b", re.IGNORECASE)
RANGE_RE = re.compile(r"[<>]=?\s*\d+(?:[.,]\d+)?")
TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="check_numbers.py")
    p.add_argument("--translations", required=True)
    p.add_argument("--segments", required=True)
    p.add_argument("--out", required=True)
    return p.parse_args(argv)


def write_atomic(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def extract_numbers(text: str) -> list[str]:
    return NUM_RE.findall(text)


def extract_units(text: str) -> list[str]:
    return UNIT_RE.findall(text)


def extract_ranges(text: str) -> list[str]:
    return RANGE_RE.findall(text)


def token_set(text: str) -> set[str]:
    return set(TOKEN_RE.findall(text.lower()))


def compare_segment(original: str, translated: str) -> dict:
    original_nums = extract_numbers(original)
    translated_nums = extract_numbers(translated)
    original_units = extract_units(original)
    translated_units = extract_units(translated)
    original_ranges = extract_ranges(original)
    translated_ranges = extract_ranges(translated)
    original_token_set = token_set(original)
    translated_token_set = token_set(translated)

    numeric_change = (
        sorted(original_nums) != sorted(translated_nums)
        or sorted(original_units) != sorted(translated_units)
        or sorted(original_ranges) != sorted(translated_ranges)
    )

    safe_reorder = (
        original_token_set == translated_token_set
        and not numeric_change
    )

    details: list[str] = []
    if sorted(original_nums) != sorted(translated_nums):
        details.append(f"números: {original_nums} → {translated_nums}")
    if sorted(original_units) != sorted(translated_units):
        details.append(f"unidades: {original_units} → {translated_units}")
    if sorted(original_ranges) != sorted(translated_ranges):
        details.append(f"rangos: {original_ranges} → {translated_ranges}")
    if safe_reorder:
        details.append("reordenamiento léxico sin cambio semántico")

    return {
        "numeric_change": numeric_change,
        "safe_reorder": safe_reorder,
        "details": details,
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    translations_dir = Path(args.translations)
    segments_doc = json.loads(Path(args.segments).read_text(encoding="utf-8"))

    by_doc: dict[str, str] = {}
    for f in segments_doc.get("files", []):
        for seg in f.get("segments", []):
            by_doc[seg["segment_id"]] = seg.get("translatable_text") or ""

    reports: list[dict] = []
    for path in sorted(translations_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            reports.append({
                "document_id": path.stem,
                "valid": False,
                "errors": [f"JSON ilegible: {e}"],
            })
            continue
        per_segment = []
        for entry in data.get("entries", []):
            sid = entry["segment_id"]
            original = by_doc.get(sid, entry.get("original_text", ""))
            translated = entry.get("translated_text", "") or ""
            cmp = compare_segment(original, translated)
            cmp["segment_id"] = sid
            per_segment.append(cmp)
        reports.append({
            "document_id": data.get("document_id", path.stem),
            "path": data.get("path"),
            "numeric_changes": sum(1 for c in per_segment if c["numeric_change"]),
            "safe_reorders": sum(1 for c in per_segment if c["safe_reorder"]),
            "per_segment": per_segment,
        })

    write_atomic(Path(args.out), {
        "translations_dir": str(translations_dir),
        "reports": reports,
        "total_numeric_changes": sum(r["numeric_changes"] for r in reports),
        "total_safe_reorders": sum(r["safe_reorders"] for r in reports),
    })
    print(f"ok: {len(reports)} documentos -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())