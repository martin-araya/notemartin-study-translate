"""Adaptador Mermaid opcional (fase 085).

Reconoce etiquetas visibles en nodos Mermaid **sin** ejecutar ni
renderizar el diagrama. Solo emite segmentos para los textos
visibles; los IDs, tipos y direcciones permanecen literales.

Activación:

- Por defecto el adaptador está **desactivado** y Mermaid se preserva
  literal como en el modo núcleo (fase 030).
- Para activar la traducción de etiquetas, el perfil debe declarar
  ``profile.mermaid.enabled: true`` con
  ``profile.mermaid.labels: "allow"``.

API:

- ``extract_mermaid_label_segments(text: str) -> list[Segment]``
- ``is_valid_mermaid(text: str) -> bool`` y
  ``mermaid_findings(text: str) -> list[dict]``.
- Constante ``LABEL_PATTERN_RE``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

LABEL_PATTERN_RE = re.compile(
    r"""(?P<id>[A-Za-z_][A-Za-z0-9_]*)\s*"""
    r"""(?P<shape>\[|\(|{|>)\s*[\[(]?"""
    r'"(?P<text>[^"]+)"'
    r"""[\])]?"""
)

EDGE_LABEL_RE = re.compile(
    r"\|(?P<text>[^|]+)\|"
)

TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|\[\]|\(\)|\{\}|\(\(|\)\)")


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


def extract_mermaid_label_segments(text: str) -> list[Segment]:
    segments: list[Segment] = []
    for m in LABEL_PATTERN_RE.finditer(text):
        node_id = m.group("id")
        body = m.group("text")
        segments.append(Segment(
            start=m.start("text"),
            end=m.end("text"),
            kind="mermaid_node_label",
            parent=node_id,
            text=body,
        ))
    for m in EDGE_LABEL_RE.finditer(text):
        segments.append(Segment(
            start=m.start("text"),
            end=m.end("text"),
            kind="mermaid_edge_label",
            parent="edge",
            text=m.group("text").strip(),
        ))
    segments.sort(key=lambda s: (s.start, s.end))
    return segments


def mermaid_findings(text: str) -> list[dict]:
    findings: list[dict] = []
    bracket_pattern = re.compile(r"\][A-Za-z0-9_]+|\)invalid|\(invalid")
    for m in bracket_pattern.finditer(text):
        findings.append({
            "kind": "unsupported_mermaid",
            "evidence": m.group(0),
            "start": m.start(),
            "end": m.end(),
            "severity": "critical",
        })
    return findings


def is_valid_mermaid(text: str) -> bool:
    return not mermaid_findings(text)


__all__ = [
    "Segment",
    "LABEL_PATTERN_RE",
    "extract_mermaid_label_segments",
    "mermaid_findings",
    "is_valid_mermaid",
]