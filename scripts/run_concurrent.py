"""Modo concurrente (fase 116 del roadmap).

Lanza ``scripts/worker.py`` en ``ThreadPoolExecutor`` con
particiones disjuntas del ``packet_schedule.json`` (si se
proporciona) o del ``packets.json``. Si el sistema tiene un solo
procesador, rechaza el modo y recomienda el serie.

Uso::

    python3 scripts/run_concurrent.py \\
        --packets reports/exec/packets.json \\
        --schedule reports/exec/packet_schedule.json \\
        --max-workers 4 \\
        --workdir work_root/

El orquestador ``--manifest`` opcional vuelca un resumen final
con el modo (``concurrent``), el número de hilos, los
``approved_segment_ids`` y la lista de hilos.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import shutil
import signal
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="run_concurrent.py")
    p.add_argument("--packets", required=True)
    p.add_argument("--schedule", default=None)
    p.add_argument("--max-workers", dest="max_workers", type=int, default=None)
    p.add_argument("--workdir", required=True)
    p.add_argument("--glossary", default=None)
    p.add_argument("--manifest", default=None)
    p.add_argument(
        "--content-dir",
        default=None,
        help="Directorio con la traducción real del agente, un <packet_id>.json por "
             "paquete. Se propaga a cada worker: sin él, los workers solo emiten "
             "candidatos pendientes y nada puede aprobarse.",
    )
    p.add_argument(
        "--allow-single-cpu",
        dest="allow_single_cpu",
        action="store_true",
        help="No rechazar cuando cpu_count == 1 (útil en CI).",
    )
    return p.parse_args(argv)


def write_atomic(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def _split_packet_ids(order: list[str], n: int) -> list[list[str]]:
    if n < 1:
        n = 1
    buckets: list[list[str]] = [[] for _ in range(n)]
    for i, pid in enumerate(order):
        buckets[i % n].append(pid)
    return [b for b in buckets if b]


def _log_event(log_path: Path, event: str, payload: dict | None = None) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(
        {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "event": event,
            **(payload or {}),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    with open(log_path, "a", encoding="utf-8") as fp:
        fp.write(line + "\n")


def _read_worker_state(worker_dir: Path) -> dict:
    """Estado final del worker. Un worker que no escribió estado no aprobó nada."""
    path = worker_dir / "state.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _translated_packet_ids(worker_dir: Path) -> list[str]:
    """Paquetes con traducción real entregada por ese worker.

    Se lee de los candidatos escritos por el worker, no de la partición que
    se le asignó: contar la partición entera como aprobada convertía una
    ejecución sin traducciones en un manifiesto con todos los segmentos
    aprobados, y el gate de escala comparaba ese número con el del modo
    serie y daba por buena una cobertura inexistente.
    """
    delivered: list[str] = []
    translations = worker_dir / "translations"
    if not translations.is_dir():
        return delivered
    for candidate in sorted(translations.glob("*.json")):
        try:
            payload = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if payload.get("content") is None:
            continue
        if payload.get("status") != "translated":
            continue
        pid = payload.get("packet_id")
        if pid:
            delivered.append(pid)
    return delivered


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    packets_payload = json.loads(Path(args.packets).read_text(encoding="utf-8"))
    packet_ids = [p["packet_id"] for p in packets_payload.get("packets", [])]

    if args.schedule:
        schedule = json.loads(Path(args.schedule).read_text(encoding="utf-8"))
        order = schedule.get("order", []) or packet_ids
        order = [pid for pid in order if pid in set(packet_ids)]
    else:
        order = packet_ids

    cpu = os.cpu_count() or 1
    if cpu <= 1 and not args.allow_single_cpu:
        print("error: cpu_count == 1; usa run_serial.py", file=sys.stderr)
        return 2

    if args.max_workers:
        max_workers = max(1, args.max_workers)
    else:
        max_workers = min(8, cpu)

    workdir = Path(args.workdir)
    if (workdir / "workers").exists():
        shutil.rmtree(workdir / "workers")
    (workdir / "workers").mkdir(parents=True, exist_ok=True)

    log_path = workdir / "concurrency_log.json"
    log_path.unlink(missing_ok=True)

    partitions = _split_packet_ids(order, max_workers)
    log_payload: dict = {
        "mode": "concurrent",
        "max_workers": max_workers,
        "cpu_count": cpu,
        "partition_sizes": [len(p) for p in partitions],
        "started_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    _log_event(log_path, "started", log_payload)

    interrupt_event = threading.Event()
    interrupted = {"flag": False}

    def handler(signum, frame):  # noqa: ARG001
        interrupted["flag"] = True
        interrupt_event.set()

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)

    def run_one(partition: list[str], worker_id: str) -> int:
        if interrupt_event.is_set():
            _log_event(log_path, "interrupted_before_next_packet", {"worker_id": worker_id})
            return 130
        worker_dir = workdir / "workers" / worker_id
        worker_dir.mkdir(parents=True, exist_ok=True)
        (worker_dir / "partition.txt").write_text(
            "\n".join(partition) + "\n", encoding="utf-8"
        )
        cmd = [
            sys.executable,
            str(ROOT / "scripts" / "worker.py"),
            "--id", worker_id,
            "--packets", args.packets,
            "--packet-ids", str(worker_dir / "partition.txt"),
            "--out", str(worker_dir),
        ]
        if args.glossary:
            cmd += ["--glossary", args.glossary]
        if args.content_dir:
            cmd += ["--content-dir", args.content_dir]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        _log_event(log_path, "worker_finished", {
            "worker_id": worker_id,
            "returncode": proc.returncode,
            "packet_count": len(partition),
        })
        return proc.returncode

    approved: list[str] = []
    pending: list[str] = []
    worker_errors: list[str] = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {
            ex.submit(run_one, partition, f"W{i+1}"): (f"W{i+1}", partition)
            for i, partition in enumerate(partitions)
        }
        for fut, (worker_id, partition) in futures.items():
            try:
                rc = fut.result(timeout=300)
            except Exception as e:  # noqa: BLE001
                _log_event(log_path, "worker_error", {"error": str(e)})
                rc = 1
            worker_dir = workdir / "workers" / worker_id
            state = _read_worker_state(worker_dir)
            if rc != 0 or state.get("status") == "failed":
                worker_errors.append(worker_id)
            if not interrupt_event.is_set():
                delivered = _translated_packet_ids(worker_dir)
                approved.extend(delivered)
                pending.extend(pid for pid in partition if pid not in delivered)
            if interrupt_event.is_set():
                break

    approved.sort()
    pending.sort()
    finished = datetime.datetime.now(datetime.timezone.utc)
    manifest_payload = {
        "mode": "concurrent",
        "max_workers": max_workers,
        "cpu_count": cpu,
        "started_at": log_payload["started_at"],
        "finished_at": finished.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "packet_count": len(approved) + len(pending),
        "approved_count": len(approved),
        "pending_count": len(pending),
        "approved_segment_ids": approved,
        "pending_segment_ids": pending,
        "current_state_distribution": {
            "approved": len(approved),
            "pending_translation": len(pending),
        },
        "worker_errors": worker_errors,
        "interrupted": interrupted["flag"],
    }
    if args.manifest:
        write_atomic(Path(args.manifest), manifest_payload)
    summary = workdir / "concurrent_summary.json"
    summary.write_text(
        json.dumps(
            {
                **log_payload,
                "approved": len(approved),
                "pending": len(pending),
                "worker_errors": worker_errors,
                "interrupted": interrupted["flag"],
            },
            indent=2, ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )

    if interrupted["flag"]:
        _log_event(log_path, "graceful_shutdown", {"approved": len(approved)})
        return 130
    print(
        f"ok: concurrent → {len(approved)} paquetes traducidos, "
        f"{len(pending)} pendientes, {max_workers} hilos"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
