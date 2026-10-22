"""Resuelve las disposiciones ambiguas que deja ``detect_language.py``.

El detector de idioma clasifica cada segmento en una disposición a partir
de su prosa. Deja tres categorías que no son decisiones, sino falta de
decisión:

- ``unknown``: el detector no dio veredicto de idioma. Contiene rutas de
  módulo, etiquetas de enlace y prosa real mezcladas sin separación.
- ``mixed_or_code``: la parte traducible es menor que el umbral. Puede
  ser un párrafo con mucha referencia inline o, como se midió sobre el
  corpus beta, un tipo genérico de TypeScript entre acentos graves.
- ``too_short``: fragmentos por debajo del mínimo Morfológico.

Este script **no traduce**. Decide, para cada segmento, si hay prosa que
traducir o si el segmento es literal protegido. Devuelve el recuento
para que el denominador no se reduzca en silencio: INV-12 exige que
toda región tenga propietario o disposición explícita, y una exclusión no
cuenta como traducción.

Reglas, en orden de aplicación:

1. Vacío o solo espacios → ``no_text``.
2. Si, tras enmascarar código inline, enlaces, anclas HTML y
   autolinks, no queda prosa → ``code_skip`` (literal, no se traduce).
3. Si lo que queda es una ruta de módulo, una ruta de archivo o un
   identificador compound → ``code_skip``.
4. Si la prosa es demasiado corta para decidir → ``too_short``.
5. En cualquier otro caso → ``translatable``.

El umbral de longitud se mide sobre la prosa enmascarada, no sobre el
texto completo: un párrafo con diez referencias inline y treinta
palabras tiene prosa traducible aunque su texto bruto sea largo.

    python3 scripts/resolve_dispositions.py \\
        --segments segments_classified.json \\
        --out segments_resolved.json --report reports/dispositions.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

# La cuenta de palabras y el agregado por archivo son reglas compartidas
# con la clasificación por idioma (fase 104). Viven en el núcleo para que
# este script no dependa de un módulo opcional.
from text_signals import file_disposition, word_count  # noqa: F401

INLINE_CODE_RE = re.compile(r"(`+)(?:(?!\1)[\s\S])*?\1")
WIKILINK_RE = re.compile(r"\[\[[^\]]+\]\]")
LINK_RE = re.compile(r"!?\[[^\]]*\]\([^)]*\)")
AUTOLINK_RE = re.compile(r"<https?://[^>]+>")
HTML_ANCHOR_RE = re.compile(r"<a\s[^>]*>\s*</a>")
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\([^)]*\)")

MODULE_PATH_RE = re.compile(r"^[@~\w][\w./@-]*/[\w./@-]+$")
FILE_PATH_RE = re.compile(r"^[\w@][\w@./-]*\.[A-Za-z0-9]+$")
COMPOUND_ID_RE = re.compile(r"^[\w@.\-]+$")
VERSION_RE = re.compile(r"^v?\d+(\.\d+)*$")
URL_RE = re.compile(r"^(https?://|mailto:)", re.IGNORECASE)

RESOLVED = {"unknown", "mixed_or_code", "too_short"}

DEFAULT_MIN_WORDS = 3


def mask_literals(text: str) -> str:
    """Devuelve el texto con los literales protegidos sustit por espacios.

    Sustituye por un espacio en vez de borrar para no fusionar palabras
    que en el original estaban separadas por un literal.

    Las imágenes conservan su `alt`: es texto visible para lectores de
    pantalla y, cuando describe el contenido, es prosa traducible. Lo que
    se retira es el destino, que es un literal funcional.
    """
    out = IMAGE_RE.sub(lambda m: " " + m.group(1) + " ", text)
    out = INLINE_CODE_RE.sub(" ", out)
    out = WIKILINK_RE.sub(" ", out)
    out = LINK_RE.sub(" ", out)
    out = AUTOLINK_RE.sub(" ", out)
    out = HTML_ANCHOR_RE.sub(" ", out)
    return out


def is_literal_only(text: str) -> bool:
    """Cierto si el texto es un literal protegido y no prosa."""
    stripped = text.strip()
    if not stripped:
        return True
    if URL_RE.match(stripped):
        return True
    if MODULE_PATH_RE.match(stripped):
        return True
    if FILE_PATH_RE.match(stripped):
        return True
    if VERSION_RE.match(stripped):
        return True
    return COMPOUND_ID_RE.match(stripped) is not None


def prose_of(text: str) -> str:
    """Prosa traducible: lo que queda tras enmascarar los literales."""
    return " ".join(mask_literals(text).split())


def resolve(text: str, min_words: int = DEFAULT_MIN_WORDS) -> tuple[str, str]:
    """Devuelve (disposición, motivo) para un segmento."""
    raw = text or ""
    if not raw.strip():
        return "no_text", "segmento vacío"

    prose = prose_of(raw)

    if not prose:
        return "code_skip", "solo literales protegidos: no queda prosa"
    if is_literal_only(prose):
        return "code_skip", "identificador o ruta, no prosa"

    words = word_count(prose)
    if words < min_words:
        return "too_short", f"{words} palabras por debajo del mínimo {min_words}"

    return "translatable", f"{words} palabras de prosa traducible"


def refresh_file_dispositions(doc: dict) -> list[str]:
    """Recalcula `file_disposition` y `file_disposition_counts` por archivo.

    El agregado es **derivado**: si se escribe una vez y después se cambian
    disposiciones de segmento, el agregado miente. Se regenera aquí con la
    misma regla que usa la clasificación por idioma, que vive en
    `text_signals.file_disposition` (núcleo) para que las dos rutas no
    puedan divergir.

    Devuelve las rutas cuyo agregado cambió.
    """
    changed: list[str] = []
    for entry in doc.get("files", []):
        counts: dict[str, int] = {}
        for seg in entry.get("segments", []):
            disposition = seg.get("disposition")
            counts[disposition] = counts.get(disposition, 0) + 1
        before = (entry.get("file_disposition"), entry.get("file_disposition_counts"))
        entry["file_disposition_counts"] = counts
        entry["file_disposition"] = file_disposition(counts)
        after = (entry.get("file_disposition"), entry.get("file_disposition_counts"))
        if before != after:
            changed.append(entry.get("path") or entry.get("document_id") or "?")
    return changed


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="resolve_dispositions.py")
    p.add_argument("--segments", required=True,
                   help="JSON de detect_language.py (segments_classified.json).")
    p.add_argument("--out", required=True, help="JSON de salida con las resoluciones.")
    p.add_argument("--report", help="Reporte JSON opcional con los recuentos.")
    p.add_argument("--min-words", type=int, default=DEFAULT_MIN_WORDS,
                   help=f"Palabras mínimas para considerar traducible (por defecto {DEFAULT_MIN_WORDS}).")
    p.add_argument("--apply", action="store_true",
                   help="Escribir el archivo de salida. Sin este flag solo se informa.")
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args(argv)


def write_atomic(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    doc = json.loads(Path(args.segments).read_text(encoding="utf-8"))

    transitions: dict[str, Counter] = {}
    reason_kinds: dict[str, Counter] = {}
    total_changed = 0

    for entry in doc.get("files", []):
        for seg in entry.get("segments", []):
            current = seg.get("disposition")
            if current not in RESOLVED:
                continue
            text = seg.get("translatable_text", "") or ""
            new, reason = resolve(text, args.min_words)
            seg["previous_disposition"] = current
            seg["disposition"] = new
            seg["disposition_reason"] = reason
            transitions.setdefault(current, Counter())[new] += 1
            reason_kinds.setdefault(current, Counter())[reason.split(":")[0]] += 1
            total_changed += 1

    by_disposition = Counter()
    for entry in doc.get("files", []):
        for seg in entry.get("segments", []):
            by_disposition[seg.get("disposition")] += 1

    # El agregado por archivo se recalcula aquí. `detect_language.py` lo
    # escribe al clasificar, pero este script cambia disposiciones y el
    # agregado se quedaba con el valor anterior: un documento declaraba
    # 189 segmentos traducibles y tenía 255. El agregado era el número que
    # se leía al informar y no era cierto.
    refreshed = refresh_file_dispositions(doc)

    report = {
        "segments_examined": sum(
            1 for e in doc.get("files", []) for s in e.get("segments", [])
            if s.get("disposition") in RESOLVED or s.get("previous_disposition")
        ),
        "segments_resolved": total_changed,
        "transitions": {k: dict(v) for k, v in sorted(transitions.items())},
        "reason_kinds": {k: dict(v) for k, v in sorted(reason_kinds.items())},
        "dispositions_after": dict(by_disposition.most_common()),
        "file_dispositions_refreshed": refreshed,
        "min_words": args.min_words,
    }

    if args.apply and not args.dry_run:
        write_atomic(Path(args.out), doc)
        report["written"] = True
        report["out"] = args.out
    else:
        report["written"] = False

    if args.report:
        write_atomic(Path(args.report), report)
        report["report"] = args.report

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())