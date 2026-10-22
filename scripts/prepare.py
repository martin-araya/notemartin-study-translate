"""Preparación y clasificación de archivos Markdown.

Operaciones que soporta:

- ``--out <ruta>`` — veredictos por archivo (existente desde 019).
- ``--segments <ruta>`` — segmentos traducibles con literales protegidos
  e IDs deterministas (fases 016, 017, 018).
- ``--snapshots <ruta>`` — instantáneas estructurales con encabezados,
  enlaces, tablas y ``structure_hash`` (fase 019).

El parser es ``markdown-it-py`` fijado en
``references/markdown-contract.md`` §8. Las posiciones de byte se
derivan de ``token.map`` (líneas 0-indexadas) mediante un ``LineIndex``
local. La regla de no partir codepoints UTF-8 se aplica en cada corte.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote

from markdown_it import MarkdownIt
from markdown_it.token import Token

# Extractores de los módulos opcionales (081-090). prepare.py es núcleo y
# un módulo opcional no puede ser dependencia del flujo básico, así que
# importa **las librerías puras** de detección, nunca sus CLIs. Lo que el
# perfil enciende es la capacidad de tratar la construcción, no el
# módulo entero.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import admonitions  # noqa: E402
import directives  # noqa: E402
import html_parser  # noqa: E402
import mermaid_adapter  # noqa: E402
import mdx_selector  # noqa: E402

PARSER = (
    MarkdownIt("commonmark", {"html": True, "linkify": False, "typographer": False})
    .enable("table")
    .enable("strikethrough")
)

HTML_BLOCKLIST = {
    "div", "section", "article", "aside", "nav", "figure", "main",
    "header", "footer", "form", "button", "iframe", "script", "style",
}
JSX_RE = re.compile(r"<[A-Z][A-Za-z0-9]*(\s|/?>|$)")
WIKILINK_RE = re.compile(r"\[\[[^\]]+\]\]")
HTML_BLOCK_RE = re.compile(
    r"<(" + "|".join(HTML_BLOCKLIST) + r")(\s|/?>)", re.IGNORECASE
)
ADMONITION_RE = re.compile(r"^:::(?P<kind>[A-Za-z][\w-]*)?[ \t]*$")
# Una lista de definiciones es un término en una línea y su definición en
# la siguiente, ambas indentadas. Sin este patrón el perfil podía encender
# `definition_lists` y el gate no tenía nada que levantar.
DEFINITION_LIST_RE = re.compile(r"^:\s+\S.*$", re.MULTILINE)
INLINE_CODE_RE = re.compile(r"(`+)(?:(?!\1)[\s\S])*?\1")
FRONTMATTER_RE = re.compile(r"\A---[ \t]*\r?\n[\s\S]*?\r?\n---[ \t]*(?:\r?\n|\Z)")
ANCHOR_RE_BYTES = re.compile(rb'<a\s+id="([^"]+)"\s*></a>')
EXTERNAL_LINK_RE = re.compile(r"^(https?://|mailto:)", re.IGNORECASE)


class LineIndex:
    """Indexa bytes de inicio de cada línea sobre los bytes originales.

    Los offsets son offsets de bytes en el archivo original, no offsets
    de caracteres en una versión decodificada. Esto evita confusión
    con secuencias multibyte al traducir a rangos de bytes reales.
    """

    def __init__(self, source_bytes: bytes) -> None:
        self.source_bytes = source_bytes
        self.starts: list[int] = [0]
        for i, b in enumerate(source_bytes):
            if b == 0x0A:
                self.starts.append(i + 1)
        self.starts.append(len(source_bytes))

    def line_count(self) -> int:
        return len(self.starts) - 1

    def line_range_bytes(self, line_start: int, line_end: int) -> tuple[int, int]:
        """Convierte un rango de líneas a offsets de bytes.

        ``map = [line_start, line_end]`` en markdown-it-py usa
        ``line_end`` exclusivo: el bloque termina justo antes de esa
        línea. Por eso ``byte_end`` se toma de ``starts[line_end]``.
        """
        if line_start < 0:
            return (0, 0)
        max_line = self.line_count()
        if line_start > max_line:
            line_start = max_line
        if line_end < line_start:
            line_end = line_start
        if line_end > max_line:
            line_end = max_line
        byte_start = self.starts[line_start]
        byte_end = self.starts[line_end] if line_end < len(self.starts) else len(self.source_bytes)
        return (byte_start, byte_end)


def strip_inline_code(text: str) -> str:
    """Quita los tramos de código inline.

    Un tramo entre comillas invertidas es un literal protegido (INV-05): su
    contenido no es prosa del documento. Sin esta máscara, `Array<T>` se
    detectaría como componente JSX y `` `[[x]]` `` como wikilink.
    """
    return INLINE_CODE_RE.sub(" ", text)


def strip_frontmatter(text: str) -> str:
    """Quita el bloque de frontmatter inicial.

    El frontmatter se preserva literal por política, así que sus aliases y
    rutas no son construcciones del cuerpo del documento.
    """
    return FRONTMATTER_RE.sub("", text, count=1)


def detect_findings(text: str) -> list[dict]:
    """Detecta construcciones bloqueantes fuera de fences.

    La comprobación se hace sobre la prosa real: sin fences, sin código
    inline y sin frontmatter. Esas tres zonas están preservadas y nunca
    blockean por sí solas.

    Cada hallazgo lleva el dato que necesita el gate del módulo para
    decidir: el tipo de admonition, el nombre de la directiva o el tipo de
    lista de definiciones. Un hallazgo sin ese dato solo permite apagar o
    encender todo el módulo, que es exactamente lo que el contrato no
    permite.
    """
    segments = split_fences(text)
    outside = strip_inline_code(strip_frontmatter(
        "".join(content for kind, content in segments if kind == "text")
    ))
    findings: list[dict] = []

    if JSX_RE.search(outside):
        findings.append({
            "type": "mdx_component",
            "severity": "bloqueante",
            "evidence": "componente JSX/MDX fuera de fence",
        })

    for line in outside.splitlines():
        m = ADMONITION_RE.match(line)
        if not m:
            continue
        admonition_type = (m.groupdict().get("kind") or "").lower() or None
        findings.append({
            "type": "directive_admonition",
            "severity": "bloqueante",
            "admonition_type": admonition_type,
            "evidence": f"directiva :::{admonition_type} fuera de fence",
        })
        if admonition_type and admonition_type not in admonitions.SUPPORTED:
            findings.append({
                "type": "unsupported_admonition",
                "severity": "bloqueante",
                "admonition_type": admonition_type,
                "evidence": (
                    f"tipo de admonition no soportado: {admonition_type} "
                    f"(soportados: {', '.join(sorted(admonitions.SUPPORTED))})"
                ),
            })
        break

    if HTML_BLOCK_RE.search(outside):
        findings.append({
            "type": "html_embebido",
            "severity": "bloqueante",
            "evidence": "etiqueta HTML fuera del conjunto CommonMark",
        })

    if WIKILINK_RE.search(outside):
        findings.append({
            "type": "wikilink",
            "severity": "bloqueante",
            "evidence": "wikilink [[...]] fuera de fence",
        })

    if DEFINITION_LIST_RE.search(outside):
        findings.append({
            "type": "definition_list",
            "severity": "bloqueante",
            "evidence": "lista de definiciones fuera de fence",
        })

    # Las directivas de documentación viven en bloques de código: solo se
    # informa de las que no son código traducible, nunca se traducen.
    _segments, unknown = directives.extract_directive_segments(outside)
    for item in unknown:
        findings.append({
            "type": "unsupported_directive",
            "severity": "bloqueante",
            "directive_name": item["name"],
            "evidence": f"directiva no soportada: :{item['name']}:",
        })

    for kind, content in segments:
        if kind != "code":
            continue
        if re.match(r"^```mermaid\b", content) or re.match(r"^~~~mermaid\b", content):
            findings.append({
                "type": "mermaid_in_fence",
                "severity": "info",
                "evidence": "Mermaid dentro de fence; se preserva",
            })
            for problem in mermaid_adapter.mermaid_findings(content):
                findings.append({
                    "type": "mermaid_unsupported",
                    "severity": "info",
                    "evidence": f"Mermaid no soportado: {problem['evidence']}",
                })
            break

    return findings


def split_fences(text: str) -> list[tuple[str, str]]:
    lines = text.splitlines(keepends=True)
    out: list[tuple[str, str]] = []
    in_fence = False
    buf: list[str] = []
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            if in_fence:
                buf.append(line)
                out.append(("code", "".join(buf)))
                buf = []
                in_fence = False
            else:
                if buf:
                    out.append(("text", "".join(buf)))
                    buf = []
                buf.append(line)
                in_fence = True
        else:
            buf.append(line)
    if buf:
        out.append(("code" if in_fence else "text", "".join(buf)))
    return out


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def document_id(source_bytes: bytes) -> str:
    return "doc-" + sha256_hex(source_bytes)[:8]


def segment_id(doc_id: str, byte_start: int, byte_end: int, structural_type: str) -> str:
    payload = f"{doc_id}:{byte_start}:{byte_end}:{structural_type}"
    return "seg-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:8]


def safe_byte_slice(source_bytes: bytes, start: int, end: int) -> tuple[int, int]:
    """Ajusta el corte al límite de codepoint UTF-8 más cercano.

    Un índice ``i`` es un corte válido si el byte que hay **en** ``i`` no
    es un byte de continuación: ``i`` es entonces el primer byte de un
    codepoint y sirve tanto para abrir como para cerrar un rango.

    La comprobación anterior miraba el byte anterior a ``i`` y, cuando
    veía un byte de continuación, **recortaba** el final hacia atrás. Con
    un literal multibyte eso deja el último byte fuera: `ƒ` (0xC6 0x92)
    quedaba en 0xC6 solo y se guardaba como U+FFFD. La protección de
    código seguía marcando el segmento, pero con un valor corrupto.
    """
    n = len(source_bytes)
    start = max(0, min(start, n))
    end = max(start, min(end, n))

    def is_continuation(idx: int) -> bool:
        if idx < 0 or idx >= n:
            return False
        return (source_bytes[idx] & 0xC0) == 0x80

    while start < end and is_continuation(start):
        start += 1
    while end < n and is_continuation(end):
        end += 1
    return (start, end)


def inline_code_spans(line_bytes: bytes) -> list[tuple[int, int]]:
    """Tramos de código inline de una línea, como offsets dentro de ella."""
    spans: list[tuple[int, int]] = []
    pos = 0
    fence = re.compile(rb"`+")
    while True:
        opening = fence.search(line_bytes, pos)
        if opening is None:
            break
        mark = opening.group(0)
        closing = line_bytes.find(mark, opening.end())
        if closing == -1:
            break
        spans.append((opening.end(), closing))
        pos = closing + len(mark)
    return spans


def inline_spans_by_token(
    source_bytes: bytes, idx: "LineIndex", tokens: list[Token]
) -> dict[int, tuple[int, int]]:
    """Empareja cada token `code_inline` con su tramo en la fuente.

    La clave es la posición del token en la lista. La búsqueda por
    posición, y no la primera coincidencia de la línea, es lo que
    distingue dos tramos inline en la misma línea: antes ambos recibían
    el valor del primero y el segundo literal desaparecía.
    """
    cursor_by_line: dict[tuple[int, int], int] = {}
    out: dict[int, tuple[int, int]] = {}
    for position, tok in enumerate(tokens):
        if tok.type != "code_inline" or tok.map is None:
            continue
        line_s, line_e = tok.map
        bs, be = idx.line_range_bytes(line_s, line_e)
        key = (bs, be)
        cursor = cursor_by_line.get(key, 0)
        cursor_by_line[key] = cursor + 1
        spans = inline_code_spans(source_bytes[bs:be])
        if cursor < len(spans):
            start, end = spans[cursor]
            out[position] = safe_byte_slice(source_bytes, bs + start, bs + end)
    return out


def raw_destination(src: str, line_bytes: bytes) -> str:
    """Destino de enlace o imagen tal como aparece en la fuente.

    markdown-it normaliza el href con percent-encoding: un destino con
    acentos llega como `res%C3%BAmenes/…` mientras la fuente tiene
    `resúmenes/…`. Guardar la forma normalizada haría que el literal no
    apareciera en el texto (el paquete lo daba por perdido) y que al
    ensamblar se cambiaran los bytes de origen.
    """
    if not src or "%" not in src:
        return src
    try:
        decoded = unquote(src)
    except Exception:
        return src
    return decoded if decoded.encode("utf-8") in line_bytes else src


def extract_protected_literals(
    source_bytes: bytes, idx: LineIndex, tokens: list[Token]
) -> list[dict]:
    """Enumera los literales protegidos detectados por markdown-it-py."""
    literals: list[dict] = []

    # markdown-it entrega los tramos de código inline en el orden del
    # documento, así que el n-ésimo tramo de una línea corresponde al
    # n-ésimo token. Se emparejan una sola vez, antes del recorrido.
    inline_positions = inline_spans_by_token(source_bytes, idx, tokens)
    cursor_by_line: dict[tuple[int, int], int] = {}

    for position, tok in enumerate(tokens):
        if tok.type == "code_inline" and tok.content is not None and tok.map is not None:
            line_s, line_e = tok.map
            bs, be = idx.line_range_bytes(line_s, line_e)
            span = inline_positions.get(position)
            if span is not None:
                inner_start, inner_end = span
                literals.append({
                    "type": "code_inline",
                    "byte_range": {"start": inner_start, "end": inner_end},
                    "value": source_bytes[inner_start:inner_end].decode("utf-8", errors="replace"),
                })
            else:
                literals.append({
                    "type": "code_inline",
                    "byte_range": {"start": bs, "end": be},
                    "value": tok.content,
                })

        elif tok.type == "fence" and tok.map is not None:
            line_s, line_e = tok.map
            bs, be = idx.line_range_bytes(line_s, line_e)
            bs, be = safe_byte_slice(source_bytes, bs, be)
            literals.append({
                "type": "code_fenced",
                "byte_range": {"start": bs, "end": be},
                "language": (tok.info or "").strip() or None,
                "value": source_bytes[bs:be].decode("utf-8", errors="replace"),
            })

        elif tok.type == "code_block" and tok.map is not None:
            line_s, line_e = tok.map
            bs, be = idx.line_range_bytes(line_s, line_e)
            bs, be = safe_byte_slice(source_bytes, bs, be)
            literals.append({
                "type": "code_indented",
                "byte_range": {"start": bs, "end": be},
                "value": source_bytes[bs:be].decode("utf-8", errors="replace"),
            })

        elif tok.type == "image" and tok.attrs is not None and tok.map is not None:
            line_s, line_e = tok.map
            bs, be = idx.line_range_bytes(line_s, line_e)
            src = tok.attrs.get("src")
            alt = tok.content or ""
            literals.append({
                "type": "image_destination",
                "byte_range": {"start": bs, "end": be},
                "value": src or "",
            })
            if alt:
                literals.append({
                    "type": "image_alt",
                    "byte_range": {"start": bs, "end": be},
                    "value": alt,
                })

        elif tok.type == "image" and tok.attrs is not None and tok.map is not None:
            line_s, line_e = tok.map
            bs, be = idx.line_range_bytes(line_s, line_e)
            src = raw_destination(tok.attrs.get("src") or "", source_bytes[bs:be])
            alt = tok.content or ""
            literals.append({
                "type": "image_destination",
                "byte_range": {"start": bs, "end": be},
                "value": src,
            })
            if alt:
                literals.append({
                    "type": "image_alt",
                    "byte_range": {"start": bs, "end": be},
                    "value": alt,
                })

        elif tok.type == "inline" and tok.children and tok.map is not None:
            line_s, line_e = tok.map
            bs, be = idx.line_range_bytes(line_s, line_e)
            line_bytes = source_bytes[bs:be]
            cursor = cursor_by_line.get((bs, be), 0)
            for child in tok.children:
                if child.type == "code_inline" and child.content is not None:
                    spans = inline_code_spans(line_bytes)
                    if cursor < len(spans):
                        inner_start, inner_end = safe_byte_slice(
                            source_bytes, bs + spans[cursor][0], bs + spans[cursor][1]
                        )
                        cursor += 1
                        literals.append({
                            "type": "code_inline",
                            "byte_range": {"start": inner_start, "end": inner_end},
                            "value": source_bytes[inner_start:inner_end].decode("utf-8", errors="replace"),
                        })
                    else:
                        literals.append({
                            "type": "code_inline",
                            "byte_range": {"start": bs, "end": be},
                            "value": child.content,
                        })
                elif child.type == "image" and child.attrs is not None:
                    src = raw_destination(child.attrs.get("src") or "", line_bytes)
                    alt = child.content or ""
                    literals.append({
                        "type": "image_destination",
                        "byte_range": {"start": bs, "end": be},
                        "value": src,
                    })
                    if alt:
                        literals.append({
                            "type": "image_alt",
                            "byte_range": {"start": bs, "end": be},
                            "value": alt,
                        })
            cursor_by_line[(bs, be)] = cursor

        elif tok.type in ("html_inline", "html_block") and tok.map is not None:
            line_s, line_e = tok.map
            bs, be = idx.line_range_bytes(line_s, line_e)
            bs, be = safe_byte_slice(source_bytes, bs, be)
            literals.append({
                "type": tok.type,
                "byte_range": {"start": bs, "end": be},
                "value": source_bytes[bs:be].decode("utf-8", errors="replace"),
            })

        elif tok.type == "inline" and tok.children and tok.map is not None:
            line_s, line_e = tok.map
            bs, be = idx.line_range_bytes(line_s, line_e)
            line_bytes = source_bytes[bs:be]
            for child in tok.children:
                if child.type == "code_inline" and child.content is not None:
                    markup = (child.markup or "`").encode("utf-8")
                    pattern = re.escape(markup).replace(re.escape(b"`"), b"`") + rb"+"
                    pat = re.compile(pattern + rb"(.*?)" + pattern, re.DOTALL)
                    m = pat.search(line_bytes)
                    if m:
                        inner_bytes = m.group(1)
                        inner_start = bs + m.start(1)
                        inner_end = inner_start + len(inner_bytes)
                        inner_start, inner_end = safe_byte_slice(source_bytes, inner_start, inner_end)
                        literals.append({
                            "type": "code_inline",
                            "byte_range": {"start": inner_start, "end": inner_end},
                            "value": source_bytes[inner_start:inner_end].decode("utf-8", errors="replace"),
                        })
                    else:
                        literals.append({
                            "type": "code_inline",
                            "byte_range": {"start": bs, "end": be},
                            "value": child.content,
                        })
                elif child.type == "image" and child.attrs is not None:
                    src = child.attrs.get("src")
                    alt = child.content or ""
                    literals.append({
                        "type": "image_destination",
                        "byte_range": {"start": bs, "end": be},
                        "value": src or "",
                    })
                    if alt:
                        literals.append({
                            "type": "image_alt",
                            "byte_range": {"start": bs, "end": be},
                            "value": alt,
                        })

    for m in ANCHOR_RE_BYTES.finditer(source_bytes):
        bs, be = safe_byte_slice(source_bytes, m.start(), m.end())
        literals.append({
            "type": "anchor",
            "byte_range": {"start": bs, "end": be},
            "value": m.group(0).decode("utf-8", errors="replace"),
        })

    seen: set[tuple[int, int, str]] = set()
    unique = []
    for lit in literals:
        br = lit["byte_range"]
        key = (br["start"], br["end"], lit["type"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(lit)
    literals = unique

    literals.sort(key=lambda lit: (lit["byte_range"]["start"], lit["byte_range"]["end"]))
    return literals


def narrow_range_to_text(source_bytes: bytes, seg: dict) -> dict:
    """Ajusta el rango del segmento a los bytes reales de su texto.

    Los rangos se calculan a nivel de línea, así que incluyen el marcador
    `## `, el cierre de hashes y el salto de línea final. Eso es correcto
    para el modo identidad, pero al ensamblar una traducción el rango se
    sustituye entero por `translated_text` y esos bytes se pierden: el
    documento entregado se queda sin encabezados.

    Aquí el rango se reduce a la prosa exacta. Los marcadores quedan fuera
    del parche y `assemble.py` los copia literalmente.
    """
    text = seg.get("translatable_text") or ""
    if not text:
        return seg
    br = seg["byte_range"]
    span = source_bytes[br["start"]:br["end"]]
    needle = text.encode("utf-8")
    offset = span.find(needle)
    if offset < 0:
        return seg
    start = br["start"] + offset
    end = start + len(needle)
    if (start, end) == (br["start"], br["end"]):
        return seg
    narrowed = dict(seg)
    narrowed["byte_range"] = {"start": start, "end": end}
    return narrowed


def extract_segments(
    source_bytes: bytes, idx: LineIndex, tokens: list[Token], doc_id: str
) -> list[dict]:
    """Convierte el árbol de tokens en segmentos con literales."""
    segments: list[dict] = []
    heading_path: list[dict] = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok.type == "heading_open" and tok.map is not None:
            level = int(tok.tag[1])
            line_s, line_e = tok.map
            bs, be = idx.line_range_bytes(line_s, line_e)
            inline_tok = tokens[i + 1] if i + 1 < len(tokens) else None
            text_buf = inline_tok.content if inline_tok and inline_tok.type == "inline" else ""
            bs, be = safe_byte_slice(source_bytes, bs, be)
            anchor = None
            anchor_re = re.compile(r'<a\s+id="([^"]+)"\s*></a>')
            for j in range(i + 2, min(i + 6, len(tokens))):
                nxt = tokens[j]
                if nxt.type in ("heading_close", "heading_open"):
                    break
                if nxt.type in ("html_inline", "html_block") and nxt.content:
                    m = anchor_re.search(nxt.content)
                    if m:
                        anchor = m.group(1)
                        break
            seg_id = segment_id(doc_id, bs, be, "heading")
            seg_lits = [l for l in extract_protected_literals(source_bytes, idx, [tok] + ([inline_tok] if inline_tok else []))
                       if l["byte_range"]["start"] >= bs and l["byte_range"]["end"] <= be]
            segments.append({
                "segment_id": seg_id,
                "structural_type": "heading",
                "byte_range": {"start": bs, "end": be},
                "line_range": {"start": line_s, "end": line_e},
                "heading_path": list(heading_path),
                "translatable_text": text_buf,
                "anchor": anchor,
                "protected_literals": seg_lits,
            })
            heading_path[:] = [
                hp for hp in heading_path if hp["level"] < level
            ] + [{
                "level": level,
                "text": text_buf,
                "byte_range": {"start": bs, "end": be},
            }]
            i += 3
            continue

        if tok.type == "paragraph_open" and tok.map is not None:
            line_s, line_e = tok.map
            bs, be = idx.line_range_bytes(line_s, line_e)
            inline_tok = tokens[i + 1] if i + 1 < len(tokens) else None
            txt = inline_tok.content if inline_tok and inline_tok.type == "inline" else ""
            bs, be = safe_byte_slice(source_bytes, bs, be)
            seg_id = segment_id(doc_id, bs, be, "paragraph")
            seg_lits = [l for l in extract_protected_literals(source_bytes, idx, [tok] + ([inline_tok] if inline_tok else []))
                       if l["byte_range"]["start"] >= bs and l["byte_range"]["end"] <= be]
            segments.append({
                "segment_id": seg_id,
                "structural_type": "paragraph",
                "byte_range": {"start": bs, "end": be},
                "line_range": {"start": line_s, "end": line_e},
                "heading_path": list(heading_path),
                "translatable_text": txt,
                "protected_literals": seg_lits,
            })
            i += 3
            continue

        if tok.type == "fence" and tok.map is not None:
            line_s, line_e = tok.map
            bs, be = idx.line_range_bytes(line_s, line_e)
            bs, be = safe_byte_slice(source_bytes, bs, be)
            seg_id = segment_id(doc_id, bs, be, "code_fenced")
            literals = [l for l in extract_protected_literals(source_bytes, idx, [tok])
                        if l["byte_range"]["start"] >= bs and l["byte_range"]["end"] <= be]
            segments.append({
                "segment_id": seg_id,
                "structural_type": "code_fenced",
                "byte_range": {"start": bs, "end": be},
                "line_range": {"start": line_s, "end": line_e},
                "heading_path": list(heading_path),
                "language": (tok.info or "").strip() or None,
                "translatable_text": "",
                "protected_literals": literals,
            })
            i += 1
            continue

        if tok.type == "code_block" and tok.map is not None:
            line_s, line_e = tok.map
            bs, be = idx.line_range_bytes(line_s, line_e)
            bs, be = safe_byte_slice(source_bytes, bs, be)
            seg_id = segment_id(doc_id, bs, be, "code_indented")
            literals = [l for l in extract_protected_literals(source_bytes, idx, [tok])
                        if l["byte_range"]["start"] >= bs and l["byte_range"]["end"] <= be]
            segments.append({
                "segment_id": seg_id,
                "structural_type": "code_indented",
                "byte_range": {"start": bs, "end": be},
                "line_range": {"start": line_s, "end": line_e},
                "heading_path": list(heading_path),
                "translatable_text": "",
                "protected_literals": literals,
            })
            i += 1
            continue

        if tok.type == "bullet_list_open" or tok.type == "ordered_list_open":
            line_s, line_e = tok.map or (0, 0)
            j = i + 1
            depth = 1
            while j < len(tokens) and depth > 0:
                t = tokens[j]
                if t.type in ("bullet_list_open", "ordered_list_open"):
                    depth += 1
                elif t.type in ("bullet_list_close", "ordered_list_close"):
                    depth -= 1
                if depth == 0:
                    line_e = t.map[0] if t.map else line_e
                    break
                j += 1
            bs, be = idx.line_range_bytes(line_s, line_e)
            bs, be = safe_byte_slice(source_bytes, bs, be)
            seg_id = segment_id(doc_id, bs, be, "list_item")
            segments.append({
                "segment_id": seg_id,
                "structural_type": "list_item",
                "byte_range": {"start": bs, "end": be},
                "line_range": {"start": line_s, "end": line_e},
                "heading_path": list(heading_path),
                "translatable_text": "",
                "protected_literals": [],
            })
            i = j + 1
            continue

        if tok.type == "table_open" and tok.map is not None:
            line_s, line_e = tok.map
            depth = 1
            j = i + 1
            while j < len(tokens) and depth > 0:
                t = tokens[j]
                if t.type == "table_open":
                    depth += 1
                elif t.type == "table_close":
                    depth -= 1
                    if depth == 0:
                        line_e = t.map[1] if t.map else line_e
                        break
                j += 1
            bs, be = idx.line_range_bytes(line_s, line_e)
            bs, be = safe_byte_slice(source_bytes, bs, be)
            seg_id = segment_id(doc_id, bs, be, "table")
            segments.append({
                "segment_id": seg_id,
                "structural_type": "table",
                "byte_range": {"start": bs, "end": be},
                "line_range": {"start": line_s, "end": line_e},
                "heading_path": list(heading_path),
                "translatable_text": "",
                "protected_literals": [],
            })
            i = j + 1
            continue

        if tok.type == "blockquote_open" and tok.map is not None:
            line_s, line_e = tok.map
            depth = 1
            j = i + 1
            while j < len(tokens) and depth > 0:
                t = tokens[j]
                if t.type == "blockquote_open":
                    depth += 1
                elif t.type == "blockquote_close":
                    depth -= 1
                    if depth == 0:
                        line_e = t.map[1] if t.map else line_e
                        break
                j += 1
            bs, be = idx.line_range_bytes(line_s, line_e)
            bs, be = safe_byte_slice(source_bytes, bs, be)
            seg_id = segment_id(doc_id, bs, be, "blockquote")
            segments.append({
                "segment_id": seg_id,
                "structural_type": "blockquote",
                "byte_range": {"start": bs, "end": be},
                "line_range": {"start": line_s, "end": line_e},
                "heading_path": list(heading_path),
                "translatable_text": "",
                "protected_literals": [],
            })
            i = j + 1
            continue

        if tok.type == "html_block" and tok.map is not None:
            line_s, line_e = tok.map
            bs, be = idx.line_range_bytes(line_s, line_e)
            bs, be = safe_byte_slice(source_bytes, bs, be)
            seg_id = segment_id(doc_id, bs, be, "html_block")
            segments.append({
                "segment_id": seg_id,
                "structural_type": "html_block",
                "byte_range": {"start": bs, "end": be},
                "line_range": {"start": line_s, "end": line_e},
                "heading_path": list(heading_path),
                "translatable_text": "",
                "protected_literals": [],
            })
            i += 1
            continue

        i += 1

    return [narrow_range_to_text(source_bytes, seg) for seg in segments]


def canonical_json(payload) -> bytes:
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def extract_snapshot(source_bytes: bytes, idx: LineIndex, tokens: list[Token]) -> dict:
    headings: list[dict] = []
    links: list[dict] = []
    tables: list[dict] = []
    current_table: list[dict] | None = None

    for tok in tokens:
        if tok.type == "heading_open" and tok.map is not None:
            level = int(tok.tag[1])
            line_s, line_e = tok.map
            headings.append({
                "level": level,
                "line_range": {"start": line_s, "end": line_e},
            })

        if tok.type == "inline" and headings:
            inline_text = tok.content or ""
            h = headings[-1]
            if "text" not in h and tok.map:
                line_s, _ = tok.map
                bs, be = idx.line_range_bytes(line_s, line_s)
                h["text"] = inline_text
                h["byte_range"] = {"start": bs, "end": be}

        if tok.type == "html_inline" and tok.content:
            m = re.search(r'<a\s+id="([^"]+)"\s*></a>', tok.content)
            if m and headings:
                headings[-1]["anchor"] = m.group(1)

        if tok.type == "inline" and tok.children:
            for child in tok.children:
                if child.type == "link_open" and child.attrs:
                    href = child.attrs.get("href")
                    if href is None:
                        continue
                    kind = "external" if EXTERNAL_LINK_RE.match(href) else "internal"
                    line_s, line_e = tok.map if tok.map else (0, 0)
                    bs, be = idx.line_range_bytes(line_s, line_e)
                    links.append({
                        "kind": kind,
                        "target": href,
                        "byte_range": {"start": bs, "end": be},
                    })
                if child.type == "image" and child.attrs:
                    src = child.attrs.get("src")
                    if src is None:
                        continue
                    kind = "external" if EXTERNAL_LINK_RE.match(src) else "internal"
                    line_s, line_e = tok.map if tok.map else (0, 0)
                    bs, be = idx.line_range_bytes(line_s, line_e)
                    links.append({
                        "kind": kind,
                        "target": src,
                        "byte_range": {"start": bs, "end": be},
                    })

        if tok.type == "link_open" and tok.map is not None and tok.attrs:
            href = tok.attrs.get("href")
            if href is not None:
                kind = "external" if EXTERNAL_LINK_RE.match(href) else "internal"
                line_s, line_e = tok.map
                bs, be = idx.line_range_bytes(line_s, line_e)
                links.append({
                    "kind": kind,
                    "target": href,
                    "byte_range": {"start": bs, "end": be},
                })

        if tok.type == "table_open" and tok.map is not None:
            current_table = {"headers": [], "alignments": []}
        if tok.type == "th" and tok.content is not None and current_table is not None:
            current_table["headers"].append(tok.content)
        if tok.type == "th" and tok.attrs and current_table is not None:
            style = (tok.attrs.get("style") or "").lower()
            align = None
            if "text-align:center" in style:
                align = "center"
            elif "text-align:right" in style:
                align = "right"
            elif "text-align:left" in style:
                align = "left"
            current_table["alignments"].append(align)
        if tok.type == "table_close" and tok.map is not None and current_table is not None:
            line_s, line_e = tok.map
            bs, be = idx.line_range_bytes(line_s, line_e)
            current_table["byte_range"] = {"start": bs, "end": be}
            tables.append(current_table)
            current_table = None

    structure_hash = sha256_hex(canonical_json({
        "headings": [{"level": h["level"], "text": h.get("text", "")} for h in headings],
        "tables": [t["headers"] for t in tables],
    }))

    return {
        "headings": headings,
        "links": links,
        "tables": tables,
        "footnotes": [],
        "structure_hash": structure_hash,
    }


def gate_settings(profile_path: str | None) -> dict:
    """Configuración de los módulos opcionales leída del perfil.

    Ningún módulo opcional está activo sin declarar su clave en el perfil,
    y cada clave que el esquema acepta tiene aquí un lector: una opción
    validada por el esquema que no llega aquí sería una mentira operativa.
    """
    return {
        "mdx_enabled": mdx_gate_enabled(profile_path),
        "html_enabled": html_gate_enabled(profile_path),
        "admonitions_enabled": admonitions_gate_enabled(profile_path),
        "admonition_types": admonitions_allowed_types(profile_path),
        "definitions_enabled": definition_lists_gate_enabled(profile_path),
        "directives_enabled": directives_gate_enabled(profile_path),
        "directive_names": directives_allowed_names(profile_path),
        "mermaid_enabled": mermaid_gate_enabled(profile_path),
        "mermaid_labels": mermaid_labels_policy(profile_path),
        "wikilinks_enabled": wikilinks_gate_enabled(profile_path),
    }


def classify_file(
    entry: dict,
    source_root: Path,
    mdx_enabled: bool = False,
    html_enabled: bool = False,
    admonitions_enabled: bool = False,
    definitions_enabled: bool = False,
    directives_enabled: bool = False,
    mermaid_enabled: bool = False,
    mermaid_labels: str = "deny",
    wikilinks_enabled: bool = False,
    admonition_types: tuple[str, ...] | None = None,
    directive_names: tuple[str, ...] | None = None,
) -> dict:
    if entry["type"] != "markdown":
        return {**entry, "verdict": "ok", "findings": []}
    path = source_root / entry["path"]
    text = path.read_bytes().decode("utf-8", errors="replace")
    findings = detect_findings(text)
    # El gate MDX se levanta por el hallazgo, no por la extensión del
    # archivo: `flag_mdx` significa ".mdx", y el corpus real usa componentes
    # MDX dentro de `.md` igual de legítimamente.
    if mdx_enabled:
        # Encender el módulo no significa permitir cualquier JSX: el
        # contrato decide qué se admite y el resto bloquea con su propio
        # hallazgo, en lugar de desaparecer del informe.
        findings = [f for f in findings if f.get("type") != "mdx_component"]
        findings.extend(mdx_selector.contract_findings(text))
    if html_enabled:
        findings = [f for f in findings if f.get("type") != "html_embebido"]
        findings.extend(html_parser.contract_findings(text))
    if admonitions_enabled:
        # Encender el módulo levanta el bloqueo de los tipos que el perfil
        # admite. Un tipo que no admite sigue bloqueando: la lista de
        # `types` restringe, no autoriza de más.
        findings = [
            f for f in findings
            if not (
                f.get("type") == "directive_admonition"
                and (admonition_types is None or f.get("admonition_type") in admonition_types)
            )
        ]
    if definitions_enabled:
        findings = [f for f in findings if f.get("type") != "definition_list"]
    if directives_enabled:
        findings = [
            f for f in findings
            if not (
                f.get("type") == "unsupported_directive"
                and (directive_names is None or f.get("directive_name") in directive_names)
            )
        ]
    if wikilinks_enabled:
        findings = [f for f in findings if f.get("type") != "wikilink"]
    if mermaid_enabled and mermaid_labels == "allow":
        # Solo al traducir etiquetas el Mermaid malformado deja de ser una
        # nota y pasa a bloquear: en modo núcleo se preserva literal.
        for f in findings:
            if f.get("type") == "mermaid_unsupported":
                f["severity"] = "bloqueante"
    verdict = "blocked" if any(f["severity"] == "bloqueante" for f in findings) else "ok"
    return {**entry, "verdict": verdict, "findings": findings}


def build_segments_payload(source_root: Path, classified: list[dict]) -> dict:
    files: list[dict] = []
    for entry in classified:
        if entry["type"] != "markdown":
            continue
        path = source_root / entry["path"]
        data = path.read_bytes()
        idx = LineIndex(data)
        text = data.decode("utf-8", errors="replace")
        tokens = PARSER.parse(text)
        doc_id = document_id(data)
        segs = extract_segments(data, idx, tokens, doc_id)
        files.append({
            "document_id": doc_id,
            "path": entry["path"],
            "source_hash": entry["sha256"],
            "source_size": len(data),
            "segments": segs,
        })
    return {
        "source_root": str(source_root),
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "files": files,
    }


def build_snapshots_payload(source_root: Path, classified: list[dict]) -> dict:
    files: list[dict] = []
    for entry in classified:
        if entry["type"] != "markdown":
            continue
        path = source_root / entry["path"]
        data = path.read_bytes()
        idx = LineIndex(data)
        text = data.decode("utf-8", errors="replace")
        tokens = PARSER.parse(text)
        snap = extract_snapshot(data, idx, tokens)
        files.append({
            "document_id": document_id(data),
            "path": entry["path"],
            **snap,
        })
    return {
        "source_root": str(source_root),
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "files": files,
    }


def write_atomic(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="prepare.py")
    p.add_argument("--inventory", required=True, help="JSON producido por inventory.py.")
    p.add_argument("--out", help="Ruta del JSON de veredictos.")
    p.add_argument("--segments", help="Ruta del JSON de segmentos.")
    p.add_argument("--snapshots", help="Ruta del JSON de snapshots estructurales.")
    p.add_argument("--profile", help="Perfil JSON. Si incluye mdx.enabled=true, el gate MDX se activa.")
    return p.parse_args(argv)


def _profile_block(profile_path: str | None, key: str) -> dict:
    if not profile_path:
        return {}
    try:
        data = json.loads(Path(profile_path).read_text(encoding="utf-8"))
    except Exception:
        return {}
    block = data.get(key)
    return block if isinstance(block, dict) else {}


def mdx_gate_enabled(profile_path: str | None) -> bool:
    return bool(_profile_block(profile_path, "mdx").get("enabled", False))


def html_gate_enabled(profile_path: str | None) -> bool:
    return bool(_profile_block(profile_path, "html").get("enabled", False))


def admonitions_gate_enabled(profile_path: str | None) -> bool:
    return bool(_profile_block(profile_path, "admonitions").get("enabled", False))


def admonitions_allowed_types(profile_path: str | None) -> tuple[str, ...] | None:
    """Tipos que el perfil admite. `None` significa que no se restringe."""
    types = _profile_block(profile_path, "admonitions").get("types")
    if not isinstance(types, list) or not types:
        return None
    return tuple(str(t) for t in types)


def wikilinks_gate_enabled(profile_path: str | None) -> bool:
    return bool(_profile_block(profile_path, "wikilinks").get("enabled", False))


def definition_lists_gate_enabled(profile_path: str | None) -> bool:
    return bool(_profile_block(profile_path, "definition_lists").get("enabled", False))


def directives_gate_enabled(profile_path: str | None) -> bool:
    return bool(_profile_block(profile_path, "directives").get("enabled", False))


def directives_allowed_names(profile_path: str | None) -> tuple[str, ...] | None:
    names = _profile_block(profile_path, "directives").get("names")
    if not isinstance(names, list) or not names:
        return None
    return tuple(str(n) for n in names)


def mermaid_gate_enabled(profile_path: str | None) -> bool:
    return bool(_profile_block(profile_path, "mermaid").get("enabled", False))


def mermaid_labels_policy(profile_path: str | None) -> str:
    """`deny` por defecto: en el núcleo las etiquetas Mermaid se preservan."""
    value = _profile_block(profile_path, "mermaid").get("labels")
    return value if value in {"allow", "deny"} else "deny"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not (args.out or args.segments or args.snapshots):
        print("error: indique al menos --out, --segments o --snapshots", file=sys.stderr)
        return 2

    inv_path = Path(args.inventory)
    inventory = json.loads(inv_path.read_text(encoding="utf-8"))
    source_root = Path(inventory["source_root"])
    gates = gate_settings(args.profile)

    if args.out:
        classified = [classify_file(e, source_root, **gates) for e in inventory["files"]]
        payload = {
            "source_root": inventory["source_root"],
            "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "total_files": len(classified),
            "blocked_count": sum(1 for e in classified if e.get("verdict") == "blocked"),
            "files": classified,
        }
        write_atomic(Path(args.out), payload)
        print(
            f"ok: {payload['total_files']} archivos, "
            f"{payload['blocked_count']} bloqueantes -> {args.out}"
        )

    if args.segments or args.snapshots:
        classified = [classify_file(e, source_root, **gates) for e in inventory["files"]]
        if args.segments:
            seg_payload = build_segments_payload(source_root, classified)
            write_atomic(Path(args.segments), seg_payload)
            total_segments = sum(len(f["segments"]) for f in seg_payload["files"])
            print(f"ok: {total_segments} segmentos en {len(seg_payload['files'])} archivos -> {args.segments}")
        if args.snapshots:
            snap_payload = build_snapshots_payload(source_root, classified)
            write_atomic(Path(args.snapshots), snap_payload)
            total_h = sum(len(f["headings"]) for f in snap_payload["files"])
            total_l = sum(len(f["links"]) for f in snap_payload["files"])
            print(f"ok: {total_h} headings, {total_l} enlaces -> {args.snapshots}")

    return 0


if __name__ == "__main__":
    sys.exit(main())