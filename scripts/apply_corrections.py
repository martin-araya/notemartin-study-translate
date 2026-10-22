"""Aplica correcciones explícitas a entradas de traducción (fase 043).

Recibe un JSON de correcciones con la forma::

    [
      {
        "segment_id": "seg-xxxxxxxx",
        "corrected_text": "...",
        "reason": "..."
      },
      ...
    ]

Por cada corrección, busca el ``segment_id`` en cada archivo de
``translations/`` y reemplaza ``translated_text`` por
``corrected_text``. Las correcciones aplicadas incrementan un
contador en el manifiesto si se proporciona ``--manifest``.

Cada corrección invalida la revisión anterior del segmento. El
reporte marca los segmentos modificados como ``corrections_applied``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="apply_corrections.py")
    p.add_argument("--translations", required=True)
    p.add_argument("--corrections", required=True)
    p.add_argument("--out-translations", required=True)
    p.add_argument("--manifest", help="manifest.json a actualizar (opcional).")
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


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        corrections = json.loads(Path(args.corrections).read_text(encoding="utf-8"))
    except Exception as e:
        print(f"error: JSON de correcciones inválido: {e}", file=sys.stderr)
        return 2
    if not isinstance(corrections, list):
        print("error: el JSON debe ser una lista de correcciones", file=sys.stderr)
        return 2

    corrections_by_id: dict[str, dict] = {c["segment_id"]: c for c in corrections if "segment_id" in c}

    applied: list[dict] = []
    not_found: list[dict] = []

    translations_dir = Path(args.translations)
    out_dir = Path(args.out_translations)

    affected_files: set[str] = set()
    for path in sorted(translations_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            continue
        modified = False
        for entry in data.get("entries", []):
            sid = entry["segment_id"]
            if sid in corrections_by_id:
                entry["translated_text"] = corrections_by_id[sid]["corrected_text"]
                applied.append({"path": path.name, "segment_id": sid, "reason": corrections_by_id[sid].get("reason")})
                modified = True
                affected_files.add(path.name)
        if modified:
            write_atomic(out_dir / path.name, data)

    for sid, c in corrections_by_id.items():
        if not any(a["segment_id"] == sid for a in applied):
            not_found.append({"segment_id": sid, "reason": c.get("reason")})

    if args.manifest:
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        manifest["corrections_applied"] = manifest.get("corrections_applied", 0) + len(applied)
        manifest.setdefault("affected_files", [])
        for f in sorted(affected_files):
            if f not in manifest["affected_files"]:
                manifest["affected_files"].append(f)
        write_atomic(Path(args.manifest), manifest)

    write_atomic(Path(args.report), {
        "applied_count": len(applied),
        "not_found_count": len(not_found),
        "applied": applied,
        "not_found": not_found,
        "affected_files": sorted(affected_files),
    })
    print(f"ok: aplicadas={len(applied)} no_encontradas={len(not_found)} archivos_afectados={len(affected_files)} -> {args.report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())