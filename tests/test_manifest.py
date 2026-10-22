"""Pruebas de invalidez por cambio de procedencia (fase 033)."""

from __future__ import annotations

import tempfile
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APPROVE = ROOT / "scripts" / "approve_pilot.py"
INVENTORY = ROOT / "scripts" / "inventory.py"
PREPARE = ROOT / "scripts" / "prepare.py"
DETECT = ROOT / "scripts" / "detect_language.py"
BUILD = ROOT / "scripts" / "build_packets.py"
EXTRACT = ROOT / "scripts" / "extract_terms.py"
TRANSLATE = ROOT / "scripts" / "translate_pilot.py"
PILOT = ROOT / "tests" / "fixtures" / "pilot"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def build_initial_files() -> tuple[Path, Path, Path]:
    inv = TMP / "inv.json"
    seg = TMP / "segments.json"
    classified = TMP / "classified.json"
    snaps = TMP / "snapshots.json"
    glossary = TMP / "glossary.json"
    packets = TMP / "packets_final.json"
    translations = TMP / "translations"
    manifest = TMP / "manifest.json"
    profile = TMP / "profile.json"

    profile.write_text(json.dumps({
        "target_language": "es",
        "source_language": "auto",
        "markdown_dialect": "commonmark+gfm",
        "slug_algorithm": {"name": "github", "version": "v1"},
        "code_preservation": "strict",
        "frontmatter_policy": "preserve",
        "bilingual_policy": "first-mention-per-document",
        "punctuation_preference": "es-comma-period",
        "review_mode": "assisted",
        "paths": {"source_root": str(PILOT), "work_root": "/tmp", "output_root": "/tmp"},
        "exclusions": [],
        "context_budget": 1500,
        "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
    }, indent=2), encoding="utf-8")

    assert run([str(INVENTORY), "--source", str(PILOT), "--out", str(inv)]).returncode == 0
    assert run([str(PREPARE), "--inventory", str(inv), "--segments", str(seg), "--snapshots", str(snaps)]).returncode == 0
    assert run([str(DETECT), "--segments", str(seg), "--out", str(classified)]).returncode == 0
    assert run([str(EXTRACT),
                "--inventory", str(inv),
                "--snapshots", str(snaps),
                "--segments", str(classified),
                "--out", str(glossary)]).returncode == 0
    assert run([str(BUILD),
                "--segments", str(classified),
                "--profile", str(profile),
                "--out", str(packets)]).returncode == 0
    if translations.exists():
        import shutil
        shutil.rmtree(translations)
    translations.mkdir(parents=True)
    assert run([str(TRANSLATE),
                "--packets", str(packets),
                "--segments", str(classified),
                "--out", str(translations),
                "--mode", "identity"]).returncode == 0

    doc_ids = json.loads(classified.read_text(encoding="utf-8"))["files"]
    files = []
    for f in doc_ids:
        files.append({
            "path": f["path"],
            "document_id": f["document_id"],
            "source_hash": f["source_hash"],
            "current_state": "translated",
            "state_history": [
                {"state": "inventoried", "timestamp": "2026-10-19T20:00:00Z", "reason": "init"},
                {"state": "translated", "timestamp": "2026-10-19T20:01:00Z", "reason": "done"},
            ],
            "last_transition_at": "2026-10-19T20:01:00Z",
        })
    manifest_payload = {
        "run_id": "run-12345678",
        "created_at": "2026-10-19T20:00:00Z",
        "skill_version": "0.1.0",
        "parser": {"name": "markdown-it-py", "version": "3.0.0"},
        "anchor_policy": {"algorithm": "github", "version": "v1"},
        "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
        "glossary_snapshot": {"version": 1, "hash": "abc123", "frozen": False},
        "profile_snapshot": {"hash": "def456"},
        "inputs": {"source_root": str(PILOT), "total_files": len(files), "total_bytes": 0, "hashes_indexed": True},
        "files": files,
        "pilot_approved": False,
    }
    manifest.write_text(json.dumps(manifest_payload, indent=2), encoding="utf-8")
    return manifest, glossary, translations


def approve_once() -> subprocess.CompletedProcess:
    return run([
        str(APPROVE),
        "--manifest", str(TMP / "manifest.json"),
        "--translations", str(TMP / "translations"),
        "--glossary", str(TMP / "glossary.json"),
        "--approver", "test-user",
    ])


def mutate(key_path: list, new_value) -> None:
    manifest = TMP / "manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    obj = data
    for k in key_path[:-1]:
        if isinstance(k, int):
            obj = obj[k]
        else:
            obj = obj[k]
    last = key_path[-1]
    if isinstance(last, int):
        obj[last] = new_value
    else:
        obj[last] = new_value
    manifest.write_text(json.dumps(data, indent=2), encoding="utf-8")


def reset_state() -> None:
    build_initial_files()
    assert approve_once().returncode == 0


def test_cambio_source_hash_invalida() -> None:
    reset_state()
    mutate(["files", 0, "source_hash"], "deadbeef")
    proc = approve_once()
    assert proc.returncode != 0
    manifest = json.loads((TMP / "manifest.json").read_text(encoding="utf-8"))
    assert any(f.get("current_state") == "invalid" for f in manifest["files"])


def test_cambio_glossary_hash_invalida() -> None:
    reset_state()
    mutate(["glossary_snapshot", "hash"], "newhash")
    proc = approve_once()
    assert proc.returncode != 0


def test_cambio_profile_hash_invalida() -> None:
    reset_state()
    mutate(["profile_snapshot", "hash"], "newprofhash")
    proc = approve_once()
    assert proc.returncode != 0


def test_cambio_parser_version_invalida() -> None:
    reset_state()
    mutate(["parser", "version"], "3.1.0")
    proc = approve_once()
    assert proc.returncode != 0


def test_cambio_prompt_version_invalida() -> None:
    reset_state()
    mutate(["model_metadata", "prompt_version"], "v1")
    proc = approve_once()
    assert proc.returncode != 0


def test_aprobacion_repetida_sin_cambios_aprueba() -> None:
    reset_state()
    proc = approve_once()
    assert proc.returncode == 0
