"""Pruebas de la extensión definition lists (fase 083)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "definitions"
REF = ROOT / "references" / "definition-lists.md"

sys.path.insert(0, str(SCRIPTS))

import definition_lists


def test_referencia_existe_y_declara_correspondencia() -> None:
    assert REF.exists()
    text = REF.read_text(encoding="utf-8")
    assert "Término" in text or "T" in text
    assert "definici" in text.lower()


def test_term_traducible() -> None:
    text = (FIXTURES / "basic.md").read_text(encoding="utf-8")
    segments, _ = definition_lists.extract_definition_segments(text)
    term_segs = [s for s in segments if s.kind == "definition_term"]
    assert any("API" in s.text for s in term_segs)


def test_definition_traducible() -> None:
    text = (FIXTURES / "basic.md").read_text(encoding="utf-8")
    segments, _ = definition_lists.extract_definition_segments(text)
    def_segs = [s for s in segments if s.kind == "definition_def"]
    assert any("Application Programming Interface" in s.text for s in def_segs)


def test_correspondencia_term_y_def() -> None:
    text = (FIXTURES / "basic.md").read_text(encoding="utf-8")
    _, pairs = definition_lists.extract_definition_segments(text)
    assert len(pairs) == 3
    for p in pairs:
        assert p.term.parent == p.defs[0].parent


def test_round_trip_conserva_estructura() -> None:
    text = (FIXTURES / "basic.md").read_text(encoding="utf-8")
    segments, _ = definition_lists.extract_definition_segments(text)
    out = text
    for s in sorted(segments, key=lambda x: -x.start):
        out = out[:s.start] + s.text + out[s.end:]
    assert out == text


def test_sin_definitions_devuelve_vacio() -> None:
    text = "# heading\n\nparagraph only.\n"
    segments, pairs = definition_lists.extract_definition_segments(text)
    assert segments == []
    assert pairs == []


def test_term_sin_definicion_no_produce_par() -> None:
    text = "API\n\nREST\n: Representational State Transfer.\n"
    segments, pairs = definition_lists.extract_definition_segments(text)
    assert len(pairs) == 1
    assert "REST" in pairs[0].term.text