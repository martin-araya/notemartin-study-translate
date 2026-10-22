"""Casos positivos y negativos del corpus permanente de regresión (fase 141).

Cada entrada de ``evals/regression/registry.json`` tiene un caso positivo
(que **no** debe generar hallazgo) y un caso negativo (que **sí** debe
generarlo). Este módulo ejecuta el detector declarado para cada entrada y
comprueba la expectativa.

Los detectores viven en ``scripts/regression_detectors.py`` y son funciones
puras sobre los fixtures de ``tests/fixtures/regression/``. Ninguna prueba
de este archivo lee la fuente autorizada ni escribe en un ``work_root``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from regression_detectors import detect  # noqa: E402

REGISTRY = ROOT / "evals" / "regression" / "registry.json"


def _entries() -> dict[str, dict]:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    return {entry["known_failure"]: entry for entry in payload["cases"]}


ENTRIES = _entries()

PARAMS = [
    (known_failure, variant)
    for known_failure in sorted(ENTRIES)
    for variant in ("positive", "negative")
]


def _run(known_failure: str, variant: str) -> tuple[dict, dict]:
    entry = ENTRIES[known_failure]
    spec = entry[variant]
    fixture_path = ROOT / spec["fixture"]
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    result = detect(known_failure, fixture.get("case") or {}, fixture[spec["variant_key"]])
    return result, spec


@pytest.mark.parametrize("known_failure,variant", PARAMS)
def test_caso_regresion(known_failure: str, variant: str) -> None:
    result, spec = _run(known_failure, variant)
    expected = spec["expectation"] == "finding"
    assert result["detected"] is expected, (
        f"{known_failure}/{variant}: esperado detected={expected}, "
        f"obtenido {result['detected']} con hallazgos {result['findings']}"
    )
    if expected:
        assert result["findings"], "un hallazgo sin detalle no es un hallazgo auditable"


@pytest.mark.parametrize("known_failure", sorted(ENTRIES))
def test_todo_fallo_conocido_tiene_par_completo(known_failure: str) -> None:
    entry = ENTRIES[known_failure]
    assert entry["positive"]["expectation"] == "no_finding"
    assert entry["negative"]["expectation"] == "finding"
    assert entry["positive"]["fixture"] == entry["negative"]["fixture"]
    assert entry["tests"]["positive"].endswith("-positive]")
    assert entry["tests"]["negative"].endswith("-negative]")


def test_el_registro_cubre_todos_los_fallos_conocidos() -> None:
    payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert sorted(payload["known_failures"]) == sorted(ENTRIES)


def test_todos_los_fixtures_de_regresion_son_sinteticos() -> None:
    """Decisión D2: sin prosa real nueva en el registro permanente."""
    for entry in ENTRIES.values():
        assert entry["provenance"]["kind"] == "synthetic", entry["case_id"]
        assert entry["provenance"]["anonymized"] is True