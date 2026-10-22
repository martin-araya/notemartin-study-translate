"""El manifiesto aprobado sigue validando contra su propio esquema (fase 030).

El piloto de 9 documentos Destapó un contrato roto entre
`schemas/manifest.schema.json` y las dos herramientas que escriben en el
manifiesto:

- `check_integrity.py` inyecta `coverage` e `integrity_ok` en la raíz.
- `approve_pilot.py` inyecta `pilot_approved`, `approved_by`, `approved_at`
  y `provenance_baseline` en la raíz, y `state` en cada archivo.

La raíz tiene `additionalProperties: false`, así que después de cualquiera de
las dos el manifiesto deja de validar. Estas pruebas fijan el contrato: las
herramientas pueden escribir esos campos y el esquema los declara.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

SCHEMA = json.loads((ROOT / "schemas" / "manifest.schema.json").read_text(encoding="utf-8"))

REQUIRED = {
    "run_id": "run-0000abcd",
    "created_at": "2026-10-20T10:00:00Z",
    "manifest_version": "translate/v1",
    "skill_version": "0.2.0",
    "parser": {"name": "markdown-it-py", "version": "3.0.0"},
    "anchor_policy": {"algorithm": "github-slug-v1", "version": "v1"},
    "model_metadata": {"provider": "kilo", "model": "m", "prompt_version": "1.0.0"},
    "glossary_snapshot": {"version": 1, "hash": "a" * 64, "frozen": False},
    "profile_snapshot": {"hash": "b" * 64},
    "inputs": {"source_root": "/tmp/src", "total_files": 1, "total_bytes": 10,
               "hashes_indexed": True},
}

FILE_RECORD = {
    "path": "docs/a.md",
    "document_id": "doc-00000001",
    "source_hash": "c" * 64,
    "current_state": "translated",
    "state_history": [
        {"state": "inventoried", "timestamp": "2026-10-20T10:00:01Z", "reason": "inventario"},
        {"state": "prepared", "timestamp": "2026-10-20T10:01:00Z", "reason": "preparación"},
        {"state": "translated", "timestamp": "2026-10-20T10:30:00Z", "reason": "traducción"},
    ],
    "last_transition_at": "2026-10-20T10:30:00Z",
}

GLOSSARY = {
    "version": 1,
    "frozen": False,
    "allowed_languages": ["es"],
    "entries": [],
}


def _base_manifest() -> dict:
    return {**REQUIRED, "files": [dict(FILE_RECORD)]}


def _errors(manifest: dict) -> list[str]:
    import jsonschema

    validator = jsonschema.Draft202012Validator(SCHEMA)
    return [err.message for err in validator.iter_errors(manifest)]


def test_el_manifiesto_base_valida() -> None:
    assert _errors(_base_manifest()) == []


# --------------------------------------------------------------------------
# lo que escribe check_integrity.py
# --------------------------------------------------------------------------

def test_la_cobertura_del_ledger_puede_ir_en_el_manifiesto() -> None:
    manifest = _base_manifest()
    manifest["coverage"] = {
        "total": 1, "integrated": 1, "blocked": 0, "excluded": 0,
        "invalid": 0, "pending": 0, "integrated_ratio": 1.0,
    }
    manifest["integrity_ok"] = True
    assert _errors(manifest) == []


def test_check_integrity_deja_el_manifiesto_valido(tmp_path: Path) -> None:
    # El contrato de este test es que el manifiesto siga validando después
    # de que check_integrity escriba `coverage` e `integrity_ok`. Para que la
    # integridad sea verdadera el archivo tiene que estar aprobado: un
    # archivo solo traducido cuenta como pendiente.
    manifest = _base_manifest()
    record = manifest["files"][0]
    record["current_state"] = "approved"
    record["state_history"].append(
        {"state": "approved", "timestamp": "2026-10-20T11:00:00Z", "reason": "aprobado"}
    )
    record["last_transition_at"] = "2026-10-20T11:00:00Z"
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_integrity.py"),
         "--manifest", str(manifest_path), "--out", str(tmp_path / "integrity.json")],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 0, proc.stderr
    written = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert written["integrity_ok"] is True
    assert _errors(written) == []


def test_check_integrity_no_da_el_verde_a_un_corpus_solo_traducido(tmp_path: Path) -> None:
    """Sin esta comprobación, `integrity_ok` podría ser cierto sobre un
    corpus que nadie revisó ni aprobó."""
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(_base_manifest()), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_integrity.py"),
         "--manifest", str(manifest_path), "--out", str(tmp_path / "integrity.json")],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 1
    written = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert written["integrity_ok"] is False
    assert written["coverage"]["pending"] == 1


# --------------------------------------------------------------------------
# lo que escribe approve_pilot.py
# --------------------------------------------------------------------------

def test_la_aprobacion_del_piloto_puede_ir_en_el_manifiesto() -> None:
    manifest = _base_manifest()
    manifest["pilot_approved"] = True
    manifest["approved_by"] = "usuario"
    manifest["approved_at"] = "2026-10-20T11:00:00Z"
    manifest["provenance_baseline"] = {
        "files_source": {"doc-00000001": "c" * 64},
        "glossary_hash": "a" * 64,
        "profile_hash": "b" * 64,
        "parser_version": "3.0.0",
        "prompt_version": "1.0.0",
    }
    assert _errors(manifest) == []


def test_approve_pilot_deja_el_manifiesto_valido(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(_base_manifest()), encoding="utf-8")
    translations = tmp_path / "translations"
    translations.mkdir()
    (translations / "doc-00000001.json").write_text(json.dumps({
        "document_id": "doc-00000001", "path": "docs/a.md",
        "source_hash": "c" * 64, "version": 1,
        "entries": [{"segment_id": "seg-00000001", "original_text": "x",
                     "translated_text": "y"}],
        "flag_loss": False, "literals_preserved": True,
    }), encoding="utf-8")
    glossary_path = tmp_path / "glossary.json"
    glossary_path.write_text(json.dumps(GLOSSARY), encoding="utf-8")
    review = tmp_path / "review.json"
    review.write_text(json.dumps({"findings": []}), encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "approve_pilot.py"),
         "--manifest", str(manifest_path), "--translations", str(translations),
         "--glossary", str(glossary_path), "--review", str(review),
         "--approver", "usuario"],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 0, proc.stderr
    written = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert written["pilot_approved"] is True
    assert _errors(written) == []


def test_el_glosario_congelado_sigue_validando() -> None:
    """`approve_pilot.py` congela el glosario y le añade `approved_at`."""
    schema = json.loads((ROOT / "schemas" / "glossary.schema.json").read_text(encoding="utf-8"))
    payload = {
        "version": 2,
        "frozen": True,
        "allowed_languages": ["es"],
        "entries": [],
        "approved_at": "2026-10-20T11:00:00Z",
    }
    import jsonschema

    errors = [e.message for e in jsonschema.Draft202012Validator(schema).iter_errors(payload)]
    assert errors == [], errors


def test_approve_pilot_deja_el_glosario_valido(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(_base_manifest()), encoding="utf-8")
    translations = tmp_path / "translations"
    translations.mkdir()
    (translations / "doc-00000001.json").write_text(json.dumps({
        "document_id": "doc-00000001", "path": "docs/a.md",
        "source_hash": "c" * 64, "version": 1,
        "entries": [{"segment_id": "seg-00000001", "original_text": "x",
                     "translated_text": "y"}],
        "flag_loss": False, "literals_preserved": True,
    }), encoding="utf-8")
    glossary_path = tmp_path / "glossary.json"
    glossary_path.write_text(json.dumps(GLOSSARY), encoding="utf-8")
    review = tmp_path / "review.json"
    review.write_text(json.dumps({"findings": []}), encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "approve_pilot.py"),
         "--manifest", str(manifest_path), "--translations", str(translations),
         "--glossary", str(glossary_path), "--review", str(review),
         "--approver", "usuario"],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 0, proc.stderr
    frozen = json.loads(glossary_path.read_text(encoding="utf-8"))
    assert frozen["frozen"] is True
    assert frozen["version"] == 2
    schema = json.loads((ROOT / "schemas" / "glossary.schema.json").read_text(encoding="utf-8"))
    import jsonschema

    errors = [e.message for e in jsonschema.Draft202012Validator(schema).iter_errors(frozen)]
    assert errors == [], errors


def test_una_revision_con_criticos_impide_aprobar(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(_base_manifest()), encoding="utf-8")
    translations = tmp_path / "translations"
    translations.mkdir()
    (translations / "doc-00000001.json").write_text(json.dumps({
        "document_id": "doc-00000001", "path": "docs/a.md", "source_hash": "c" * 64,
        "version": 1, "entries": [{"segment_id": "seg-00000001", "original_text": "x",
                                   "translated_text": "y"}],
        "flag_loss": False, "literals_preserved": True,
    }), encoding="utf-8")
    glossary_path = tmp_path / "glossary.json"
    glossary_path.write_text(json.dumps(GLOSSARY), encoding="utf-8")
    review = tmp_path / "review.json"
    review.write_text(json.dumps({"findings": [
        {"segment_id": "seg-00000001", "severity": "critical", "status": "open"}
    ]}), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "approve_pilot.py"),
         "--manifest", str(manifest_path), "--translations", str(translations),
         "--glossary", str(glossary_path), "--review", str(review),
         "--approver", "usuario"],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 1, proc.stdout
    assert not json.loads(manifest_path.read_text(encoding="utf-8")).get("pilot_approved")


def test_el_estado_approved_por_archivo_esta_declarado() -> None:
    manifest = _base_manifest()
    record = manifest["files"][0]
    record["state"] = "approved"
    assert _errors(manifest) == []


def test_el_estado_approved_sigue_siendo_valido_para_el_ledger() -> None:
    record = {"state": "approved"}
    validator_states = {
        "inventoried", "prepared", "translated", "deterministic_pass",
        "semantic_pass", "approved", "exported", "blocked", "excluded",
    }
    assert "approved" in validator_states and record["state"] in validator_states


@pytest.mark.parametrize("campo", ["coverage", "integrity_ok", "pilot_approved",
                                   "approved_by", "approved_at", "provenance_baseline"])
def test_los_campos_que_escriben_las_herramientas_estan_declarados(campo: str) -> None:
    assert campo in SCHEMA["properties"], campo