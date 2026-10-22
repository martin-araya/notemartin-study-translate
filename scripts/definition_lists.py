"""Extractor de definition lists (fase 083).

Reconoce pares ``Término\n: Definición`` (Pandoc/Markdown extra).

API:

- ``extract_definition_segments(text: str) -> list[Segment]``: emite
  un segmento por término y otro por cada definición. El ``parent``
  del término es ``term:<n>`` y el de la definición comparte el
  mismo ``parent`` para preservar la correspondencia.
- ``SegPair``: par ``(term, defs)`` para inspección programática.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

TERM_LINE_RE = re.compile(r"^(?!:\s)(.+?)\s*$", re.MULTILINE)
DEF_LINE_RE = re.compile(r"^:\s+(?:    )?(.+?)\s*$", re.MULTILINE)


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


@dataclass
class SegPair:
    term: Segment
    defs: list[Segment]


def extract_definition_segments(text: str) -> tuple[list[Segment], list[SegPair]]:
    segments: list[Segment] = []
    pairs: list[SegPair] = []

    lines = text.splitlines(keepends=True)
    cursor = 0
    n = len(lines)
    pair_idx = 0
    while cursor < n:
        line = lines[cursor]
        stripped = line.rstrip("\n")
        if not stripped or stripped.startswith(":"):
            cursor += 1
            continue
        term_line = stripped
        line_start = sum(len(l) for l in lines[:cursor])
        term_seg = Segment(
            start=line_start,
            end=line_start + len(term_line),
            kind="definition_term",
            parent=f"term:{pair_idx}",
            text=term_line,
        )

        defs: list[Segment] = []
        j = cursor + 1
        while j < n:
            d = lines[j].rstrip("\n")
            m = DEF_LINE_RE.match(d)
            if not m:
                break
            d_start = sum(len(l) for l in lines[:j])
            value_start = d_start + m.start(1)
            def_seg = Segment(
                start=value_start,
                end=value_start + len(m.group(1)),
                kind="definition_def",
                parent=f"term:{pair_idx}",
                text=m.group(1),
            )
            defs.append(def_seg)
            segments.append(def_seg)
            j += 1

        if defs:
            segments.append(term_seg)
            pairs.append(SegPair(term=term_seg, defs=defs))
            pair_idx += 1
            cursor = j
        else:
            cursor += 1

    segments.sort(key=lambda s: (s.start, s.end))
    return segments, pairs


__all__ = ["Segment", "SegPair", "extract_definition_segments"]