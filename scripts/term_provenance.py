"""Adjuntar procedencia a un glosario (fase 096).

Añade (o reemplaza idempotentemente) el campo ``provenance`` en cada
entrada del glosario sin tocar ``source_term``, ``sense`` ni
``preferred``. La procedencia registra la fuente externa del
término, su versión y el importador.

API:

- ``attach_provenance(glossary: dict, source: str, source_version: str, *, url: str | None = None, importer: str | None = None, fetched_at: str | None = None) -> dict``
  Devuelve una copia modificada del glosario. Idempotente: aplicar
  dos veces con la misma fuente no produce duplicados.

- ``has_provenance(glossary: dict) -> bool``: ``True`` si al menos
  una entrada tiene ``provenance``.

La documentación traducible no se sustituye: este módulo solo añade
metadatos sobre las decisiones existentes.
"""

from __future__ import annotations

import copy
import datetime
from typing import Optional


def attach_provenance(
    glossary: dict,
    source: str,
    source_version: str,
    *,
    url: Optional[str] = None,
    importer: Optional[str] = None,
    fetched_at: Optional[str] = None,
) -> dict:
    if not source:
        raise ValueError("source no puede estar vacío")
    if not source_version:
        raise ValueError("source_version no puede estar vacío")
    out = copy.deepcopy(glossary)
    when = fetched_at or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    provenance = {
        "source": source,
        "source_version": source_version,
        "fetched_at": when,
    }
    if url:
        provenance["url"] = url
    if importer:
        provenance["importer"] = importer
    for entry in out.get("entries", []):
        entry["provenance"] = dict(provenance)
    return out


def has_provenance(glossary: dict) -> bool:
    return any("provenance" in entry for entry in glossary.get("entries", []))


__all__ = ["attach_provenance", "has_provenance"]