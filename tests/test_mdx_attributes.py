"""Pruebas de la lista permitida de atributos MDX (fase 065)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
REF = ROOT / "references" / "mdx-attributes.md"

sys.path.insert(0, str(SCRIPTS))

import mdx_parser
import mdx_selector


def test_referencia_existe_y_tabla_de_atributos() -> None:
    text = REF.read_text(encoding="utf-8")
    assert "title" in text
    assert "label" in text


def test_referencia_prohibe_atributos_funcionales() -> None:
    text = REF.read_text(encoding="utf-8")
    forbidden = ["onClick", "className", "style", "as", "href", "src"]
    for attr in forbidden:
        assert attr in text, f"falta prohibición explícita de {attr!r}"


def test_selector_no_produce_segmentos_para_atributo_prohibido() -> None:
    text = (ROOT / "tests" / "fixtures" / "mdx" / "tabs_install.mdx").read_text(encoding="utf-8")
    segments = mdx_selector.select_translatable(text)
    bad_attrs = {"value", "icon", "type", "severity", "cols", "defaultValue"}
    produced = {s.attribute for s in segments if s.kind == "attribute"}
    assert produced.isdisjoint(bad_attrs)


def test_selector_personalizado_puede_anadir_atributo_permitido() -> None:
    text = """<Card title="My title" icon="user">body</Card>"""
    base = mdx_selector.select_translatable(text)
    base_attrs = {s.attribute for s in base if s.kind == "attribute"}
    assert "title" in base_attrs
    assert "icon" not in base_attrs

    contract = {
        "components": ["Card"],
        "translatable_attributes": ["title", "icon"],
    }
    extended = mdx_selector.select_translatable(text, contract=contract)
    extended_attrs = {s.attribute for s in extended if s.kind == "attribute"}
    assert {"title", "icon"}.issubset(extended_attrs)


def test_procedimiento_para_anadir_atributo_documentado() -> None:
    text = REF.read_text(encoding="utf-8")
    assert "Procedimiento" in text or "procedimiento" in text
    assert "manifest.json" in text