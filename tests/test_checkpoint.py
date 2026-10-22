"""Pruebas para scripts/checkpoint.py (fase 032)."""

from __future__ import annotations

import tempfile
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECKPOINT = ROOT / "scripts" / "checkpoint.py"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def fresh_work_root() -> Path:
    out = TMP / "checkpoint_work"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    return out


def test_save_y_load_round_trip() -> None:
    work = fresh_work_root()
    state = {
        "run_id": "run-aabbccdd",
        "created_at": "2026-10-19T20:00:00Z",
        "last_segment_id": "seg-12345678",
        "files_state": {"doc-a": "translated", "doc-b": "approved"},
        "glossary_snapshot": {"version": 1, "hash": "abc", "frozen": False},
        "profile_snapshot": {"hash": "def"},
        "parser": {"name": "markdown-it-py", "version": "3.0.0"},
        "prompt_version": "v0",
    }
    state_file = TMP / "ckpt_state.json"
    state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")

    assert run([str(CHECKPOINT), "save", "--state", str(state_file), "--work-root", str(work)]).returncode == 0
    proc = run([str(CHECKPOINT), "load", "--work-root", str(work), "--run-id", "run-aabbccdd"])
    assert proc.returncode == 0, proc.stderr
    loaded = json.loads(proc.stdout)
    assert loaded["run_id"] == "run-aabbccdd"
    assert loaded["last_segment_id"] == "seg-12345678"


def test_dos_saves_producen_dos_archivos_list_ordenados() -> None:
    work = fresh_work_root()
    state_file = TMP / "ckpt_state.json"
    state_file.write_text(json.dumps({"run_id": "run-12345678", "v": 1}, indent=2), encoding="utf-8")
    run([str(CHECKPOINT), "save", "--state", str(state_file), "--work-root", str(work)])
    state_file.write_text(json.dumps({"run_id": "run-12345678", "v": 2}, indent=2), encoding="utf-8")
    run([str(CHECKPOINT), "save", "--state", str(state_file), "--work-root", str(work)])
    proc = run([str(CHECKPOINT), "list", "--work-root", str(work), "--run-id", "run-12345678"])
    assert proc.returncode == 0
    files = [Path(line) for line in proc.stdout.splitlines() if line]
    assert len(files) == 2
    assert files[0].name < files[1].name


def test_archivo_corrupto_no_impide_cargar_validos() -> None:
    work = fresh_work_root()
    state_file = TMP / "ckpt_state.json"
    state_file.write_text(json.dumps({"run_id": "run-12345678", "v": 1}, indent=2), encoding="utf-8")
    run([str(CHECKPOINT), "save", "--state", str(state_file), "--work-root", str(work)])

    cp_dir = work / "run-12345678" / "checkpoints"
    paths = sorted(cp_dir.glob("checkpoint-*.json"))
    assert paths
    paths[0].write_text("{not valid json", encoding="utf-8")

    state_file.write_text(json.dumps({"run_id": "run-12345678", "v": 2}, indent=2), encoding="utf-8")
    run([str(CHECKPOINT), "save", "--state", str(state_file), "--work-root", str(work)])

    proc = run([str(CHECKPOINT), "load", "--work-root", str(work), "--run-id", "run-12345678"])
    assert proc.returncode == 0
    loaded = json.loads(proc.stdout)
    assert loaded["v"] == 2


def test_load_sin_checkpoints_devuelve_error() -> None:
    work = fresh_work_root()
    proc = run([str(CHECKPOINT), "load", "--work-root", str(work), "--run-id", "run-empty"])
    assert proc.returncode != 0
