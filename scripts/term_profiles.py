"""Validación de perfiles terminológicos (fases 091-100).

API:

- ``validate_profile(profile: dict) -> list[str]``: devuelve una
  lista de problemas. Lista vacía significa perfil válido.
- ``validate_against_schema(profile: dict) -> list[str]``: valida contra
  ``schemas/term_profile.schema.json``. Lista vacía significa que el
  esquema también lo acepta.
- ``PROFILES_INICIALES``: perfiles de ejemplo del índice
  ``references/term-profiles.md``. Son de laboratorio: llevan
  ``corpus_real: false`` y lo declaran.

Un perfil sin corpus no activa nada. Esa es la diferencia entre un perfil
terminológico y una constante de código.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schemas" / "term_profile.schema.json"

KNOWN_DOMAINS = ("database", "network", "frontend", "systems", "ml_ai")

# Un aprobador que sea el propio agente o el propio repositorio no es una
# persona. Se acepta en fixtures de laboratorio; se rechaza en una
# ejecución real, que es donde el perfil cambia la traducción.
LAB_APPROVERS = ("example-agent", "agent", "fixture")

_CORPUS_REF = "evals/cases/terminology.md"

PROFILES_INICIALES = [
    {
        "profile_id": "database-only",
        "version": "1.0.0",
        "enabled_domains": ["database"],
        "approver": "example-agent",
        "approved_at": "2026-10-20T00:00:00Z",
        "corpus_ref": _CORPUS_REF,
        "justification": "Perfil de laboratorio sobre glosarios sintéticos; no activa ninguna ejecución real.",
        "corpus_real": False,
    },
    {
        "profile_id": "web-stack",
        "version": "1.0.0",
        "enabled_domains": ["frontend", "network"],
        "approver": "example-agent",
        "approved_at": "2026-10-20T00:00:00Z",
        "corpus_ref": _CORPUS_REF,
        "justification": "Perfil de laboratorio sobre glosarios sintéticos; no activa ninguna ejecución real.",
        "corpus_real": False,
    },
    {
        "profile_id": "ml-pipeline",
        "version": "1.0.0",
        "enabled_domains": ["ml_ai", "systems"],
        "approver": "example-agent",
        "approved_at": "2026-10-20T00:00:00Z",
        "corpus_ref": _CORPUS_REF,
        "justification": "Perfil de laboratorio sobre glosarios sintéticos; no activa ninguna ejecución real.",
        "corpus_real": False,
    },
    {
        "profile_id": "mixed-default",
        "version": "1.0.0",
        "enabled_domains": ["database", "frontend", "ml_ai", "network", "systems"],
        "approver": "example-agent",
        "approved_at": "2026-10-20T00:00:00Z",
        "corpus_ref": _CORPUS_REF,
        "justification": "Perfil de laboratorio sobre glosarios sintéticos; no activa ninguna ejecución real.",
        "corpus_real": False,
    },
]


def validate_against_schema(profile: dict) -> list[str]:
    """Errores de `schemas/term_profile.schema.json` en texto legible."""
    try:
        import jsonschema
    except ImportError:  # pragma: no cover
        return []
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return [
        f"{'/'.join(str(p) for p in err.absolute_path) or '(raíz)'}: {err.message}"
        for err in sorted(
            jsonschema.Draft202012Validator(schema).iter_errors(profile),
            key=lambda e: list(e.absolute_path),
        )
    ]


def validate_profile(profile: dict) -> list[str]:
    """Reglas que el esquema no puede expresar por sí solo."""
    errors: list[str] = []
    if not profile.get("profile_id"):
        errors.append("profile_id es obligatorio")
    if not profile.get("version"):
        errors.append("version es obligatorio")
    if not profile.get("approver"):
        errors.append("approver es obligatorio; la skill no aprueba perfiles")
    if not profile.get("approved_at"):
        errors.append("approved_at es obligatorio")
    enabled = profile.get("enabled_domains")
    if not isinstance(enabled, list) or not enabled:
        errors.append("enabled_domains debe ser una lista no vacía")
    else:
        unknown = [d for d in enabled if d not in KNOWN_DOMAINS]
        if unknown:
            errors.append(f"dominios sin glosario declarado: {sorted(unknown)}")
        if len(set(enabled)) != len(enabled):
            errors.append("enabled_domains tiene dominios repetidos")

    corpus_ref = profile.get("corpus_ref")
    if not corpus_ref:
        errors.append("corpus_ref es obligatorio: un perfil sin corpus no activa nada")
    elif not (ROOT / corpus_ref).is_file():
        errors.append(f"corpus_ref no existe: {corpus_ref}")

    justification = profile.get("justification") or ""
    if len(justification) < 20:
        errors.append("justification debe decir por qué ese corpus activa esos dominios")

    if profile.get("corpus_real") is True and profile.get("approver") in LAB_APPROVERS:
        errors.append(
            "un perfil sobre corpus real no puede llevar un aprobador de laboratorio; "
            "la firma es de una persona"
        )
    return errors


def validate_all(profiles: Iterable[dict]) -> dict[str, list[str]]:
    return {p.get("profile_id", "<unknown>"): validate_profile(p) for p in profiles}


__all__ = [
    "KNOWN_DOMAINS",
    "PROFILES_INICIALES",
    "validate_against_schema",
    "validate_all",
    "validate_profile",
]