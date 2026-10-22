"""Selector de hijos textuales traducibles en MDX (fase 064).

Toma el árbol producido por ``mdx_parser.parse_mdx`` y devuelve los
segmentos de texto visibles que pueden traducirse, junto con el
componente padre y los hermanos preservados.

Reglas:

- Solo texto plano entre etiquetas se considera traducible. Las
  expresiones ``{...}`` y los bloques de código se excluyen.
- Si un componente no está en el contrato MDX
  (``references/mdx-contract.md``), su texto se marca como
  ``unsupported_component`` y se excluye.
- Los atributos permitidos (``title``, ``label``, ``altText``)
  producen segmentos adicionales marcados con ``kind: attribute``.

API:

- ``select_translatable(text: str, contract: dict | None = None) -> list[Segment]``
- ``Segment``: ``dataclass`` con ``start``, ``end``, ``kind``,
  ``parent``, ``text``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable

from mdx_parser import (
    MdxDocument,
    MdxNode,
    Span,
    parse_mdx,
)
from mdx_protect import extract_protections


DEFAULT_SUPPORTED = {
    "Info", "Note", "Warning", "Tabs", "TabItem", "TabPanel",
    "Card", "CardGroup", "Callout", "CodeGroup",
}
DEFAULT_TRANSLATABLE_ATTRS = {"title", "label", "altText"}

# Atributos que ejecutan código o resuelven recursos. No se traducen ni se
# tocan: su presencia bloquea el archivo (`references/mdx-contract.md` §4).
EXECUTABLE_PROPS = {
    "onClick", "onChange", "onSubmit", "onLoad", "onError",
    "dangerouslySetInnerHTML", "href", "src", "style", "as",
}
UNSAFE_TAGS = {"script", "style"}
# MDX v2 con pipes: la sintaxis no está en el contrato y bloquea.
PIPE_RE = re.compile(r"export\s+const\s+\w+\s*=\s*\|>")


@dataclass
class Segment:
    start: int
    end: int
    kind: str
    parent: str = ""
    text: str = ""
    attribute: str = ""

    def to_dict(self) -> dict:
        return {
            "start": self.start,
            "end": self.end,
            "kind": self.kind,
            "parent": self.parent,
            "text": self.text,
            "attribute": self.attribute,
        }


def select_translatable(text: str, contract: dict | None = None) -> list[Segment]:
    doc = parse_mdx(text)
    supported = set((contract or {}).get("components", DEFAULT_SUPPORTED))
    translatable_attrs = set((contract or {}).get("translatable_attributes", DEFAULT_TRANSLATABLE_ATTRS))

    segments: list[Segment] = []
    for node in doc.nodes:
        if isinstance(node, Span):
            continue
        segments.extend(_node_segments(text, node, supported, translatable_attrs, parent_name=node.name))
    segments.sort(key=lambda s: (s.start, s.end))
    return segments


def _node_segments(
    text: str,
    node: MdxNode,
    supported: set[str],
    translatable_attrs: set[str],
    parent_name: str = "",
) -> list[Segment]:
    out: list[Segment] = []
    is_unsupported = bool(node.name) and node.name not in supported
    if is_unsupported:
        out.append(Segment(
            start=node.start,
            end=node.end,
            kind="unsupported_component",
            parent=node.name,
            text=text[node.start:node.end],
        ))

    effective_parent = node.name if node.name else parent_name

    for attr in node.attributes:
        if attr["name"] in translatable_attrs and attr["kind"] == "string":
            value = attr["value"][1:-1]
            attr_offset = text.find(attr["value"], node.start, node.end)
            if attr_offset == -1:
                continue
            out.append(Segment(
                start=attr_offset + 1,
                end=attr_offset + 1 + len(value),
                kind="attribute",
                parent=effective_parent,
                attribute=attr["name"],
                text=value,
            ))

    for child in node.children:
        if isinstance(child, Span):
            if child.kind == "text":
                cleaned = _strip_expressions(child.value)
                if cleaned:
                    out.append(Segment(
                        start=child.start,
                        end=child.end,
                        kind="text",
                        parent=effective_parent,
                        text=cleaned,
                    ))
            continue
        out.extend(_node_segments(text, child, supported, translatable_attrs, parent_name=effective_parent))
    return out


def _strip_expressions(text: str) -> str:
    out: list[str] = []
    cursor = 0
    for m in re.compile(r"\{[^{}]*\}").finditer(text):
        out.append(text[cursor:m.start()])
        cursor = m.end()
    out.append(text[cursor:])
    return "".join(out)


def iter_components(doc: MdxDocument):
    """Cada nodo JSX del árbol, incluidos los anidados."""
    for node in doc.nodes:
        if isinstance(node, Span):
            continue
        yield node
        for child in node.children:
            if isinstance(child, MdxNode):
                if child.kind == "jsx_child_document":
                    yield from _iter_nodes(child.children)
                else:
                    yield from _iter_nodes([child])


def _iter_nodes(nodes):
    for node in nodes:
        if isinstance(node, Span):
            continue
        yield node
        for child in node.children:
            if isinstance(child, MdxNode):
                yield from _iter_nodes([child])


def contract_findings(text: str, contract: dict | None = None) -> list[dict]:
    """Aplicación del contrato MDX a un documento.

    Es la diferencia entre «encender el módulo» y «permitir cualquier
    JSX»: antes, activar el gate quitaba el hallazgo entero. Ahora cada
    componente, atributo o patrón fuera del contrato produce su propio
    hallazgo bloqueante, que es lo que `references/mdx-contract.md` §2 y §4
    prometen.

    Devuelve dicts con `type`, `severity`, `evidence` y `component`, en el
    mismo formato que emite `prepare.detect_findings`.
    """
    supported = set((contract or {}).get("components", DEFAULT_SUPPORTED))
    doc = parse_mdx(text)
    findings: list[dict] = []
    seen: set[str] = set()

    for node in iter_components(doc):
        name = node.name
        if name and name not in supported and name not in seen:
            seen.add(name)
            findings.append({
                "type": "unsupported_component",
                "severity": "bloqueante",
                "component": name,
                "evidence": (
                    f"componente fuera del contrato MDX: <{name}> "
                    f"(soportados: {', '.join(sorted(supported))})"
                ),
            })
        for attr in node.attributes:
            if attr["name"] in EXECUTABLE_PROPS:
                findings.append({
                    "type": "unsupported_attribute",
                    "severity": "bloqueante",
                    "component": name,
                    "evidence": f"atributo con código o recurso: {name}.{attr['name']}",
                })

    lowered = text.lower()
    for tag in sorted(UNSAFE_TAGS):
        if f"<{tag}" in lowered:
            findings.append({
                "type": "unsafe_html",
                "severity": "bloqueante",
                "component": tag,
                "evidence": f"bloque <{tag}> inline: no se carga ni se preserva en el flujo",
            })
    if PIPE_RE.search(text):
        findings.append({
            "type": "unsupported_mdx_syntax",
            "severity": "bloqueante",
            "component": "",
            "evidence": "MDX v2 con pipes (export const x = |>): fuera del contrato",
        })
    return findings


def link_tab_panels(text: str) -> list[dict]:
    """Empareja cada ``<TabItem value="X">`` con el panel que
    referencia ese valor. Reconoce tres formas de anclar el panel:

    - ``<TabPanel id="X">``
    - ``<div id="X">`` o cualquier etiqueta con ``id="X"``
    - Encabezado Markdown con anchor ``{#X}``
    - Atributo ``data-tab="X"``

    Devuelve una lista de pares ``{tabitem_value, panel_kind,
    panel_id, byte_range_tabitem, byte_range_panel}``. No es
    error que falte el panel; simplemente no aparece en el resultado.
    """
    import re

    doc = parse_mdx(text)

    tabitems: list[dict] = []
    for node in doc.nodes:
        if isinstance(node, Span):
            continue
        _collect_tabitems(text, node, tabitems)

    panels_by_value: dict[str, dict] = {}
    for ti in tabitems:
        v = ti["value"]
        idx = _find_panel(text, v)
        if idx is None:
            continue
        panels_by_value[v] = idx

    pairs: list[dict] = []
    for ti in tabitems:
        v = ti["value"]
        panel = panels_by_value.get(v)
        if panel is None:
            continue
        pairs.append({
            "tabitem_value": v,
            "panel_kind": panel["kind"],
            "panel_byte_range": panel["byte_range"],
            "tabitem_byte_range": ti["byte_range"],
            "tabitem_label": ti.get("label"),
        })
    return pairs


def _collect_tabitems(text: str, node, out: list[dict]) -> None:
    from mdx_parser import MdxNode

    if node.name == "TabItem":
        value_attr = next((a for a in node.attributes if a["name"] == "value"), None)
        if value_attr and value_attr["kind"] == "string":
            attr_offset = text.find(value_attr["value"], node.start, node.end)
            label_attr = next((a for a in node.attributes if a["name"] == "label"), None)
            label = None
            if label_attr and label_attr["kind"] == "string":
                label = label_attr["value"][1:-1]
            out.append({
                "value": value_attr["value"][1:-1],
                "label": label,
                "byte_range": {"start": node.start, "end": node.end},
            })
    for child in node.children:
        if isinstance(child, MdxNode):
            _collect_tabitems(text, child, out)


def _find_panel(text: str, value: str) -> dict | None:
    """Busca un anclaje cuyo identificador sea ``value``."""
    import re

    candidates: list[tuple[str, str, int, int]] = []
    patterns = [
        (r'<TabPanel\b[^>]*\bid\s*=\s*"' + re.escape(value) + r'"', "tabpanel"),
        (r'<\w+\b[^>]*\bid\s*=\s*"' + re.escape(value) + r'"', "element_id"),
        (r'<\w+\b[^>]*\bdata-tab\s*=\s*"' + re.escape(value) + r'"', "data_tab"),
        (r'^#{1,6}\s+[^\n]*\s*\{#' + re.escape(value) + r'\}', "heading_anchor"),
    ]
    for pat, kind in patterns:
        m = re.search(pat, text, re.MULTILINE)
        if m:
            candidates.append((kind, m.group(0), m.start(), m.end()))
    if not candidates:
        return None
    candidates.sort(key=lambda c: c[2])
    kind, raw, start, end = candidates[0]
    return {"kind": kind, "value": value, "byte_range": {"start": start, "end": end}, "raw": raw}


__all__ = ["Segment", "select_translatable", "link_tab_panels"]