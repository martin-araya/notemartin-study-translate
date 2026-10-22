"""Extractor de literales protegidos para MDX (fase 063).

Devuelve los rangos de bytes que **no deben traducirse** en un
archivo MDX. La API principal es:

- ``extract_protections(text: str) -> list[dict]``: lista de
  ``ProtectedSpan`` con ``kind``, ``byte_range`` y ``value``.
- ``protected_values(text: str) -> list[str]``: lista plana de
  valores a marcar como literales protegidos.

Kinds reconocidos (alineados con el parser):

- ``frontmatter``: bloque YAML inicial.
- ``import``: sentencias ``import`` completas.
- ``export``: sentencias ``export`` completas.
- ``code_fenced`` y ``code_indented``: bloques de código Markdown.
- ``expression``: cualquier ``{...}`` JSX.
- ``jsx_open``, ``jsx_close``, ``jsx_self_closing``: las propias
  etiquetas.
- ``attribute_value``: valor entre comillas o expresión de un
  atributo no permitido por la lista de la fase 065.
"""

from __future__ import annotations

from typing import Iterable

from mdx_parser import (
    MdxDocument,
    MdxNode,
    Span,
    parse_mdx,
)

JSX_EXPR_RE = __import__("re").compile(r"\{[^{}]*\}")


def _flatten(node: MdxNode | Span) -> Iterable[Span]:
    if isinstance(node, Span):
        yield node
        return
    for child in node.children:
        yield from _flatten(child)


def _attributes_block(attrs: list[dict], source: str) -> list[Span]:
    out: list[Span] = []
    for a in attrs:
        if a["kind"] == "expression":
            start = source.find("{", a["value"].find, 0) if False else -1
        out.append(Span(start=-1, end=-1, kind="attribute", name=a["name"]))
    return out


def extract_protections(text: str) -> list[dict]:
    doc = parse_mdx(text)
    spans: list[dict] = []

    if doc.frontmatter is not None:
        spans.append(doc.frontmatter.to_dict())

    for s in doc.imports:
        spans.append(s.to_dict())
    for s in doc.exports:
        spans.append(s.to_dict())
    for s in doc.code_blocks:
        spans.append(s.to_dict())

    def _walk(node) -> None:
        for child in node.children:
            if isinstance(child, Span):
                if child.kind == "text":
                    for m in JSX_EXPR_RE.finditer(child.value):
                        abs_start = child.start + m.start()
                        abs_end = child.start + m.end()
                        spans.append({
                            "start": abs_start,
                            "end": abs_end,
                            "kind": "expression",
                            "value": m.group(0),
                        })
            else:
                _walk(child)

    for node in doc.nodes:
        if isinstance(node, Span):
            continue
        spans.append({
            "start": node.start,
            "end": node.end,
            "kind": "jsx_element",
            "name": node.name,
            "value": text[node.start:node.end],
        })
        for attr in node.attributes:
            if attr["kind"] == "expression":
                attr_offset = text.find(attr["value"], node.start, node.end)
                if attr_offset == -1:
                    continue
                spans.append({
                    "start": attr_offset,
                    "end": attr_offset + len(attr["value"]),
                    "kind": "expression",
                    "value": attr["value"],
                })
        _walk(node)

    spans.sort(key=lambda s: (s["start"], s["end"]))
    return spans


def protected_values(text: str) -> list[str]:
    return [s["value"] for s in extract_protections(text) if s.get("value")]


TECHNICAL_PROP_NAMES = frozenset({
    "id", "name", "key", "className", "style", "href", "src", "onClick", "as",
    "value", "icon", "type", "severity", "cols", "defaultValue",
})


def extract_technical_props(
    text: str,
    translatable_attributes: set[str] | None = None,
) -> list[dict]:
    """Devuelve todos los atributos cuyo nombre no está en la lista
    traducible. Cada entrada lleva ``component``, ``name``, ``value``,
    ``kind`` (``string`` o ``expression``) y ``byte_range``."""
    from mdx_parser import parse_mdx

    if translatable_attributes is None:
        from mdx_selector import DEFAULT_TRANSLATABLE_ATTRS
        translatable_attributes = DEFAULT_TRANSLATABLE_ATTRS

    doc = parse_mdx(text)
    props: list[dict] = []

    def _walk(node) -> None:
        for attr in node.attributes:
            if attr["name"] in translatable_attributes:
                continue
            if attr["name"] not in TECHNICAL_PROP_NAMES:
                continue
            attr_offset = text.find(attr["value"], node.start, node.end)
            if attr_offset == -1:
                continue
            props.append({
                "component": node.name,
                "name": attr["name"],
                "kind": attr["kind"],
                "value": attr["value"],
                "byte_range": {"start": attr_offset, "end": attr_offset + len(attr["value"])},
                "literal_value": attr["value"][1:-1] if attr["kind"] == "string" else None,
            })
        for child in node.children:
            if not isinstance(child, __import__("mdx_parser").MdxNode):
                continue
            _walk(child)

    for node in doc.nodes:
        from mdx_parser import MdxNode
        if isinstance(node, MdxNode):
            _walk(node)

    props.sort(key=lambda p: (p["byte_range"]["start"], p["byte_range"]["end"]))
    return props


__all__ = ["extract_protections", "protected_values", "extract_technical_props", "TECHNICAL_PROP_NAMES"]