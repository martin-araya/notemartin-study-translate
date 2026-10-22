"""Pruebas del ensamblado HTML por parches (fase 075)."""

from __future__ import annotations

import tempfile
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "html"
TMP = Path(tempfile.gettempdir()) / "nst-tests"

sys.path.insert(0, str(SCRIPTS))

import html_assemble


def fixture_files() -> list[Path]:
    return sorted(FIXTURES.glob("*.md"))


def test_assemble_identity_recupera_bytes() -> None:
    for path in fixture_files():
        text = path.read_text(encoding="utf-8")
        source_bytes = text.encode("utf-8")
        segments = html_assemble.segments_from_text(text)
        out = html_assemble.assemble(source_bytes, segments, identity=True)
        assert out == source_bytes, f"identity round-trip falla en {path.name}"


def test_assemble_sustituye_solo_rangos_autorizados() -> None:
    text = "<details><summary>Original summary</summary>body</details>"
    source_bytes = text.encode("utf-8")
    segments = html_assemble.segments_from_text(text)
    summary_seg = next(s for s in segments if s.get("tag") == "summary" and s.get("kind") == "text")
    summary_seg["translated_text"] = "Translated summary"
    out = html_assemble.assemble(source_bytes, segments)
    assert "Translated summary" in out.decode("utf-8")
    assert "Original summary" not in out.decode("utf-8")


def test_assemble_preserva_anidamiento() -> None:
    text = (FIXTURES / "details_nested.md").read_text(encoding="utf-8")
    source_bytes = text.encode("utf-8")
    segments = html_assemble.segments_from_text(text)
    out = html_assemble.assemble(source_bytes, segments, identity=True)
    assert out == source_bytes


def test_assemble_preserva_atributos_prohibidos() -> None:
    text = (FIXTURES / "kbd_code_inline.md").read_text(encoding="utf-8")
    source_bytes = text.encode("utf-8")
    segments = html_assemble.segments_from_text(text)
    out = html_assemble.assemble(source_bytes, segments)
    assert b"src=\"https://example.com/logo.png\"" in out
    assert b"href=\"https://example.com\"" in out or b"https://example.com" in out


def test_assemble_sin_reserializar() -> None:
    text = "<a title=\"Welcome\" href=\"x\">link</a>"
    source_bytes = text.encode("utf-8")
    segments = html_assemble.segments_from_text(text)
    title_seg = next(s for s in segments if s.get("attribute") == "title")
    title_seg["translated_text"] = "Hola"
    out = html_assemble.assemble(source_bytes, segments)
    expected = bytearray(source_bytes)
    expected[title_seg["start"]:title_seg["end"]] = "Hola".encode("utf-8")
    assert bytes(expected) == out


def test_assemble_conserva_unsafe_tags() -> None:
    text = "# t\n\n<script>alert(1)</script>\n"
    source_bytes = text.encode("utf-8")
    segments = html_assemble.segments_from_text(text)
    out = html_assemble.assemble(source_bytes, segments, identity=True)
    assert b"<script>alert(1)</script>" in out


def test_cli_assemble_identity() -> None:
    text = (FIXTURES / "details_summary.md").read_text(encoding="utf-8")
    source_path = TMP / "html_assemble_test.md"
    source_path.write_text(text, encoding="utf-8")
    segments_path = TMP / "segments_html.json"
    segments_path.write_text(json.dumps(html_assemble.segments_from_text(text), ensure_ascii=False), encoding="utf-8")
    out_path = TMP / "html_assemble_out.md"
    proc = subprocess.run([
        sys.executable, str(SCRIPTS / "html_assemble.py"),
        "--source", str(source_path),
        "--segments-json", str(segments_path),
        "--out", str(out_path),
        "--identity",
    ], capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr
    assert out_path.read_text(encoding="utf-8") == text
