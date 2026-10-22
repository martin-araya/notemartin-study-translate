"""Pruebas de la extensión math (fase 086)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "math"
REF = ROOT / "references" / "math.md"

sys.path.insert(0, str(SCRIPTS))

import math_ext as math


def test_referencia_existe_y_declara_latex_literal() -> None:
    assert REF.exists()
    text = REF.read_text(encoding="utf-8")
    assert "literal" in text.lower()


def test_eccuacion_display_es_literal() -> None:
    text = (FIXTURES / "basic.md").read_text(encoding="utf-8")
    spans = math.collect_math_spans(text)
    displays = [s for s in spans if s.kind == "math_display"]
    assert len(displays) >= 2


def test_eccuacion_inline_es_literal() -> None:
    text = "Inline $E = mc^2$ here."
    spans = math.collect_math_spans(text)
    assert any(s.kind == "math_inline" for s in spans)


def test_prosa_entre_eccuaciones_traducible() -> None:
    text = """intro text

$$x = 1$$

middle text

$$y = 2$$

end text"""
    spans = math.collect_text_spans(text)
    assert any("middle text" in s.value for s in spans)
    assert any("intro text" in s.value for s in spans)


def test_round_trip_conserva_latex_byte_exacto() -> None:
    text = (FIXTURES / "basic.md").read_text(encoding="utf-8")
    spans = math.collect_text_spans(text)
    out = text
    for s in sorted(spans, key=lambda x: -x.start):
        out = out[:s.start] + s.value + out[s.end:]
    assert out == text


def test_entornos_alineados_se_preservan() -> None:
    text = """$$
\\begin{aligned}
a &= b
\\end{aligned}
$$"""
    spans = math.collect_math_spans(text)
    assert spans
    assert "\\begin{aligned}" in spans[0].value


def test_sin_eccuaciones_devuelve_texto_unico() -> None:
    text = "plain prose without equations"
    spans = math.collect_math_spans(text)
    assert spans == []
    text_spans = math.collect_text_spans(text)
    assert len(text_spans) == 1
    assert text_spans[0].value == text


def test_caracter_dolar_en_prosa_no_es_math() -> None:
    text = "the price is $5 today."
    spans = math.collect_math_spans(text)
    assert spans == []