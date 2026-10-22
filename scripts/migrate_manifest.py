"""Migración de manifiestos `translate/v0` → `translate/v1` (fase 143).

La migración **nunca convierte una revisión antigua en una aprobación
vigente**. Concretamente:

- marca `stale: true` en toda `approval` y `decision` migrada,
- baja cualquier archivo en `approved` o `exported` a `deterministic_pass`
  con la lista de comprobaciones que hay que repetir,
- conserva `state_history` literal y añade la transición de migración,
- deja `created_at` y los hashes de origen intactos.

Códigos de salida:

    0 = migración aplicada (o manifiesto ya vigente y sin cambios)
    2 = entrada inválida (no existe, no es JSON o no parece un manifiesto)
    3 = el manifiesto migrado no valida contra schemas/manifest.schema.json
    4 = el hash de origen no coincide con --expected-source-hash
    5 = versión de manifiesto desconocida (futura o no soportada)
    6 = el manifiesto ya declara translate/v1 y no se pasa --force-revalidate

Uso::

    python scripts/migrate_manifest.py --in work_root/run-0000beef/manifest.json \\
        --dry-run --out /tmp/migrated.json

    python scripts/migrate_manifest.py --in manifest.json --apply \\
        --out manifest.json --authorized-by "nombre"
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from delivery_common import now_iso, sha256_bytes, write_atomic  # noqa: E402

TARGET_VERSION = "translate/v1"
SOURCE_VERSION = "translate/v0"
TOOL_VERSION = "1.0.0"
SCHEMA_PATH = ROOT / "schemas" / "manifest.schema.json"

REVALIDATION = ["hashes", "literals", "structure", "links", "semantic_pass", "export"]
DOWNGRADE_STATES = ("approved", "exported")
FALLBACK_STATE = "deterministic_pass"
STALE_REASON = "manifest_migration"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="migrate_manifest.py")
    p.add_argument("--in", dest="source", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--apply", action="store_true",
                   help="Escribe el resultado. Sin este flag solo informa (equivalente a --dry-run).")
    p.add_argument("--dry-run", action="store_true", help="No escribe nada.")
    p.add_argument("--expected-source-hash", default=None,
                   help="SHA-256 esperado del manifiesto de origen.")
    p.add_argument("--force-revalidate", action="store_true",
                   help="Permite revalidar un manifiesto ya migrado.")
    p.add_argument("--authorized-by", default=None)
    return p.parse_args(argv)


def load_manifest(path: Path) -> dict | None:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) and "files" in data else None


def schema_violations(manifest: dict) -> list[str]:
    try:
        import jsonschema
    except ImportError:  # pragma: no cover
        return []
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    return [
        f"{'/'.join(str(p) for p in err.absolute_path) or '(raíz)'}: {err.message}"
        for err in sorted(validator.iter_errors(manifest), key=lambda e: list(e.absolute_path))
    ]


def migrate(manifest: dict, source_sha256: str, now: str | None = None) -> dict:
    """Devuelve ``(manifiesto_migrado, informe)`` sin tocar la entrada."""
    migrated = copy.deepcopy(manifest)
    report: dict = {
        "from": manifest.get("manifest_version") or SOURCE_VERSION,
        "to": TARGET_VERSION,
        "stale_approvals": [],
        "stale_decisions": [],
        "downgraded_files": [],
        "preserved_history": 0,
        "changed": False,
    }

    migrated["manifest_version"] = TARGET_VERSION
    report["changed"] = True

    for approval in migrated.get("approvals") or []:
        approval["stale"] = True
        approval["stale_reason"] = STALE_REASON
        if approval.get("status") in (None, "valid"):
            approval["status"] = "stale"
        report["stale_approvals"].append(approval.get("approval_id"))

    for decision in migrated.get("decisions") or []:
        decision["stale"] = True
        decision["stale_reason"] = STALE_REASON
        report["stale_decisions"].append(decision.get("decision_id"))

    for record in migrated.get("files") or []:
        history = record.get("state_history") or []
        report["preserved_history"] += len(history)
        if record.get("current_state") in DOWNGRADE_STATES:
            record["current_state"] = FALLBACK_STATE
            record["requires_revalidation"] = list(REVALIDATION)
            stamp = now or now_iso()
            history.append({
                "state": FALLBACK_STATE,
                "timestamp": stamp,
                "reason": STALE_REASON,
            })
            record["state_history"] = history
            record["last_transition_at"] = stamp
            report["downgraded_files"].append(record.get("path"))

    migrations = list(migrated.get("migrations") or [])
    migrations.append({
        "from": report["from"],
        "to": TARGET_VERSION,
        "applied_at": now or now_iso(),
        "tool_version": TOOL_VERSION,
        "source_sha256": source_sha256,
        "reason": STALE_REASON,
    })
    migrated["migrations"] = migrations
    return migrated, report


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source = Path(args.source)
    raw = None
    if source.exists():
        raw = source.read_bytes()

    manifest = load_manifest(source)
    if manifest is None:
        print(f"error: no se puede leer un manifiesto desde {source}", file=sys.stderr)
        return 2

    source_sha = sha256_bytes(raw) if raw is not None else sha256_bytes(b"")
    if args.expected_source_hash and args.expected_source_hash != source_sha:
        print(
            f"error: hash de origen distinto (esperado {args.expected_source_hash}, real {source_sha})",
            file=sys.stderr,
        )
        return 4

    version = manifest.get("manifest_version")
    if version and version != TARGET_VERSION:
        print(f"error: versión de manifiesto no soportada: {version}", file=sys.stderr)
        return 5

    if version == TARGET_VERSION and not args.force_revalidate:
        print(
            f"ok: el manifiesto ya declara {TARGET_VERSION}; usa --force-revalidate para revalidarlo",
        )
        return 6

    migrated, report = migrate(manifest, source_sha)
    violations = schema_violations(migrated)
    if violations:
        print("error: el manifiesto migrado no valida: " + json.dumps(violations, ensure_ascii=False),
              file=sys.stderr)
        return 3

    if args.apply and not args.dry_run:
        if not args.authorized_by:
            print("error: --apply exige --authorized-by", file=sys.stderr)
            return 3
        write_atomic(Path(args.out), migrated)

    print(json.dumps({
        "ok": True,
        "written": bool(args.apply and not args.dry_run),
        "out": str(args.out),
        "source_sha256": source_sha,
        **report,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())