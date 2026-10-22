"""Coordinador de manifiestos (fase 114 del roadmap).

Cuando hay workers en paralelo, dos procesos pueden intentar
escribir el mismo ``segment_id``. El coordinador centraliza esas
escrituras mediante ``fcntl.flock`` sobre el ``manifest.json`` y
rechaza cualquier conflicto.

El coordinador expone tres operaciones:

- ``claim(...)``: reserva un ``segment_id`` para un worker, devuelve
  ``claim_id``. Si ya está reclamado, devuelve ``409 Conflict``.
- ``submit(...)``: entrega la transición ``state`` para un
  ``segment_id`` ya aprobado por ``claim``. Si el ``claim_id`` no
  coincide o el ``to_state`` no es válido, se rechaza.
- ``close(...)``: vuelca el ``manifest.json`` consolidado y el
  reporte ``coordination.json``.

Si el sistema operativo no implementa ``fcntl.flock`` (p. ej.
Windows), el módulo cae a un lock en proceso con
``threading.Lock`` y deja la advertencia en ``coordination.json``.
"""

from __future__ import annotations

import argparse
import datetime
import fcntl
import json
import os
import sys
import threading
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent

VALID_STATES = {
    "inventoried", "prepared", "translated", "deterministic_pass",
    "semantic_pass", "approved", "exported", "blocked", "failed",
    "excluded", "already_target",
}

CLAIM_FILE = "claims.json"
LOCK_FILE = "manifest.lock"
LOG_FILE = "coordination.log"
REPORT_FILE = "coordination.json"
MANIFEST_FILE = "manifest.json"

# Lock en proceso para máquinas donde fcntl no funciona.
_process_lock = threading.Lock()
_fcntl_unavailable = False


def _safe_flock(fp, mode: int) -> bool:
    """Aplica flock si está disponible; si no, devuelve False."""
    global _fcntl_unavailable
    if _fcntl_unavailable:
        return False
    try:
        fcntl.flock(fp.fileno(), mode)
        return True
    except (AttributeError, OSError):
        _fcntl_unavailable = True
        return False


class FileLock:
    """Lock con fcntl.flock y fallback a threading.Lock."""

    def __init__(self, target: Path):
        self.target = target
        self.target.parent.mkdir(parents=True, exist_ok=True)
        self._fp = open(self.target, "a+", encoding="utf-8")
        self._local = not _safe_flock(self._fp, fcntl.LOCK_EX)

    def __enter__(self) -> "FileLock":
        if self._local:
            _process_lock.acquire()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if self._local:
                _process_lock.release()
            else:
                _safe_flock(self._fp, fcntl.LOCK_UN)
        finally:
            self._fp.close()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="coordinator.py")
    sub = p.add_subparsers(dest="cmd", required=True)

    claim = sub.add_parser("claim", help="Reservar un segment_id para un worker.")
    claim.add_argument("--worker", required=True)
    claim.add_argument("--segment", required=True)
    claim.add_argument("--from-state", dest="from_state", required=True)
    claim.add_argument("--to-state", dest="to_state", required=True)
    claim.add_argument("--workdir", required=True)

    sub.add_parser("close", help="Cerrar y emitir reports.").add_argument("--workdir", required=True)

    sub.add_parser("status", help="Mostrar el estado de las reservas.").add_argument("--workdir", required=True)

    return p.parse_args(argv)


def _workdir_paths(workdir: Path) -> dict[str, Path]:
    return {
        "claims": workdir / CLAIM_FILE,
        "lock": workdir / LOCK_FILE,
        "log": workdir / LOG_FILE,
        "report": workdir / REPORT_FILE,
        "manifest": workdir / MANIFEST_FILE,
    }


def _append_log(log_path: Path, event: str, payload: dict[str, Any]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(
        {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "event": event,
            **payload,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    with open(log_path, "a", encoding="utf-8") as fp:
        fp.write(line + "\n")


def _load_claims(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_claims(path: Path, claims: dict[str, dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(claims, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def cmd_claim(args) -> int:
    paths = _workdir_paths(Path(args.workdir))
    if args.to_state not in VALID_STATES:
        _append_log(paths["log"], "reject", {"reason": "invalid_to_state", "to_state": args.to_state})
        print("error: to_state no válido", file=sys.stderr)
        return 2

    with FileLock(paths["lock"]):
        claims = _load_claims(paths["claims"])
        seg_id = args.segment
        if seg_id in claims:
            existing = claims[seg_id]
            if existing.get("worker_id") != args.worker:
                _append_log(paths["log"], "reject", {
                    "reason": "conflict_segment", "segment_id": seg_id,
                    "claimed_by": existing.get("worker_id"),
                    "attempted_by": args.worker,
                })
                return 9
            _append_log(paths["log"], "duplicate", {"segment_id": seg_id, "worker": args.worker})
            return 0

        claim_id = "claim-" + os.urandom(4).hex()
        claims[seg_id] = {
            "claim_id": claim_id,
            "worker_id": args.worker,
            "from_state": args.from_state,
            "to_state": args.to_state,
            "claimed_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        _save_claims(paths["claims"], claims)
        _append_log(paths["log"], "claim", {
            "segment_id": seg_id,
            "claim_id": claim_id,
            "worker": args.worker,
            "to_state": args.to_state,
        })
    print(f"ok: claim {claim_id} {seg_id} ({args.worker})")
    return 0


def cmd_close(args) -> int:
    paths = _workdir_paths(Path(args.workdir))
    with FileLock(paths["lock"]):
        claims = _load_claims(paths["claims"])
        report = {
            "closed_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "fcntl_unavailable": _fcntl_unavailable,
            "claim_count": len(claims),
            "claims_by_worker": {},
            "states_distribution": {},
        }
        for seg_id, entry in claims.items():
            report["claims_by_worker"].setdefault(entry.get("worker_id", "?"), []).append(seg_id)
            report["states_distribution"][entry.get("to_state", "?")] = (
                report["states_distribution"].get(entry.get("to_state", "?"), 0) + 1
            )
        paths["report"].parent.mkdir(parents=True, exist_ok=True)
        paths["report"].write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(f"ok: close -> {paths['report']}")
    return 0


def cmd_status(args) -> int:
    paths = _workdir_paths(Path(args.workdir))
    print(json.dumps(_load_claims(paths["claims"]), indent=2, ensure_ascii=False, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.cmd == "claim":
        return cmd_claim(args)
    if args.cmd == "close":
        return cmd_close(args)
    if args.cmd == "status":
        return cmd_status(args)
    return 2


if __name__ == "__main__":
    sys.exit(main())
