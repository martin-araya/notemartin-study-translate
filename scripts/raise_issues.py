"""Consolida dudas y problemas en reports/issues.json (fase 044).

Recorre ``translations/<doc_id>.json`` y registra hallazgos que
requieren decisión humana:

- ``flag_loss``: pérdida real de literales protegidos.
- Identidad sospechosa: ``translated_text == original_text`` cuando
  el segmento está marcado como ``translatable``.
- Pérdida de negación: ya validada por ``validate_translations.py``,
  re-registrada como issue.
- Ambigüedad y solicitudes de aclaración detectadas por reglas
  ligeras.

El script no corrige contenido técnico por sí mismo. Solo registra
lo que el usuario debe decidir.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path

NEG_RE = re.compile(r"\bnot\b", re.IGNORECASE)
NEG_ES_RE = re.compile(r"\bno\b", re.IGNORECASE)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="raise_issues.py")
    p.add_argument("--translations", required=True)
    p.add_argument("--segments", required=True)
    p.add_argument("--issues-out", default="reports/issues.json")
    p.add_argument("--report", help="Reporte adicional (opcional).")
    return p.parse_args(argv)


def write_atomic(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    translations_dir = Path(args.translations)
    segments_doc = json.loads(Path(args.segments).read_text(encoding="utf-8"))
    by_doc: dict[str, dict[str, str]] = {}
    for f in segments_doc.get("files", []):
        for seg in f.get("segments", []):
            by_doc[seg["segment_id"]] = {
                "disposition": seg.get("disposition"),
                "translatable_text": seg.get("translatable_text") or "",
            }

    issues: list[dict] = []
    for path in sorted(translations_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            issues.append({
                "category": "technical",
                "severity": "critical",
                "status": "open",
                "path": path.name,
                "message": f"JSON ilegible: {e}",
            })
            continue
        doc_id = data.get("document_id", path.stem)
        for entry in data.get("entries", []):
            sid = entry["segment_id"]
            seg = by_doc.get(sid, {})
            disposition = seg.get("disposition")
            original = entry.get("original_text") or ""
            translated = entry.get("translated_text") or ""

            if entry.get("flag_loss") or entry.get("missing_literals"):
                issues.append({
                    "category": "technical",
                    "severity": "critical",
                    "status": "open",
                    "path": data.get("path", path.name),
                    "segment_id": sid,
                    "message": f"literales perdidos: {entry.get('missing_literals')}",
                })

            if disposition == "translatable" and translated.strip() == original.strip():
                issues.append({
                    "category": "ambiguous",
                    "severity": "info",
                    "status": "open",
                    "path": data.get("path", path.name),
                    "segment_id": sid,
                    "message": "traducción idéntica al original; confirmar si es intencional",
                })

            if NEG_RE.search(original) and not NEG_ES_RE.search(translated):
                issues.append({
                    "category": "clarification_needed",
                    "severity": "major",
                    "status": "open",
                    "path": data.get("path", path.name),
                    "segment_id": sid,
                    "message": "negación del original no aparece en el candidato",
                })

    payload = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "translations_dir": str(translations_dir),
        "total_issues": len(issues),
        "by_severity": {
            "critical": sum(1 for i in issues if i["severity"] == "critical"),
            "major": sum(1 for i in issues if i["severity"] == "major"),
            "info": sum(1 for i in issues if i["severity"] == "info"),
        },
        "issues": issues,
    }

    write_atomic(Path(args.issues_out), payload)

    if args.report:
        write_atomic(Path(args.report), {
            "issues_path": str(args.issues_out),
            **payload,
        })

    critical = payload["by_severity"]["critical"]
    print(f"ok: {len(issues)} issues (critical={critical}) -> {args.issues_out}")
    return 0 if critical == 0 else 1


if __name__ == "__main__":
    sys.exit(main())