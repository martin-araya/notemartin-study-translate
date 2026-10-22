"""Pruebas del selector de nodos de texto HTML (fase 073)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "html"

sys.path.insert(0, str(SCRIPTS))

import html_parser
import html_selector


def test_selector_detecta_texto_en_summary() -> None:
    text = (FIXTURES / "details_summary.md").read_text(encoding="utf-8")
    segments = html_selector.select_translatable(text)
    summary_segments = [s for s in segments if s.kind == "text" and s.tag == "summary"]
    assert any("How do I obtain a token" in s.text for s in summary_segments)


def test_selector_detecta_atributos_visibles() -> None:
    text = (FIXTURES / "kbd_code_inline.md").read_text(encoding="utf-8")
    segments = html_selector.select_translatable(text)
    title_segments = [s for s in segments if s.kind == "attribute" and s.attribute == "title"]
    assert any("Our logo" in s.text for s in title_segments)


def test_selector_no_emite_segmentos_para_atributos_prohibidos() -> None:
    text = (FIXTURES / "kbd_code_inline.md").read_text(encoding="utf-8")
    segments = html_selector.select_translatable(text)
    forbidden = {"href", "src", "id", "class", "style"}
    produced = {s.attribute for s in segments if s.kind == "attribute"}
    assert produced.isdisjoint(forbidden)


def test_selector_no_emite_seguridad_for_unsafe_tags() -> None:
    text = "# x\n\n<script>alert(1)</script>\n"
    segments = html_selector.select_translatable(text)
    assert all(s.tag != "script" for s in segments)


def test_selector_detecta_texto_en_tabla() -> None:
    text = (FIXTURES / "tables_accessibility.md").read_text(encoding="utf-8")
    segments = html_selector.select_translatable(text)
    cell_segments = [s for s in segments if s.kind == "text" and s.tag == "td"]
    assert any("OK" in s.text for s in cell_segments)


def test_selector_orden_por_posicion() -> None:
    text = (FIXTURES / "details_nested.md").read_text(encoding="utf-8")
    segments = html_selector.select_translatable(text)
    starts = [s.start for s in segments]
    assert starts == sorted(starts)


def test_selector_recurse_en_anidamiento() -> None:
    text = (FIXTURES / "details_nested.md").read_text(encoding="utf-8")
    segments = html_selector.select_translatable(text)
    summary_segments = [s for s in segments if s.kind == "text" and s.tag == "summary"]
    texts = [s.text.strip() for s in summary_segments]
    assert any("Top level" in t for t in texts)
    assert any("Nested level" in t for t in texts)
    assert any("Deep level" in t for t in texts)


def test_selector_excluye_imagenes_como_texto() -> None:
    text = """<p>Before <img src="x" alt="alt text" /> after</p>"""
    segments = html_selector.select_translatable(text)
    img_segments = [s for s in segments if s.tag == "img"]
    assert not img_segments or all(s.kind == "attribute" for s in img_segments)


def test_selector_personalizado_anade_atributo() -> None:
    text = "<a href=\"https://example.com\" aria-label=\"Documentation\">Doc</a>"
    base = html_selector.select_translatable(text)
    base_attrs = {s.attribute for s in base if s.kind == "attribute"}
    assert "aria-label" in base_attrs

    contract = {"attributes": ["title", "aria-label", "data-help"]}
    out = html_selector.select_translatable(text, contract=contract)
    out_attrs = {s.attribute for s in out if s.kind == "attribute"}
    assert {"aria-label", "title", "data-help"}.issuperset(out_attrs)