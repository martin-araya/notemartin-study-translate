"""Detector de expresiones matemáticas (fase 086).

Reconoce límites de ``$$...$$`` (display) y ``$...$`` (inline) sin
parsear LaTeX. La prosa entre expresiones es traducible; las
equations no.

API:

- ``collect_math_spans(text: str) -> list[Span]``: devuelve los
  rangos literales de display e inline.
- ``collect_text_spans(text: str) -> list[Span]``: devuelve los
  rangos traducibles (prosa entre ecuaciones).
"""

from __future__ import annotations

import re
from dataclasses import dataclass


DISPLAY_RE = re.compile(r"\$\$[\s\S]*?\$\$", re.MULTILINE)
INLINE_RE = re.compile(r"(?<!\$)\$(?!\$)[^\$\n]+\$(?!\$)")


@dataclass
class Span:
    start: int
    end: int
    kind: str
    value: str = ""

    def to_dict(self) -> dict:
        return {
            "start": self.start,
            "end": self.end,
            "kind": self.kind,
            "value": self.value,
        }


def collect_math_spans(text: str) -> list[Span]:
    out: list[Span] = []
    for m in DISPLAY_RE.finditer(text):
        out.append(Span(start=m.start(), end=m.end(), kind="math_display", value=m.group(0)))
    for m in INLINE_RE.finditer(text):
        out.append(Span(start=m.start(), end=m.end(), kind="math_inline", value=m.group(0)))
    out.sort(key=lambda s: (s.start, s.end))
    return out


def collect_text_spans(text: str) -> list[Span]:
    reserved = [(s.start, s.end) for s in collect_math_spans(text)]
    reserved.sort()
    out: list[Span] = []
    cursor = 0
    n = len(text)
    for start, end in reserved:
        if cursor < start:
            chunk = text[cursor:start]
            if chunk.strip():
                out.append(Span(start=cursor, end=start, kind="text", value=chunk))
        cursor = end
    if cursor < n:
        chunk = text[cursor:n]
        if chunk.strip():
            out.append(Span(start=cursor, end=n, kind="text", value=chunk))
    return out


__all__ = ["Span", "collect_math_spans", "collect_text_spans"]