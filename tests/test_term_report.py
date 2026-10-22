"""Pruebas del reporte terminológico (fase 099)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "glossaries"

sys.path.insert(0, str(SCRIPTS))

import term_report


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_render_markdown_agrupa_por_dominio() -> None:
    glossaries = [_load("databases.json"), _load("frontend.json")]
    md = term_report.render_markdown(glossaries)
    assert "## Dominio: database" in md
    assert "## Dominio: frontend" in md


def test_render_markdown_incluye_ejemplos_y_decisiones() -> None:
    glossaries = [_load("databases.json")]
    md = term_report.render_markdown(glossaries)
    assert "`schema`" in md
    assert "`translate`" in md
    assert "esquema" in md


def test_render_markdown_sin_entradas_devuelve_texto_vacio() -> None:
    md = term_report.render_markdown([])
    assert "Sin entradas" in md


def test_render_json_estructurado_para_tooling() -> None:
    glossaries = [_load("databases.json"), _load("frontend.json")]
    data = term_report.render_json(glossaries)
    assert "domains" in data
    assert "database" in data["domains"]
    assert "frontend" in data["domains"]
    assert data["summary"]["total_domains"] == 2
    assert data["summary"]["total_entries"] >= 10


def test_report_no_se_mezcla_con_release_notes() -> None:
    """El reporte no debe mencionarse en RELEASE_NOTES ni en la salida
    de la skill."""
    glossaries = [_load("databases.json")]
    md = term_report.render_markdown(glossaries)
    assert "RELEASE_NOTES" not in md
    assert "release_notes" not in md.lower() or "report" in md.lower()


def test_render_json_no_duplica_entradas_entre_glosarios() -> None:
    """Si dos glosarios tienen la misma entrada, ambas aparecen."""
    glossaries = [_load("databases.json"), _load("databases.json")]
    data = term_report.render_json(glossaries)
    db_count = len(data["domains"]["database"])
    assert db_count == 2 * 5