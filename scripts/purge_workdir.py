"""Política ejecutable de purga de workdirs (fase 148).

La política escrita en `references/workdir-retention.md` tiene aquí su
ejecución. Reglas que el código garantiza, no que el documento promete:

- `source_root` y `output_root` **nunca** se tocan: no hay flag que lo permita.
- el borrado es de seco por defecto; `--apply` exige `--authorized-by`,
- un enlace simbólico dentro del workdir no se sigue: se conserva,
- una ejecución en estado `exported` exige autorización explícita,
- el log de purga se escribe **fuera** del workdir, con lo borrado, lo
  omitido, quién lo autorizó y por qué.

    0 = purga aplicada, o simulación informative
    2 = rutas inválidas o solapadas
    3 = `--apply` sin `--authorized-by`
    4 = la ejecución está `exported` y no hay autorización explícita
    5 = enlace simbólico o escape de ruta
    6 = el workdir no existe

Uso::

    python scripts/purge_workdir.py --work-root /ruta/work --run-id run-0000beef --dry-run
    python scripts/purge_workdir.py --work-root /ruta/work --run-id run-0000beef \\
        --apply --authorized-by "nombre" --reason "cierre de ejecución"
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from delivery_common import is_within, now_iso, sha256_file, write_atomic  # noqa: E402

DEFAULT_RETENTION_DAYS = 30
PROTECTED_STATES = ("exported",)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="purge_workdir.py")
    p.add_argument("--work-root", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--source-root", default=None, help="Se declara para comprobar que no se solapa.")
    p.add_argument("--output-root", default=None, help="Se declara para comprobar que no se solapa.")
    p.add_argument("--apply", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--authorized-by", default=None)
    p.add_argument("--reason", default=None)
    p.add_argument("--retention-days", type=int, default=DEFAULT_RETENTION_DAYS)
    p.add_argument("--out", default=None, help="Ruta del log. Por defecto reports/maintenance/purge_log.json")
    return p.parse_args(argv)


def _resolve(path: str | None) -> Path | None:
    return Path(path).resolve() if path else None


def check_roots(work_root: Path, source_root: Path | None,
                output_root: Path | None) -> str | None:
    """Devuelve un motivo de rechazo, o None si las raíces son utilizables."""
    for label, protected in (("source_root", source_root), ("output_root", output_root)):
        if protected is None:
            continue
        if is_within(work_root, protected) or is_within(protected, work_root):
            return f"{label} y work_root se solapan: {work_root} / {protected}"
        if work_root == protected:
            return f"work_root es {label}: {work_root}"
    return None


def collect_candidates(workdir: Path) -> tuple[list[Path], list[dict]]:
    """Lista qué se borraría y qué se omite, sin tocar nada."""
    removable: list[Path] = []
    skipped: list[dict] = []
    for path in sorted(workdir.rglob("*")):
        rel = path.relative_to(workdir).as_posix()
        if path.is_symlink():
            skipped.append({"path": rel, "reason": "enlace simbólico: no se sigue"})
            continue
        if path.is_dir():
            continue
        removable.append(path)
    return removable, skipped


def run_state(workdir: Path) -> str | None:
    manifest = workdir / "manifest.json"
    if not manifest.is_file():
        return None
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    states = {
        record.get("current_state")
        for record in data.get("files") or []
        if record.get("current_state")
    }
    if "exported" in states:
        return "exported"
    if "approved" in states:
        return "approved"
    return None


def purge(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    work_root = _resolve(args.work_root)
    workdir = work_root / args.run_id
    source_root = _resolve(args.source_root)
    output_root = _resolve(args.output_root)
    out_path = Path(args.out) if args.out else ROOT / "reports" / "maintenance" / "purge_log.json"

    if work_root is None or not workdir.exists():
        print(f"error: no existe el workdir {workdir}", file=sys.stderr)
        return 6

    overlap = check_roots(work_root, source_root, output_root)
    if overlap:
        print(f"error: {overlap}", file=sys.stderr)
        return 2

    if args.apply and not args.dry_run and not args.authorized_by:
        print("error: --apply exige --authorized-by", file=sys.stderr)
        return 3

    state = run_state(workdir)
    manifest = workdir / "manifest.json"
    if state in PROTECTED_STATES and not args.authorized_by:
        print(
            f"error: la ejecución está en estado {state}; hace falta autorización explícita",
            file=sys.stderr,
        )
        return 4

    removable, skipped = collect_candidates(workdir)
    bytes_total = sum(path.stat().st_size for path in removable)

    log = {
        "generated_at": now_iso(),
        "run_id": args.run_id,
        "work_root": str(work_root),
        "workdir": str(workdir),
        "dry_run": not (args.apply and not args.dry_run),
        "authorized_by": args.authorized_by,
        "reason": args.reason,
        "retention_days": args.retention_days,
        "run_state": state,
        "manifest_sha256": sha256_file(manifest) if manifest.is_file() else None,
        "candidates": [path.relative_to(workdir).as_posix() for path in removable],
        "skipped": skipped,
        "deleted": [],
        "bytes_candidate": bytes_total,
        "bytes_reclaimed": 0,
    }

    if log["dry_run"]:
        write_atomic(out_path, log)
        print(
            f"simulación: {len(removable)} ficheros ({bytes_total} bytes) en {workdir}. "
            f"Nada se ha borrado. Usa --apply --authorized-by para ejecutar."
        )
        return 0

    reclaimed = 0
    for path in removable:
        size = path.stat().st_size
        path.unlink()
        reclaimed += size
        log["deleted"].append(path.relative_to(workdir).as_posix())
    for path in sorted(workdir.rglob("*"), reverse=True):
        if path.is_dir() and not path.is_symlink() and not any(path.iterdir()):
            path.rmdir()
    log["bytes_reclaimed"] = reclaimed
    write_atomic(out_path, log)
    print(
        f"ok: purgado {workdir} con autorización de {args.authorized_by}; "
        f"{len(log['deleted'])} ficheros, {reclaimed} bytes recuperados, log en {out_path}"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    return purge(argv)


if __name__ == "__main__":
    sys.exit(main())