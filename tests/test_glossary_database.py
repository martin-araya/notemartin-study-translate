"""Pruebas del glosario de bases de datos (fase 091)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "tests" / "fixtures" / "glossaries" / "databases.json"
SCHEMA = json.loads((ROOT / "schemas" / "glossary.schema.json").read_text(encoding="utf-8"))


def test_glosario_existe_y_valida() -> None:
    import jsonschema
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    jsonschema.validate(data, SCHEMA)


def test_glosario_tiene_terminos_clave() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    terms = {e["source_term"] for e in data["entries"]}
    assert "schema" in terms
    assert "transaction" in terms
    assert "query" in terms
    assert "instance" in terms


def test_glosario_entries_tienen_examples_y_justificacion() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    for entry in data["entries"]:
        assert len(entry["context_examples"]) >= 1
        assert entry["justification"]
        assert entry["preservation_policy"] in {"translate", "keep-original", "translate-with-original-on-first-mention"}


def test_glosario_distincion_schema_e_instancia() -> None:
    """Diferencia entre schema (estructura) e instance (servidor)."""
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    schema_entry = next(e for e in data["entries"] if e["source_term"] == "schema")
    instance_entry = next(e for e in data["entries"] if e["source_term"] == "instance")
    assert schema_entry["sense"] != instance_entry["sense"]
    assert schema_entry["preferred"]["term"] == "esquema"
    assert instance_entry["preferred"]["term"] == "instancia"