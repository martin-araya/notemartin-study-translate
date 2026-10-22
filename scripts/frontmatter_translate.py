"""Extractor de campos traducibles del frontmatter (fase 088).

Cuando ``frontmatter_policy: translate-allowlist`` está activo y
``frontmatter_allowed_fields`` lista los campos permitidos, el
extractor emite segmentos para esos campos.

API:

- ``extract_frontmatter_segments(text: str, allowed: list[str]) -> list[Segment]``
- ``frontmatter_findings(text: str, allowed: list[str]) -> list[dict]``
"""

from __future__ import annotations

import re
from dataclasses import dataclass

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
FIELD_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_\-]*):\s*(.*)$", re.MULTILINE)


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


def extract_frontmatter_segments(text: str, allowed: list[str]) -> list[Segment]:
    segments: list[Segment] = []
    fm = FRONTMATTER_RE.match(text)
    if not fm:
        return segments
    body = fm.group(1)
    body_start = fm.start(1)
    allowed_set = set(allowed)
    for m in FIELD_RE.finditer(body):
        name = m.group(1)
        value = m.group(2).strip()
        if name not in allowed_set:
            continue
        seg_start = body_start + m.start(2)
        seg_end = body_start + m.end(2)
        segments.append(Segment(
            start=seg_start,
            end=seg_end,
            kind="frontmatter_field",
            parent=name,
            text=value,
        ))
    segments.sort(key=lambda s: (s.start, s.end))
    return segments


def frontmatter_findings(text: str, allowed: list[str]) -> list[dict]:
    findings: list[dict] = []
    fm = FRONTMATTER_RE.match(text)
    if not fm:
        return findings
    body = fm.group(1)
    body_start = fm.start(1)
    allowed_set = set(allowed)
    for m in FIELD_RE.finditer(body):
        name = m.group(1)
        value = m.group(2).strip()
        if name in allowed_set:
            continue
        findings.append({
            "kind": "literal_frontmatter_field",
            "name": name,
            "value": value,
            "start": body_start + m.start(),
            "end": body_start + m.end(),
        })
    return findings


__all__ = ["Segment", "extract_frontmatter_segments", "frontmatter_findings"]