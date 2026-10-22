"""Parser MDX con rangos de bytes y round-trip preservado (fase 062).

No ejecuta JavaScript. Reconoce:

- Frontmatter YAML (preservado literal).
- ``import ... from ...;`` (preservado literal).
- ``export ...;`` (preservado literal).
- Etiquetas JSX ``<Component ...>...</Component>`` y
  ``<Component ... />`` con sus atributos.
- Expresiones ``{...}`` dentro de JSX o como hijos.
- Bloques de código fenced (preservados literales).
- Bloques de código indentado (preservados literales).
- Texto plano entre componentes.

La API pública:

- ``parse_mdx(text: str) -> MdxDocument``: árbol con posiciones de
  bytes verificables.
- ``round_trip(text: str) -> str``: sustituye cada nodo por su
  texto original. Debe recuperar los bytes exactos.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable


@dataclass
class Span:
    start: int
    end: int
    kind: str
    value: str = ""

    def to_dict(self) -> dict:
        return {
            "start": self.start,
            "end": self.end,
            "kind": self.kind,
            "value": self.value,
        }


@dataclass
class MdxNode:
    kind: str
    start: int
    end: int
    name: str = ""
    self_closing: bool = False
    attributes: list[dict] = field(default_factory=list)
    children: list["MdxNode | Span"] = field(default_factory=list)
    raw: str = ""

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "start": self.start,
            "end": self.end,
            "name": self.name,
            "self_closing": self.self_closing,
            "attributes": self.attributes,
            "children": [c.to_dict() if isinstance(c, MdxNode) else c.to_dict() for c in self.children],
            "raw": self.raw,
        }


@dataclass
class MdxDocument:
    source: str
    frontmatter: Span | None = None
    imports: list[Span] = field(default_factory=list)
    exports: list[Span] = field(default_factory=list)
    code_blocks: list[Span] = field(default_factory=list)
    nodes: list[MdxNode | Span] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "frontmatter": self.frontmatter.to_dict() if self.frontmatter else None,
            "imports": [s.to_dict() for s in self.imports],
            "exports": [s.to_dict() for s in self.exports],
            "code_blocks": [s.to_dict() for s in self.code_blocks],
            "nodes": [n.to_dict() if isinstance(n, MdxNode) else n.to_dict() for n in self.nodes],
        }


FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
IMPORT_RE = re.compile(r"^(import\s+[^;]+?;)\s*$", re.MULTILINE)
EXPORT_RE = re.compile(r"^(export\s+(?:const|let|var|function|default)[^;{]*?(?:\{[^}]*?\}|;|[^;{]+?;?))\s*$", re.MULTILINE)
CODE_FENCE_RE = re.compile(r"^(`{3,}|~{3,})[^\n]*\n.*?\n\1\s*$", re.MULTILINE | re.DOTALL)
CODE_INDENT_RE = re.compile(r"^(    [^\n]+(?:\n    [^\n]+)*\n?)+", re.MULTILINE)
JSX_TAG_OPEN_RE = re.compile(r"<([A-Z][A-Za-z0-9_]*)([^>]*?)(/?)>")
JSX_TAG_CLOSE_RE = "</{name}>".format
ATTR_RE = re.compile(r"([A-Za-z][A-Za-z0-9_:-]*)\s*=\s*(\{[^}]*\}|\"[^\"]*\"|'[^']*')")
EXPR_RE = re.compile(r"\{([^{}]*)\}")


def _is_inside(start: int, ranges: Iterable[tuple[int, int]]) -> bool:
    for s, e in ranges:
        if s <= start < e:
            return True
    return False


def _rebase_node(node: MdxNode, offset: int) -> MdxNode:
    new_children = []
    for child in node.children:
        if isinstance(child, Span):
            new_children.append(Span(
                start=child.start + offset,
                end=child.end + offset,
                kind=child.kind,
                value=child.value,
            ))
        else:
            new_children.append(_rebase_node(child, offset))
    return MdxNode(
        kind=node.kind,
        start=node.start + offset,
        end=node.end + offset,
        name=node.name,
        self_closing=node.self_closing,
        attributes=node.attributes,
        children=new_children,
        raw=node.raw,
    )


def parse_mdx(text: str) -> MdxDocument:
    doc = MdxDocument(source=text)
    pos = 0

    fm_match = FRONTMATTER_RE.match(text)
    if fm_match:
        doc.frontmatter = Span(
            start=fm_match.start(),
            end=fm_match.end(),
            kind="frontmatter",
            value=fm_match.group(0),
        )
        pos = fm_match.end()

    reserved_ranges: list[tuple[int, int]] = []
    if doc.frontmatter:
        reserved_ranges.append((doc.frontmatter.start, doc.frontmatter.end))

    for m in IMPORT_RE.finditer(text, pos):
        if _is_inside(m.start(), reserved_ranges):
            continue
        doc.imports.append(Span(start=m.start(), end=m.end(), kind="import", value=m.group(1)))
        reserved_ranges.append((m.start(), m.end()))

    for m in EXPORT_RE.finditer(text, pos):
        if _is_inside(m.start(), reserved_ranges):
            continue
        doc.exports.append(Span(start=m.start(), end=m.end(), kind="export", value=m.group(1)))
        reserved_ranges.append((m.start(), m.end()))

    for m in CODE_FENCE_RE.finditer(text, pos):
        if _is_inside(m.start(), reserved_ranges):
            continue
        doc.code_blocks.append(Span(start=m.start(), end=m.end(), kind="code_fenced", value=m.group(0)))
        reserved_ranges.append((m.start(), m.end()))

    for m in CODE_INDENT_RE.finditer(text, pos):
        if _is_inside(m.start(), reserved_ranges):
            continue
        doc.code_blocks.append(Span(start=m.start(), end=m.end(), kind="code_indented", value=m.group(0)))
        reserved_ranges.append((m.start(), m.end()))

    cursor = pos
    n = len(text)
    while cursor < n:
        if _is_inside(cursor, reserved_ranges):
            next_reserved = min((e for s, e in reserved_ranges if s <= cursor < e), default=n)
            cursor = next_reserved
            continue

        newline_idx = text.find("\n", cursor)
        line_end = newline_idx if newline_idx != -1 else n
        include_newline = newline_idx != -1
        line_end_with_nl = line_end + 1 if include_newline else line_end

        line = text[cursor:line_end]

        jsx_match = JSX_TAG_OPEN_RE.search(line)
        if jsx_match:
            leading_ws = jsx_match.start()
            tag_open_start = cursor + leading_ws
            tag_name = jsx_match.group(1)
            attr_text = jsx_match.group(2)
            self_closing = jsx_match.group(3) == "/"
            tag_open_end = cursor + jsx_match.end()
            attrs = _parse_attributes(attr_text)

            if leading_ws > 0:
                doc.nodes.append(Span(
                    start=cursor,
                    end=tag_open_start,
                    kind="text",
                    value=text[cursor:tag_open_start],
                ))

            if self_closing:
                node = MdxNode(
                    kind="jsx_element",
                    start=cursor,
                    end=tag_open_end,
                    name=tag_name,
                    self_closing=True,
                    attributes=attrs,
                    raw=text[cursor:tag_open_end],
                )
                doc.nodes.append(node)
                cursor = tag_open_end
                continue

            close_marker = JSX_TAG_CLOSE_RE(name=tag_name)
            close_idx = text.find(close_marker, tag_open_end)
            if close_idx == -1:
                doc.nodes.append(Span(
                    start=cursor,
                    end=line_end_with_nl,
                    kind="text",
                    value=text[cursor:line_end_with_nl],
                ))
                cursor = line_end_with_nl
                continue

            body_text = text[tag_open_end:close_idx]
            body_doc = parse_mdx(body_text)
            offset = tag_open_end
            rebased_children: list = []
            for child in body_doc.nodes:
                if isinstance(child, Span):
                    rebased_children.append(Span(
                        start=child.start + offset,
                        end=child.end + offset,
                        kind=child.kind,
                        value=child.value,
                    ))
                else:
                    rebased_children.append(_rebase_node(child, offset))
            rebased_imports = [
                Span(start=s.start + offset, end=s.end + offset, kind=s.kind, value=s.value)
                for s in body_doc.imports
            ]
            rebased_exports = [
                Span(start=s.start + offset, end=s.end + offset, kind=s.kind, value=s.value)
                for s in body_doc.exports
            ]
            rebased_code = [
                Span(start=s.start + offset, end=s.end + offset, kind=s.kind, value=s.value)
                for s in body_doc.code_blocks
            ]
            nested_nodes = [MdxNode(
                kind="jsx_child_document",
                start=tag_open_end,
                end=close_idx,
                name="",
                children=rebased_children,
                raw=body_text,
            )]
            for s in rebased_imports + rebased_exports + rebased_code:
                nested_nodes.append(s)

            full_end = close_idx + len(close_marker)
            node = MdxNode(
                kind="jsx_element",
                start=cursor,
                end=full_end,
                name=tag_name,
                self_closing=False,
                attributes=attrs,
                children=nested_nodes,
                raw=text[cursor:full_end],
            )
            doc.nodes.append(node)
            cursor = full_end
            continue

        doc.nodes.append(Span(
            start=cursor,
            end=line_end_with_nl,
            kind="text",
            value=text[cursor:line_end_with_nl],
        ))
        cursor = line_end_with_nl

    return doc


def _parse_attributes(text: str) -> list[dict]:
    attrs: list[dict] = []
    for m in ATTR_RE.finditer(text):
        name = m.group(1)
        raw_value = m.group(2)
        kind = "string" if raw_value.startswith(('"', "'")) else "expression"
        attrs.append({"name": name, "kind": kind, "value": raw_value})
    return attrs


def round_trip(text: str) -> str:
    """Sustituye cada nodo por sí mismo. Debe recuperar los bytes."""
    doc = parse_mdx(text)
    return _round_trip_doc(doc)


def _round_trip_doc(doc: MdxDocument) -> str:
    spans: list[tuple[int, int]] = []
    if doc.frontmatter is not None:
        spans.append((doc.frontmatter.start, doc.frontmatter.end))
    for s in doc.imports + doc.exports + doc.code_blocks:
        spans.append((s.start, s.end))
    for n in doc.nodes:
        spans.append((n.start, n.end))
    spans.sort(key=lambda x: (x[0], x[1]))
    merged: list[tuple[int, int]] = []
    for s, e in spans:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    return "".join(doc.source[s:e] for s, e in merged)


__all__ = [
    "Span",
    "MdxNode",
    "MdxDocument",
    "parse_mdx",
    "round_trip",
]