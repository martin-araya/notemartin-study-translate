"""Detección de deriva terminológica entre versiones (fase 098).

API:

- ``compute_drift(old: dict, new: dict) -> dict``: compara dos
  glosarios del mismo dominio y devuelve el delta.

El delta tiene tres listas:

- ``added``: ``(id, source_term, domain)`` de entradas nuevas.
- ``removed``: ``(id, source_term, domain)`` de entradas eliminadas.
- ``changed``: lista con ``{id, source_term, domain, field, old, new}``
  para cada campo cambiado (``preferred.term``, ``preservation_policy``
  o ``sense``).

Los segmentos afectados por la deriva se identifican por el par
``(source_term, domain)``: cualquier segmento cuya coincidencia
puede cambiar debe invalidarse. La función no escribe en
``manifest.json``; solo emite el reporte.
"""

from __future__ import annotations


def _index(glossary: dict) -> dict[str, dict]:
    return {e["id"]: e for e in glossary.get("entries", [])}


def compute_drift(old: dict, new: dict) -> dict:
    old_idx = _index(old)
    new_idx = _index(new)
    added: list[dict] = []
    removed: list[dict] = []
    changed: list[dict] = []

    for entry_id, entry in new_idx.items():
        if entry_id not in old_idx:
            added.append({
                "id": entry_id,
                "source_term": entry.get("source_term"),
                "domain": entry.get("domain"),
            })

    for entry_id, entry in old_idx.items():
        if entry_id not in new_idx:
            removed.append({
                "id": entry_id,
                "source_term": entry.get("source_term"),
                "domain": entry.get("domain"),
            })

    for entry_id, new_entry in new_idx.items():
        old_entry = old_idx.get(entry_id)
        if old_entry is None:
            continue
        for field in ("source_term", "sense", "preservation_policy"):
            if old_entry.get(field) != new_entry.get(field):
                changed.append({
                    "id": entry_id,
                    "source_term": new_entry.get("source_term"),
                    "domain": new_entry.get("domain"),
                    "field": field,
                    "old": old_entry.get(field),
                    "new": new_entry.get(field),
                })
        old_term = old_entry.get("preferred", {}).get("term")
        new_term = new_entry.get("preferred", {}).get("term")
        if old_term != new_term:
            changed.append({
                "id": entry_id,
                "source_term": new_entry.get("source_term"),
                "domain": new_entry.get("domain"),
                "field": "preferred.term",
                "old": old_term,
                "new": new_term,
            })

    affected_segments: list[dict] = []
    for change in changed:
        affected_segments.append({
            "source_term": change["source_term"],
            "domain": change["domain"],
            "id": change["id"],
        })

    return {
        "added": added,
        "removed": removed,
        "changed": changed,
        "affected_segments": affected_segments,
        "summary": {
            "added": len(added),
            "removed": len(removed),
            "changed": len(changed),
            "affected_segments": len(affected_segments),
        },
    }


__all__ = ["compute_drift"]