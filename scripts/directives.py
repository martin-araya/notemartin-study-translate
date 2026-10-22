"""Extractor de directivas de documentación (fase 084).

Reconoce directivas Sphinx/Numpydoc en bloques de docstring.

API:

- ``extract_directive_segments(text: str) -> list[Segment]``
- ``DIRECTIVES``: frozenset con los nombres permitidos.
- Las directivas con nombre desconocido NO emiten segmentos y se
  reportan en ``unknown_directives``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

DIRECTIVES = (
    "param", "type", "returns", "rtype", "raises",
)

DIRECTIVE_RE = re.compile(
    r"^\s*:(?P<name>" + "|".join(DIRECTIVES) + r")"
    r"(?:\s+(?P<arg>[A-Za-z_][A-Za-z0-9_.\[\] |]*))?"
    r":\s*(?P<body>.+?)\s*$",
    re.MULTILINE,
)

UNKNOWN_RE = re.compile(
    r"^\s*:(?P<name>[A-Za-z_][A-Za-z0-9_]*)"
    r"(?:\s+(?P<arg>[A-Za-z_][A-Za-z0-9_.\[\] |]*))?"
    r":\s*(?P<body>.+?)\s*$",
    re.MULTILINE,
)


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


def extract_directive_segments(text: str) -> tuple[list[Segment], list[dict]]:
    segments: list[Segment] = []
    unknown: list[dict] = []

    for m in DIRECTIVE_RE.finditer(text):
        name = m.group("name")
        body = m.group("body") or ""
        segments.append(Segment(
            start=m.start("body"),
            end=m.end("body"),
            kind="directive_text",
            parent=name,
            text=body,
        ))

    for m in UNKNOWN_RE.finditer(text):
        name = m.group("name")
        if name in DIRECTIVES:
            continue
        unknown.append({
            "name": name,
            "start": m.start(),
            "end": m.end(),
            "severity": "critical",
        })

    segments.sort(key=lambda s: (s.start, s.end))
    return segments, unknown


__all__ = ["Segment", "extract_directive_segments", "DIRECTIVES"]