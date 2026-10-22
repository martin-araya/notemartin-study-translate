"""Ensamblado HTML mediante parches por rangos (fase 075).

Análogo a ``mdx_assemble.py``: aplica reemplazos de bytes sin
reserializar el documento. Los segmentos se leen como JSON:
``{start, end, translated_text, tag, kind}``. Sin solapamiento.

Uso::

    python scripts/html_assemble.py \\
        --source path/to/file.md \\
        --segments-json path/to/segments.json \\
        --out path/to/output.md

Con ``--identity`` sustituye cada segmento por sí mismo y debe
recuperar los bytes originales.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from html_parser import HtmlNode, Span, parse_html


def assemble(
    source_bytes: bytes,
    segments,
    identity: bool = False,
) -> bytes:
    def _start(s):
        return s["start"] if isinstance(s, dict) else s.start
    def _end(s):
        return s["end"] if isinstance(s, dict) else s.end
    def _text(s):
        return s["translated_text"] if isinstance(s, dict) else s.text

    sorted_segs = sorted(segments, key=lambda s: (_start(s), _end(s)))
    for a, b in zip(sorted_segs, sorted_segs[1:]):
        if _end(a) > _start(b):
            raise ValueError(
                f"segments solapados: {_start(a)}-{_end(a)} y {_start(b)}-{_end(b)}"
            )

    out = bytearray()
    cursor = 0
    for seg in sorted_segs:
        start = _start(seg)
        end = _end(seg)
        if cursor < start:
            out.extend(source_bytes[cursor:start])
        if identity:
            out.extend(source_bytes[start:end])
        else:
            replacement = _text(seg) or source_bytes[start:end].decode("utf-8")
            out.extend(replacement.encode("utf-8"))
        cursor = end
    if cursor < len(source_bytes):
        out.extend(source_bytes[cursor:])
    return bytes(out)


def segments_from_text(text: str) -> list[dict]:
    from html_selector import DEFAULT_TRANSLATABLE_ATTRS

    doc = parse_html(text)
    segments: list[dict] = []

    def _walk(node: HtmlNode) -> None:
        for attr in node.attributes:
            if attr["name"] in DEFAULT_TRANSLATABLE_ATTRS and attr["kind"] == "string":
                value = attr["value"][1:-1]
                attr_offset = text.find(attr["value"], node.start, node.end)
                if attr_offset == -1:
                    continue
                segments.append({
                    "start": attr_offset + 1,
                    "end": attr_offset + 1 + len(value),
                    "translated_text": value,
                    "tag": node.name,
                    "attribute": attr["name"],
                    "kind": "attribute",
                })
        for child in node.children:
            if isinstance(child, Span) and child.kind == "text":
                if child.value.strip():
                    segments.append({
                        "start": child.start,
                        "end": child.end,
                        "translated_text": child.value,
                        "tag": node.name,
                        "kind": "text",
                    })
            elif isinstance(child, HtmlNode):
                _walk(child)

    for node in doc.nodes:
        if isinstance(node, HtmlNode):
            _walk(node)
    return segments


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="html_assemble.py")
    p.add_argument("--source", required=True)
    p.add_argument("--segments-json", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--identity", action="store_true")
    return p.parse_args(argv)


def write_atomic(target: Path, payload: bytes) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_bytes(payload)
    os.replace(tmp, target)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source_path = Path(args.source)
    segments_path = Path(args.segments_json)
    out_path = Path(args.out)

    source_bytes = source_path.read_bytes()
    segments = json.loads(segments_path.read_text(encoding="utf-8"))
    result = assemble(source_bytes, segments, identity=args.identity)
    write_atomic(out_path, result)
    print(f"ok: {len(result)} bytes ({'identity' if args.identity else 'patches'}) -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())