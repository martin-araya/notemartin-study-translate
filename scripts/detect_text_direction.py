"""Detección de dirección de texto y sistema de numerales (fase 108).

Asigna a cada segmento un campo ``text_direction`` ∈
``{ltr, rtl, mixed}`` y un campo ``digits`` ∈
``{ascii, arabic_indic, arabic_eastern, other}``.

Esta función se invoca después de ``prepare.py`` y antes de la
clasificación de idioma. El módulo es seguro para importarse sin
efectos secundarios.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Iterable


ASCII_DIGITS = set("0123456789")
ARABIC_INDIC = {"\u0660", "\u0661", "\u0662", "\u0663", "\u0664",
                "\u0665", "\u0666", "\u0667", "\u0668", "\u0669"}
ARABIC_EASTERN = {"\u06f0", "\u06f1", "\u06f2", "\u06f3", "\u06f4",
                  "\u06f5", "\u06f6", "\u06f7", "\u06f8", "\u06f9"}
RTL_RANGES = [
    (0x0590, 0x05FF),  # Hebrew
    (0x0600, 0x06FF),  # Arabic
    (0x0700, 0x074F),  # Syriac
    (0x0750, 0x077F),  # Arabic Supplement
    (0x0780, 0x07BF),  # Thaana
    (0x07C0, 0x07FF),  # NKo
    (0x0800, 0x083F),  # Samaritan
    (0x0840, 0x085F),  # Mandaic
    (0xFB1D, 0xFB4F),
    (0xFB50, 0xFDFF),  # Arabic Presentation Forms-A
    (0xFE70, 0xFEFF),  # Arabic Presentation Forms-B
]


def _is_rtl(char: str) -> bool:
    if not char.strip():
        return False
    cp = ord(char)
    for start, end in RTL_RANGES:
        if start <= cp <= end:
            return True
    return False


def detect_text_direction(text: str) -> str:
    """Devuelve ``ltr``, ``rtl`` o ``mixed`` según los caracteres no-espacio."""
    has_ltr = False
    has_rtl = False
    for ch in text:
        if not ch.strip():
            continue
        if _is_rtl(ch):
            has_rtl = True
        else:
            has_ltr = True
        if has_ltr and has_rtl:
            return "mixed"
    if has_rtl:
        return "rtl"
    return "ltr"


def detect_digits(text: str) -> str:
    """Detecta el sistema numérico dominante en ``text``.

    Devuelve ``ascii``, ``arabic_indic``, ``arabic_eastern`` u ``other``.
    Si no hay dígitos, devuelve ``other``.
    """
    counts = {"ascii": 0, "arabic_indic": 0, "arabic_eastern": 0}
    for ch in text:
        if ch in ASCII_DIGITS:
            counts["ascii"] += 1
        elif ch in ARABIC_INDIC:
            counts["arabic_indic"] += 1
        elif ch in ARABIC_EASTERN:
            counts["arabic_eastern"] += 1
    found = {k: v for k, v in counts.items() if v > 0}
    if not found:
        return "other"
    return max(found.items(), key=lambda kv: kv[1])[0]


def classify_segment(seg: dict) -> tuple[str, str]:
    text = seg.get("translatable_text") or ""
    return detect_text_direction(text), detect_digits(text)


def classify_all(segments: Iterable[dict]) -> dict[str, int]:
    counts: dict[str, int] = {"ltr": 0, "rtl": 0, "mixed": 0}
    for seg in segments:
        text = seg.get("translatable_text") or ""
        td, _digits = classify_segment(seg)
        seg["text_direction"] = td
        counts[td] += 1
    return counts


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("uso: python3 scripts/detect_text_direction.py <segments.json>", file=sys.stderr)
        sys.exit(0 if len(sys.argv) > 1 else 2)
    payload = json.loads(open(sys.argv[1], encoding="utf-8").read())
    files = payload.get("files", []) if isinstance(payload, dict) else payload
    total = {"ltr": 0, "rtl": 0, "mixed": 0}
    for f in files:
        segs = f.get("segments", []) if isinstance(f, dict) else []
        counts = classify_all(segs)
        for k, v in counts.items():
            total[k] += v
    print(json.dumps(total, ensure_ascii=False))
