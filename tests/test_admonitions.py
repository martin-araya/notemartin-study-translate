"""Pruebas de la extensión admonitions (fase 082)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "admonitions"
REF = ROOT / "references" / "admonitions.md"

sys.path.insert(0, str(SCRIPTS))

import admonitions


def test_referencia_existe_y_lista_tipos() -> None:
    text = REF.read_text(encoding="utf-8")
    for t in ("note", "warning", "tip", "info", "caution"):
        assert t in text, f"falta tipo {t!r} en admonitions.md"


def test_admonition_text_es_traducible() -> None:
    text = (FIXTURES / "basic.md").read_text(encoding="utf-8")
    segments = admonitions.extract_admonition_segments(text)
    assert segments
    warning_segs = [s for s in segments if s.parent == "warning"]
    note_segs = [s for s in segments if s.parent == "note"]
    assert warning_segs
    assert note_segs


def test_admonition_type_literal_no_es_segmento() -> None:
    text = ":::warning\nbody\n:::"
    segments = admonitions.extract_admonition_segments(text)
    assert len(segments) == 1
    assert "warning" not in segments[0].text


def test_warning_no_se_rebaja_a_note() -> None:
    """El validador de cambios debe detectar la rebaja."""
    warning_text = ":::warning\nOriginal warning body\n:::"
    note_text = ":::note\nOriginal warning body\n:::"
    segments_w = admonitions.extract_admonition_segments(warning_text)
    segments_n = admonitions.extract_admonition_segments(note_text)
    assert segments_w[0].parent == "warning"
    assert segments_n[0].parent == "note"
    assert segments_w[0].parent != segments_n[0].parent


def test_round_trip_conserva_tipo_y_contenido() -> None:
    text = (FIXTURES / "basic.md").read_text(encoding="utf-8")
    segments = admonitions.extract_admonition_segments(text)
    out = text
    for s in sorted(segments, key=lambda x: -x.start):
        out = out[:s.start] + s.text + out[s.end:]
    assert out == text


def test_admonition_no_soportada_bloquea() -> None:
    text = ":::danger\nbody\n:::"
    segments = admonitions.extract_admonition_segments(text)
    assert segments == []


def test_sin_admonitions_devuelve_vacio() -> None:
    text = "# heading\n\nno admonitions here\n"
    assert admonitions.extract_admonition_segments(text) == []


def test_multiples_bloques_conservan_tipos() -> None:
    text = ":::warning\nw\n:::\n\ntext\n\n:::note\nn\n:::"
    segments = admonitions.extract_admonition_segments(text)
    parents = [s.parent for s in segments]
    assert parents == ["warning", "note"]