"""Pruebas de preservación de props técnicas y componentes (fase 066)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "mdx"

sys.path.insert(0, str(SCRIPTS))

import mdx_parser
import mdx_protect


def test_props_tecnicas_marcadas_como_protegidas() -> None:
    text = (FIXTURES / "tabs_install.mdx").read_text(encoding="utf-8")
    props = mdx_protect.extract_technical_props(text)
    names = {p["name"] for p in props}
    assert "value" in names
    assert "defaultValue" in names
    for p in props:
        assert p["name"] not in {"title", "label", "altText"}


def test_props_tecnicas_no_se_modifican_en_traduccion_simulada() -> None:
    text = (FIXTURES / "cards.mdx").read_text(encoding="utf-8")
    props = mdx_protect.extract_technical_props(text)
    for p in props:
        slice_ = text[p["byte_range"]["start"]:p["byte_range"]["end"]]
        assert slice_ == p["value"]


def test_round_trip_conserva_props_byte_a_byte() -> None:
    for name in ("info_callout", "tabs_install", "note_warning", "cards"):
        text = (FIXTURES / f"{name}.mdx").read_text(encoding="utf-8")
        rt = mdx_parser.round_trip(text)
        assert rt == text
        props_before = mdx_protect.extract_technical_props(text)
        props_after = mdx_protect.extract_technical_props(rt)
        assert props_before == props_after


def test_componente_no_listado_no_altera_props() -> None:
    text = """<FancyThing id="my-id" data-tab="alpha">
title here
</FancyThing>"""
    props = mdx_protect.extract_technical_props(text)
    assert any(p["component"] == "FancyThing" for p in props)


def test_props_excluye_atributos_traducibles() -> None:
    text = (FIXTURES / "info_callout.mdx").read_text(encoding="utf-8")
    props = mdx_protect.extract_technical_props(text, translatable_attributes={"title"})
    names = {p["name"] for p in props}
    assert "title" not in names
    assert "type" in names


def test_expresion_en_atributo_tecnico() -> None:
    text = """<CardGroup cols={2}>
  <Card title="A">x</Card>
  <Card title="B">y</Card>
</CardGroup>"""
    props = mdx_protect.extract_technical_props(text)
    cols_props = [p for p in props if p["name"] == "cols"]
    assert cols_props
    assert cols_props[0]["kind"] == "expression"
    assert cols_props[0]["value"] == "{2}"


def test_no_props_en_texto_plano() -> None:
    text = "# Heading without JSX\n\nSome prose."
    props = mdx_protect.extract_technical_props(text)
    assert props == []