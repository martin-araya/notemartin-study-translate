"""Toda herramienta de `scripts/` debe responder a `--help`.

Una herramienta que revienta al pedirle su propia ayuda no es una
herramienta que alguien pueda seguir en un procedimiento documentado.
`gate_scale.py` fallaba por un `%` sin escapar en un `help=` de argparse:
`ValueError: unsupported format character ')'`. Ninguna prueba lo cubría
porque ninguna invocaba `--help` sobre el conjunto completo de scripts.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"


def _tools() -> list[Path]:
    return sorted(p for p in SCRIPTS.glob("*.py") if p.name != "__init__.py")


def test_hay_herramientas_que_auditar() -> None:
    assert len(_tools()) > 50, "la lista de scripts parece vacía o rota"


def test_toda_herramienta_responde_a_help() -> None:
    fallos: list[str] = []
    for path in _tools():
        proc = subprocess.run(
            [sys.executable, str(path), "--help"],
            capture_output=True, text=True, check=False, timeout=60,
        )
        if proc.returncode != 0:
            ultimo = (proc.stderr or proc.stdout).strip().splitlines()
            fallos.append(f"{path.name}: rc={proc.returncode} {ultimo[-1] if ultimo else ''}")
    assert not fallos, "herramientas que no responden a --help:\n" + "\n".join(fallos)


def test_toda_herramienta_tiene_uso_o_ayuda() -> None:
    """Sin argumentos, una herramienta indica cómo usarse y sale con código 2."""
    sin_uso: list[str] = []
    for path in _tools():
        proc = subprocess.run(
            [sys.executable, str(path)],
            capture_output=True, text=True, check=False, timeout=60,
        )
        salida = (proc.stdout + proc.stderr).lower()
        if proc.returncode not in (0, 1, 2):
            continue
        if proc.returncode == 2 and not any(
            token in salida for token in ("uso", "usage", "required", "obligatorio", "error")
        ):
            sin_uso.append(path.name)
    assert not sin_uso, "herramientas que fallan sin explicar el uso:\n" + "\n".join(sin_uso)