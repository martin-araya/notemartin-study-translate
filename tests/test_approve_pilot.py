"""Pruebas para scripts/approve_pilot.py (fase 030)."""

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
EXTRACT = ROOT / "scripts" / "extract_terms.py"
TRANSLATE = ROOT / "scripts" / "translate_pilot.py"
APPROVE = ROOT / "scripts" / "approve_pilot.py"
PILOT = ROOT / "tests" / "fixtures" / "pilot"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def setup_full() -> dict:
    inv = TMP / "inv.json"
    seg = TMP / "segments.json"
    classified = TMP / "classified.json"
    snaps = TMP / "snapshots.json"
    glossary = TMP / "glossary.json"
    packets = TMP / "packets_final.json"
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
        "manifest_version": "translate/v1",
        "created_at": "2026-10-19T20:00:00Z",
        "skill_version": "0.1.0",
        "parser": {"name": "markdown-it-py", "version": "3.0.0"},
        "anchor_policy": {"algorithm": "github-slug-v1", "version": "v1"},
        "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
        "glossary_snapshot": {"version": 1, "hash": "0" * 64, "frozen": False},
        "profile_snapshot": {"hash": "0" * 64},
        "inputs": {"source_root": str(PILOT), "total_files": len(files), "total_bytes": 0, "hashes_indexed": True},
        "files": files,
        "pilot_approved": False,
    }
    manifest.write_text(json.dumps(manifest_payload, indent=2), encoding="utf-8")
    return manifest_payload


def test_aprobacion_exitosa() -> None:
    setup_full()
    proc = run([
        str(APPROVE),
        "--manifest", str(TMP / "manifest.json"),
        "--translations", str(TMP / "translations"),
        "--glossary", str(TMP / "glossary.json"),
        "--approver", "test-user",
    ])
    assert proc.returncode == 0, proc.stderr

    manifest = json.loads((TMP / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["pilot_approved"] is True
    assert manifest["approved_by"] == "test-user"
    assert "approved_at" in manifest
    assert manifest["glossary_snapshot"]["frozen"] is True

    glossary = json.loads((TMP / "glossary.json").read_text(encoding="utf-8"))
    assert glossary["frozen"] is True
    assert glossary["version"] == 2


def test_la_aprobacion_escribe_current_state() -> None:
    """La aprobación tiene que verse en `current_state`.

    `schemas/manifest.schema.json` dice de `state` que complementa a
    `current_state` y no lo sustituye, y todos los gates leen
    `current_state`. Escribir solo `state` dejaba el manifiesto del
    piloto con `current_state: translated` después de aprobar, que es un
    corpus que ningún gate daba por aprobado.
    """
    setup_full()
    proc = run([
        str(APPROVE),
        "--manifest", str(TMP / "manifest.json"),
        "--translations", str(TMP / "translations"),
        "--glossary", str(TMP / "glossary.json"),
        "--approver", "test-user",
    ])
    assert proc.returncode == 0, proc.stderr
    manifest = json.loads((TMP / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["files"], "el manifiesto no tiene archivos"
    for record in manifest["files"]:
        assert record["current_state"] == "approved", f"{record['path']} no quedó aprobado"
        assert record["state_history"][-1]["state"] == "approved"


def test_la_aprobacion_deja_el_manifiesto_valido_contra_el_esquema() -> None:
    setup_full()
    proc = run([
        str(APPROVE),
        "--manifest", str(TMP / "manifest.json"),
        "--translations", str(TMP / "translations"),
        "--glossary", str(TMP / "glossary.json"),
        "--approver", "test-user",
    ])
    assert proc.returncode == 0, proc.stderr
    manifest = json.loads((TMP / "manifest.json").read_text(encoding="utf-8"))
    import jsonschema

    schema = json.loads((ROOT / "schemas" / "manifest.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(manifest, schema)


def test_aprobacion_rechaza_si_hay_perdida() -> None:
    setup_full()
    target = next(iter((TMP / "translations").glob("*.json")))
    data = json.loads(target.read_text(encoding="utf-8"))
    data["flag_loss"] = True
    target.write_text(json.dumps(data, indent=2), encoding="utf-8")
    proc = run([
        str(APPROVE),
        "--manifest", str(TMP / "manifest.json"),
        "--translations", str(TMP / "translations"),
        "--glossary", str(TMP / "glossary.json"),
        "--approver", "test-user",
    ])
    assert proc.returncode != 0
    assert "pérdida" in proc.stderr.lower()


def test_aprobacion_rechaza_si_falta_documento() -> None:
    setup_full()
    target = next(iter((TMP / "translations").glob("*.json")))
    target.unlink()
    proc = run([
        str(APPROVE),
        "--manifest", str(TMP / "manifest.json"),
        "--translations", str(TMP / "translations"),
        "--glossary", str(TMP / "glossary.json"),
        "--approver", "test-user",
    ])
    assert proc.returncode != 0
    assert "traducción" in proc.stderr.lower()


def test_aprobacion_rechaza_revision_con_hallazgo_critico() -> None:
    setup_full()
    review = TMP / "review.json"
    review.write_text(json.dumps({
        "findings": [{"severity": "critical", "message": "negación perdida"}]
    }), encoding="utf-8")
    proc = run([
        str(APPROVE),
        "--manifest", str(TMP / "manifest.json"),
        "--translations", str(TMP / "translations"),
        "--glossary", str(TMP / "glossary.json"),
        "--review", str(review),
        "--approver", "test-user",
    ])
    assert proc.returncode != 0
    assert "crítico" in proc.stderr.lower()
