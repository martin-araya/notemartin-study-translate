"""Pruebas del extractor de protecciones MDX (fase 063)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "mdx"

sys.path.insert(0, str(SCRIPTS))

import mdx_protect


def test_extract_protections_incluye_imports_y_exports() -> None:
    text = (FIXTURES / "tabs_install.mdx").read_text(encoding="utf-8")
    spans = mdx_protect.extract_protections(text)
    kinds = {s["kind"] for s in spans}
    assert "import" in kinds
    assert "export" in kinds


def test_extract_protections_incluye_code_blocks() -> None:
    text = (FIXTURES / "tabs_install.mdx").read_text(encoding="utf-8")
    spans = mdx_protect.extract_protections(text)
    code_kinds = {s["kind"] for s in spans if s["kind"].startswith("code_")}
    assert "code_fenced" in code_kinds
    assert len([s for s in spans if s["kind"] == "code_fenced"]) == 3


def test_extract_protections_incluye_expresiones() -> None:
    text = (FIXTURES / "note_warning.mdx").read_text(encoding="utf-8")
    spans = mdx_protect.extract_protections(text)
    expressions = [s for s in spans if s["kind"] == "expression"]
    assert any("severity" in s["value"] for s in expressions)


def test_extract_protections_bytes_exactos() -> None:
    text = (FIXTURES / "note_warning.mdx").read_text(encoding="utf-8")
    spans = mdx_protect.extract_protections(text)
    for s in spans:
        if s["kind"] == "expression":
            assert text[s["start"]:s["end"]] == s["value"]


def test_protected_values_incluye_imports() -> None:
    text = (FIXTURES / "info_callout.mdx").read_text(encoding="utf-8")
    values = mdx_protect.protected_values(text)
    assert any("import" in v and "Callout" in v for v in values)


def test_no_solapamiento_en_protecciones_top_level() -> None:
    """Las protecciones de frontera (frontmatter, imports, exports,
    code_blocks) no se solapan entre sí. JSX y expresiones anidadas
    sí pueden solaparse con su JSX padre."""
    text = (FIXTURES / "cards.mdx").read_text(encoding="utf-8")
    spans = mdx_protect.extract_protections(text)
    boundary_kinds = {"frontmatter", "import", "export", "code_fenced", "code_indented"}
    ranges = [(s["start"], s["end"]) for s in spans if s["kind"] in boundary_kinds]
    ranges.sort()
    for a, b in zip(ranges, ranges[1:]):
        assert a[1] <= b[0], f"solapamiento entre protecciones de frontera {a} vs {b}"