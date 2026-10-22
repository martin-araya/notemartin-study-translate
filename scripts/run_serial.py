"""Modo serie (fase 117 del roadmap).

Recorre el orden topológico de ``packet_schedule.json`` y lanza
``scripts/worker.py`` con un único worker llamado ``serial``. Por
cada paquete, vuelca su candidato en el directorio del worker.

Este modo es la **referencia de equivalencia** que el gate 120 usa
para comparar con el modo concurrente (fase 116).

Uso::

    python3 scripts/run_serial.py \\
        --packets reports/exec/packets.json \\
        --schedule reports/exec/packet_schedule.json \\
        --workdir work_root/

Sin ``--schedule``, los paquetes se procesan en su orden de
aparición (modo "free" del planificador).
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="run_serial.py")
    p.add_argument("--packets", required=True)
    p.add_argument("--schedule", default=None)
    p.add_argument("--workdir", required=True)
    p.add_argument("--glossary", default=None)
    p.add_argument("--manifest", default=None)
    return p.parse_args(argv)


def write_atomic(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    packets = json.loads(Path(args.packets).read_text(encoding="utf-8"))
    packet_ids = [p["packet_id"] for p in packets.get("packets", [])]

    if args.schedule:
        schedule = json.loads(Path(args.schedule).read_text(encoding="utf-8"))
        order = schedule.get("order", []) or packet_ids
        # Sólo los packet_id presentes en --packets.
        order = [pid for pid in order if pid in set(packet_ids)]
    else:
        order = packet_ids

    worker_dir = Path(args.workdir) / "workers" / "serial"
    if worker_dir.exists():
        shutil.rmtree(worker_dir)
    worker_dir.mkdir(parents=True, exist_ok=True)
    part_file = worker_dir / "partition.txt"
    part_file.write_text("\n".join(order) + "\n", encoding="utf-8")

    started = datetime.datetime.now(datetime.timezone.utc)
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "worker.py"),
        "--id", "serial",
        "--packets", args.packets,
        "--packet-ids", str(part_file),
        "--out", str(worker_dir),
    ]
    if args.glossary:
        cmd += ["--glossary", args.glossary]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0 and proc.stderr:
        print(proc.stderr, file=sys.stderr)
    finished = datetime.datetime.now(datetime.timezone.utc)

    state = json.loads((worker_dir / "state.json").read_text(encoding="utf-8"))

    # Solo se declaran traducidos los paquetes con contenido real. La lista
    # de paquetes no es una lista de traducciones: contarla como aprobada
    # convertía el modo serie en un generador de informes verdes.
    approved = sorted(
        path.stem
        for path in (worker_dir / "translations").glob("*.json")
        if json.loads(path.read_text(encoding="utf-8")).get("to_state") == "deterministic_pass"
    )
    pending = [pid for pid in order if pid not in set(approved)]

    manifest = {
        "mode": "serial",
        "started_at": started.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "finished_at": finished.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "packet_count": len(order),
        "worker_state": state,
        "packet_ids": order,
        "approved_segment_ids": approved,
        "pending_segment_ids": pending,
        "current_state_distribution": {"approved": len(approved), "pending": len(pending)},
    }
    if args.manifest:
        write_atomic(Path(args.manifest), manifest)

    summary = {
        "ok": proc.returncode == 0,
        "mode": "serial",
        "packet_count": len(order),
        "approved": len(approved),
        "pending_translation": len(pending),
        "worker_status": state.get("status"),
    }
    summary_path = Path(args.workdir) / "serial_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    if proc.returncode != 0:
        return proc.returncode
    print(
        f"ok: serial → {len(order)} paquetes en {worker_dir} "
        f"({len(approved)} traducidos, {len(pending)} pendientes)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
