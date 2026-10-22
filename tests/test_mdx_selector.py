"""Pruebas del selector de hijos textuales MDX (fase 064)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "mdx"

sys.path.insert(0, str(SCRIPTS))

import mdx_parser
import mdx_selector


def test_selector_detecta_texto_de_info_callout() -> None:
    text = (FIXTURES / "info_callout.mdx").read_text(encoding="utf-8")
    segments = mdx_selector.select_translatable(text)
    text_kinds = [s for s in segments if s.kind == "text"]
    assert text_kinds
    joined = "\n".join(s.text for s in text_kinds)
    assert "Authorization" in joined or "API key" in joined


def test_selector_detecta_titulo_atributo_permitido() -> None:
    text = (FIXTURES / "info_callout.mdx").read_text(encoding="utf-8")
    segments = mdx_selector.select_translatable(text)
    title_segments = [s for s in segments if s.kind == "attribute" and s.attribute == "title"]
    assert any("Authentication required" in s.text for s in title_segments)


def test_selector_excluye_expresiones() -> None:
    text = (FIXTURES / "note_warning.mdx").read_text(encoding="utf-8")
    segments = mdx_selector.select_translatable(text)
    for s in segments:
        if s.kind == "text":
            assert "{severity}" not in s.text


def test_selector_excluye_value_atributo_prohibido() -> None:
    text = (FIXTURES / "tabs_install.mdx").read_text(encoding="utf-8")
    segments = mdx_selector.select_translatable(text)
    value_attrs = [s for s in segments if s.attribute == "value"]
    assert value_attrs == []


def test_selector_marca_componente_no_soportado() -> None:
    text = """---
title: x
---

<FancyThing>Texto</FancyThing>
"""
    segments = mdx_selector.select_translatable(text)
    unsupported = [s for s in segments if s.kind == "unsupported_component"]
    assert any(s.parent == "FancyThing" for s in unsupported)


def test_selector_incluye_label_de_tabitem() -> None:
    text = (FIXTURES / "tabs_install.mdx").read_text(encoding="utf-8")
    segments = mdx_selector.select_translatable(text)
    labels = [s for s in segments if s.kind == "attribute" and s.attribute == "label"]
    assert any("Node.js" in s.text for s in labels)


def test_selector_orden_por_posicion() -> None:
    text = (FIXTURES / "cards.mdx").read_text(encoding="utf-8")
    segments = mdx_selector.select_translatable(text)
    starts = [s.start for s in segments]
    assert starts == sorted(starts)