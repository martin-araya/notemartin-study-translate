"""Parser HTML con rangos de bytes y round-trip preservado (fase 072).

Reconoce un subconjunto limitado de HTML embebido (ver
``references/html-contract.md``). No carga scripts, no sigue URLs,
no interpreta JavaScript. La API es análoga a ``mdx_parser.py``:

- ``parse_html(text: str) -> HtmlDocument``: árbol con posiciones
  de bytes verificables.
- ``round_trip(text: str) -> str``: debe recuperar los bytes exactos
  cuando se aplica el patrón de identidad.

Las etiquetas no reconocidas se reportan como ``unsupported_html``
con severidad ``critical``. No se eliminan: se preservan literales.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable


SUPPORTED_TAGS = frozenset({
    "details", "summary", "a", "img", "table", "thead", "tbody", "tfoot",
    "tr", "th", "td", "code", "kbd", "br", "span",
})

UNSAFE_TAGS = frozenset({"script", "style", "iframe", "object", "embed"})

VOID_TAGS = frozenset({"br", "img"})

# Atributos admitidos por el contrato. `href`, `src`, `open`, `id` y `alt`
# son literales funcionales: se preservan, pero traducirlos o moverlos no
# es competencia de este módulo. Un `on*` o un `data-*` de terceros no
# está en la lista y bloquea.
ALLOWED_ATTRIBUTES = frozenset({
    "alt", "aria-label", "aria-labelledby", "aria-describedby", "class",
    "id", "colspan", "rowspan", "headers", "scope", "open", "role",
    "title", "width", "height", "href", "src", "rel", "lang", "dir",
})

FENCE_RE = re.compile(r"^(`{3,}|~{3,})[^\n]*\n.*?\n\1\s*$", re.MULTILINE | re.DOTALL)


def _find_code_fences(text: str) -> list[tuple[int, int]]:
    """Devuelve rangos ``(start, end)`` de cada bloque fenced."""
    return [(m.start(), m.end()) for m in FENCE_RE.finditer(text)]


@dataclass
class Span:
    start: int
    end: int
    kind: str
    value: str = ""

    def to_dict(self) -> dict:
        return {"start": self.start, "end": self.end, "kind": self.kind, "value": self.value}


@dataclass
class HtmlNode:
    kind: str
    start: int
    end: int
    name: str = ""
    self_closing: bool = False
    attributes: list[dict] = field(default_factory=list)
    children: list = field(default_factory=list)
    raw: str = ""

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "start": self.start,
            "end": self.end,
            "name": self.name,
            "self_closing": self.self_closing,
            "attributes": self.attributes,
            "children": [c.to_dict() if isinstance(c, HtmlNode) else c.to_dict() for c in self.children],
            "raw": self.raw,
        }


@dataclass
class HtmlDocument:
    source: str
    nodes: list = field(default_factory=list)
    unsafe_findings: list[dict] = field(default_factory=list)
    unsupported_findings: list[dict] = field(default_factory=list)
    malformed_findings: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "nodes": [n.to_dict() if isinstance(n, HtmlNode) else n.to_dict() for n in self.nodes],
            "unsafe_findings": self.unsafe_findings,
            "unsupported_findings": self.unsupported_findings,
            "malformed_findings": self.malformed_findings,
        }


OPEN_RE = re.compile(r"<([A-Za-z][A-Za-z0-9_-]*)\b([^>]*)>")
CLOSE_RE_TEMPLATE = "</{name}>"
ATTR_RE = re.compile(r"([A-Za-z_:][A-Za-z0-9_.:-]*)\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)")


def _rebase_node(node: HtmlNode, offset: int) -> HtmlNode:
    new_children = []
    for child in node.children:
        if isinstance(child, Span):
            new_children.append(Span(start=child.start + offset, end=child.end + offset, kind=child.kind, value=child.value))
        else:
            new_children.append(_rebase_node(child, offset))
    return HtmlNode(
        kind=node.kind,
        start=node.start + offset,
        end=node.end + offset,
        name=node.name,
        self_closing=node.self_closing,
        attributes=node.attributes,
        children=new_children,
        raw=node.raw,
    )


def _parse_attrs(text: str) -> list[dict]:
    out: list[dict] = []
    for m in ATTR_RE.finditer(text):
        name = m.group(1)
        value = m.group(2)
        if value.startswith("\"") or value.startswith("'"):
            value_kind = "string"
        else:
            value_kind = "bare"
        out.append({"name": name, "kind": value_kind, "value": value})
    return out


def parse_html(text: str) -> HtmlDocument:
    doc = HtmlDocument(source=text)
    fence_ranges = _find_code_fences(text)

    if fence_ranges:
        cursor = 0
        for fence_start, fence_end in fence_ranges:
            if cursor < fence_start:
                doc.nodes.extend(_parse_at(text, cursor, doc, skip_end=fence_start))
            doc.nodes.append(Span(
                start=fence_start,
                end=fence_end,
                kind="code_fenced",
                value=text[fence_start:fence_end],
            ))
            cursor = fence_end
        if cursor < len(text):
            doc.nodes.extend(_parse_at(text, cursor, doc))
    else:
        doc.nodes = _parse_at(text, 0, doc)
    _detect_malformed(text, doc)
    return doc


def _detect_malformed(text: str, doc: HtmlDocument) -> None:
    """Detecta HTML malformado sin repararlo.

    Tres tipos:
    - ``unclosed_tag``: apertura sin cierre al final del documento.
    - ``orphan_close``: cierre sin apertura previa.
    - ``misnested_close``: cierre que no coincide con la apertura
      más reciente.

    INV-03 del proyecto prohíbe la normalización silenciosa. El
    parser solo emite hallazgos; los bytes de salida no se alteran.
    """
    OPEN_TAG_RE = re.compile(r"<([A-Za-z][A-Za-z0-9_-]*)\b[^>]*?(/?)>")
    CLOSE_TAG_RE = re.compile(r"</([A-Za-z][A-Za-z0-9_-]*)\s*>")

    in_fence = [False]
    fence_pos: list[int] = []

    def _in_fence(pos: int) -> bool:
        return any(s <= pos < e for s, e in fence_pos)

    fence_pos.extend(_find_code_fences(text))

    stack: list[tuple[str, int]] = []

    def _fence_ending_at(pos: int) -> int | None:
        for s, e in fence_pos:
            if s <= pos < e:
                return e
        return None

    cursor = 0
    while cursor < len(text):
        if _in_fence(cursor):
            cursor += 1
            continue
        next_open = OPEN_TAG_RE.search(text, cursor)
        next_close = CLOSE_TAG_RE.search(text, cursor)
        if not next_open and not next_close:
            break
        if next_open and (not next_close or next_open.start() < next_close.start()):
            # Una etiqueta puede empezar fuera de un fence y el cursor
            # acabar dentro, o al revés. Lo que decide es dónde **empieza**
            # la coincidencia: si empieza dentro de un fence, es código y
            # no se inspecciona. Antes se comprobaba el cursor, y un
            # `<details>` dentro de un bloque de código abría una pila que
            # cerraba la etiqueta real de más abajo.
            fence_end = _fence_ending_at(next_open.start())
            if fence_end is not None:
                cursor = fence_end
                continue
            tag = next_open.group(1).lower()
            if next_open.group(2) != "/":
                if tag not in VOID_TAGS:
                    stack.append((tag, next_open.start()))
            cursor = next_open.end()
        else:
            fence_end = _fence_ending_at(next_close.start())
            if fence_end is not None:
                cursor = fence_end
                continue
            tag = next_close.group(1).lower()
            if not stack:
                doc.malformed_findings.append({
                    "kind": "orphan_close",
                    "tag": tag,
                    "start": next_close.start(),
                    "end": next_close.end(),
                    "severity": "critical",
                })
            else:
                top_tag, top_start = stack[-1]
                if top_tag != tag:
                    doc.malformed_findings.append({
                        "kind": "misnested_close",
                        "expected": top_tag,
                        "actual": tag,
                        "start": next_close.start(),
                        "end": next_close.end(),
                        "severity": "critical",
                    })
                    while stack and stack[-1][0] != tag:
                        stack.pop()
                    if stack:
                        stack.pop()
                else:
                    stack.pop()
            cursor = next_close.end()

    while stack:
        tag, start = stack.pop()
        doc.malformed_findings.append({
            "kind": "unclosed_tag",
            "tag": tag,
            "start": start,
            "end": len(text),
            "severity": "critical",
        })


def _find_matching_close(text: str, tag_name: str, start: int, limit: int | None = None) -> int:
    """Encuentra el ``</tag>`` que cierra la apertura en ``start``.

    Tiene en cuenta el anidamiento de la misma etiqueta.
    Devuelve -1 si no se encuentra."""
    end_search = limit if limit is not None else len(text)
    open_pattern = re.compile(r"<" + re.escape(tag_name) + r"\b")
    close_pattern = re.compile(r"</" + re.escape(tag_name) + r"\s*>")
    depth = 1
    cursor = start
    while cursor < end_search:
        next_open = open_pattern.search(text, cursor, end_search)
        next_close = close_pattern.search(text, cursor, end_search)
        if not next_close:
            return -1
        if next_open and next_open.start() < next_close.start():
            depth += 1
            cursor = next_open.end()
        else:
            depth -= 1
            if depth == 0:
                return next_close.start()
            cursor = next_close.end()
    return -1


def _parse_at(text: str, offset: int, doc: HtmlDocument, skip_end: int | None = None) -> list:
    nodes: list = []
    cursor = offset
    n = skip_end if skip_end is not None else len(text)
    while cursor < n:
        open_match = OPEN_RE.search(text, cursor, n)
        if not open_match:
            text_end = text.find("<", cursor)
            if text_end == -1:
                text_end = n
            text_chunk = text[cursor:text_end]
            if text_chunk:
                nodes.append(Span(start=cursor, end=text_end, kind="text", value=text_chunk))
                cursor = text_end
            break
        if open_match.start() > cursor:
            text_chunk = text[cursor:open_match.start()]
            if text_chunk.strip():
                nodes.append(Span(start=cursor, end=open_match.start(), kind="text", value=text_chunk))
            cursor = open_match.start()

        tag_name = open_match.group(1).lower()
        attr_text = open_match.group(2)
        attrs = _parse_attrs(attr_text)
        is_self_closing = tag_name in VOID_TAGS or attr_text.rstrip().endswith("/")
        tag_open_end = open_match.end()

        if tag_name in UNSAFE_TAGS:
            close_marker = CLOSE_RE_TEMPLATE.format(name=tag_name)
            close_idx = _find_matching_close(text, tag_name, tag_open_end, limit=n)
            if close_idx == -1:
                close_idx = n
            full_end = close_idx + len(close_marker) if close_idx != n else n
            doc.unsafe_findings.append({
                "kind": f"unsafe_{tag_name}",
                "start": cursor,
                "end": full_end,
                "severity": "critical",
            })
            nodes.append(Span(start=cursor, end=full_end, kind="unsafe_tag", value=text[cursor:full_end]))
            cursor = full_end
            continue

        if is_self_closing:
            node = HtmlNode(
                kind="html_element",
                start=cursor,
                end=tag_open_end,
                name=tag_name,
                self_closing=True,
                attributes=attrs,
                raw=text[cursor:tag_open_end],
            )
            nodes.append(node)
            cursor = tag_open_end
            continue

        close_idx = _find_matching_close(text, tag_name, tag_open_end, limit=n)
        if close_idx == -1:
            if tag_name not in SUPPORTED_TAGS:
                doc.unsupported_findings.append({
                    "kind": "unsupported_html",
                    "tag": tag_name,
                    "start": cursor,
                    "end": tag_open_end,
                    "severity": "critical",
                })
            nodes.append(Span(start=cursor, end=tag_open_end, kind="text", value=text[cursor:tag_open_end]))
            cursor = tag_open_end
            continue

        body_text = text[tag_open_end:close_idx]
        body_nodes = _parse_at(body_text, 0, doc)
        offset_inner = tag_open_end
        rebased_children = []
        for child in body_nodes:
            if isinstance(child, Span):
                rebased_children.append(Span(start=child.start + offset_inner, end=child.end + offset_inner, kind=child.kind, value=child.value))
            else:
                rebased_children.append(_rebase_node(child, offset_inner))

        full_end = close_idx + len(CLOSE_RE_TEMPLATE.format(name=tag_name))
        if tag_name not in SUPPORTED_TAGS:
            doc.unsupported_findings.append({
                "kind": "unsupported_html",
                "tag": tag_name,
                "start": cursor,
                "end": full_end,
                "severity": "critical",
            })
            nodes.append(Span(start=cursor, end=full_end, kind="text", value=text[cursor:full_end]))
            cursor = full_end
            continue

        node = HtmlNode(
            kind="html_element",
            start=cursor,
            end=full_end,
            name=tag_name,
            self_closing=False,
            attributes=attrs,
            children=rebased_children,
            raw=text[cursor:full_end],
        )
        nodes.append(node)
        cursor = full_end

    return nodes


def contract_findings(text: str) -> list[dict]:
    """Hallazgos del contrato HTML en el formato que consume `prepare.py`.

    `parse_html` detecta; esta función traduce esos hallazgos al formato
    común (`type`, `severity`, `evidence`) y añade los dos que el contrato
    promete y el parser no emitía:

    - `unsupported_attribute`: atributo fuera de la lista permitida.
    - `accessibility_missing_alt`: `<img>` sin texto alternativo.

    Sin esta traducción, activar el gate HTML equivalía a permitir
    cualquier HTML: los hallazgos se producían y nadie los consumía.
    """
    doc = parse_html(text)
    findings: list[dict] = []

    for item in doc.unsafe_findings:
        findings.append({
            "type": "unsafe_html",
            "severity": "bloqueante",
            "tag": item.get("tag", ""),
            "evidence": f"etiqueta activa preservada literal: <{item.get('tag', '')}>",
        })
    for item in doc.unsupported_findings:
        findings.append({
            "type": "unsupported_html",
            "severity": "bloqueante",
            "tag": item.get("tag", ""),
            "evidence": (
                f"etiqueta fuera del contrato HTML: <{item.get('tag', '')}> "
                f"(soportadas: {', '.join(sorted(SUPPORTED_TAGS))})"
            ),
        })
    for item in doc.malformed_findings:
        findings.append({
            "type": "malformed_html",
            "severity": "bloqueante",
            "tag": item.get("tag", ""),
            "evidence": (
                f"HTML malformado ({item['kind']}): no se repara ni se normaliza "
                "a escondidas (INV-03)"
            ),
        })

    for node in _iter_elements(doc):
        for attr in node.attributes:
            if attr["name"] not in ALLOWED_ATTRIBUTES:
                findings.append({
                    "type": "unsupported_attribute",
                    "severity": "bloqueante",
                    "tag": node.name,
                    "evidence": (
                        f"atributo fuera del contrato: <{node.name} {attr['name']}=…> "
                        f"(permitidos: {', '.join(sorted(ALLOWED_ATTRIBUTES))})"
                    ),
                })
        if node.name == "img":
            names = {a["name"] for a in node.attributes}
            if not ({"alt", "aria-label"} & names):
                findings.append({
                    "type": "accessibility_missing_alt",
                    "severity": "aviso",
                    "tag": "img",
                    "evidence": "<img> sin alt ni aria-label: la traducción no puede corregirlo sola",
                })

    return findings


def _iter_elements(doc: HtmlDocument):
    def walk(nodes):
        for node in nodes:
            if isinstance(node, Span):
                continue
            yield node
            yield from walk(node.children)
    return walk(doc.nodes)


def round_trip(text: str) -> str:
    doc = parse_html(text)
    spans: list[tuple[int, int]] = []
    for n in doc.nodes:
        spans.append((n.start, n.end))
    spans.sort(key=lambda x: (x[0], x[1]))
    merged: list[tuple[int, int]] = []
    for s, e in spans:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    return "".join(text[s:e] for s, e in merged)


__all__ = [
    "Span", "HtmlNode", "HtmlDocument",
    "SUPPORTED_TAGS", "UNSAFE_TAGS", "VOID_TAGS",
    "parse_html", "round_trip",
]