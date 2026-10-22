"""Validador de candidatos de traducción (fase 034).

Comprueba que cada ``translations/<doc_id>.json`` cumple las reglas:

- IDs ajenos: ningún ``segment_id`` fuera de los esperados.
- Segmentos ausentes: todo segmento traducible tiene entrada.
- Marcadores extra: ``translated_text`` no contiene ``§§``.
- Respuestas truncadas: ``translated_text`` no es 0 bytes.
- Negación perdida: si el original contiene `` not ``, el traducido
  contiene `` no `` (case-insensitive).

Salida: JSON con ``{document_id, valid, errors: [...]}`` por candidato.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="validate_translations.py")
    p.add_argument("--translations", required=True)
    p.add_argument("--segments", required=True)
    p.add_argument("--out", required=True)
    return p.parse_args(argv)


def write_atomic(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def validate_doc(candidate: dict, expected_ids: set[str]) -> dict:
    errors: list[str] = []
    entries = candidate.get("entries") or []
    seen_ids = set()
    for e in entries:
        sid = e.get("segment_id")
        if sid not in expected_ids:
            errors.append(f"ID ajeno: {sid}")
        if sid in seen_ids:
            errors.append(f"ID duplicado: {sid}")
        seen_ids.add(sid)
        translated = e.get("translated_text") or ""
        if "§§" in translated:
            errors.append(f"marcador extra en {sid}")
        if not translated.strip():
            errors.append(f"respuesta truncada en {sid}")
        original = (e.get("original_text") or "").lower()
        translated_lower = translated.lower()
        if " not " in original and " no " not in translated_lower:
            errors.append(f"negación perdida en {sid}")
    missing = expected_ids - seen_ids
    for sid in sorted(missing):
        errors.append(f"segmento ausente: {sid}")
    return {
        "document_id": candidate.get("document_id"),
        "path": candidate.get("path"),
        "valid": not errors,
        "errors": errors,
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    translations_dir = Path(args.translations)
    segments_doc = json.loads(Path(args.segments).read_text(encoding="utf-8"))
    by_doc: dict[str, set[str]] = {}
    skipped_dispositions = {"code_skip", "no_text", "too_short", "mixed_or_code"}
    for f in segments_doc.get("files", []):
        doc_id = f["document_id"]
        expected = set()
        for s in f.get("segments", []):
            if s.get("disposition") not in skipped_dispositions:
                expected.add(s["segment_id"])
        by_doc[doc_id] = expected

    results: list[dict] = []
    for path in sorted(translations_dir.glob("*.json")):
        try:
            candidate = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            results.append({
                "document_id": path.stem,
                "valid": False,
                "errors": [f"JSON ilegible: {e}"],
            })
            continue
        doc_id = candidate.get("document_id", path.stem)
        expected_ids = by_doc.get(doc_id, set())
        results.append(validate_doc(candidate, expected_ids))

    write_atomic(Path(args.out), {
        "translations_dir": str(translations_dir),
        "results": results,
        "total_valid": sum(1 for r in results if r["valid"]),
        "total_invalid": sum(1 for r in results if not r["valid"]),
    })
    print(f"ok: {len(results)} candidatos -> {args.out}")
    return 0 if all(r["valid"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())