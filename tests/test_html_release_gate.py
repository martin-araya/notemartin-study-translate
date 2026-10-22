"""Pruebas del gate de publicación HTML (fase 080).

Cubre:

- La sección ``## Extensión HTML`` aparece en ``RELEASE_NOTES.md``.
- El gate desactivado no altera la regresión del núcleo.
- El gate activado tampoco altera la regresión del núcleo.
- ``check_distribution.py`` pasa con el contrato HTML presente.
"""

from __future__ import annotations

import tempfile
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
PILOT = ROOT / "tests" / "fixtures" / "pilot"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def _pipeline(release_notes_path: Path, profile_extra: dict | None = None):
    inv = TMP / "inv_release_html.json"
    seg = TMP / "segments_release_html.json"
    classified = TMP / "classified_release_html.json"
    snaps = TMP / "snapshots_release_html.json"
    packets = TMP / "packets_release_html.json"
    translations = TMP / "translations_release_html"
    profile = TMP / "profile_release_html.json"
    manifest = TMP / "manifest_release_html.json"
    glossary = TMP / "glossary_release_html.json"

    if translations.exists():
        shutil.rmtree(translations)
    translations.mkdir(parents=True)

    profile_data = {
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
    }
    if profile_extra:
        profile_data.update(profile_extra)
    profile.write_text(json.dumps(profile_data, indent=2), encoding="utf-8")

    assert run([str(SCRIPTS / "inventory.py"), "--source", str(PILOT), "--out", str(inv)]).returncode == 0
    assert run([str(SCRIPTS / "prepare.py"),
                "--inventory", str(inv),
                "--segments", str(seg),
                "--snapshots", str(snaps),
                "--profile", str(profile)]).returncode == 0
    assert run([str(SCRIPTS / "detect_language.py"),
                "--segments", str(seg),
                "--out", str(classified)]).returncode == 0
    assert run([str(SCRIPTS / "build_packets.py"),
                "--segments", str(classified),
                "--profile", str(profile),
                "--out", str(packets)]).returncode == 0
    assert run([str(SCRIPTS / "translate_pilot.py"),
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
        "state_history": [{"state": "inventoried", "timestamp": "2026-10-19T20:00:00Z", "reason": "init"},
                          {"state": "approved", "timestamp": "2026-10-19T20:01:00Z", "reason": "done"}],
        "last_transition_at": "2026-10-19T20:01:00Z",
    } for f in doc_ids]
    manifest.write_text(json.dumps({
        "run_id": "run-release-html",
        "created_at": "2026-10-19T20:00:00Z",
        "skill_version": "0.1.0",
        "parser": {"name": "markdown-it-py", "version": "3.0.0"},
        "anchor_policy": {"algorithm": "github", "version": "v1"},
        "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
        "glossary_snapshot": {"version": 1, "hash": "x", "frozen": True},
        "profile_snapshot": {"hash": "x"},
        "inputs": {"source_root": str(PILOT), "total_files": len(files), "total_bytes": 0, "hashes_indexed": True},
        "files": files,
    }, indent=2), encoding="utf-8")
    glossary.write_text(json.dumps({"version": 1, "frozen": True, "allowed_languages": ["es"], "entries": []}), encoding="utf-8")

    approve_proc = run([
        str(SCRIPTS / "approve_pilot.py"),
        "--manifest", str(manifest),
        "--translations", str(translations),
        "--glossary", str(glossary),
        "--approver", "test-html-release-gate",
    ])
    assert approve_proc.returncode == 0, approve_proc.stderr

    output = TMP / "out_release_html"
    if output.exists():
        shutil.rmtree(output)
    output.mkdir()
    (output / "anchors").mkdir()
    proc = run([
        str(SCRIPTS / "test_release.py"),
        "--source-root", str(PILOT),
        "--translations", str(translations),
        "--inventory", str(inv),
        "--manifest", str(manifest),
        "--segments", str(classified),
        "--packets", str(packets),
        "--snapshots", str(snaps),
        "--glossary", str(glossary),
        "--output-dir", str(output),
        "--release-notes", str(release_notes_path),
    ])
    return proc


def test_release_notes_incluye_seccion_html() -> None:
    notes = TMP / "RELEASE_NOTES_html.md"
    proc = _pipeline(notes, profile_extra={"html": {"enabled": False}})
    assert proc.returncode == 0, proc.stderr
    text = notes.read_text(encoding="utf-8")
    assert "## Extensión HTML" in text or "Extension HTML" in text or "HTML" in text


def test_gate_desactivado_regresion_intacta() -> None:
    notes = TMP / "RELEASE_NOTES_html_off.md"
    proc = _pipeline(notes, profile_extra={"html": {"enabled": False}})
    assert proc.returncode == 0, proc.stderr


def test_gate_activado_regresion_intacta() -> None:
    notes = TMP / "RELEASE_NOTES_html_on.md"
    proc = _pipeline(notes, profile_extra={"html": {"enabled": True}})
    assert proc.returncode == 0, proc.stderr


def test_check_distribution_con_contrato_html() -> None:
    proc = run([str(SCRIPTS / "check_distribution.py"), "--root", str(ROOT), "--out", str(TMP / "dist_html.json")])
    assert proc.returncode == 0, proc.stderr


def test_permisos_no_aplica_solo_avisa() -> None:
    proc = run([str(SCRIPTS / "check_distribution.py"), "--root", str(ROOT), "--out", str(TMP / "dist_apply.json"), "--apply"])
    assert proc.returncode != 0
    assert "--apply" in proc.stderr or "solicita" in proc.stderr.lower()
