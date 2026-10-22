"""Worker CLI (fase 113 del roadmap).

Esqueleto ejecutable que toma una partición de paquetes, escribe
candidatos vacíos (el contenido lo rellenaría el agente en un
sistema real) y respeta el aislamiento de manifests.

El worker no modifica el ``manifest.json`` central; solo escribe
en ``work_root/workers/<worker_id>/``. El coordinador (fase 114)
reconcilia los resultados.

Uso::

    python3 scripts/worker.py \\
        --id W1 \\
        --packets reports/exec/packets.json \\
        --packet-ids work_root/parts/W1.txt \\
        --out work_root/workers/W1/ \\
        --glossary evals/glossary.json
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="worker.py")
    p.add_argument("--id", required=True, help="Identificador del worker (W1, W2, ...).")
    p.add_argument("--packets", required=True, help="JSON de packetize.py con todos los paquetes.")
    p.add_argument(
        "--packet-ids",
        required=True,
        help="Archivo con un packet_id por línea, indicando la partición del worker.",
    )
    p.add_argument("--out", required=True, help="Directorio de salida del worker.")
    p.add_argument("--glossary", default=None, help="Glosario congelado (solo lectura).")
    p.add_argument(
        "--content-dir",
        default=None,
        help="Directorio con la traducción real del agente, un <packet_id>.json por "
             "paquete. Sin este directorio el worker emite candidatos pendientes: "
             "un esqueleto vacío nunca cuenta como traducción.",
    )
    return p.parse_args(argv)


def load_packet_ids(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def sha256_file(path: Path | None) -> str | None:
    if path is None or not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_atomic(target: Path, payload: dict | str) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, dict):
        text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    else:
        text = payload
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, target)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    out_dir = Path(args.out)
    translations = out_dir / "translations"
    translations.mkdir(parents=True, exist_ok=True)

    packets_path = Path(args.packets)
    if not packets_path.exists():
        print(f"error: --packets no existe: {packets_path}", file=sys.stderr)
        return 2
    payload = json.loads(packets_path.read_text(encoding="utf-8"))
    packets_by_id = {p["packet_id"]: p for p in payload.get("packets", [])}

    partition_path = Path(args.packet_ids)
    partition = load_packet_ids(partition_path)

    unknown = [pid for pid in partition if pid not in packets_by_id]
    if unknown:
        print(f"error: packet_ids no presentes en --packets: {unknown}", file=sys.stderr)
        return 1

    glossary_path = Path(args.glossary) if args.glossary else None
    glossary_hash_at_start = sha256_file(glossary_path)
    content_dir = Path(args.content_dir) if args.content_dir else None

    started = datetime.datetime.now(datetime.timezone.utc)
    errors = 0
    delivered = 0
    for pid in partition:
        pkt = packets_by_id[pid]
        content = None
        content_hash = None
        if content_dir is not None:
            candidate_path = content_dir / f"{pid}.json"
            if candidate_path.exists():
                raw = candidate_path.read_bytes()
                content = json.loads(raw.decode("utf-8"))
                content_hash = hashlib.sha256(raw).hexdigest()
                delivered += 1

        # Sin contenido real el candidato queda pendiente y no propone
        # transición: un esqueleto que se declara `deterministic_pass`
        # convierte el pipeline en un generador de informes verdes.
        candidate = {
            "kind": "candidate",
            "worker_id": args.id,
            "packet_id": pid,
            "content": content,
            "from_state": "translated",
            "to_state": "deterministic_pass" if content is not None else None,
            "status": "translated" if content is not None else "pending_translation",
            "evidence": {
                "dispatched_at": started.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "glossary_hash_at_start": glossary_hash_at_start,
                "marker_count": (pkt.get("translatable_text_with_markers") or "").count("§§"),
                "content_sha256": content_hash,
            },
            "router_note": (
                "Esqueleto del worker: el contenido debe rellenarlo la traducción "
                "asistida. Mantener el orden de los packet_id y no salir del scope."
            ),
        }
        write_atomic(translations / f"{pid}.json", candidate)

    # Verificar que el glosario no se modificó durante el trabajo.
    glossary_hash_at_end = sha256_file(glossary_path)
    if glossary_path and glossary_hash_at_start != glossary_hash_at_end:
        errors += 1
        with (out_dir / "errors.jsonl").open("a", encoding="utf-8") as fp:
            fp.write(
                json.dumps(
                    {
                        "worker_id": args.id,
                        "error": "glossary_hash_changed",
                        "before": glossary_hash_at_start,
                        "after": glossary_hash_at_end,
                        "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

    finished = datetime.datetime.now(datetime.timezone.utc)
    state = {
        "worker_id": args.id,
        "started_at": started.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "finished_at": finished.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "packet_count": len(partition),
        "translated_count": delivered,
        "pending_translation": len(partition) - delivered,
        "errors": errors,
        "glossary_hash_at_start": glossary_hash_at_start,
        "glossary_hash_at_end": glossary_hash_at_end,
        "status": "failed" if errors else ("done" if delivered == len(partition) else "pending_translation"),
    }
    write_atomic(out_dir / "state.json", state)
    print(
        f"ok: worker {args.id} → {len(partition)} candidatos en {translations} "
        f"({delivered} traducidos, {len(partition) - delivered} pendientes)"
    )
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
