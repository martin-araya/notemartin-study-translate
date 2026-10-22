"""Pruebas del reporte de release con secciones explícitas (fase 059).

Cubre:

- ``RELEASE_NOTES.md`` incluye las cuatro secciones obligatorias
  (``Pruebas automáticas``, ``Revisión asistida``, ``Revisión
  humana``, ``Notion``).
- La sección Notion marca explícitamente "no verificado".
- Sin ``--human-reviewed``, la sección dice "Ninguna registrada".
- Las limitaciones aceptadas listan issues no críticos o declaran
  "ninguna" si no hay.
"""

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


def setup_approved(human_review_path: str | None = None) -> dict[str, Path]:
    inv = TMP / "inv_rel.json"
    seg = TMP / "segments_rel.json"
    classified = TMP / "classified_rel.json"
    snaps = TMP / "snapshots_rel.json"
    glossary = TMP / "glossary_rel.json"
    packets = TMP / "packets_rel.json"
    translations = TMP / "translations_rel"
    profile = TMP / "profile_rel.json"
    manifest = TMP / "manifest_rel.json"

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
        "state_history": [
            {"state": "inventoried", "timestamp": "2026-10-19T20:00:00Z", "reason": "init"},
            {"state": "approved", "timestamp": "2026-10-19T20:01:00Z", "reason": "done"},
        ],
        "last_transition_at": "2026-10-19T20:01:00Z",
    } for f in doc_ids]
    manifest.write_text(json.dumps({
        "run_id": "run-rel-notes",
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
    return {
        "packets": packets, "snapshots": snaps, "segments": classified, "translations": translations,
        "manifest": manifest, "glossary": glossary, "source": PILOT, "inv": inv,
        "human_review_path": Path(human_review_path) if human_review_path else None,
    }


def test_release_notes_incluye_secciones_obligatorias() -> None:
    paths = setup_approved()
    assert run([str(APPROVE),
                "--manifest", str(paths["manifest"]),
                "--translations", str(paths["translations"]),
                "--glossary", str(paths["glossary"]),
                "--approver", "release-notes-test"]).returncode == 0
    output = TMP / "rel_out1"
    if output.exists():
        shutil.rmtree(output)
    output.mkdir()
    (output / "anchors").mkdir()
    notes = TMP / "RELEASE_NOTES_059_a.md"
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
    text = notes.read_text(encoding="utf-8")
    for section in ("## Pruebas automáticas", "## Revisión asistida", "## Revisión humana", "## Notion"):
        assert section in text, f"falta la sección {section!r} en RELEASE_NOTES.md"


def test_release_notes_notion_no_verificado() -> None:
    paths = setup_approved()
    assert run([str(APPROVE),
                "--manifest", str(paths["manifest"]),
                "--translations", str(paths["translations"]),
                "--glossary", str(paths["glossary"]),
                "--approver", "release-notes-test"]).returncode == 0
    output = TMP / "rel_out2"
    if output.exists():
        shutil.rmtree(output)
    output.mkdir()
    (output / "anchors").mkdir()
    notes = TMP / "RELEASE_NOTES_059_b.md"
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
    text = notes.read_text(encoding="utf-8")
    assert "No verificado" in text


def test_release_notes_sin_human_reviewed_marca_ninguna() -> None:
    paths = setup_approved()
    assert run([str(APPROVE),
                "--manifest", str(paths["manifest"]),
                "--translations", str(paths["translations"]),
                "--glossary", str(paths["glossary"]),
                "--approver", "release-notes-test"]).returncode == 0
    output = TMP / "rel_out3"
    if output.exists():
        shutil.rmtree(output)
    output.mkdir()
    (output / "anchors").mkdir()
    notes = TMP / "RELEASE_NOTES_059_c.md"
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
    text = notes.read_text(encoding="utf-8")
    assert "Ninguna registrada" in text


def test_release_notes_con_human_reviewed_lista_segmentos() -> None:
    review_path = TMP / "human_review.json"
    review_path.write_text(json.dumps({"segments": ["seg-a", "seg-b", "seg-c"]}), encoding="utf-8")
    paths = setup_approved(human_review_path=str(review_path))
    assert run([str(APPROVE),
                "--manifest", str(paths["manifest"]),
                "--translations", str(paths["translations"]),
                "--glossary", str(paths["glossary"]),
                "--approver", "release-notes-test"]).returncode == 0
    output = TMP / "rel_out4"
    if output.exists():
        shutil.rmtree(output)
    output.mkdir()
    (output / "anchors").mkdir()
    notes = TMP / "RELEASE_NOTES_059_d.md"
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
        "--human-reviewed", str(review_path),
    ])
    assert proc.returncode == 0, proc.stderr
    text = notes.read_text(encoding="utf-8")
    assert "3 segmentos revisados manualmente" in text
    assert "seg-a" in text


def test_release_notes_limitaciones_aceptadas_o_ninguna() -> None:
    paths = setup_approved()
    assert run([str(APPROVE),
                "--manifest", str(paths["manifest"]),
                "--translations", str(paths["translations"]),
                "--glossary", str(paths["glossary"]),
                "--approver", "release-notes-test"]).returncode == 0
    output = TMP / "rel_out5"
    if output.exists():
        shutil.rmtree(output)
    output.mkdir()
    (output / "anchors").mkdir()
    notes = TMP / "RELEASE_NOTES_059_e.md"
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
    text = notes.read_text(encoding="utf-8")
    assert "## Limitaciones aceptadas" in text
    assert ("Ninguna registrada como issue no crítico" in text
            or "INFO" in text
            or "WARNING" in text)
