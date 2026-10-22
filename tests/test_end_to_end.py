"""Pruebas para scripts/run_end_to_end.py (fase 049)."""

from __future__ import annotations

import json
import tempfile
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUN_E2E = ROOT / "scripts" / "run_end_to_end.py"
PILOT = ROOT / "tests" / "fixtures" / "pilot"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def test_pipeline_ejecuta_sin_errores() -> None:
    out = TMP / "e2e_out1"
    proc = run([
        str(RUN_E2E),
        "--source-root", str(PILOT),
        "--output-dir", str(out),
        "--run-id", "run-e2e-1",
    ])
    assert (out / "run-e2e-1" / "END_TO_END_REPORT.md").exists()


def test_pipeline_genera_reporte_con_hashes() -> None:
    out = TMP / "e2e_out2"
    run([
        str(RUN_E2E),
        "--source-root", str(PILOT),
        "--output-dir", str(out),
        "--run-id", "run-e2e-2",
    ])
    report = (out / "run-e2e-2" / "END_TO_END_REPORT.md").read_text(encoding="utf-8")
    assert "SHA-256" in report
    assert "Pasos del pipeline" in report


def test_el_recorrido_declara_que_no_traduce() -> None:
    """El recorrido usa identidad. Si su informe no lo dice, alguien puede
    leer un informe verde como si fuera una traducción."""
    out = TMP / "e2e_out3"
    run([
        str(RUN_E2E),
        "--source-root", str(PILOT),
        "--output-dir", str(out),
        "--run-id", "run-e2e-3",
    ])
    report = (out / "run-e2e-3" / "END_TO_END_REPORT.md").read_text(encoding="utf-8")
    assert "identidad" in report
    assert "No es una traducción" in report


def test_el_manifiesto_que_crea_no_inventa_procedencia() -> None:
    out = TMP / "e2e_out4"
    run([
        str(RUN_E2E),
        "--source-root", str(PILOT),
        "--output-dir", str(out),
        "--run-id", "run-e2e-4",
    ])
    manifest = json.loads((out / "run-e2e-4" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["run_id"] == "run-e2e-4"
    for record in manifest["files"]:
        for transition in record["state_history"]:
            assert not transition["timestamp"].startswith("2026-10-19"), "timestamp fabricated"
    assert manifest["glossary_snapshot"]["hash"] != "x"
    assert manifest["profile_snapshot"]["hash"] != "x"
    import re

    assert re.fullmatch(r"[0-9a-f]{64}", manifest["glossary_snapshot"]["hash"])
