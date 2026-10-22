"""Pruebas de la extensión frontmatter translate-allowlist (fase 088)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "frontmatter"

sys.path.insert(0, str(SCRIPTS))

import frontmatter_translate


def test_campo_listado_es_traducible() -> None:
    text = (FIXTURES / "with_translatable.md").read_text(encoding="utf-8")
    segments = frontmatter_translate.extract_frontmatter_segments(text, ["title", "summary"])
    fields = {s.parent for s in segments}
    assert "title" in fields
    assert "summary" in fields
    assert "version" not in fields


def test_campo_no_listado_es_literal() -> None:
    text = """---
title: Hello
version: 1
---
"""
    findings = frontmatter_translate.frontmatter_findings(text, ["title"])
    names = {f["name"] for f in findings}
    assert "version" in names
    assert "title" not in names


def test_tipos_yaml_no_se_cambian() -> None:
    text = """---
title: Hello
tags: [a, b, c]
---
"""
    segments = frontmatter_translate.extract_frontmatter_segments(text, ["title"])
    assert segments
    assert segments[0].text == "Hello"


def test_frontmatter_policy_preserve_no_segmentos() -> None:
    """Con ``allowed`` vacío (equivalente a ``preserve`` efectivo), no
    se emite ningún segmento, ni siquiera para campos listados."""
    text = """---
title: Hello
---
body
"""
    segments = frontmatter_translate.extract_frontmatter_segments(text, [])
    assert segments == []


def test_frontmatter_inexistente_no_segmentos() -> None:
    text = "no frontmatter here"
    assert [] == frontmatter_translate.extract_frontmatter_segments(text, ["title"])


def test_round_trip_conserva_campos_listados() -> None:
    text = (FIXTURES / "with_translatable.md").read_text(encoding="utf-8")
    segments = frontmatter_translate.extract_frontmatter_segments(text, ["title", "summary"])
    out = text
    for s in sorted(segments, key=lambda x: -x.start):
        out = out[:s.start] + s.text + out[s.end:]
    assert out == text


def test_valores_con_formato_yaml_complejo_no_se_traducen() -> None:
    text = """---
metadata: {key: value, other: thing}
list:
  - a
  - b
---
"""
    findings = frontmatter_translate.frontmatter_findings(text, ["title"])
    assert any(f["name"] == "metadata" for f in findings)
    assert any(f["name"] == "list" for f in findings)