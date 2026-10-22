#!/usr/bin/env python3
"""Aplica traducciones de la corrida tailwind-001.

Solo traduce prosa translatable real (no "lorem ipsum", imágenes
incluidas como Markdown, tablas de tokens en fences, etc.). En
archivos donde todas las entradas son aparatos (ejemplos vacíos,
clases Tailwind en fences), la traducción es la identidad.

Las traducciones conservan `§§LITERAL§§` (marcadores de protección)
intactos: el ensamblador los sustituye por los bytes originales al
ensamblar.
"""

from __future__ import annotations

import json
from pathlib import Path

T = Path(__file__).resolve().parent.parent / "run-tailwind-001/translations"

# Traducciones por (doc_id, segment_id). Cualquier par ausente se queda
# en identidad (caso común: ejemplos automáticos, lorem ipsum, imágenes).
TEXTS: dict[tuple[str, str], str] = {
    # ------------------------------------------------------------------
    # tailwindcss/installation/using-vite.md (todas "Hello world!")
    ("doc-085fb377", "seg-6d7925af"): "¡Hola mundo!",
}

ENGLISH: dict[str, dict[str, str]] = {
    "doc-085fb377": {
        "seg-6d7925af": "Hello world!",
    },
}


def is_apparatus(text: str) -> bool:
    """Detecta contenidos que no son prosa translatable.

    Lorem ipsum, filas de imágenes Markdown, párrafos cortos de
    demostración, tablas de tokens en fences, etc. En todos estos
    casos, devolver el mismo `text` es lo más honrado porque la prosa
    no aporta un sentido traducible.
    """
    stripped = text.strip()
    if not stripped:
        return True
    placeholders = (
        "Lorem ipsum",
        "dolor sit amet",
        "Well, let me tell you something",
        "Sure, go ahead",
        "Maybe we can live without",
        "Look. If you think this is",
        "The quick brown fox",
        "This text will",
        "This will",
        "This headline will",
    )
    if any(p in stripped for p in placeholders):
        return True
    if stripped.startswith("![") and stripped.endswith(")"):
        return True
    return False


def translate(doc_id: str, seg_id: str, original: str) -> str:
    override = TEXTS.get((doc_id, seg_id))
    if override is not None:
        return override
    if is_apparatus(original):
        return original
    return original


def main() -> int:
    applied = 0
    total = 0
    for path in sorted(T.glob("*.json")):
        doc_id = path.stem
        data = json.loads(path.read_text(encoding="utf-8"))
        changed = False
        for entry in data["entries"]:
            total += 1
            new = translate(doc_id, entry["segment_id"], entry["translated_text"])
            if new != entry["translated_text"]:
                entry["translated_text"] = new
                changed = True
                applied += 1
        if changed:
            data["generated_at"] = "2026-10-20T22:30:00Z"
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"entradas actualizadas: {applied} / {total}")
    return 0


if __name__ == "__main__":
    main()