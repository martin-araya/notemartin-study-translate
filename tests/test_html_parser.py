"""Pruebas del parser HTML (fase 072)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "html"

sys.path.insert(0, str(SCRIPTS))

import html_parser


def fixture_files() -> list[Path]:
    return sorted(FIXTURES.glob("*.md"))


def test_round_trip_para_todos_los_fixtures() -> None:
    for path in fixture_files():
        text = path.read_text(encoding="utf-8")
        assert html_parser.round_trip(text) == text, f"round_trip falla en {path.name}"


def test_parser_detecta_etiquetas_soportadas() -> None:
    text = (FIXTURES / "details_summary.md").read_text(encoding="utf-8")
    doc = html_parser.parse_html(text)
    collected: list = []

    def _walk(n):
        if isinstance(n, html_parser.HtmlNode):
            collected.append(n.name)
            for c in n.children:
                _walk(c)

    for n in doc.nodes:
        _walk(n)
    assert "details" in collected
    assert "summary" in collected


def test_parser_detecta_script_como_unsafe() -> None:
    text = "# t\n\n<script>alert(1)</script>\n"
    doc = html_parser.parse_html(text)
    assert any(f["kind"] == "unsafe_script" for f in doc.unsafe_findings)


def test_parser_detecta_iframe_como_unsafe() -> None:
    text = "before <iframe src=\"x\"></iframe> after"
    doc = html_parser.parse_html(text)
    assert any(f["kind"] == "unsafe_iframe" for f in doc.unsafe_findings)


def test_parser_no_ejecuta_javascript() -> None:
    text = "<a href=\"x\" onclick=\"alert(1)\">link</a>"
    src = (SCRIPTS / "html_parser.py").read_text(encoding="utf-8")
    forbidden = ("eval(", "exec(", "subprocess.run", "subprocess.Popen", "os.system", "urllib.request")
    for token in forbidden:
        assert token not in src, f"html_parser.py no debe usar {token!r}"
    doc = html_parser.parse_html(text)
    assert html_parser.round_trip(text) == text


def test_parser_detecta_etiqueta_no_soportada() -> None:
    text = "<custom-thing>x</custom-thing>"
    doc = html_parser.parse_html(text)
    assert any(f["kind"] == "unsupported_html" for f in doc.unsupported_findings)


def test_rangos_no_cortan_utf8() -> None:
    text = (FIXTURES / "kbd_code_inline.md").read_text(encoding="utf-8")
    doc = html_parser.parse_html(text)
    for n in doc.nodes:
        chunk = text[n.start:n.end]
        assert chunk.encode("utf-8").decode("utf-8") == chunk


def test_etiquetas_void_no_buscansu_close() -> None:
    text = "x<br />y<br>z"
    doc = html_parser.parse_html(text)
    assert html_parser.round_trip(text) == text


def test_atributos_escapados_se_preservan() -> None:
    text = "<a title=\"Hello \"\"world\"\"\">link</a>"
    assert html_parser.round_trip(text) == text


def test_no_ejecuta_estilos_inlines() -> None:
    text = "<style>body { color: red; }</style>rest"
    doc = html_parser.parse_html(text)
    assert any(f["kind"] == "unsafe_style" for f in doc.unsafe_findings)
    assert html_parser.round_trip(text) == text