"""Pruebas de la extensión footnotes (fase 081)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "footnotes"
REF = ROOT / "references" / "footnotes.md"

sys.path.insert(0, str(SCRIPTS))

import footnotes


def test_referencia_existe_y_declara_id_literal() -> None:
    assert REF.exists()
    text = REF.read_text(encoding="utf-8")
    assert "literal" in text.lower()
    assert "[^id]" in text or "[^id]" in text


def test_footnote_text_es_traducible() -> None:
    text = (FIXTURES / "basic.md").read_text(encoding="utf-8")
    segments = footnotes.extract_footnote_segments(text)
    assert segments
    assert any(s.parent == "1" for s in segments)
    assert any("Confirm" in s.text for s in segments)


def test_footnote_id_literal_no_es_segmento() -> None:
    text = (FIXTURES / "basic.md").read_text(encoding="utf-8")
    segments = footnotes.extract_footnote_segments(text)
    ids_in_segments = [s.parent for s in segments]
    assert "1" in ids_in_segments
    assert "2" in ids_in_segments
    for s in segments:
        assert s.kind == "footnote_text"


def test_round_trip_conserva_id_y_referencia() -> None:
    text = (FIXTURES / "basic.md").read_text(encoding="utf-8")
    segments = footnotes.extract_footnote_segments(text)
    out = text
    for s in sorted(segments, key=lambda x: -x.start):
        out = out[:s.start] + s.text + out[s.end:]
    assert out == text


def test_referencias_en_cuerpo_no_emiten_segmentos() -> None:
    text = "body[^1]\n\n[^1]: footer"
    segments = footnotes.extract_footnote_segments(text)
    assert len(segments) == 1
    assert segments[0].kind == "footnote_text"


def test_footnote_inexistente_no_segmento() -> None:
    text = "no footnotes here."
    assert footnotes.extract_footnote_segments(text) == []


def test_multiples_footnotes_conservan_ids() -> None:
    text = "[^a]: one\n[^b]: two\n[^c]: three"
    segments = footnotes.extract_footnote_segments(text)
    parents = [s.parent for s in segments]
    assert parents == ["a", "b", "c"]


def test_footnote_segment_posiciona_en_definicion() -> None:
    text = (FIXTURES / "basic.md").read_text(encoding="utf-8")
    segments = footnotes.extract_footnote_segments(text)
    for s in segments:
        chunk = text[s.start:s.end]
        assert chunk == s.text