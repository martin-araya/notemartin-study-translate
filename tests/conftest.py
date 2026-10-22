"""Configuración compartida de la suite.

Crea el directorio temporal de trabajo antes de que corra ninguna prueba.
Su ruta se calcula con ``tempfile.gettempdir()`` para que la suite no
dependa del sistema operativo donde se ejecuta (fase 147).
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

WORK_DIR_NAME = "nst-tests"

# La suite importa módulos de scripts/ y tests/ directamente. Sin esta
# bandera, cada ejecución deja __pycache__ dentro del paquete y
# check_distribution.py lo marca como artefacto prohibido (fase 147).
sys.dont_write_bytecode = True


def work_dir() -> Path:
    target = Path(tempfile.gettempdir()) / WORK_DIR_NAME
    target.mkdir(parents=True, exist_ok=True)
    return target


def pytest_configure(config) -> None:  # noqa: D401 - firma de pytest
    """ Garantiza que el directorio temporal compartido existe."""
    work_dir()