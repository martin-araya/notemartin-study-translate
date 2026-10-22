"""Pruebas del esquema de decisiones humanas (fase 123).

Comprueba que ``schemas/manifest.schema.json`` rechaza decisiones
inválidas y acepta decisiones válidas con la forma esperada.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schemas" / "manifest.schema.json"


def _load() -> dict:
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def _base_manifest() -> dict:
    schema = _load()
    required = schema["required"]
    sample: dict = {}
    for k in required:
        if k == "run_id":
            sample[k] = "run-aaaaaaaa"
        elif k == "created_at":
            sample[k] = "2026-10-20T00:00:00Z"
        elif k == "manifest_version":
            sample[k] = "translate/v1"
        elif k == "skill_version":
            sample[k] = "0.6.0"
        elif k == "parser":
            sample[k] = {"name": "python-markdown-it", "version": "3.5.0"}
        elif k == "anchor_policy":
            sample[k] = {"algorithm": "github", "version": "v1"}
        elif k == "model_metadata":
            sample[k] = {"provider": "unknown", "model": "unknown", "prompt_version": "v0"}
        elif k == "glossary_snapshot":
            sample[k] = {"version": 1, "hash": "a" * 64, "frozen": True}
        elif k == "profile_snapshot":
            sample[k] = {"hash": "b" * 64}
        elif k == "inputs":
            sample[k] = {
                "source_root": "/tmp",
                "total_files": 1,
                "total_bytes": 1,
                "hashes_indexed": True,
            }
        elif k == "files":
            sample[k] = [
                {
                    "path": "a.md",
                    "source_hash": "c" * 64,
                    "current_state": "inventoried",
                    "state_history": [{"state": "inventoried", "timestamp": "2026-10-20T00:00:00Z", "reason": "x"}],
                    "last_transition_at": "2026-10-20T00:00:00Z",
                }
            ]
    return sample


def _decision(**overrides) -> dict:
    base = {
        "author": "tester",
        "role": "reviewer",
        "pair": "en -> es",
        "scope": "global",
        "reason": "Aprobado tras revisar el informe bilingüe de muestra.",
        "reviewed_hashes": ["d" * 64],
        "decided_at": "2026-10-20T00:00:00Z",
        "kind": "approve",
    }
    base.update(overrides)
    return base


def test_acepta_decision_valida() -> None:
    schema = _load()
    manifest = _base_manifest()
    manifest["decisions"] = [_decision()]
    jsonschema.validate(manifest, schema)


def test_rechaza_decision_sin_reviewed_hashes() -> None:
    schema = _load()
    manifest = _base_manifest()
    manifest["decisions"] = [_decision(reviewed_hashes=[])]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(manifest, schema)


def test_rechaza_decision_sin_motivo() -> None:
    schema = _load()
    manifest = _base_manifest()
    manifest["decisions"] = [_decision(reason="")]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(manifest, schema)


def test_rechaza_author_vacio() -> None:
    schema = _load()
    manifest = _base_manifest()
    manifest["decisions"] = [_decision(author="")]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(manifest, schema)


def test_rechaza_kind_invalido() -> None:
    schema = _load()
    manifest = _base_manifest()
    manifest["decisions"] = [_decision(kind="maybe")]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(manifest, schema)


def test_defer_exige_referencias_opcional() -> None:
    schema = _load()
    manifest = _base_manifest()
    manifest["decisions"] = [
        _decision(kind="defer", references=["issue-0001"])
    ]
    jsonschema.validate(manifest, schema)


def test_decision_local_scope_a_rutas() -> None:
    schema = _load()
    manifest = _base_manifest()
    manifest["decisions"] = [_decision(scope=["a.md", "b.md"])]
    jsonschema.validate(manifest, schema)


def test_decisiones_opcional_pero_es_quando_se_presenta() -> None:
    schema = _load()
    manifest = _base_manifest()
    # Sin decisions el manifiesto sigue siendo válido.
    jsonschema.validate(manifest, schema)
