"""Pruebas para scripts/detect_language.py (fase 021)."""

from __future__ import annotations

import tempfile
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INVENTORY = ROOT / "scripts" / "inventory.py"
PREPARE = ROOT / "scripts" / "prepare.py"
DETECT = ROOT / "scripts" / "detect_language.py"
PILOT = ROOT / "tests" / "fixtures" / "pilot"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def prepare_classified() -> dict:
    inv = TMP / "inv.json"
    seg = TMP / "segments.json"
    classified = TMP / "classified.json"
    assert run([str(INVENTORY), "--source", str(PILOT), "--out", str(inv)]).returncode == 0
    assert run([str(PREPARE), "--inventory", str(inv), "--segments", str(seg)]).returncode == 0
    assert run([str(DETECT), "--segments", str(seg), "--out", str(classified)]).returncode == 0
    return json.loads(classified.read_text(encoding="utf-8"))


def doc(payload: dict, name: str) -> dict:
    for f in payload["files"]:
        if f["path"] == name:
            return f
    raise AssertionError(f"no se encontró {name}")


def test_segmentos_tienen_language_y_disposition() -> None:
    payload = prepare_classified()
    for f in payload["files"]:
        for s in f["segments"]:
            assert "language" in s
            assert "disposition" in s
            assert s["language"] in {"es", "en", "code", "empty", "unknown", "other", "mixed"}
            assert s["disposition"] in {
                "already_target", "translatable", "code_skip",
                "no_text", "too_short", "mixed_or_code", "unknown",
            }


def test_archivo_mdn_es_already_target() -> None:
    payload = prepare_classified()
    d = doc(payload, "developer-mozilla_Guides_Cascading_variables_Using_custom_properties.md")
    assert d["file_disposition"] == "already_target"
    es_count = sum(1 for s in d["segments"] if s["language"] == "es")
    assert es_count > 0


def test_archivo_typescript_no_es_español() -> None:
    payload = prepare_classified()
    d = doc(payload, "typescriptlang_handbook_2_basic-types.md")
    assert d["file_disposition"] == "translatable"
    for s in d["segments"]:
        if s["disposition"] != "code_skip" and s["disposition"] != "no_text":
            assert s["language"] != "es", f"typescr segment no debe ser es: {s}"


def test_archivo_mixto_no_se_clasifica_completamente() -> None:
    """El archivo OpenRouter 01 tiene títulos en español y cuerpo en inglés.

    Su disposición global debe ser 'mixed' o 'translatable'; nunca
    'already_target' porque contiene prosa traducible.
    """
    payload = prepare_classified()
    d = doc(payload, "APIs_OpenRouter_01_-_Introducción,_Autenticación_y_Formato_General.md")
    assert d["file_disposition"] in {"mixed", "translatable"}
    assert d["file_disposition"] != "already_target"


def test_texto_corto_marcado_unknown() -> None:
    payload = prepare_classified()
    found = False
    for f in payload["files"]:
        for s in f["segments"]:
            if s["disposition"] == "too_short":
                found = True
                assert s["language"] == "unknown"
    assert found, "se esperaba al menos un segmento demasiado corto"


def test_code_fenced_no_se_intenta_clasificar() -> None:
    payload = prepare_classified()
    for f in payload["files"]:
        for s in f["segments"]:
            if s["structural_type"] == "code_fenced":
                assert s["language"] == "code"
                assert s["disposition"] == "code_skip"
