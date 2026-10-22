"""Detección de idioma por región de prosa.

Clasifica el ``translatable_text`` de cada segmento en
``{es, en, fr, other, unknown}`` y asigna una disposición entre
``{translatable, already_target, code_skip, no_text, too_short,
mixed_or_code}``.

Implementación con ``langdetect``. La semilla se fija para que dos
ejecuciones produzcan clasificaciones estables. Los segmentos cortos
no se clasifican.

Importante: la clasificación es por segmento, no por archivo. Un
archivo inglés con ejemplos en español se mantiene como
``translatable`` para los segmentos en inglés; los segmentos en
español se marcan ``already_target``. Desde la fase 104 el
clasificador distingue explícitamente ``fr`` como categoría
reconocible (no la agrupa con ``other``) cuando el ``profile``
incluye ``mixed_profile.allowed_source_languages``. Si el perfil no
lo declara, ``fr`` sigue cayendo en ``other``.

La lista de idiomas reconocibles se configura con la variable de
entorno ``RECOGNIZED_SOURCE_LANGUAGES`` (lista separada por comas,
p. ej. ``en,fr``) o por el flag ``--recognized``. El valor por
defecto es ``en`` para mantener la compatibilidad con el núcleo
estabilizado en 060.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path

from langdetect import DetectorFactory, detect_langs

# El agregado por archivo es una regla compartida con el núcleo: si las dos
# rutas tuvieran copias distintas, el manifiesto informaría de un número que
# no es el que hay.
from text_signals import file_disposition  # noqa: F401  (reexportado)

DetectorFactory.seed = 42

CODE_TYPES = {"code_fenced", "code_indented", "code_inline"}
MIN_LEN = 10
ES_CONF = 0.6
DEFAULT_RECOGNIZED = ("en",)


def classify_segment(seg: dict, recognized: tuple[str, ...] = DEFAULT_RECOGNIZED) -> tuple[str, str, float]:
    """Devuelve ``(language, disposition, confidence)`` para un segmento.

    ``recognized`` controla qué idiomas distintos de ``es`` se exponen
    explícitamente (p. ej. ``en``, ``fr``). Los idiomas no reconocidos
    caen en ``other``.
    """
    stype = seg.get("structural_type", "")
    text = seg.get("translatable_text") or ""

    if stype in CODE_TYPES:
        return ("code", "code_skip", 1.0)
    if not text.strip():
        return ("empty", "no_text", 1.0)
    if len(text) < MIN_LEN:
        return ("unknown", "too_short", 0.0)

    literals = seg.get("protected_literals") or []
    if literals and stype in {"paragraph", "heading", "list_item", "blockquote"}:
        non_literal = text
        for lit in literals:
            v = lit.get("value") or ""
            if v:
                non_literal = non_literal.replace(v, "", 1)
        if len(non_literal.strip()) < max(3, len(text) // 4):
            return ("mixed", "mixed_or_code", 0.0)

    try:
        results = detect_langs(text)
    except Exception:
        return ("unknown", "unknown", 0.0)

    if not results:
        return ("unknown", "unknown", 0.0)

    best = results[0]
    if best.lang == "es" and best.prob >= ES_CONF:
        return ("es", "already_target", best.prob)

    recognized_set = set(recognized)
    if best.lang in recognized_set and best.prob >= 0.6:
        return (best.lang, "translatable", best.prob)

    if best.prob >= 0.6:
        return ("other", "translatable", best.prob)
    return ("unknown", "unknown", best.prob)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="detect_language.py")
    p.add_argument("--segments", required=True, help="JSON producido por prepare.py --segments.")
    p.add_argument("--out", required=True, help="JSON con language y disposition por segmento.")
    p.add_argument("--seed", type=int, default=42, help="Semilla para langdetect.")
    p.add_argument(
        "--recognized",
        default=os.environ.get("RECOGNIZED_SOURCE_LANGUAGES"),
        help=(
            "Lista separada por comas de idiomas reconocibles además del español. "
            f"Por defecto '{','.join(DEFAULT_RECOGNIZED)}'."
        ),
    )
    return p.parse_args(argv)


def write_atomic(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    DetectorFactory.seed = args.seed

    if args.recognized:
        recognized: tuple[str, ...] = tuple(
            lang.strip() for lang in args.recognized.split(",") if lang.strip()
        ) or DEFAULT_RECOGNIZED
    else:
        recognized = DEFAULT_RECOGNIZED

    seg_path = Path(args.segments)
    out_path = Path(args.out)
    payload = json.loads(seg_path.read_text(encoding="utf-8"))

    file_counts: dict[str, dict[str, int]] = {}

    for f in payload.get("files", []):
        doc_id = f.get("document_id", "?")
        file_counts[doc_id] = {}
        for seg in f.get("segments", []):
            lang, disposition, conf = classify_segment(seg, recognized=recognized)
            seg["language"] = lang
            seg["disposition"] = disposition
            seg["confidence"] = conf
            file_counts[doc_id][disposition] = file_counts[doc_id].get(disposition, 0) + 1

    for f in payload.get("files", []):
        doc_id = f.get("document_id", "?")
        counts = file_counts.get(doc_id, {})
        f["file_disposition"] = file_disposition(counts)
        f["file_disposition_counts"] = counts

    payload["generated_at"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    payload["recognized_source_languages"] = list(recognized)

    write_atomic(out_path, payload)
    total = sum(len(f["segments"]) for f in payload.get("files", []))
    print(f"ok: {total} segmentos clasificados -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())