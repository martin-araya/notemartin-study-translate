"""Pruebas del glosario de frontend (fase 093)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "tests" / "fixtures" / "glossaries" / "frontend.json"
SCHEMA = json.loads((ROOT / "schemas" / "glossary.schema.json").read_text(encoding="utf-8"))


def test_glosario_existe_y_valida() -> None:
    import jsonschema
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    jsonschema.validate(data, SCHEMA)


def test_glosario_tiene_terminos_clave() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    terms = {e["source_term"] for e in data["entries"]}
    assert "render" in terms
    assert "state" in terms
    assert "binding" in terms
    assert "component" in terms
    assert "hook" in terms


def test_glosario_identificadores_no_se_traducen() -> None:
    """Términos como 'hook' o nombres propios no se traducen."""
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    hook_entry = next(e for e in data["entries"] if e["source_term"] == "hook")
    assert hook_entry["preferred"]["term"] == "hook"
    assert hook_entry["preservation_policy"] == "keep-original"


def test_glosario_decide_entre_renderizar_y_renderizar() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    render_entry = next(e for e in data["entries"] if e["source_term"] == "render")
    assert render_entry["preferred"]["term"] == "renderizar"
    assert "renderizar el componente" in render_entry["allowed_variants"]