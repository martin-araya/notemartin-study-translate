"""Pruebas del glosario de ML/IA (fase 095)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "tests" / "fixtures" / "glossaries" / "ml_ai.json"
SCHEMA = json.loads((ROOT / "schemas" / "glossary.schema.json").read_text(encoding="utf-8"))


def test_glosario_existe_y_valida() -> None:
    import jsonschema
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    jsonschema.validate(data, SCHEMA)


def test_glosario_tiene_terminos_clave() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    terms = {e["source_term"] for e in data["entries"]}
    assert "training" in terms
    assert "inference" in terms
    assert "embedding" in terms
    assert "gradient" in terms
    assert "fine-tuning" in terms


def test_glosario_distingue_training_e_inference() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    training_entry = next(e for e in data["entries"] if e["source_term"] == "training")
    inference_entry = next(e for e in data["entries"] if e["source_term"] == "inference")
    assert training_entry["sense"] != inference_entry["sense"]
    assert training_entry["preferred"]["term"] == "entrenamiento"
    assert inference_entry["preferred"]["term"] == "inferencia"


def test_glosario_decisiones_justificadas() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    for entry in data["entries"]:
        assert entry["justification"]
        assert "decidido por" not in entry["justification"].lower()
        assert entry["preservation_policy"] in {"translate", "keep-original", "translate-with-original-on-first-mention"}