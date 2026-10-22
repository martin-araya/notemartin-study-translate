"""Agrupa segmentos en paquetes respetando el presupuesto del perfil.

Lee el perfil para obtener ``context_budget`` y aplica las mismas
reglas que ``scripts/packetize.py``, pero con el presupuesto del
perfil en lugar del default. Si un segmento excede individualmente el
presupuesto, se marca como ``overflow: true`` y se emite en un
paquete propio.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import subprocess
import sys
from pathlib import Path


def load_context_budget(profile_path: Path) -> int:
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    return int(profile.get("context_budget", 8000))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="build_packets.py")
    p.add_argument("--segments", required=True)
    p.add_argument("--profile", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--markers", default="§§")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    budget = load_context_budget(Path(args.profile))

    packetize_script = Path(__file__).resolve().parent / "packetize.py"
    cmd = [
        sys.executable,
        str(packetize_script),
        "--segments", args.segments,
        "--out", args.out,
        "--context-budget", str(budget),
        "--markers", args.markers,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    sys.stdout.write(proc.stdout)
    sys.stderr.write(proc.stderr)
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())