"""Pruebas del parser MDX (fase 062).

Cubre:

- Round-trip byte-exacto para cada fixture sintético.
- Detección de frontmatter, imports, exports y code blocks.
- Sin ejecución de JavaScript.
- Posiciones verificables.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "mdx"

sys.path.insert(0, str(SCRIPTS))

import mdx_parser


def fixture_files() -> list[Path]:
    return sorted(FIXTURES.glob("*.mdx"))


def test_round_trip_para_todos_los_fixtures() -> None:
    for path in fixture_files():
        text = path.read_text(encoding="utf-8")
        assert mdx_parser.round_trip(text) == text, f"round_trip falla en {path.name}"


def test_round_trip_con_expresiones_y_atributos() -> None:
    text = """---
title: Sample
---

import {Info} from '@ui';

export const v = 1;

<Info title="Welcome">
  Use the `{endpoint}` and {`name`}.
</Info>
"""
    assert mdx_parser.round_trip(text) == text


def test_parser_detecta_frontmatter() -> None:
    text = (FIXTURES / "cards.mdx").read_text(encoding="utf-8")
    doc = mdx_parser.parse_mdx(text)
    assert doc.frontmatter is not None
    assert text[doc.frontmatter.start:doc.frontmatter.end].startswith("---")


def test_parser_detecta_imports_y_exports() -> None:
    text = (FIXTURES / "tabs_install.mdx").read_text(encoding="utf-8")
    doc = mdx_parser.parse_mdx(text)
    assert len(doc.imports) == 1
    assert len(doc.exports) == 1
    assert "Tabs" in doc.imports[0].value
    assert "languages" in doc.exports[0].value


def test_parser_detecta_code_blocks() -> None:
    text = (FIXTURES / "tabs_install.mdx").read_text(encoding="utf-8")
    doc = mdx_parser.parse_mdx(text)
    assert len(doc.code_blocks) == 3
    for cb in doc.code_blocks:
        assert cb.kind in ("code_fenced", "code_indented")


def test_parser_no_ejecuta_javascript() -> None:
    text = (FIXTURES / "note_warning.mdx").read_text(encoding="utf-8")
    src = (SCRIPTS / "mdx_parser.py").read_text(encoding="utf-8")
    forbidden = ("eval(", "exec(", "subprocess.run", "subprocess.Popen", "os.system")
    for token in forbidden:
        assert token not in src, f"mdx_parser.py no debe usar {token!r}"
    assert mdx_parser.round_trip(text) == text


def test_rangos_no_cortan_utf8() -> None:
    text = (FIXTURES / "info_callout.mdx").read_text(encoding="utf-8")
    doc = mdx_parser.parse_mdx(text)
    for span in [doc.frontmatter] + doc.imports + doc.exports + doc.code_blocks:
        if span is None:
            continue
        chunk = text[span.start:span.end]
        assert chunk.encode("utf-8").decode("utf-8") == chunk


def test_rangos_no_se_solapan() -> None:
    text = (FIXTURES / "note_warning.mdx").read_text(encoding="utf-8")
    doc = mdx_parser.parse_mdx(text)
    ranges = []
    if doc.frontmatter:
        ranges.append((doc.frontmatter.start, doc.frontmatter.end))
    for s in doc.imports + doc.exports + doc.code_blocks:
        ranges.append((s.start, s.end))
    for i, a in enumerate(ranges):
        for b in ranges[i + 1:]:
            assert a[1] <= b[0] or b[1] <= a[0], f"solapamiento {a} vs {b}"