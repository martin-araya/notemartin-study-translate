"""Extractor de admonitions (fase 082).

Reconoce bloques ``:::tipo ... :::``. Sin ejecución de JavaScript.

API:

- ``extract_admonition_segments(text: str) -> list[Segment]``: emite
  un segmento por bloque, con ``parent`` igual al tipo.
- ``supported_admonitions``: frozenset con los tipos permitidos.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

SUPPORTED = frozenset({"note", "tip", "info", "warning", "caution"})

OPEN_RE = re.compile(r"^:::(\w+)[ \t]*$", re.MULTILINE)


@dataclass
class Segment:
    start: int
    end: int
    kind: str
    parent: str = ""
    text: str = ""

    def to_dict(self) -> dict:
        return {
            "start": self.start,
            "end": self.end,
            "kind": self.kind,
            "parent": self.parent,
            "text": self.text,
            "translated_text": self.text,
        }


def extract_admonition_segments(text: str) -> list[Segment]:
    segments: list[Segment] = []
    for m in OPEN_RE.finditer(text):
        kind = m.group(1).lower()
        if kind not in SUPPORTED:
            continue
        body_start = m.end() + 1
        close_pattern = re.compile(r"^:::[ \t]*$", re.MULTILINE)
        close = close_pattern.search(text, body_start)
        if not close:
            continue
        body = text[body_start:close.start()]
        segments.append(Segment(
            start=body_start,
            end=close.start(),
            kind="admonition_text",
            parent=kind,
            text=body,
        ))
    segments.sort(key=lambda s: (s.start, s.end))
    return segments


__all__ = ["Segment", "extract_admonition_segments", "SUPPORTED"]