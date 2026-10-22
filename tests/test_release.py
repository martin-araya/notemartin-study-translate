"""Pruebas para scripts/test_release.py (fase 050)."""

from __future__ import annotations

import tempfile
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INVENTORY = ROOT / "scripts" / "inventory.py"
PREPARE = ROOT / "scripts" / "prepare.py"
DETECT = ROOT / "scripts" / "detect_language.py"
BUILD = ROOT / "scripts" / "build_packets.py"
TRANSLATE = ROOT / "scripts" / "translate_pilot.py"
APPROVE = ROOT / "scripts" / "approve_pilot.py"
TEST_RELEASE = ROOT / "scripts" / "test_release.py"
PILOT = ROOT / "tests" / "fixtures" / "pilot"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def setup_approved() -> dict[str, Path]:
    inv = TMP / "inv.json"
    seg = TMP / "segments.json"
    classified = TMP / "classified.json"
    snaps = TMP / "snapshots.json"
    glossary = TMP / "glossary.json"
    packets = TMP / "packets.json"
    translations = TMP / "translations"
    profile = TMP / "profile.json"
    manifest = TMP / "manifest.json"

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
    assert run([str(BUILD),
                "--segments", str(classified),
                "--profile", str(profile),
                "--out", str(packets)]).returncode == 0
    assert run([str(ROOT / "scripts" / "extract_terms.py"),
                "--inventory", str(inv),
                "--snapshots", str(snaps),
                "--segments", str(classified),
                "--out", str(glossary)]).returncode == 0
    if translations.exists():
        shutil.rmtree(translations)
    translations.mkdir(parents=True)
    assert run([str(TRANSLATE),
                "--packets", str(packets),
                "--segments", str(classified),
                "--out", str(translations),
                "--mode", "identity"]).returncode == 0

    doc_ids = json.loads(classified.read_text(encoding="utf-8"))["files"]
    files = [{
        "path": f["path"],
        "document_id": f["document_id"],
        "source_hash": f["source_hash"],
        "current_state": "approved",
        "state_history": [{"state": "inventoried", "timestamp": "2026-10-19T20:00:00Z", "reason": "init"}, {"state": "approved", "timestamp": "2026-10-19T20:01:00Z", "reason": "done"}],
        "last_transition_at": "2026-10-19T20:01:00Z",
    } for f in doc_ids]
    manifest.write_text(json.dumps({
        "run_id": "run-release",
        "created_at": "2026-10-19T20:00:00Z",
        "skill_version": "0.1.0",
        "parser": {"name": "markdown-it-py", "version": "3.0.0"},
        "anchor_policy": {"algorithm": "github", "version": "v1"},
        "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
        "glossary_snapshot": {"version": 1, "hash": "x", "frozen": False},
        "profile_snapshot": {"hash": "x"},
        "inputs": {"source_root": str(PILOT), "total_files": len(files), "total_bytes": 0, "hashes_indexed": True},
        "files": files,
    }, indent=2), encoding="utf-8")
    return {"packets": packets, "snapshots": snaps, "segments": classified, "translations": translations, "manifest": manifest, "glossary": glossary, "source": PILOT, "inv": inv}


def test_release_pasa_con_manifesto_aprobado() -> None:
    paths = setup_approved()
    assert run([str(APPROVE),
                "--manifest", str(paths["manifest"]),
                "--translations", str(paths["translations"]),
                "--glossary", str(paths["glossary"]),
                "--approver", "release-test"]).returncode == 0
    output = TMP / "release_out"
    notes = TMP / "RELEASE_NOTES.md"
    if output.exists():
        shutil.rmtree(output)
    output.mkdir()
    anchors = output / "anchors"
    anchors.mkdir()
    proc = run([
        str(TEST_RELEASE),
        "--source-root", str(paths["source"]),
        "--translations", str(paths["translations"]),
        "--inventory", str(paths["inv"]),
        "--manifest", str(paths["manifest"]),
        "--segments", str(paths["segments"]),
        "--packets", str(paths["packets"]),
        "--snapshots", str(paths["snapshots"]),
        "--glossary", str(paths["glossary"]),
        "--output-dir", str(output),
        "--release-notes", str(notes),
    ])
    assert proc.returncode == 0, proc.stderr
    assert notes.exists()
    text = notes.read_text(encoding="utf-8")
    assert "Notas de release" in text
    assert "SHA-256" in text


def test_release_falla_si_flag_loss() -> None:
    paths = setup_approved()
    assert run([str(APPROVE),
                "--manifest", str(paths["manifest"]),
                "--translations", str(paths["translations"]),
                "--glossary", str(paths["glossary"]),
                "--approver", "release-test"]).returncode == 0
    target = next(paths["translations"].glob("*.json"))
    data = json.loads(target.read_text(encoding="utf-8"))
    if data["entries"]:
        data["entries"][0]["flag_loss"] = True
        data["entries"][0]["missing_literals"] = ["fake"]
    target.write_text(json.dumps(data, indent=2), encoding="utf-8")
    output = TMP / "release_out_fail"
    notes = TMP / "RELEASE_NOTES_FAIL.md"
    if output.exists():
        shutil.rmtree(output)
    output.mkdir()
    (output / "anchors").mkdir()
    proc = run([
        str(TEST_RELEASE),
        "--source-root", str(paths["source"]),
        "--translations", str(paths["translations"]),
        "--inventory", str(paths["inv"]),
        "--manifest", str(paths["manifest"]),
        "--segments", str(paths["segments"]),
        "--packets", str(paths["packets"]),
        "--snapshots", str(paths["snapshots"]),
        "--glossary", str(paths["glossary"]),
        "--output-dir", str(output),
        "--release-notes", str(notes),
    ])
    assert proc.returncode != 0
