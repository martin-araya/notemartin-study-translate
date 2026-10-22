"""Reporte terminológico para revisión humana (fase 099).

API:

- ``render_markdown(glossaries) -> str``: tabla Markdown agrupada por
  dominio con source_term, equivalente preferido, política,
  justificación y ejemplos.
- ``render_json(glossaries) -> dict``: estructura JSON con la misma
  información orientada a tooling programático.

El reporte es **informativo**: nunca se mezcla con ``RELEASE_NOTES.md``
ni con el output de la skill. Vive en ``reports/term/``.
"""

from __future__ import annotations

import json
from collections import defaultdict


def render_markdown(glossaries: list[dict]) -> str:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for glossary in glossaries:
        for entry in glossary.get("entries", []):
            domain = entry.get("domain") or "global"
            grouped[domain].append(entry)

    lines: list[str] = ["# Reporte terminológico", ""]
    if not grouped:
        lines.append("(Sin entradas)")
        return "\n".join(lines)

    for domain in sorted(grouped):
        lines.append(f"## Dominio: {domain}")
        lines.append("")
        lines.append("| source_term | equivalente | política | justificación | ejemplos |")
        lines.append("|---|---|---|---|---|")
        for entry in sorted(grouped[domain], key=lambda e: e["source_term"]):
            equivalent = entry.get("preferred", {}).get("term", "")
            policy = entry.get("preservation_policy", "")
            examples = "; ".join(
                f"{ex.get('before', '').strip()}…{ex.get('after', '').strip()}"
                for ex in entry.get("context_examples", [])
            )
            lines.append(
                f"| `{entry['source_term']}` | `{equivalent}` | `{policy}` | "
                f"{entry.get('justification', '')} | {examples} |"
            )
        lines.append("")
    return "\n".join(lines)


def render_json(glossaries: list[dict]) -> dict:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for glossary in glossaries:
        glossary_id = glossary.get("source") or id(glossary).__str__()
        for entry in glossary.get("entries", []):
            domain = entry.get("domain") or "global"
            grouped[domain].append({
                "glossary_id": glossary_id,
                "id": entry["id"],
                "source_term": entry["source_term"],
                "preferred": entry.get("preferred"),
                "preservation_policy": entry.get("preservation_policy"),
                "justification": entry.get("justification"),
                "context_examples": entry.get("context_examples", []),
            })
    return {
        "domains": dict(grouped),
        "summary": {
            "total_entries": sum(len(v) for v in grouped.values()),
            "total_domains": len(grouped),
        },
    }


__all__ = ["render_markdown", "render_json"]