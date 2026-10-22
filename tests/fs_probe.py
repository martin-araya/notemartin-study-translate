"""Helpers para detectar comportamiento del sistema de archivos."""

from __future__ import annotations

import os
import sys
import tempfile
import unicodedata
from pathlib import Path


def filesystem_is_case_insensitive() -> bool:
    """Detecta si el FS trata como iguales nombres con distinta capitalización."""
    with tempfile.TemporaryDirectory() as d:
        upper = Path(d) / "ProbeUpper"
        lower = Path(d) / "probeupper"
        try:
            upper.write_text("u")
            lower.write_text("l")
        except OSError:
            return True
        return not upper.exists() or not lower.exists() or upper.samefile(lower)


def filesystem_normalizes_unicode() -> bool:
    """Detecta si el FS normaliza NFD/NFC al comparar nombres."""
    with tempfile.TemporaryDirectory() as d:
        nfc = Path(d) / "café.txt"
        nfd_name = unicodedata.normalize("NFD", "café") + ".txt"
        nfd = Path(d) / nfd_name
        try:
            nfc.write_text("nfc")
            nfd.write_text("nfd")
        except OSError:
            return True
        try:
            return nfc.samefile(nfd)
        except OSError:
            return True