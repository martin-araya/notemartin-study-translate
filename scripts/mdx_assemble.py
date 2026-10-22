"""Ensamblado MDX mediante parches por rangos (fase 068).

Aplica reemplazos de bytes sobre el documento fuente sin
reserializarlo. Cada ``Segment`` lleva ``start``, ``end`` y
``translated_text``. Los segmentos pueden tener ``parent``
(componente MDX) o ``parent`` vacío (texto plano).

Modo ``--identity``: sustituye cada segmento por sí mismo. El
resultado debe coincidir exactamente con los bytes originales.

Uso::

    python scripts/mdx_assemble.py \\
        --source path/to/file.mdx \\
        --segments-json path/to/segments.json \\
        --out path/to/output.mdx

Los segmentos se leen como JSON: una lista de ``{start, end,
translated_text, parent}``. El modo por defecto aplica
``translated_text``; con ``--identity`` aplica el texto original.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from mdx_parser import parse_mdx, Span, MdxNode


def assemble(
    source_bytes: bytes,
    segments: list[dict],
    identity: bool = False,
) -> bytes:
    """Aplica parches por rango de bytes en una sola pasada.

    Los segmentos se ordenan por ``start``. Se exige que no se
    solapen entre sí; en caso contrario se eleva ``ValueError`` con
    el primer par solapado. Esto reproduce la regla de INV-03 del
    proyecto (rangos sin huecos ni solapamientos indebidos)."""
    sorted_segs = sorted(segments, key=lambda s: (s["start"], s["end"]))
    for a, b in zip(sorted_segs, sorted_segs[1:]):
        if a["end"] > b["start"]:
            raise ValueError(
                f"segments solapados: {a['start']}-{a['end']} y {b['start']}-{b['end']}"
            )

    out = bytearray()
    cursor = 0
    for seg in sorted_segs:
        start = seg["start"]
        end = seg["end"]
        if cursor < start:
            out.extend(source_bytes[cursor:start])
        if identity:
            out.extend(source_bytes[start:end])
        else:
            replacement = seg.get("translated_text", source_bytes[start:end].decode("utf-8"))
            out.extend(replacement.encode("utf-8"))
        cursor = end
    if cursor < len(source_bytes):
        out.extend(source_bytes[cursor:])
    return bytes(out)


def segments_from_text(text: str) -> list[dict]:
    """Convierte el árbol parseado en una lista de segmentos
    traducibles aptos para reensamblar. Cada texto plano y atributo
    traducible produce un segmento con ``start`` y ``end``
    absolutos."""
    from mdx_selector import (
        DEFAULT_SUPPORTED,
        DEFAULT_TRANSLATABLE_ATTRS,
        _strip_expressions,
    )

    doc = parse_mdx(text)
    out: list[dict] = []
    for node in doc.nodes:
        if isinstance(node, Span):
            if node.kind == "text":
                cleaned = _strip_expressions(node.value)
                if cleaned.strip():
                    out.append({
                        "start": node.start,
                        "end": node.end,
                        "translated_text": cleaned,
                        "parent": "",
                        "kind": "text",
                    })
            continue
        _emit_node_segments(text, node, out, DEFAULT_SUPPORTED, DEFAULT_TRANSLATABLE_ATTRS)
    return out


def _emit_node_segments(text, node, out, supported, translatable_attrs) -> None:
    for attr in node.attributes:
        if attr["name"] in translatable_attrs and attr["kind"] == "string":
            value = attr["value"][1:-1]
            attr_offset = text.find(attr["value"], node.start, node.end)
            if attr_offset == -1:
                continue
            out.append({
                "start": attr_offset + 1,
                "end": attr_offset + 1 + len(value),
                "translated_text": value,
                "parent": node.name,
                "attribute": attr["name"],
                "kind": "attribute",
            })
    for child in node.children:
        if isinstance(child, Span):
            if child.kind == "text":
                from mdx_selector import _strip_expressions
                cleaned = _strip_expressions(child.value)
                if cleaned.strip():
                    out.append({
                        "start": child.start,
                        "end": child.end,
                        "translated_text": cleaned,
                        "parent": node.name,
                        "kind": "text",
                    })
            continue
        _emit_node_segments(text, child, out, supported, translatable_attrs)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="mdx_assemble.py")
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