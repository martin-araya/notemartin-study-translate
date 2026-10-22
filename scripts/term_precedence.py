"""Reglas de precedencia entre glosarios (fase 097).

Resuelve qué entrada gana cuando varios glosarios declaran el mismo
``source_term``. La precedencia es por **dominio**:

- Una entrada con ``domain == target`` gana sobre ``domain == None``
  (o cualquier otro dominio).
- Dos entradas con el mismo dominio y el mismo ``source_term`` se
  reportan como **conflicto** (no se reemplazan mutuamente).

API:

- ``resolve_conflict(source_term: str, domain: str | None, glossaries: list[dict]) -> dict | None``
- ``list_conflicts(glossaries: list[dict]) -> list[dict]``: enumera
  los conflictos donde varios glosarios declaran el mismo
  ``(source_term, domain)`` con equivalentes distintos.
"""

from __future__ import annotations

import re


def normalize_term(term: str) -> str:
    return re.sub(r"\s+", " ", term.strip().lower())


def _find_matches(source_term: str, domain, glossaries: list[dict]) -> list[dict]:
    target = normalize_term(source_term)
    matches: list[dict] = []
    for glossary in glossaries:
        for entry in glossary.get("entries", []):
            if normalize_term(entry["source_term"]) != target:
                continue
            if entry.get("domain") == domain:
                matches.append({"entry": entry, "glossary": glossary, "kind": "exact_domain"})
            elif domain is None or entry.get("domain") is None:
                matches.append({"entry": entry, "glossary": glossary, "kind": "fallback_global"})
    return matches


def resolve_conflict(source_term: str, domain, glossaries: list[dict]) -> dict | None:
    """Devuelve la entrada ganadora o ``None`` si no hay match."""
    matches = _find_matches(source_term, domain, glossaries)
    if not matches:
        return None
    exact = [m for m in matches if m["kind"] == "exact_domain"]
    if exact:
        if len(exact) > 1:
            return None
        return exact[0]["entry"]
    fallback = [m for m in matches if m["kind"] == "fallback_global"]
    if len(fallback) > 1:
        return None
    if fallback:
        return fallback[0]["entry"]
    return None


def list_conflicts(glossaries: list[dict]) -> list[dict]:
    """Devuelve entradas donde ``(source_term, domain)`` aparece en
    varios glosarios con ``preferred.term`` distinto."""
    index: dict[tuple[str, str], dict[str, dict]] = {}
    for glossary in glossaries:
        glossary_id = glossary.get("source") or id(glossary).__str__()
        for entry in glossary.get("entries", []):
            key = (normalize_term(entry["source_term"]), entry.get("domain") or "__null__")
            value = entry.get("preferred", {}).get("term", "")
            index.setdefault(key, {}).setdefault(glossary_id, {
                "term": value,
                "source_term": entry["source_term"],
                "domain": entry.get("domain"),
            })

    conflicts: list[dict] = []
    for key, by_source in index.items():
        if len(by_source) < 2:
            continue
        values = {item["term"] for item in by_source.values()}
        if len(values) <= 1:
            continue
        conflicts.append({
            "source_term": key[0],
            "domain": None if key[1] == "__null__" else key[1],
            "entries": list(by_source.values()),
        })
    return conflicts


__all__ = ["normalize_term", "resolve_conflict", "list_conflicts"]