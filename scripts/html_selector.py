"""Selector de nodos de texto HTML traducibles (fase 073).

Toma el árbol producido por ``html_parser.parse_html`` y devuelve
los segmentos visibles que pueden traducirse. Las reglas siguen
``references/html-contract.md``:

- Las etiquetas listadas como "texto traducible" producen segmentos
  de texto y, en su caso, de atributos visibles.
- Las etiquetas listadas como "contenedor" se recorren recursivamente
  sin producir segmento propio.
- Las etiquetas ``unsafe_*`` (script, style, iframe, object, embed)
  se ignoran: ya están preservadas por el parser.
- Los atributos de cada etiqueta siguen una lista blanca
  (``translatable_attributes``); los demás son literales.

API:

- ``select_translatable(text: str, contract: dict | None = None) -> list[Segment]``
- ``Segment``: ``dataclass`` con ``start``, ``end``, ``kind``
  (``text`` o ``attribute``), ``tag``, ``attribute`` y ``text``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from html_parser import HtmlNode, HtmlDocument, Span, parse_html


TAGS_WITH_TEXT = {
    "summary", "a", "th", "td", "code", "kbd", "span",
}
CONTAINER_TAGS = {
    "details", "table", "thead", "tbody", "tfoot", "tr", "br",
}
NON_TEXT_TAGS = {"img"}
DEFAULT_TRANSLATABLE_ATTRS = {"title", "aria-label", "alt"}


@dataclass
class Segment:
    start: int
    end: int
    kind: str
    tag: str = ""
    attribute: str = ""
    text: str = ""

    def to_dict(self) -> dict:
        return {
            "start": self.start,
            "end": self.end,
            "kind": self.kind,
            "tag": self.tag,
            "attribute": self.attribute,
            "text": self.text,
            "translated_text": self.text,
        }


def select_translatable(text: str, contract: dict | None = None) -> list[Segment]:
    doc = parse_html(text)
    translatable_attrs = set((contract or {}).get("attributes", DEFAULT_TRANSLATABLE_ATTRS))
    segments: list[Segment] = []

    def _walk(node: HtmlNode) -> None:
        for attr in node.attributes:
            if attr["name"] in translatable_attrs and attr["kind"] == "string":
                value = attr["value"][1:-1]
                attr_offset = text.find(attr["value"], node.start, node.end)
                if attr_offset == -1:
                    continue
                segments.append(Segment(
                    start=attr_offset + 1,
                    end=attr_offset + 1 + len(value),
                    kind="attribute",
                    tag=node.name,
                    attribute=attr["name"],
                    text=value,
                ))
        if node.name in TAGS_WITH_TEXT:
            for child in node.children:
                if isinstance(child, Span) and child.kind == "text":
                    if child.value.strip():
                        segments.append(Segment(
                            start=child.start,
                            end=child.end,
                            kind="text",
                            tag=node.name,
                            text=child.value,
                        ))
        for child in node.children:
            if isinstance(child, HtmlNode):
                _walk(child)

    for node in doc.nodes:
        if isinstance(node, HtmlNode):
            _walk(node)

    segments.sort(key=lambda s: (s.start, s.end))
    return segments


__all__ = ["Segment", "select_translatable"]