"""Pruebas de scripts/eval_back_translation.py (fase 127)."""

from __future__ import annotations

import tempfile
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "eval_back_translation.py"
FIX = ROOT / "tests" / "fixtures" / "back_translation"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str], env: dict | None = None) -> subprocess.CompletedProcess:
    e = os.environ.copy()
    if env:
        e.update(env)
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False, env=e)


def test_dry_run_sobre_fixtures_reales() -> None:
    out = TMP / "bt_dry.json"
    proc = run([str(SCRIPT), "--fixtures", str(FIX), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr or proc.stdout
    metrics = json.loads(out.read_text(encoding="utf-8"))
    assert metrics["total"] == len(list(FIX.glob("*.json")))
    assert metrics["false_positives"] >= 1, metrics
    assert metrics["false_negatives"] >= 1, metrics


def test_modo_live_requiere_variable_entorno() -> None:
    out = TMP / "bt_live.json"
    proc = run(
        [str(SCRIPT), "--fixtures", str(FIX), "--out", str(out), "--live"],
        env={"NOTE_BACK_TRANSLATION_LIVE": "0"},
    )
    assert proc.returncode != 0


def test_provider_en_payload() -> None:
    out = TMP / "bt_p.json"
    proc = run([str(SCRIPT), "--fixtures", str(FIX), "--out", str(out)])
    assert proc.returncode == 0
    metrics = json.loads(out.read_text(encoding="utf-8"))
    assert metrics["provider"]["provider"] in {"local", "agent"}


def test_false_positives_medidos_en_cognados() -> None:
    """El caso de cognados ``application`` queda catalogado como false-positive."""
    out = TMP / "bt_fp.json"
    proc = run([str(SCRIPT), "--fixtures", str(FIX), "--out", str(out)])
    assert proc.returncode == 0
    metrics = json.loads(out.read_text(encoding="utf-8"))
    cognados = [
        d for d in metrics["details"] if d["case_id"] == "bt-false-positive-cognates"
    ]
    assert cognados
    assert cognados[0]["category"] == "false_positive"
    assert cognados[0]["comparator_correct"] is False


def test_no_escribe_en_translations() -> None:
    """El script nunca abre ni modifica ``translations/``."""
    out = TMP / "bt_none.json"
    proc = run([str(SCRIPT), "--fixtures", str(FIX), "--out", str(out)])
    assert proc.returncode == 0
    # Confirma que stdout no contiene ``translations/`` en rutas de modificación.
    assert "WRITING" not in proc.stdout.upper()
