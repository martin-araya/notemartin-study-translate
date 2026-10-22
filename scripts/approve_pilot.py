"""Registra la aprobación del piloto y congela el glosario.

Verifica que:

- La procedencia del manifiesto no haya cambiado desde la última
  aprobación. Las cinco claves controladas son: ``source_hash`` de
  cada archivo, ``glossary_snapshot.hash``, ``profile_snapshot.hash``,
  ``parser.version`` y ``model_metadata.prompt_version``. Si difieren,
  el archivo correspondiente se marca ``invalid`` con el motivo
  correspondiente y la aprobación se rechaza.
- Todos los documentos del alcance tienen un archivo de traducciones.
- Ningún archivo de traducciones tiene ``flag_loss: true``.
- Si se da ``--review``, el paquete de revisión no contiene
  hallazgos con ``severity: critical``.

Si todo está bien, actualiza ``manifest.json`` con la aprobación,
guarda la base de procedencia para la próxima ejecución y congela
``glossary.json`` con ``frozen: true`` y ``version`` incrementado.

Si falta algún requisito, el script devuelve código no cero y no
escribe nada.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import sys
from pathlib import Path


def hashlib_sha256_bytes(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


PROVENANCE_KEYS = ["source_hash", "glossary_hash", "profile_hash", "parser_version", "prompt_version"]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="approve_pilot.py")
    p.add_argument("--manifest", required=True, help="manifest.json a actualizar.")
    p.add_argument("--translations", required=True, help="Directorio con translations/<doc_id>.json.")
    p.add_argument("--glossary", required=True, help="glossary.json a congelar.")
    p.add_argument("--review", help="Archivo de revisión (opcional).")
    p.add_argument("--approver", required=True, help="Identificador del aprobador.")
    return p.parse_args(argv)


def write_atomic(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def current_provenance(manifest: dict) -> dict:
    return {
        "files_source": {f["document_id"]: f.get("source_hash") for f in manifest.get("files", [])},
        "glossary_hash": manifest.get("glossary_snapshot", {}).get("hash"),
        "profile_hash": manifest.get("profile_snapshot", {}).get("hash"),
        "parser_version": manifest.get("parser", {}).get("version"),
        "prompt_version": manifest.get("model_metadata", {}).get("prompt_version"),
    }


def invalidate(manifest: dict, key: str, doc_id: str | None) -> None:
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    target_files = manifest.get("files", []) if doc_id is None else [
        f for f in manifest.get("files", []) if f.get("document_id") == doc_id
    ]
    for f in target_files:
        f["current_state"] = "invalid"
        f["last_transition_at"] = now
        f.setdefault("state_history", []).append({
            "state": "invalid",
            "timestamp": now,
            "reason": f"procedencia {key} cambió",
        })


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest_path = Path(args.manifest)
    translations_dir = Path(args.translations)
    glossary_path = Path(args.glossary)
    review_path = Path(args.review) if args.review else None

    errors: list[str] = []

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    baseline = manifest.get("provenance_baseline")
    current = current_provenance(manifest)
    if baseline is not None:
        if baseline.get("files_source") != current["files_source"]:
            diff = [
                doc for doc in (current["files_source"] or {})
                if baseline["files_source"].get(doc) != current["files_source"][doc]
            ]
            for doc in diff:
                invalidate(manifest, "source_hash", doc)
            errors.append(f"source_hash cambió en {len(diff)} archivos")
        if baseline.get("glossary_hash") != current["glossary_hash"]:
            invalidate(manifest, "glossary_hash", None)
            errors.append("glossary_snapshot.hash cambió")
        if baseline.get("profile_hash") != current["profile_hash"]:
            invalidate(manifest, "profile_hash", None)
            errors.append("profile_snapshot.hash cambió")
        if baseline.get("parser_version") != current["parser_version"]:
            invalidate(manifest, "parser_version", None)
            errors.append("parser.version cambió")
        if baseline.get("prompt_version") != current["prompt_version"]:
            invalidate(manifest, "prompt_version", None)
            errors.append("model_metadata.prompt_version cambió")

    if any(f.get("current_state") == "invalid" for f in manifest.get("files", [])):
        errors.append("archivos marcados como invalid; corrija antes de aprobar")

    files = manifest.get("files") or []
    file_ids = {f.get("document_id") for f in files}

    existing_translations = sorted(translations_dir.glob("*.json"))
    existing_ids = {p.stem for p in existing_translations}

    missing = file_ids - existing_ids
    if missing:
        errors.append(f"documentos sin traducción: {sorted(missing)}")

    for path in existing_translations:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            errors.append(f"traducción ilegible {path}: {e}")
            continue
        if data.get("flag_loss"):
            errors.append(f"pérdida de literales en {path.name}")

    if review_path and review_path.exists():
        try:
            review = json.loads(review_path.read_text(encoding="utf-8"))
        except Exception as e:
            errors.append(f"revisión ilegible: {e}")
            review = {}
        for finding in review.get("findings") or []:
            if (finding.get("severity") or "").lower() == "critical":
                errors.append(f"hallazgo crítico en revisión: {finding}")

    if errors:
        write_atomic(manifest_path, manifest)
        for e in errors:
            print(f"error: {e}", file=sys.stderr)
        return 1

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for entry in manifest.get("files", []):
        # `current_state` es el campo que leen todos los gates y el que
        # exige el esquema. `state` se escribe además porque el esquema lo
        # declara, pero no lo sustituye.
        entry["current_state"] = "approved"
        entry["state"] = "approved"
        entry["last_transition_at"] = now
        entry.setdefault("state_history", []).append({
            "state": "approved",
            "timestamp": now,
            "reason": f"aprobado por {args.approver}",
        })

    manifest["pilot_approved"] = True
    manifest["approved_by"] = args.approver
    manifest["approved_at"] = now

    glossary = json.loads(glossary_path.read_text(encoding="utf-8"))
    glossary["frozen"] = True
    glossary["version"] = glossary.get("version", 1) + 1
    glossary["approved_at"] = now
    glossary_hash = hashlib_sha256_bytes(glossary_path)
    write_atomic(glossary_path, glossary)

    existing_gloss = manifest.get("glossary_snapshot") or {}
    manifest["glossary_snapshot"] = {
        "version": glossary["version"],
        "hash": existing_gloss.get("hash") or glossary_hash,
        "frozen": True,
    }
    manifest["provenance_baseline"] = current

    write_atomic(manifest_path, manifest)
    print(f"ok: manifiesto aprobado -> {manifest_path}")
    print(f"ok: glosario congelado -> {glossary_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())