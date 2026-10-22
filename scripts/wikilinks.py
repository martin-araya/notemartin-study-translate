"""Extractor de wikilinks (fase 087).

Reconoce wikilinks estilo Obsidian:

- ``[[Target]]``
- ``[[Target|Alias]]``
- ``[[Target#Section]]``
- ``[[Target#Section|Alias]]``

API:

- ``extract_wikilink_segments(text: str) -> list[Segment]``
- ``wikilink_targets(text: str) -> list[str]``: lista de targets
  literales (sin alias).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

WIKILINK_RE = re.compile(r"\[\[([^\[\]\|]+?)(?:\|([^\[\]\|]+?))?\]\]")


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


def extract_wikilink_segments(text: str) -> list[Segment]:
    segments: list[Segment] = []
    for m in WIKILINK_RE.finditer(text):
        target = m.group(1)
        if m.group(2):
            alias = m.group(2)
            seg_start = m.start(2)
            seg_end = m.end(2)
            segments.append(Segment(
                start=seg_start,
                end=seg_end,
                kind="wikilink_alias",
                parent=target,
                text=alias,
            ))
    segments.sort(key=lambda s: (s.start, s.end))
    return segments


def wikilink_targets(text: str) -> list[str]:
    return [m.group(1) for m in WIKILINK_RE.finditer(text)]


__all__ = ["Segment", "extract_wikilink_segments", "wikilink_targets", "WIKILINK_RE"]