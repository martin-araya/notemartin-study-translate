"""Pruebas del coordinador de manifiestos (fase 114)."""

from __future__ import annotations

import tempfile
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COORD = ROOT / "scripts" / "coordinator.py"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def _claim(worker: str, segment: str, workdir: Path, from_state: str = "translated",
           to_state: str = "deterministic_pass") -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(COORD), "claim",
         "--worker", worker, "--segment", segment,
         "--from-state", from_state, "--to-state", to_state,
         "--workdir", str(workdir)],
        capture_output=True, text=True, check=False,
    )


def test_claim_exitoso_devuelve_0() -> None:
    wd = TMP / "co-1"
    if wd.exists():
        shutil.rmtree(wd)
    rc = _claim("W1", "seg-aaaa", wd).returncode
    assert rc == 0
    claims = json.loads((wd / "claims.json").read_text(encoding="utf-8"))
    assert "seg-aaaa" in claims
    assert claims["seg-aaaa"]["worker_id"] == "W1"


def test_segundo_worker_mismo_segmento_es_rechazado() -> None:
    wd = TMP / "co-conflict"
    if wd.exists():
        shutil.rmtree(wd)
    rc1 = _claim("W1", "seg-bbbb", wd).returncode
    assert rc1 == 0
    rc2 = _claim("W2", "seg-bbbb", wd).returncode
    assert rc2 == 9


def test_mismo_worker_puede_reclamar_mismo_segmento() -> None:
    """Idempotencia: el mismo worker reclamando el mismo segmento no falla."""
    wd = TMP / "co-idem"
    if wd.exists():
        shutil.rmtree(wd)
    rc1 = _claim("W1", "seg-cccc", wd).returncode
    rc2 = _claim("W1", "seg-cccc", wd).returncode
    assert rc1 == 0
    assert rc2 == 0


def test_to_state_invalido_falla_con_codigo_2() -> None:
    wd = TMP / "co-bad-state"
    if wd.exists():
        shutil.rmtree(wd)
    rc = subprocess.run(
        [sys.executable, str(COORD), "claim",
         "--worker", "W1", "--segment", "seg-aaaa",
         "--from-state", "translated", "--to-state", "broken_state",
         "--workdir", str(wd)],
        capture_output=True, text=True, check=False,
    ).returncode
    assert rc == 2


def test_close_emite_report() -> None:
    wd = TMP / "co-close"
    if wd.exists():
        shutil.rmtree(wd)
    _claim("W1", "seg-1", wd)
    _claim("W1", "seg-2", wd)
    _claim("W2", "seg-3", wd)
    rc = subprocess.run(
        [sys.executable, str(COORD), "close", "--workdir", str(wd)],
        capture_output=True, text=True, check=False,
    ).returncode
    assert rc == 0
    report = json.loads((wd / "coordination.json").read_text(encoding="utf-8"))
    assert report["claim_count"] == 3
    assert "W1" in report["claims_by_worker"]
    assert "W2" in report["claims_by_worker"]


def test_log_persistente_por_evento() -> None:
    wd = TMP / "co-log"
    if wd.exists():
        shutil.rmtree(wd)
    _claim("W1", "seg-log1", wd)
    _claim("W2", "seg-log1", wd)  # debe rechazarse y generar log
    log_path = wd / "coordination.log"
    assert log_path.exists()
    lines = log_path.read_text(encoding="utf-8").splitlines()
    events = [json.loads(line)["event"] for line in lines]
    assert "claim" in events
    assert "reject" in events


def test_status_imprime_claims() -> None:
    wd = TMP / "co-status"
    if wd.exists():
        shutil.rmtree(wd)
    _claim("W1", "seg-st", wd)
    rc = subprocess.run(
        [sys.executable, str(COORD), "status", "--workdir", str(wd)],
        capture_output=True, text=True, check=False,
    ).returncode
    assert rc == 0
    body = json.loads(subprocess.run(
        [sys.executable, str(COORD), "status", "--workdir", str(wd)],
        capture_output=True, text=True, check=True,
    ).stdout)
    assert "seg-st" in body


def test_claim_dos_workers_diferentes_sobre_dos_segmentos_distintos() -> None:
    """El escenario normal: dos workers, dos segmentos, todos los claims pasan."""
    wd = TMP / "co-disjoint"
    if wd.exists():
        shutil.rmtree(wd)
    rc1 = _claim("W1", "seg-x", wd).returncode
    rc2 = _claim("W2", "seg-y", wd).returncode
    assert rc1 == 0
    assert rc2 == 0
