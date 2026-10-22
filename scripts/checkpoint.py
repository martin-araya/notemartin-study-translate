"""Guarda y restaura el estado de la ejecución con escritura atómica.

Funciones públicas:

- ``save(state, work_root)``: escribe ``work_root/<run_id>/checkpoints/checkpoint-<ts>.json`` con ``os.replace``. Devuelve la ruta.
- ``load(work_root, run_id)``: lee el checkpoint más reciente. Si la lectura falla por JSON inválido, devuelve ``None``.
- ``list_checkpoints(work_root, run_id)``: lista los checkpoints en orden cronológico.

El estado guarda las claves de procedencia declaradas en C-RUN:
``run_id``, ``created_at``, ``last_segment_id``, ``files_state``,
``glossary_snapshot``, ``profile_snapshot``, ``parser``,
``prompt_version``.

Una interrupción tras ``os.replace`` deja el archivo completo. Una
interrupción antes del rename deja el archivo previo intacto (no
truncado válido).
"""

from __future__ import annotations

import datetime
import json
import os
from pathlib import Path


def checkpoints_dir(work_root: Path, run_id: str) -> Path:
    return work_root / run_id / "checkpoints"


def save(state: dict, work_root: Path) -> Path:
    run_id = state.get("run_id", "run-unknown")
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out_dir = checkpoints_dir(work_root, run_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"checkpoint-{ts}.json"
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)
    return target


def load(work_root: Path, run_id: str) -> dict | None:
    paths = list_checkpoints(work_root, run_id)
    for path in reversed(paths):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
    return None


def list_checkpoints(work_root: Path, run_id: str) -> list[Path]:
    out_dir = checkpoints_dir(work_root, run_id)
    if not out_dir.is_dir():
        return []
    return sorted(out_dir.glob("checkpoint-*.json"))


def parse_args(argv: list[str] | None = None):
    import argparse
    p = argparse.ArgumentParser(prog="checkpoint.py")
    sub = p.add_subparsers(dest="cmd", required=True)
    save_p = sub.add_parser("save")
    save_p.add_argument("--state", required=True)
    save_p.add_argument("--work-root", required=True)
    load_p = sub.add_parser("load")
    load_p.add_argument("--work-root", required=True)
    load_p.add_argument("--run-id", required=True)
    load_p.add_argument("--out")
    list_p = sub.add_parser("list")
    list_p.add_argument("--work-root", required=True)
    list_p.add_argument("--run-id", required=True)
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    import sys
    args = parse_args(argv)
    if args.cmd == "save":
        state = json.loads(Path(args.state).read_text(encoding="utf-8"))
        path = save(state, Path(args.work_root))
        print(f"ok: checkpoint guardado en {path}")
        return 0
    if args.cmd == "load":
        state = load(Path(args.work_root), args.run_id)
        if state is None:
            print(f"error: no hay checkpoint válido en {args.work_root}/{args.run_id}/checkpoints", file=sys.stderr)
            return 1
        if args.out:
            Path(args.out).write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        else:
            print(json.dumps(state, indent=2, ensure_ascii=False))
        return 0
    if args.cmd == "list":
        paths = list_checkpoints(Path(args.work_root), args.run_id)
        for p in paths:
            print(p)
        return 0
    return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())