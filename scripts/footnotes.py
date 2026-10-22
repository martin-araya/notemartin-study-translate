"""Extractor de footnotes (fase 081).

Reconoce referencias ``[^id]`` y definiciones ``[^id]: texto``.

API:

- ``extract_footnote_segments(text: str) -> list[Segment]``: emite
  un segmento por cada definición, con ``parent`` igual al ``id``.
- ``Segment``: dataclass con ``start``, ``end``, ``kind``,
  ``parent`` y ``text``.

Las referencias en el cuerpo (``[^id]``) NO emiten segmentos: son
literales. La asociación referencia↔definición se conserva porque
los bytes del ``id`` se preservan intactos.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

FOOTNOTE_DEF_RE = re.compile(r"^\[\^([A-Za-z0-9_\-]+)\]:\s+(.+)$", re.MULTILINE)


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


def extract_footnote_segments(text: str) -> list[Segment]:
    segments: list[Segment] = []
    for m in FOOTNOTE_DEF_RE.finditer(text):
        fid = m.group(1)
        body = m.group(2)
        start = m.start(2)
        end = m.end(2)
        segments.append(Segment(
            start=start,
            end=end,
            kind="footnote_text",
            parent=fid,
            text=body,
        ))
    segments.sort(key=lambda s: (s.start, s.end))
    return segments


__all__ = ["Segment", "extract_footnote_segments"]