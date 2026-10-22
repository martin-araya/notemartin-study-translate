"""Pruebas de la regla de tabs y paneles (fase 067)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "mdx"

sys.path.insert(0, str(SCRIPTS))

import mdx_parser
import mdx_selector


def test_tabitem_value_es_literal() -> None:
    text = (FIXTURES / "tabs_install.mdx").read_text(encoding="utf-8")
    segments = mdx_selector.select_translatable(text)
    value_segments = [s for s in segments if s.kind == "attribute" and s.attribute == "value"]
    assert value_segments == []


def test_panel_id_coincide_con_tabitem_value() -> None:
    text = """---
title: Tabs demo
---

<Tabs defaultValue="node">
  <TabItem value="node" label="Node.js">
    Body for Node.
  </TabItem>
  <TabItem value="python" label="Python">
    Body for Python.
  </TabItem>
</Tabs>

<div id="node">More details for Node.</div>
<div id="python">More details for Python.</div>
"""
    pairs = mdx_selector.link_tab_panels(text)
    values = {p["tabitem_value"] for p in pairs}
    assert values == {"node", "python"}


def test_tabitem_value_no_se_altera_al_traducir_label() -> None:
    text = """<TabItem value="node" label="Node.js">Body</TabItem>"""
    segments = mdx_selector.select_translatable(text)
    label_segments = [s for s in segments if s.kind == "attribute" and s.attribute == "label"]
    assert any(s.text == "Node.js" for s in label_segments)
    value_segments = [s for s in segments if s.kind == "attribute" and s.attribute == "value"]
    assert value_segments == []


def test_tabitem_sin_panel_no_bloquea() -> None:
    text = """<TabItem value="node" label="Node.js">Body</TabItem>"""
    pairs = mdx_selector.link_tab_panels(text)
    assert pairs == []


def test_tabitem_emparenta_con_data_tab() -> None:
    text = """<Tabs>
  <TabItem value="node">body</TabItem>
</Tabs>
<section data-tab="node">panel content</section>
"""
    pairs = mdx_selector.link_tab_panels(text)
    assert len(pairs) == 1
    assert pairs[0]["tabitem_value"] == "node"
    assert pairs[0]["panel_kind"] == "data_tab"


def test_panel_kind_es_tabpanel_si_existe() -> None:
    text = """<Tabs>
  <TabItem value="alpha">body</TabItem>
</Tabs>
<TabPanel id="alpha">panel content</TabPanel>
"""
    pairs = mdx_selector.link_tab_panels(text)
    assert len(pairs) == 1
    assert pairs[0]["panel_kind"] == "tabpanel"