"""Pruebas del glosario de sistemas y concurrencia (fase 094)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "tests" / "fixtures" / "glossaries" / "systems.json"
SCHEMA = json.loads((ROOT / "schemas" / "glossary.schema.json").read_text(encoding="utf-8"))


def test_glosario_existe_y_valida() -> None:
    import jsonschema
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    jsonschema.validate(data, SCHEMA)


def test_glosario_tiene_terminos_clave() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    terms = {e["source_term"] for e in data["entries"]}
    assert "thread" in terms
    assert "lock" in terms
    assert "process" in terms
    assert "mutex" in terms
    assert "deadlock" in terms


def test_glosario_distingue_thread_y_process() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    thread_entry = next(e for e in data["entries"] if e["source_term"] == "thread")
    process_entry = next(e for e in data["entries"] if e["source_term"] == "process")
    assert thread_entry["sense"] != process_entry["sense"]
    assert thread_entry["preferred"]["term"] == "hilo"
    assert process_entry["preferred"]["term"] == "proceso"


def test_glosario_distingue_lock_y_mutex() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    lock_entry = next(e for e in data["entries"] if e["source_term"] == "lock")
    mutex_entry = next(e for e in data["entries"] if e["source_term"] == "mutex")
    assert lock_entry["preferred"]["term"] == "bloqueo"
    assert lock_entry["preservation_policy"] == "translate"
    assert mutex_entry["preferred"]["term"] == "mutex"
    assert mutex_entry["preservation_policy"] == "keep-original"