"""Pruebas del fallback en serie (fase 117)."""

from __future__ import annotations

import tempfile
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERIAL = ROOT / "scripts" / "run_serial.py"
DIFF = ROOT / "scripts" / "diff_ledgers.py"
PACKETS = ROOT / "tests" / "fixtures" / "scale" / "packets_workers.json"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def _run_serial(workdir: Path, manifest: Path | None = None) -> int:
    args = [
        sys.executable, str(SERIAL),
        "--packets", str(PACKETS),
        "--workdir", str(workdir),
    ]
    if manifest:
        args += ["--manifest", str(manifest)]
    return subprocess.run(args, capture_output=True, text=True, check=False).returncode


def test_run_serial_emite_summary_y_manifest() -> None:
    workdir = TMP / "serial-test"
    if workdir.exists():
        shutil.rmtree(workdir)
    manifest = TMP / "manifest-serial.json"
    if manifest.exists():
        manifest.unlink()
    rc = _run_serial(workdir, manifest)
    assert rc == 0
    assert (workdir / "serial_summary.json").exists()
    assert manifest.exists()
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["mode"] == "serial"
    assert payload["packet_count"] >= 1
    assert len(payload["approved_segment_ids"]) + len(payload["pending_segment_ids"]) == payload["packet_count"]


def test_sin_traduccion_no_hay_segmentos_aprobados() -> None:
    """Sin contenido real, el modo serie no aprueba nada.

    Antes, `approved_segment_ids` era la lista completa de paquetes,
   -traducidos o no, y el gate de escala comparaba dos listas idénticas
    de trabajo inexistente.
    """
    workdir = TMP / "serial-sin-contenido"
    if workdir.exists():
        shutil.rmtree(workdir)
    manifest = TMP / "manifest-sin-contenido.json"
    if manifest.exists():
        manifest.unlink()
    rc = _run_serial(workdir, manifest)
    assert rc == 0
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["approved_segment_ids"] == []
    assert len(payload["pending_segment_ids"]) == payload["packet_count"]
    assert payload["current_state_distribution"]["approved"] == 0
    summary = json.loads((workdir / "serial_summary.json").read_text(encoding="utf-8"))
    assert summary["approved"] == 0
    assert summary["worker_status"] == "pending_translation"


def test_diff_dos_manifiestos_iguales_equivale_a_zero() -> None:
    workdir_a = TMP / "diff-a"
    workdir_b = TMP / "diff-b"
    for p in (workdir_a, workdir_b):
        if p.exists():
            shutil.rmtree(p)
    manifest_a = TMP / "manifest-a.json"
    manifest_b = TMP / "manifest-b.json"
    for f in (manifest_a, manifest_b):
        if f.exists():
            f.unlink()
    _run_serial(workdir_a, manifest_a)
    _run_serial(workdir_b, manifest_b)
    rc = subprocess.run(
        [sys.executable, str(DIFF),
         "--a", str(manifest_a), "--b", str(manifest_b),
         "--strict"],
        capture_output=True, text=True, check=False,
    ).returncode
    assert rc == 0


def test_diff_distingue_segmentos_exclusivos() -> None:
    """Si un manifiesto aprueba un segment_id que el otro no, el diff lo señala."""
    manifest_a = TMP / "man-A.json"
    manifest_b = TMP / "man-B.json"
    manifest_a.write_text(json.dumps({
        "mode": "serial",
        "approved_segment_ids": ["seg-A", "seg-B"],
        "current_state_distribution": {"approved": 2},
    }, ensure_ascii=False) + "\n", encoding="utf-8")
    manifest_b.write_text(json.dumps({
        "mode": "serial",
        "approved_segment_ids": ["seg-B", "seg-C"],
        "current_state_distribution": {"approved": 2},
    }, ensure_ascii=False) + "\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(DIFF),
         "--a", str(manifest_a), "--b", str(manifest_b),
         "--strict", "--out", str(TMP / "diff-output.json")],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 1
    diff = json.loads((TMP / "diff-output.json").read_text(encoding="utf-8"))
    assert "seg-A" in diff["only_in_a"]
    assert "seg-C" in diff["only_in_b"]


def test_serial_emite_worker_state_con_mode_serial() -> None:
    workdir = TMP / "serial-state"
    if workdir.exists():
        shutil.rmtree(workdir)
    _run_serial(workdir)
    state = json.loads((workdir / "workers" / "serial" / "state.json").read_text(encoding="utf-8"))
    assert state["worker_id"] == "serial"
    assert state["status"] in {"done", "pending_translation", "failed"}


def test_diff_emite_distribucion_de_estados() -> None:
    manifest_a = TMP / "dist-a.json"
    manifest_b = TMP / "dist-b.json"
    manifest_a.write_text(json.dumps({
        "approved_segment_ids": ["x", "y"],
        "current_state_distribution": {"approved": 2},
    }, ensure_ascii=False) + "\n", encoding="utf-8")
    manifest_b.write_text(json.dumps({
        "approved_segment_ids": ["x", "y"],
        "current_state_distribution": {"approved": 1, "blocked": 1},
    }, ensure_ascii=False) + "\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(DIFF),
         "--a", str(manifest_a), "--b", str(manifest_b),
         "--out", str(TMP / "dist-out.json")],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 0
    diff = json.loads((TMP / "dist-out.json").read_text(encoding="utf-8"))
    assert diff["state_distribution_a"]["approved"] == 2
    assert diff["state_distribution_b"]["blocked"] == 1
