"""Medición de tiempos del núcleo (fase 111 del roadmap).

Ejecuta la cadena determinista del núcleo (inventario → preparación
→ detección de idioma → paquetería) sobre un corpus autorizado y
vuelca un perfil de ejecución en JSON.

Regla fundamental (AGENTS.md §1, INV-01): ningún token ni costo se
inventa. ``tokens_estimated`` y ``cost_estimated_usd`` son siempre
``null`` a menos que el proveedor los exponga. ``provider_known``
queda en ``false`` salvo que el operador lo declare con
``--provider``.

Para evitar ejecuciones de horas en CI, el script admite
``--sample N`` que extrae un subconjunto aleatorio reproducible del
corpus. El subconjunto se documenta en el campo ``sample`` del JSON
resultante.

Uso::

    python3 scripts/measure_execution.py \\
        --corpus tests/fixtures/scale \\
        --pair en-es \\
        --out reports/execution_profile.json
"""

from __future__ import annotations

import tempfile
import argparse
import datetime
import hashlib
import json
import os
import platform
import random
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="measure_execution.py")
    p.add_argument("--corpus", required=True, help="Carpeta del corpus a medir.")
    p.add_argument("--pair", required="en-es", help="Par de idioma origen-destino.")
    p.add_argument("--recognized", default="en")
    p.add_argument("--out", required=True, help="Ruta del archivo JSON a generar.")
    p.add_argument("--sample", type=int, default=None,
                   help="Cantidad de archivos a muestrear (CI-friendly).")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument(
        "--provider",
        default=None,
        help="Identificador del proveedor; sin declararlo, provider_known queda en false.",
    )
    return p.parse_args(argv)


def write_atomic(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def sample_corpus(corpus: Path, n: int, seed: int) -> tuple[Path, dict]:
    """Devuelve un directorio temporal con N archivos muestreados.

    El muestreo se mantiene determinista por la semilla.
    """
    md_files = sorted([p for p in corpus.rglob("*.md") if p.is_file()])
    if not md_files:
        raise SystemExit(f"--corpus no contiene archivos .md: {corpus}")
    rng = random.Random(seed)
    if n >= len(md_files):
        chosen = md_files
        sample_meta = {
            "files_sampled": len(chosen),
            "total_files": len(md_files),
            "reason": "sample>=total",
            "seed": seed,
        }
    else:
        chosen = rng.sample(md_files, n)
        sample_meta = {
            "files_sampled": n,
            "total_files": len(md_files),
            "reason": "sample<N para CI; ver evals/cases/corpus-full.md",
            "seed": seed,
        }
    target = Path(tempfile.gettempdir()) / "nst-tests" / f"sample-{corpus.name}-{seed}-{n}"
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    for src in chosen:
        rel = src.relative_to(corpus)
        dest = target / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    return target, sample_meta


def run_module(args: list[str]) -> tuple[subprocess.CompletedProcess, float]:
    t0 = time.monotonic()
    cp = subprocess.run(
        [sys.executable, *args],
        capture_output=True, text=True, check=False,
        cwd=str(ROOT),
    )
    return cp, time.monotonic() - t0


def _fingerprint_runtime() -> dict:
    return {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "python": platform.python_version(),
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source = Path(args.corpus).resolve()
    if not source.is_dir():
        print(f"error: --corpus no existe o no es directorio: {source}", file=sys.stderr)
        return 2

    sample_meta = None
    if args.sample is not None:
        source, sample_meta = sample_corpus(source, args.sample, args.seed)

    started = datetime.datetime.now(datetime.timezone.utc)
    step_durations: dict[str, float] = {}

    inv_path = Path("/tmp") / "inv-scale.json"
    seg_path = Path("/tmp") / "seg-scale.json"
    classified_path = Path("/tmp") / "classified-scale.json"
    packets_path = Path("/tmp") / "packets-scale.json"

    _cp, dt = run_module(["scripts/inventory.py", "--source", str(source), "--out", str(inv_path)])
    step_durations["inventory"] = dt
    _cp, dt = run_module(["scripts/prepare.py", "--inventory", str(inv_path), "--segments", str(seg_path)])
    step_durations["prepare"] = dt
    _cp, dt = run_module(
        ["scripts/detect_language.py", "--segments", str(seg_path),
         "--out", str(classified_path), "--recognized", args.recognized]
    )
    step_durations["detect_language"] = dt
    _cp, dt = run_module(
        ["scripts/packetize.py", "--segments", str(classified_path), "--out", str(packets_path)]
    )
    step_durations["packetize"] = dt

    finished = datetime.datetime.now(datetime.timezone.utc)
    duration_sec = (finished - started).total_seconds()

    files_inv = json.loads(inv_path.read_text(encoding="utf-8"))
    files_list = files_inv.get("files", files_inv.get("entries", []))
    files_list = [f for f in files_list if isinstance(f, dict)]
    total_files = len(files_list)
    total_bytes = sum(f.get("size", f.get("bytes", 0)) for f in files_list)

    classified = json.loads(classified_path.read_text(encoding="utf-8"))
    packets = json.loads(packets_path.read_text(encoding="utf-8"))

    total_segments = sum(len(f["segments"]) for f in classified.get("files", []))
    translatable = sum(
        1
        for f in classified.get("files", [])
        for s in f.get("segments", [])
        if s.get("disposition") == "translatable"
    )

    metrics = {
        "files": total_files,
        "bytes": total_bytes,
        "segments": total_segments,
        "translatable_prose_segments": translatable,
        "packets": len(packets.get("packets", [])),
        "segments_per_sec": round(total_segments / duration_sec, 4) if duration_sec else 0.0,
        "bytes_per_sec": round(total_bytes / duration_sec, 4) if duration_sec else 0.0,
        "step_durations_sec": {k: round(v, 4) for k, v in step_durations.items()},
    }

    payload = {
        "pair": args.pair,
        "corpus_root": str(source),
        "started_at": started.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "finished_at": finished.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duration_sec": round(duration_sec, 4),
        "metrics": metrics,
        "provider_known": bool(args.provider),
        "cost_unknown": True,
        "tokens_estimated": None,
        "cost_estimated_usd": None,
        "sample": sample_meta,
        "host": _fingerprint_runtime(),
        "notes": (
            "Perfil de ejecución del núcleo. Los costos del proveedor son null por "
            "política (AGENTS.md §1). Active --provider con un valor conocido para "
            "registrarlo en futuras pasadas; los costos siguen siendo null hasta que "
            "el proveedor los exponga."
        ),
    }
    write_atomic(Path(args.out), payload)
    print(f"ok: execution_profile ({total_files} files, "
          f"{total_segments} segmentos, {len(packets.get('packets', []))} paquetes, "
          f"{duration_sec:.2f}s) -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
