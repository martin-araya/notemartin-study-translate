"""Pruebas del ensamblado MDX por parches (fase 068)."""

from __future__ import annotations

import tempfile
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "mdx"
TMP = Path(tempfile.gettempdir()) / "nst-tests"

sys.path.insert(0, str(SCRIPTS))

import mdx_assemble
import mdx_parser


def fixture_files() -> list[Path]:
    return sorted(FIXTURES.glob("*.mdx"))


def test_assemble_identity_recupera_bytes() -> None:
    for path in fixture_files():
        text = path.read_text(encoding="utf-8")
        source_bytes = text.encode("utf-8")
        segments = mdx_assemble.segments_from_text(text)
        out = mdx_assemble.assemble(source_bytes, segments, identity=True)
        assert out == source_bytes, f"identity round-trip falla en {path.name}"


def test_assemble_sustituye_solo_rangos_autorizados() -> None:
    text = """<Info title="Hello">
  Original content.
</Info>"""
    source_bytes = text.encode("utf-8")
    segments = mdx_assemble.segments_from_text(text)
    title_segment = next(s for s in segments if s.get("attribute") == "title")
    title_segment["translated_text"] = "Hola"
    out = mdx_assemble.assemble(source_bytes, segments)
    assert "Hola" in out.decode("utf-8")
    assert "Hello" not in out.decode("utf-8")


def test_assemble_no_reserializa_el_documento() -> None:
    """El output debe ser exactamente source_bytes con reemplazos
    aplicados en sus posiciones exactas."""
    text = """<Info title="Hi">
  Body
</Info>"""
    source_bytes = text.encode("utf-8")
    segments = mdx_assemble.segments_from_text(text)
    title_segment = next(s for s in segments if s.get("attribute") == "title")
    title_segment["translated_text"] = "Hola"
    out = mdx_assemble.assemble(source_bytes, segments)
    expected = bytearray(source_bytes)
    title_seg = next(s for s in segments if s.get("attribute") == "title")
    expected[title_seg["start"]:title_seg["end"]] = "Hola".encode("utf-8")
    assert bytes(expected) == out


def test_assemble_con_segmentos_mixtos() -> None:
    text = """# Heading

<Info title="Welcome">
  Body text.
</Info>

End.
"""
    source_bytes = text.encode("utf-8")
    segments = mdx_assemble.segments_from_text(text)
    out = mdx_assemble.assemble(source_bytes, segments, identity=True)
    assert out == source_bytes


def test_cli_assemble_identity() -> None:
    text = (FIXTURES / "info_callout.mdx").read_text(encoding="utf-8")
    source_path = TMP / "mdx_assemble_test.mdx"
    source_path.write_text(text, encoding="utf-8")
    segments_path = TMP / "segments_mdx.json"
    segments = mdx_assemble.segments_from_text(text)
    segments_path.write_text(json.dumps(segments, ensure_ascii=False), encoding="utf-8")
    out_path = TMP / "mdx_assemble_out.mdx"
    proc = subprocess.run([
        sys.executable, str(SCRIPTS / "mdx_assemble.py"),
        "--source", str(source_path),
        "--segments-json", str(segments_path),
        "--out", str(out_path),
        "--identity",
    ], capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr
    assert out_path.read_text(encoding="utf-8") == text


def test_assemble_conserva_props_tecnicas() -> None:
    text = (FIXTURES / "cards.mdx").read_text(encoding="utf-8")
    source_bytes = text.encode("utf-8")
    segments = mdx_assemble.segments_from_text(text)
    title_segments = [s for s in segments if s.get("attribute") == "title"]
    if title_segments:
        title_segments[0]["translated_text"] = "Translated"
    out = mdx_assemble.assemble(source_bytes, segments)
    text_out = out.decode("utf-8")
    assert "cols={2}" in text_out
    assert "icon=\"user\"" in text_out
    assert "icon=\"plus\"" in text_out
