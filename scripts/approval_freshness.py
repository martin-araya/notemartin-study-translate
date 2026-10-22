"""Vigencia de las aprobaciones: regla pura (núcleo).

Una aprobación es una afirmación sobre un artefacto en un estado concreto.
Si el artefacto cambia después, la afirmación deja de ser vigente aunque el
`approved_at` siga siendo el mismo. Esa regla pertenece al núcleo porque la
usan dos caminos que no pueden depender de un módulo opcional:

- ``scripts/advance_state.py`` y ``scripts/approve_pilot.py`` al promover;
- ``scripts/regression_detectors.py`` (fase 141) como detector del corpus
  permanente de regresión, a través de la interfaz de la fase 124.

La interfaz ejecutable es ``scripts/check_approval_freshness.py``.

Estados posibles por aprobación:

- ``valid``: el artefacto y los hashes dependientes coinciden.
- ``stale``: el ``target_hash`` o cualquier hash dependiente difiere.
- ``superseded``: si ``superseded_by`` apunta a otra aprobación más
  reciente del mismo artefacto. Solo se emite cuando el manifiesto
  declara ese campo; no se infiere.

Nada aquí reescribe el manifiesto: calcula y devuelve el estado.
"""

from __future__ import annotations

HASH_FIELDS = ("target_hash", "target_glossary_hash", "target_anchor_hash", "target_profile_hash")

# Un hash vigente ausente no invalida por sí solo: invalidaría toda
# aprobación de una ejecución que todavía no ha calculado ese hash. El
# hash que se compara es el que el manifiesto declara como actual.
OPTIONAL_HASH_FIELDS = ("target_glossary_hash", "target_anchor_hash", "target_profile_hash")


def source_hashes_by_path(manifest: dict) -> dict[str, str]:
    return {
        f.get("path"): f.get("source_hash")
        for f in manifest.get("files") or []
        if f.get("path")
    }


def current_hashes(manifest: dict) -> dict[str, str | None]:
    """Hashes vigentes que el propio manifiesto declara."""
    return {
        "target_glossary_hash": (manifest.get("glossary_snapshot") or {}).get("hash"),
        "target_anchor_hash": manifest.get("current_anchor_hash"),
        "target_profile_hash": (manifest.get("profile_snapshot") or {}).get("hash"),
    }


def superseded_ids(manifest: dict) -> dict[str, str]:
    """Aprobación que cada aprobación declara reemplazada."""
    out: dict[str, str] = {}
    for ap in manifest.get("approvals") or []:
        ap_id = ap.get("approval_id")
        replaced = ap.get("superseded_by")
        if ap_id and replaced:
            out[ap_id] = replaced
    return out


def evaluate(manifest: dict, overrides: dict[str, str | None] | None = None) -> dict:
    """Estado de cada aprobación del manifiesto.

    ``overrides`` permite comparar contra hashes medidos fuera del
    manifiesto (``--current-glossary-hash`` y ``--current-anchor-hash``).
    Un override ausente **no** se rellena con el valor de otro campo: la
    versión anterior asignaba el hash de anclas al hash de perfil, que
    invalidaba aprobaciones sin motivo.
    """
    overrides = dict(overrides or {})
    by_path = source_hashes_by_path(manifest)
    declared = current_hashes(manifest)

    current_glossary = (
        overrides.get("target_glossary_hash")
        or manifest.get("current_glossary_hash")
        or declared["target_glossary_hash"]
    )
    current_profile = overrides.get("target_profile_hash") or declared["target_profile_hash"]
    current_anchors = overrides.get("target_anchor_hash") or declared["target_anchor_hash"]
    current = {
        "target_glossary_hash": current_glossary,
        "target_anchor_hash": current_anchors,
        "target_profile_hash": current_profile,
    }

    replaced = superseded_ids(manifest)
    evaluated: list[dict] = []
    stale_count = 0
    for ap in manifest.get("approvals") or []:
        ap_id = ap.get("approval_id") or ""
        artifact = ap.get("artifact") or ""
        reasons: list[str] = []
        target = ap.get("target_hash")
        current_file_hash = by_path.get(artifact)
        if target and current_file_hash and target != current_file_hash:
            reasons.append(
                f"target_hash differs: expected={str(target)[:12]}.. current={str(current_file_hash)[:12]}.."
            )
        for field in OPTIONAL_HASH_FIELDS:
            if field not in ap:
                continue
            live = current.get(field)
            if live and ap[field] != live:
                reasons.append(f"{field} differs")

        status = "stale" if reasons else "valid"
        if not reasons and ap_id in replaced:
            status = "superseded"
        if status == "stale":
            stale_count += 1
        evaluated.append(
            {
                "approval_id": ap_id,
                "decision_id": ap.get("decision_id") or "",
                "artifact": artifact,
                "status": status,
                "reasons": reasons,
                "approved_at": ap.get("approved_at"),
                "superseded_by": replaced.get(ap_id),
            }
        )

    return {
        "evaluated": len(evaluated),
        "stale": stale_count,
        "valid": sum(1 for a in evaluated if a["status"] == "valid"),
        "superseded": sum(1 for a in evaluated if a["status"] == "superseded"),
        "current_glossary_hash": current_glossary,
        "approvals": evaluated,
    }