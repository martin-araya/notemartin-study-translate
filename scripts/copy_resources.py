"""Copia recursos locales preservando SHA-256 (fase 046).

Lee ``inventory.json`` y copia los archivos de tipo ``resource`` al
directorio de salida preservando la ruta relativa. Calcula el SHA-256
del original y del archivo copiado. Falla la exportación si un hash
no coincide.

Distingue entre:

- ``copied``: recurso presente y copiado con hash verificado.
- ``hash_mismatch``: recurso copiado con hash diferente.
- ``missing_resource``: recurso referenciado que no existe en
  ``source_root``. Severidad ``critical``.
- ``external_resource``: URL absoluta en lugar de ruta local.
  Severidad ``info``.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

EXTERNAL_RE = re.compile(r"^(https?://|mailto:|[a-z]+://)", re.IGNORECASE)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="copy_resources.py")
    p.add_argument("--inventory", required=True)
    p.add_argument("--source-root", required=True)
    p.add_argument("--output-root", required=True)
    p.add_argument("--report", required=True)
    return p.parse_args(argv)


def write_atomic(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def sha256_bytes(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    inventory = json.loads(Path(args.inventory).read_text(encoding="utf-8"))
    source_root = Path(args.source_root)
    output_root = Path(args.output_root)

    copied: list[dict] = []
    mismatches: list[dict] = []
    missing: list[dict] = []
    external: list[dict] = []

    for entry in inventory.get("files", []):
        if entry.get("type") != "resource":
            continue
        rel = entry["path"]
        if EXTERNAL_RE.match(rel):
            external.append({
                "path": rel,
                "kind": "external_resource",
                "severity": "info",
            })
            continue
        src_path = source_root / rel
        if not src_path.exists():
            missing.append({
                "path": rel,
                "kind": "missing_resource",
                "severity": "critical",
            })
            continue
        original_hash = entry.get("sha256") or sha256_bytes(src_path)
        target_path = output_root / rel
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src_path, target_path)
        copied_hash = sha256_bytes(target_path)
        if copied_hash != original_hash:
            mismatches.append({
                "path": rel,
                "kind": "hash_mismatch",
                "severity": "critical",
                "expected": original_hash,
                "actual": copied_hash,
            })
        else:
            copied.append({
                "path": rel,
                "sha256": copied_hash,
                "bytes": entry.get("bytes"),
            })

    report = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_root": str(source_root),
        "output_root": str(output_root),
        "copied": copied,
        "hash_mismatches": mismatches,
        "missing": missing,
        "external": external,
        "summary": {
            "copied": len(copied),
            "mismatches": len(mismatches),
            "missing": len(missing),
            "external": len(external),
        },
    }
    write_atomic(Path(args.report), report)

    print(
        f"ok: copied={len(copied)} mismatches={len(mismatches)} "
        f"missing={len(missing)} external={len(external)} -> {args.report}"
    )
    return 1 if mismatches or missing else 0


if __name__ == "__main__":
    sys.exit(main())