"""Clasificación de citas (fase 105 del roadmap).

Este módulo decide si un bloque es:

- ``cita_contractual``: licencia, términos de uso, descargo legal. Se
  preserva byte-a-byte, sin traducir.
- ``literal_tecnico``: código, comandos, identificadores. Ya cubierto
  por ``INV-05``; el clasificador lo devuelve por construcción.
- ``prosa_traducible``: cita no contractual, se traduce.

Las heurísticas son auditables y admiten ampliación. Las reglas se
documentan en ``references/citations-policy.md``. Cada adición nueva
exige un test que falle primero (TDD, ``AGENTS.md`` §10).

El módulo es seguro para importarse sin inicialización previa.
"""

from __future__ import annotations

import re
from typing import Iterable

CITATION_TYPES = ("contractual", "technical_literal", "translatable_prose")

SPDX_PATTERN = re.compile(r"SPDX-License-Identifier", re.IGNORECASE)
COPYRIGHT_PATTERN = re.compile(r"Copyright\s+(\(C\)|©|\d{4})", re.IGNORECASE)
ADMONITION_LEGAL_FR = re.compile(
    r"^\s*>\s*\*\*\s*(Note légale|Licence|Mentions légales|"
    r"Note de licence|Mentions juridiques)\b",
    re.IGNORECASE | re.MULTILINE,
)
NOTICE_LEGAL_FR = re.compile(
    r"\b(Note de licence|Mentions légales|Licence SPDX|"
    r"Licence\s+\w+|Copyright\s*\d{4})\b",
    re.IGNORECASE,
)
LEGAL_FR_PHRASES = [
    "conditions d'utilisation",
    "tous droits réservés",
    "est autorisé",
    "est interdit",
    "aux termes de",
    "limitation de responsabilité",
    "garantie",
    "à condition que",
]

CODE_TYPES = {"code_fenced", "code_indented", "code_inline"}


def classify(segment: dict, source_text: str | None = None) -> str:
    """Devuelve ``citation_type`` para un segmento dado.

    ``source_text`` es opcional; si se omite, se usa
    ``segment.get('translatable_text')``.
    """

    stype = segment.get("structural_type", "")
    if stype in CODE_TYPES:
        return "technical_literal"

    text = source_text if source_text is not None else segment.get("translatable_text") or ""

    if SPDX_PATTERN.search(text):
        return "contractual"
    if COPYRIGHT_PATTERN.search(text):
        return "contractual"
    if ADMONITION_LEGAL_FR.search(text):
        return "contractual"
    if NOTICE_LEGAL_FR.search(text):
        return "contractual"
    lowered = text.lower()
    for phrase in LEGAL_FR_PHRASES:
        if phrase in lowered:
            return "contractual"

    return "translatable_prose"


def classify_all(segments: Iterable[dict]) -> dict[str, int]:
    """Clasifica una iterable de segmentos y devuelve un conteo por tipo."""
    counts = {t: 0 for t in CITATION_TYPES}
    for seg in segments:
        if seg.get("citation_type"):
            ct = seg["citation_type"]
            if ct in counts:
                counts[ct] += 1
            continue
        ct = classify(seg)
        seg["citation_type"] = ct
        counts[ct] += 1
    return counts


def contractual_segments(segments: Iterable[dict]) -> list[dict]:
    """Devuelve los segmentos clasificados como contractuales."""
    return [s for s in segments if s.get("citation_type") == "contractual"]


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("uso: python3 scripts/citations.py <segments.json>", file=sys.stderr)
        sys.exit(0 if len(sys.argv) > 1 else 2)
    payload = json.loads(open(sys.argv[1], encoding="utf-8").read())
    files = payload.get("files", []) if isinstance(payload, dict) else payload
    total = {t: 0 for t in CITATION_TYPES}
    for f in files:
        segs = f.get("segments", []) if isinstance(f, dict) else []
        counts = classify_all(segs)
        for k, v in counts.items():
            total[k] += v
    print(json.dumps(total, ensure_ascii=False))
