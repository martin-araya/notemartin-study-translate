"""Pruebas de la extensión directives (fase 084)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "directives"
REF = ROOT / "references" / "directives.md"

sys.path.insert(0, str(SCRIPTS))

import directives


def test_referencia_existe_y_lista_cerrada() -> None:
    assert REF.exists()
    text = REF.read_text(encoding="utf-8")
    for d in ("param", "type", "returns", "rtype", "raises"):
        assert d in text, f"falta {d!r} en directives.md"


def test_directiva_conocida_traduce_contenido() -> None:
    text = (FIXTURES / "basic.md").read_text(encoding="utf-8")
    segments, unknown = directives.extract_directive_segments(text)
    param_segs = [s for s in segments if s.parent == "param"]
    assert param_segs
    assert not unknown


def test_directiva_desconocida_se_reporta() -> None:
    text = """:custom x: descripción
:param y: otra
"""
    segments, unknown = directives.extract_directive_segments(text)
    assert any(u["name"] == "custom" and u["severity"] == "critical" for u in unknown)
    assert any(s.parent == "param" for s in segments)


def test_round_trip_conserva_nombre_y_parametro() -> None:
    text = (FIXTURES / "basic.md").read_text(encoding="utf-8")
    segments, _ = directives.extract_directive_segments(text)
    out = text
    for s in sorted(segments, key=lambda x: -x.start):
        out = out[:s.start] + s.text + out[s.end:]
    assert out == text


def test_directivas_adyacentes_no_se_confunden() -> None:
    text = """:param a: one
:param b: two
:param c: three
"""
    segments, _ = directives.extract_directive_segments(text)
    bodies = [s.text for s in segments if s.parent == "param"]
    assert bodies == ["one", "two", "three"]


def test_sin_directivas_devuelve_vacio() -> None:
    text = "# heading\n\nparagraph only.\n"
    segments, unknown = directives.extract_directive_segments(text)
    assert segments == []
    assert unknown == []