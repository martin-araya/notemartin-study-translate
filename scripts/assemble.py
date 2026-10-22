"""Ensamblado de archivos Markdown a partir de segmentos.

Modo ``--identity``: aplica cada segmento del JSON como una sustitución
de ``byte_range`` por el texto original (sustitución byte-a-byte de sí
mismo). El resultado debe coincidir exactamente con el archivo
original. Este modo es la prueba base de la fase 020.

Modo por defecto: aplica cada segmento como sustitución de
``byte_range`` por ``translated_text`` desde ``translations/<clave>.json``.

La clave de traducción se resuelve con ``scripts/translation_key.py``:
``document_id`` si ese identificador no colisiona entre rutas, y
``translation_id`` (documento + ruta) si colisiona. El argumento
``--translation-id`` fuerza una clave concreta cuando la ruta no basta
para desambiguar. Sin ninguno de los dos se recurre al nombre histórico
``<document_id>.json``, que sigue siendo válido para ejecuciones
anteriores a la remediación.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from translation_key import index_by_document, resolve_key  # noqa: E402


def assemble(
    source_bytes: bytes,
    segments_doc: dict,
    identity: bool,
    translations_lookup: dict[str, str] | None = None,
) -> bytes:
    patches: list[tuple[int, int, bytes]] = []
    seg_ranges: list[tuple[int, int]] = []
    for seg in segments_doc.get("segments", []):
        start = seg["byte_range"]["start"]
        end = seg["byte_range"]["end"]
        seg_ranges.append((start, end))
        if identity:
            replacement = source_bytes[start:end]
        elif translations_lookup and seg.get("segment_id") in translations_lookup:
            replacement = translations_lookup[seg["segment_id"]].encode("utf-8")
        else:
            replacement = source_bytes[start:end]
        patches.append((start, end, replacement))

    seg_ranges.sort()
    cursor = 0
    for start, end in seg_ranges:
        if cursor < start:
            patches.append((cursor, start, source_bytes[cursor:start]))
        cursor = max(cursor, end)
    if cursor < len(source_bytes):
        patches.append((cursor, len(source_bytes), source_bytes[cursor:]))

    patches.sort(key=lambda p: p[0], reverse=True)

    out = source_bytes
    for start, end, replacement in patches:
        out = out[:start] + replacement + out[end:]
    return out


def load_translations(translations_dir: Path, key: str) -> dict[str, str]:
    path = translations_dir / f"{key}.json"
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {e["segment_id"]: e.get("translated_text", "") for e in data.get("entries", [])}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="assemble.py")
    p.add_argument("--source", required=True, help="Ruta del archivo Markdown original.")
    p.add_argument("--segments", required=True, help="JSON con los segmentos del archivo.")
    p.add_argument("--out", required=True, help="Archivo de salida ensamblado.")
    p.add_argument("--identity", action="store_true", help="Sustituye cada segmento por sí mismo.")
    p.add_argument("--translation-id",
                   help=("Clave explícita dentro de --translations. Por defecto se "
                         "resuelve de document_id y ruta (ver translation_key.py)."))
    p.add_argument("--translations", help="Directorio con translations/<clave>.json.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source_path = Path(args.source)
    segments_path = Path(args.segments)
    out_path = Path(args.out)

    source_bytes = source_path.read_bytes()
    segments_root = json.loads(segments_path.read_text(encoding="utf-8"))

    target_doc = None
    files_by_doc: dict[str, list[dict]] = {}
    if isinstance(segments_root, dict) and "files" in segments_root:
        files_by_doc = index_by_document(segments_root)
        wanted = source_path.name
        # Se busca primero por ruta completa: con dos archivos de igual
        # nombre en directorios distintos, el nombre a secas elige el
        # equivocado.
        by_name = [f for f in segments_root["files"]
                   if Path(f.get("path", "")).name == wanted]
        exact = [f for f in segments_root["files"]
                 if str(source_path).endswith(f.get("path", ""))]
        candidates = exact or by_name
        if not candidates:
            print(f"error: no se encontró {source_path.name} en segments", file=sys.stderr)
            return 4
        target_doc = candidates[0]
    else:
        target_doc = segments_root

    lookup = None
    if not args.identity:
        if args.translations:
            doc_id = target_doc.get("document_id", "")
            key = args.translation_id or resolve_key(
                files_by_doc.get(doc_id), doc_id, target_doc.get("path")
            )
            lookup = load_translations(Path(args.translations), key)
            if not lookup:
                print(f"aviso: no hay traducción para la clave {key}", file=sys.stderr)
        else:
            lookup = {}

    result = assemble(source_bytes, target_doc, identity=args.identity, translations_lookup=lookup)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    tmp.write_bytes(result)
    os.replace(tmp, out_path)
    mode = "identity" if args.identity else "traducción"
    print(f"ok: {len(result)} bytes ({mode}) -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())