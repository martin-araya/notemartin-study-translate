"""Pruebas de detección de deriva terminológica (fase 098)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "glossaries"

sys.path.insert(0, str(SCRIPTS))

import term_drift


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_drift_detecta_added_removed_changed() -> None:
    old = _load("drift_old.json")
    new = _load("drift_new.json")
    drift = term_drift.compute_drift(old, new)
    assert drift["summary"]["added"] == 1
    assert drift["summary"]["changed"] == 1
    assert drift["summary"]["removed"] == 0


def test_drift_no_fuerza_reemplazos_globales() -> None:
    """El reporte enumera, no modifica glosarios."""
    old = _load("drift_old.json")
    new = _load("drift_new.json")
    drift = term_drift.compute_drift(old, new)
    assert isinstance(drift, dict)
    assert "added" in drift and "removed" in drift and "changed" in drift
    assert old == _load("drift_old.json")
    assert new == _load("drift_new.json")


def test_drift_no_modifica_glosarios() -> None:
    old = _load("drift_old.json")
    new = _load("drift_new.json")
    old_copy = json.dumps(old)
    new_copy = json.dumps(new)
    term_drift.compute_drift(old, new)
    assert json.dumps(old) == old_copy
    assert json.dumps(new) == new_copy


def test_drift_detecta_cambio_de_preferred_term() -> None:
    old = _load("drift_old.json")
    new = _load("drift_new.json")
    drift = term_drift.compute_drift(old, new)
    changes = drift["changed"]
    preferred_change = next((c for c in changes if c["field"] == "preferred.term"), None)
    assert preferred_change is not None
    assert preferred_change["id"] == "g-d001"
    assert preferred_change["old"] == "esquema"
    assert preferred_change["new"] == "esquema_v2"


def test_drift_marca_segmentos_afectados_con_domain_y_source_term() -> None:
    old = _load("drift_old.json")
    new = _load("drift_new.json")
    drift = term_drift.compute_drift(old, new)
    affected = drift["affected_segments"]
    assert any(a["source_term"] == "schema" and a["domain"] == "database" for a in affected)
    assert all("id" in a for a in affected)


def test_drift_sin_cambios_devuelve_resumen_vacio() -> None:
    old = _load("drift_old.json")
    drift = term_drift.compute_drift(old, old)
    assert drift["summary"] == {"added": 0, "removed": 0, "changed": 0, "affected_segments": 0}