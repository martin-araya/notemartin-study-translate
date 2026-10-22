"""Pruebas de la extensión wikilinks (fase 087)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "wikilinks"
REF = ROOT / "references" / "wikilinks.md"

sys.path.insert(0, str(SCRIPTS))

import wikilinks


def test_referencia_existe_y_declara_target_literal() -> None:
    assert REF.exists()
    text = REF.read_text(encoding="utf-8")
    assert "literal" in text.lower()


def test_wikilink_target_literal() -> None:
    text = (FIXTURES / "basic.md").read_text(encoding="utf-8")
    segments = wikilinks.extract_wikilink_segments(text)
    assert all(s.kind == "wikilink_alias" for s in segments)
    targets = wikilinks.wikilink_targets(text)
    assert "Installation" in targets
    assert "OtherDoc" in targets


def test_wikilink_alias_traducible() -> None:
    text = (FIXTURES / "basic.md").read_text(encoding="utf-8")
    segments = wikilinks.extract_wikilink_segments(text)
    alias_segs = [s for s in segments if s.kind == "wikilink_alias"]
    assert any("deploy guide" in s.text for s in alias_segs)
    assert any("runbook" in s.text for s in alias_segs)


def test_wikilink_con_seccion_literal() -> None:
    text = "[[File#Section]]"
    segments = wikilinks.extract_wikilink_segments(text)
    assert segments == []
    targets = wikilinks.wikilink_targets(text)
    assert "File#Section" in targets


def test_round_trip_conserva_target() -> None:
    text = (FIXTURES / "basic.md").read_text(encoding="utf-8")
    segments = wikilinks.extract_wikilink_segments(text)
    out = text
    for s in sorted(segments, key=lambda x: -x.start):
        out = out[:s.start] + s.text + out[s.end:]
    assert out == text


def test_alias_con_seccion() -> None:
    text = "[[File#Section|Alias here]]"
    segments = wikilinks.extract_wikilink_segments(text)
    assert segments
    assert segments[0].parent == "File#Section"
    assert segments[0].text == "Alias here"


def test_wikilink_duplicado_no_falla() -> None:
    text = "[[File]] y [[File|alias]]"
    targets = wikilinks.wikilink_targets(text)
    assert targets == ["File", "File"]


def test_sin_wikilinks_devuelve_vacio() -> None:
    text = "plain prose without links"
    assert wikilinks.extract_wikilink_segments(text) == []
    assert wikilinks.wikilink_targets(text) == []