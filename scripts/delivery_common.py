"""Utilidades compartidas por la entrega local (fases 134-140).

Ninguna función toca prosa traducida ni literales protegidos. Todas
preservan los desplazamientos de bytes para poder volver a aplicar el
cambio sobre el texto original sin recalcular posiciones.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
from pathlib import Path

FENCE_RE = re.compile(r"^\s*(```|~~~)")
LINK_RE = re.compile(r"(!?)\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
EXTERNAL_RE = re.compile(r"^(?:[a-zA-Z][a-zA-Z0-9+.\-]*:|//)")
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")

# Nombres que nunca viajan dentro de un paquete de entrega.
FORBIDDEN_NAMES = (
    "manifest.json",
    "glossary.json",
    "inventory.json",
    "anchors.json",
    "output_hashes.json",
    "adaptation_report.json",
    "package_manifest.json",
    "delivery_manifest.json",
)
FORBIDDEN_DIRS = (
    "reports",
    "segments",
    "translations",
    "staged",
    "__pycache__",
)


def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_atomic(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_hashes(root: Path) -> dict[str, str]:
    """SHA-256 por ruta relativa de todo el árbol."""
    if not root.exists():
        return {}
    return {
        p.relative_to(root).as_posix(): sha256_file(p)
        for p in sorted(root.rglob("*"))
        if p.is_file() and not p.is_symlink()
    }


def strip_code_regions(text: str, mask_inline: bool = False) -> str:
    """Sustituye por espacios el contenido de bloques de código.

    Conserva la longitud exacta, de modo que los desplazamientos
    encontrados sobre el resultado siguen valiendo sobre el original.
    Las líneas delimitadoras del fence se conservan porque son
    estructura del documento.

    Con ``mask_inline=True`` el código inline también se enmascara. Ese
    modo sirve para adaptar destinos de enlace sin tocar referencias
    que viven dentro de código protegido. No se usa al calcular
    slugs, porque el algoritmo de anclas ignora los backticks en lugar
    de borrarlos.
    """
    out: list[str] = []
    in_fence = False
    fence_token = ""
    for line in text.splitlines(keepends=True):
        m = FENCE_RE.match(line)
        if m:
            token = m.group(1)
            if not in_fence:
                in_fence, fence_token = True, token
            elif token == fence_token:
                in_fence = False
            out.append(line)
            continue
        out.append(" " * len(line) if in_fence else line)
    masked = "".join(out)
    if mask_inline:
        chars = list(masked)
        for m in INLINE_CODE_RE.finditer(masked):
            for i in range(m.start(), m.end()):
                chars[i] = " "
        masked = "".join(chars)
    return masked


def iter_link_spans(text: str, mask_inline: bool = False):
    """Enlaces fuera de código con el desplazamiento de su destino.

    Devuelve (es_imagen, etiqueta, destino, inicio, fin) donde inicio y
    fin corresponden **solo al destino**, para poder sustituirlo sin
    tocar la etiqueta ni el resto de la línea.
    """
    masked = strip_code_regions(text, mask_inline=mask_inline)
    for m in LINK_RE.finditer(masked):
        yield m.group(1) == "!", m.group(2), m.group(3), m.start(3), m.end(3)


def iter_links(text: str):
    """Devuelve (es_imagen, etiqueta, destino) fuera de bloques de código."""
    for is_image, label, raw, _start, _end in iter_link_spans(text):
        yield is_image, label, raw


def split_fragment(target: str) -> tuple[str, str | None]:
    path, sep, fragment = target.partition("#")
    return path, fragment if sep else None


def is_external(target: str) -> bool:
    return bool(EXTERNAL_RE.match(target))


def decode_link_target(target: str) -> str:
    """Decodifica escapes de ruta conservando los separadores.

    Solo actúa sobre %XX; no tocaScheme ni query string.
    """
    from urllib.parse import unquote

    return unquote(target)


def ascii_slug(name: str) -> str:
    """Nombre de archivo en ASCII minúsculas separado por guiones."""
    import unicodedata

    stem, dot, ext = name.rpartition(".")
    if not dot:
        stem, ext = name, ""
    decomposed = unicodedata.normalize("NFD", stem)
    no_diacritics = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    lowered = no_diacritics.lower()
    cleaned = re.sub(r"[^a-z0-9]+", "-", lowered)
    cleaned = re.sub(r"-+", "-", cleaned).strip("-")
    if not cleaned:
        cleaned = "recurso"
    return f"{cleaned}.{ext.lower()}" if ext else cleaned


def replace_spans(text: str, spans: list[tuple[int, int, str]]) -> str:
    """Aplica sustituciones por desplazamiento, de derecha a izquierda."""
    result = text
    for start, end, new in sorted(spans, key=lambda s: s[0], reverse=True):
        result = result[:start] + new + result[end:]
    return result


def is_within(child: Path, parent: Path) -> bool:
    """True si ``child`` está dentro de ``parent`` tras resolver rutas."""
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False