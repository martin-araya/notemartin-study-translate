"""Pruebas para scripts/invalidate_run.py (fase 055).

Cubre:

- Sin cambios: todos los archivos en ``unchanged``.
- Un archivo modificado: solo ese y sus dependientes quedan
  ``invalidated``.
- Cambio solo de saltos de línea (CRLF↔LF): ``whitespace_only`` y
  traducciones no invalidadas.
- Hash registrado en el manifiesto no coincide con bytes actuales:
  se detecta sin fallar.
- ``manifest.json`` permanece intacto tras la ejecución.
"""

from __future__ import annotations

import tempfile
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
INVENTORY = SCRIPTS / "inventory.py"
INVAL = SCRIPTS / "invalidate_run.py"
PILOT = ROOT / "tests" / "fixtures" / "pilot"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fresh_dir(name: str) -> Path:
    out = TMP / name
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    return out


def setup_pilot_copy() -> Path:
    src = fresh_dir("inv_src")
    for f in PILOT.iterdir():
        if f.is_file():
            shutil.copy(f, src / f.name)
    return src


def build_manifest(src: Path) -> tuple[Path, dict]:
    inv = TMP / "inv_inc.json"
    assert run([str(INVENTORY), "--source", str(src), "--out", str(inv)]).returncode == 0
    data = json.loads(inv.read_text(encoding="utf-8"))
    files = []
    for f in data["files"]:
        files.append({
            "path": f["path"],
            "document_id": f"doc-{f['sha256'][:8]}",
            "source_hash": f["sha256"],
            "current_state": "translated",
            "state_history": [
                {"state": "inventoried", "timestamp": "2026-10-19T20:00:00Z", "reason": "init"},
                {"state": "translated", "timestamp": "2026-10-19T20:01:00Z", "reason": "done"},
            ],
            "last_transition_at": "2026-10-19T20:01:00Z",
        })
    manifest = {
        "run_id": "run-inc",
        "created_at": "2026-10-19T20:00:00Z",
        "skill_version": "0.1.0",
        "parser": {"name": "markdown-it-py", "version": "3.0.0"},
        "anchor_policy": {"algorithm": "github", "version": "v1"},
        "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
        "glossary_snapshot": {"version": 1, "hash": "x", "frozen": True},
        "profile_snapshot": {"hash": "x"},
        "inputs": {"source_root": str(src), "total_files": len(files), "total_bytes": 0, "hashes_indexed": True},
        "files": files,
    }
    manifest_path = TMP / "manifest_inc.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path, manifest


def test_no_change_marks_all_unchanged() -> None:
    src = setup_pilot_copy()
    manifest_path, manifest = build_manifest(src)
    out = TMP / "plan_unchanged.json"

    rc = run([str(INVAL),
               "--manifest", str(manifest_path),
               "--source-root", str(src),
               "--out", str(out)]).returncode
    assert rc == 0
    plan = json.loads(out.read_text(encoding="utf-8"))
    assert plan["summary"]["unchanged"] == plan["summary"]["total"]
    assert plan["summary"]["changed"] == 0
    for r in plan["files"]:
        assert r["status"] == "unchanged"
        assert r["invalidated"] is False
        assert r["previous_hash"] == r["current_hash"]


def test_one_file_changed_invalidates_dependents() -> None:
    src = setup_pilot_copy()
    manifest_path, manifest = build_manifest(src)
    out = TMP / "plan_changed.json"

    target_rel = manifest["files"][0]["path"]
    target_path = src / target_rel
    target_path.write_bytes(target_path.read_bytes() + b"\nextra line\n")

    rc = run([str(INVAL),
               "--manifest", str(manifest_path),
               "--source-root", str(src),
               "--out", str(out)]).returncode
    assert rc != 0
    plan = json.loads(out.read_text(encoding="utf-8"))
    by_path = {r["path"]: r for r in plan["files"]}
    assert by_path[target_rel]["status"] == "changed"
    assert by_path[target_rel]["invalidated"] is True
    assert by_path[target_rel]["invalidated_translations"] is True
    other_changed = [p for p, r in by_path.items() if r["status"] == "changed" and p != target_rel]
    assert other_changed == []
    unchanged_count = sum(1 for r in plan["files"] if r["status"] == "unchanged")
    assert unchanged_count == plan["summary"]["total"] - 1


def test_whitespace_only_does_not_invalidate() -> None:
    src = setup_pilot_copy()
    manifest_path, manifest = build_manifest(src)
    out = TMP / "plan_ws.json"

    target_rel = manifest["files"][0]["path"]
    target_path = src / target_rel
    original = target_path.read_bytes()
    target_path.write_bytes(original.replace(b"\n", b"\r\n"))

    rc = run([str(INVAL),
               "--manifest", str(manifest_path),
               "--source-root", str(src),
               "--out", str(out)]).returncode
    assert rc == 0
    plan = json.loads(out.read_text(encoding="utf-8"))
    by_path = {r["path"]: r for r in plan["files"]}
    assert by_path[target_rel]["status"] == "whitespace_only"
    assert by_path[target_rel]["invalidated"] is False
    assert by_path[target_rel]["invalidated_translations"] is False


def test_hash_drift_detected() -> None:
    src = setup_pilot_copy()
    manifest_path, manifest = build_manifest(src)

    manifest["files"][0]["source_hash"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    out = TMP / "plan_drift.json"
    rc = run([str(INVAL),
               "--manifest", str(manifest_path),
               "--source-root", str(src),
               "--out", str(out)]).returncode
    assert rc != 0
    plan = json.loads(out.read_text(encoding="utf-8"))
    by_path = {r["path"]: r for r in plan["files"]}
    changed = [r for r in plan["files"] if r["status"] == "changed"]
    assert len(changed) == 1


def test_manifest_no_se_modifica() -> None:
    src = setup_pilot_copy()
    manifest_path, manifest = build_manifest(src)
    out = TMP / "plan_immut.json"

    snapshot_before = manifest_path.read_bytes()
    run([str(INVAL),
         "--manifest", str(manifest_path),
         "--source-root", str(src),
         "--out", str(out)])
    snapshot_after = manifest_path.read_bytes()
    assert snapshot_before == snapshot_after
