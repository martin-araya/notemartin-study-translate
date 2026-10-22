"""Pruebas de los atributos HTML visibles y accesibilidad (fase 074)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "html"
REF = ROOT / "references" / "html-attributes.md"

sys.path.insert(0, str(SCRIPTS))

import html_selector


def test_referencia_existe_y_tabla_de_atributos() -> None:
    text = REF.read_text(encoding="utf-8")
    assert "`title`" in text or "title" in text
    assert "aria-label" in text


def test_referencia_prohibe_atributos_funcionales() -> None:
    text = REF.read_text(encoding="utf-8")
    for forbidden in ("href", "src", "id", "class", "style", "data-*", "onclick"):
        assert forbidden in text, f"falta prohibición de {forbidden!r}"


def test_referencia_docuemnta_procedimiento() -> None:
    text = REF.read_text(encoding="utf-8")
    assert "Procedimiento" in text or "procedimiento" in text
    assert "manifest.json" in text


def test_alt_en_img_es_traducible() -> None:
    text = (FIXTURES / "kbd_code_inline.md").read_text(encoding="utf-8")
    segments = html_selector.select_translatable(text)
    alt_segments = [s for s in segments if s.kind == "attribute" and s.attribute == "alt"]
    assert any("Company logo" in s.text for s in alt_segments)


def test_title_y_aria_label_traducibles() -> None:
    text = "<a href=\"https://example.com\" title=\"Documentation home\" aria-label=\"Docs\">link</a>"
    segments = html_selector.select_translatable(text)
    attrs = {s.attribute for s in segments if s.kind == "attribute"}
    assert "title" in attrs
    assert "aria-label" in attrs


def test_href_no_traducible() -> None:
    text = "<a href=\"https://example.com\" title=\"Doc\">link</a>"
    segments = html_selector.select_translatable(text)
    attrs = {s.attribute for s in segments if s.kind == "attribute"}
    assert "href" not in attrs


def test_src_no_traducible() -> None:
    text = "<img src=\"https://example.com/x.png\" alt=\"X\" />"
    segments = html_selector.select_translatable(text)
    attrs = {s.attribute for s in segments if s.kind == "attribute"}
    assert "src" not in attrs
    assert "alt" in attrs


def test_event_handler_no_traducible() -> None:
    text = "<a href=\"x\" onclick=\"alert(1)\" title=\"help\">link</a>"
    segments = html_selector.select_translatable(text)
    attrs = {s.attribute for s in segments if s.kind == "attribute"}
    assert "onclick" not in attrs
    assert "title" in attrs


def test_class_y_style_no_traducibles() -> None:
    text = "<span class=\"highlight\" style=\"color:red\" title=\"emphasis\">x</span>"
    segments = html_selector.select_translatable(text)
    attrs = {s.attribute for s in segments if s.kind == "attribute"}
    assert "class" not in attrs
    assert "style" not in attrs


def test_selector_personalizado_anade_atributo_accesibilidad() -> None:
    text = "<img src=\"x\" alt=\"A\" data-caption=\"Caption\" />"
    base = html_selector.select_translatable(text)
    base_attrs = {s.attribute for s in base if s.kind == "attribute"}
    assert "alt" in base_attrs
    assert "data-caption" not in base_attrs
    contract = {"attributes": ["title", "aria-label", "alt", "data-caption"]}
    out = html_selector.select_translatable(text, contract=contract)
    out_attrs = {s.attribute for s in out if s.kind == "attribute"}
    assert "data-caption" in out_attrs