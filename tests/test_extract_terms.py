"""Pruebas para scripts/extract_terms.py (fase 023)."""

from __future__ import annotations

import tempfile
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INVENTORY = ROOT / "scripts" / "inventory.py"
PREPARE = ROOT / "scripts" / "prepare.py"
DETECT = ROOT / "scripts" / "detect_language.py"
EXTRACT = ROOT / "scripts" / "extract_terms.py"
SCHEMA = ROOT / "schemas" / "glossary.schema.json"
PILOT = ROOT / "tests" / "fixtures" / "pilot"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def generate_glossary() -> dict:
    inv = TMP / "inv.json"
    seg = TMP / "segments.json"
    classified = TMP / "classified.json"
    snaps = TMP / "snapshots.json"
    glossary = TMP / "glossary.json"
    assert run([str(INVENTORY), "--source", str(PILOT), "--out", str(inv)]).returncode == 0
    assert run([str(PREPARE), "--inventory", str(inv), "--segments", str(seg), "--snapshots", str(snaps)]).returncode == 0
    assert run([str(DETECT), "--segments", str(seg), "--out", str(classified)]).returncode == 0
    assert run([str(EXTRACT),
                "--inventory", str(inv),
                "--snapshots", str(snaps),
                "--segments", str(classified),
                "--out", str(glossary)]).returncode == 0
    return json.loads(glossary.read_text(encoding="utf-8"))


def test_glossary_valida_contra_esquema() -> None:
    from jsonschema import Draft202012Validator
    data = generate_glossary()
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(data)


def test_glossary_no_congelado() -> None:
    data = generate_glossary()
    assert data["frozen"] is False


def test_cada_entrada_tiene_ejemplo_con_document_id() -> None:
    data = generate_glossary()
    for e in data["entries"]:
        assert e["context_examples"], f"entrada {e['id']} sin ejemplos"
        for ex in e["context_examples"]:
            assert ex["document_id"], f"ejemplo sin document_id en {e['id']}"
            assert ex["segment_id"], f"ejemplo sin segment_id en {e['id']}"


def test_justificacion_explica_decision() -> None:
    data = generate_glossary()
    for e in data["entries"]:
        assert e["justification"], f"entrada {e['id']} sin justificación"
        assert e["decided_by"], f"entrada {e['id']} sin decided_by"


def test_max_candidates_respetado() -> None:
    inv = TMP / "inv.json"
    seg = TMP / "segments.json"
    classified = TMP / "classified.json"
    snaps = TMP / "snapshots.json"
    glossary = TMP / "glossary_small.json"
    assert run([str(INVENTORY), "--source", str(PILOT), "--out", str(inv)]).returncode == 0
    assert run([str(PREPARE), "--inventory", str(inv), "--segments", str(seg), "--snapshots", str(snaps)]).returncode == 0
    assert run([str(DETECT), "--segments", str(seg), "--out", str(classified)]).returncode == 0
    proc = run([str(EXTRACT),
                "--inventory", str(inv),
                "--snapshots", str(snaps),
                "--segments", str(classified),
                "--out", str(glossary),
                "--max-candidates", "5"])
    assert proc.returncode == 0
    data = json.loads(glossary.read_text(encoding="utf-8"))
    assert len(data["entries"]) <= 5
