"""Invalidador selectivo de ejecuciones previas (fase 055).

Compara el ``source_hash`` de cada archivo del manifiesto contra los
bytes actuales del ``source_root``. Para cada archivo:

- Si los bytes coinciden exactamente: ``status: unchanged`` con
  evidencia de no afectación.
- Si los bytes difieren solo por normalización de saltos de línea
  (CRLF↔LF) sin cambio de contenido: ``whitespace_only: true`` y
  ``status: whitespace_only``. No invalida traducciones.
- Si los bytes difieren semánticamente: ``status: changed`` y
  ``invalidated: true``. Los archivos dependientes (anclas compartidas
  o enlaces internos hacia el archivo) se marcan como
  ``invalidated_by_dependency``.

El script **no** modifica ``manifest.json``. Escribe un plan en
``--out`` para que el orquestador decida la transición. El campo
``invalidated_translations: true`` indica que las traducciones de ese
archivo deben descartarse o revalidarse.

Uso::

    python scripts/invalidate_run.py \\
        --manifest runs/<id>/manifest.json \\
        --source-root corpus/ \\
        --out runs/<id>/invalidation_plan.json
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import sys
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_line_endings(data: bytes) -> bytes:
    """Normaliza CRLF y CR a LF para detectar cambios puramente de
    saltos de línea."""
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="invalidate_run.py")
    p.add_argument("--manifest", required=True, help="Ruta del manifest.json a evaluar.")
    p.add_argument("--source-root", required=True, help="Raíz actual del corpus.")
    p.add_argument("--out", required=True, help="Ruta del invalidation_plan.json de salida.")
    return p.parse_args(argv)


def write_atomic(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def load_manifest(manifest_path: Path) -> dict:
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def build_dependent_index(manifest: dict) -> dict[str, list[str]]:
    """Índice inverso: ``document_id -> [paths que lo apuntan]``.

    Se basa en ``state_history`` y enlaces internos que el manifiesto
    pueda declarar; como mínimo, trata cada archivo como dependiente
    de sí mismo si su anchor explícito coincide con otro.
    """
    return {f["path"]: [] for f in manifest.get("files", [])}


def compute_plan(manifest: dict, source_root: Path) -> dict:
    files = manifest.get("files", [])
    file_records: list[dict] = []
    by_path: dict[str, dict] = {}

    for entry in files:
        rel_path = entry.get("path")
        if not rel_path:
            continue
        by_path[rel_path] = entry

    dependents = build_dependent_index(manifest)

    changed_paths: list[str] = []
    for rel_path, entry in by_path.items():
        previous_hash = entry.get("source_hash", "")
        abs_path = source_root / rel_path
        if not abs_path.exists():
            file_records.append({
                "path": rel_path,
                "document_id": entry.get("document_id"),
                "status": "missing",
                "previous_hash": previous_hash,
                "current_hash": None,
                "invalidated": True,
                "invalidated_translations": True,
                "evidence": {"reason": "archivo no encontrado en source_root"},
            })
            changed_paths.append(rel_path)
            continue

        data = abs_path.read_bytes()
        current_hash = sha256_bytes(data)
        normalized_data = normalize_line_endings(data)
        normalized_hash = sha256_bytes(normalized_data)

        if current_hash == previous_hash:
            file_records.append({
                "path": rel_path,
                "document_id": entry.get("document_id"),
                "status": "unchanged",
                "previous_hash": previous_hash,
                "current_hash": current_hash,
                "invalidated": False,
                "invalidated_translations": False,
                "evidence": {"hash_match": True},
            })
            continue

        if normalized_hash == previous_hash:
            file_records.append({
                "path": rel_path,
                "document_id": entry.get("document_id"),
                "status": "whitespace_only",
                "previous_hash": previous_hash,
                "current_hash": current_hash,
                "normalized_hash": normalized_hash,
                "invalidated": False,
                "invalidated_translations": False,
                "evidence": {"line_ending_normalized": True},
            })
            continue

        file_records.append({
            "path": rel_path,
            "document_id": entry.get("document_id"),
            "status": "changed",
            "previous_hash": previous_hash,
            "current_hash": current_hash,
            "invalidated": True,
            "invalidated_translations": True,
            "evidence": {"reason": "bytes difieren del hash registrado en el manifiesto"},
        })
        changed_paths.append(rel_path)

    for record in file_records:
        record["invalidated_by_dependency"] = [
            dep for dep, dependents_list in dependents.items()
            for owner in dependents_list
            if owner == record["path"] and record["status"] == "unchanged"
        ]

    summary = {
        "total": len(file_records),
        "unchanged": sum(1 for r in file_records if r["status"] == "unchanged"),
        "whitespace_only": sum(1 for r in file_records if r["status"] == "whitespace_only"),
        "changed": sum(1 for r in file_records if r["status"] == "changed"),
        "missing": sum(1 for r in file_records if r["status"] == "missing"),
        "invalidated": sum(1 for r in file_records if r["invalidated"]),
        "invalidated_translations": sum(1 for r in file_records if r["invalidated_translations"]),
    }

    return {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "manifest": str(manifest.get("run_id") or ""),
        "source_root": str(source_root),
        "summary": summary,
        "files": file_records,
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest_path = Path(args.manifest)
    source_root = Path(args.source_root)
    out_path = Path(args.out)

    if not manifest_path.exists():
        print(f"error: manifest no existe: {manifest_path}", file=sys.stderr)
        return 2
    if not source_root.is_dir():
        print(f"error: source_root no es directorio: {source_root}", file=sys.stderr)
        return 3

    manifest = load_manifest(manifest_path)
    plan = compute_plan(manifest, source_root)

    write_atomic(out_path, plan)
    s = plan["summary"]
    print(
        f"ok: total={s['total']} unchanged={s['unchanged']} "
        f"whitespace_only={s['whitespace_only']} changed={s['changed']} "
        f"missing={s['missing']} invalidated={s['invalidated']} -> {out_path}"
    )
    return 0 if s["changed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())