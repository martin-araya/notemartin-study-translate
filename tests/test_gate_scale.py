"""Pruebas del gate de escala (fase 120)."""

from __future__ import annotations

import tempfile
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GATE = ROOT / "scripts" / "gate_scale.py"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def _serial_concurrent(scope: list[str] | None = None,
                       blocked_diff: int = 0,
                       failed_diff: int = 0,
                       link_diff: int = 0,
                       serial_dur: float = 10.0,
                       concurrent_dur: float = 10.0) -> tuple[Path, Path]:
    serial = TMP / "g-serial.json"
    concurrent = TMP / "g-concurrent.json"
    if serial.exists():
        serial.unlink()
    if concurrent.exists():
        concurrent.unlink()
    seg_ids = scope or ["seg-1", "seg-2", "seg-3"]
    serial.write_text(json.dumps({
        "mode": "serial",
        "approved_segment_ids": seg_ids,
        "link_anchor_errors": 5 + link_diff,
        "blocked_count": 1 + blocked_diff,
        "failed_count": 0 + failed_diff,
        "duration_sec": serial_dur,
    }, ensure_ascii=False) + "\n", encoding="utf-8")
    concurrent.write_text(json.dumps({
        "mode": "concurrent",
        "approved_segment_ids": seg_ids,
        "link_anchor_errors": 5,
        "blocked_count": 1,
        "failed_count": 0,
        "duration_sec": concurrent_dur,
    }, ensure_ascii=False) + "\n", encoding="utf-8")
    return serial, concurrent


def test_gate_pasa_con_manifiestos_equivalentes() -> None:
    s, c = _serial_concurrent(scope=["seg-1", "seg-2", "seg-3"])
    scope = TMP / "scope.json"
    scope.write_text(json.dumps({"scope": ["seg-1", "seg-2", "seg-3"]}) + "\n", encoding="utf-8")
    out = TMP / "g-out-pass.json"
    if out.exists():
        out.unlink()
    proc = subprocess.run(
        [sys.executable, str(GATE),
         "--serial", str(s), "--concurrent", str(c),
         "--scope", str(scope), "--out", str(out)],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 0, proc.stdout
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["passed"] is True
    assert all(c["passed"] for c in payload["checks"].values())


def test_gate_falla_con_cobertura_incompleta() -> None:
    s, c = _serial_concurrent(scope=["seg-1", "seg-2", "seg-3"])
    scope = TMP / "scope-incomplete.json"
    scope.write_text(json.dumps({"scope": ["seg-1", "seg-2", "seg-3", "seg-4"]}) + "\n", encoding="utf-8")
    out = TMP / "g-out-coverage.json"
    if out.exists():
        out.unlink()
    proc = subprocess.run(
        [sys.executable, str(GATE),
         "--serial", str(s), "--concurrent", str(c),
         "--scope", str(scope), "--out", str(out)],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 1
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["checks"]["coverage"]["passed"] is False
    assert payload["passed"] is False


def test_gate_falla_con_ledger_divergente() -> None:
    serial = TMP / "gd-serial.json"
    concurrent = TMP / "gd-concurrent.json"
    serial.write_text(json.dumps({"approved_segment_ids": ["a", "b"]}, ensure_ascii=False) + "\n", encoding="utf-8")
    concurrent.write_text(json.dumps({"approved_segment_ids": ["a", "c"]}, ensure_ascii=False) + "\n", encoding="utf-8")
    out = TMP / "g-out-ledger.json"
    if out.exists():
        out.unlink()
    proc = subprocess.run(
        [sys.executable, str(GATE),
         "--serial", str(serial), "--concurrent", str(concurrent),
         "--out", str(out)],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 1
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["checks"]["ledger"]["passed"] is False


def test_gate_falla_con_regresion_de_anclas() -> None:
    serial = TMP / "gr-serial.json"
    concurrent = TMP / "gr-concurrent.json"
    serial.write_text(json.dumps({
        "approved_segment_ids": ["x"],
        "link_anchor_errors": 2,
        "blocked_count": 0, "failed_count": 0,
    }, ensure_ascii=False) + "\n", encoding="utf-8")
    concurrent.write_text(json.dumps({
        "approved_segment_ids": ["x"],
        "link_anchor_errors": 5,
        "blocked_count": 0, "failed_count": 0,
    }, ensure_ascii=False) + "\n", encoding="utf-8")
    out = TMP / "g-out-regression.json"
    if out.exists():
        out.unlink()
    proc = subprocess.run(
        [sys.executable, str(GATE),
         "--serial", str(serial), "--concurrent", str(concurrent),
         "--out", str(out)],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 1
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["checks"]["link_regressions"]["passed"] is False


def test_gate_falla_por_nuevos_bloqueos() -> None:
    serial = TMP / "gb-serial.json"
    concurrent = TMP / "gb-concurrent.json"
    serial.write_text(json.dumps({
        "approved_segment_ids": ["x"],
        "link_anchor_errors": 0,
        "blocked_count": 1, "failed_count": 0,
    }, ensure_ascii=False) + "\n", encoding="utf-8")
    concurrent.write_text(json.dumps({
        "approved_segment_ids": ["x"],
        "link_anchor_errors": 0,
        "blocked_count": 5, "failed_count": 1,
    }, ensure_ascii=False) + "\n", encoding="utf-8")
    out = TMP / "g-out-blockers.json"
    if out.exists():
        out.unlink()
    proc = subprocess.run(
        [sys.executable, str(GATE),
         "--serial", str(serial), "--concurrent", str(concurrent),
         "--out", str(out)],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 1
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["checks"]["new_blockers"]["passed"] is False


def test_gate_falla_por_tiempo_fuera_de_tolerancia() -> None:
    s, c = _serial_concurrent(scope=["seg-1", "seg-2", "seg-3"],
                              serial_dur=10.0, concurrent_dur=12.0)
    scope = TMP / "scope-time.json"
    scope.write_text(json.dumps({"scope": ["seg-1", "seg-2", "seg-3"]}) + "\n", encoding="utf-8")
    out = TMP / "g-out-time.json"
    if out.exists():
        out.unlink()
    proc = subprocess.run(
        [sys.executable, str(GATE),
         "--serial", str(s), "--concurrent", str(c),
         "--scope", str(scope), "--tolerance", "0.1", "--out", str(out)],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 1
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["checks"]["time_tolerance"]["passed"] is False


def test_gate_pasa_con_tiempo_dentro_de_tolerancia() -> None:
    s, c = _serial_concurrent(scope=["seg-1"], serial_dur=10.0, concurrent_dur=10.5)
    scope = TMP / "scope-ok.json"
    scope.write_text(json.dumps({"scope": ["seg-1"]}) + "\n", encoding="utf-8")
    out = TMP / "g-out-ok.json"
    if out.exists():
        out.unlink()
    proc = subprocess.run(
        [sys.executable, str(GATE),
         "--serial", str(s), "--concurrent", str(c),
         "--scope", str(scope), "--tolerance", "0.1", "--out", str(out)],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["checks"]["time_tolerance"]["passed"] is True
