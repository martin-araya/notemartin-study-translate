"""Pruebas de la migración de manifiestos (fase 143).

La aceptación de la fase es una sola, y es negativa: una migración **nunca**
convierte una revisión antigua en una aprobación vigente. Todo el resto de
pruebas fija las reglas concretas del procedimiento.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from migrate_manifest import (  # noqa: E402
    REVALIDATION,
    STALE_REASON,
    TARGET_VERSION,
    main,
    migrate,
    schema_violations,
)

FIXTURES = ROOT / "tests" / "fixtures" / "migrations"
V0_APPROVED = FIXTURES / "manifest_v0_approved.json"
V0_EXPORTED = FIXTURES / "manifest_v0_exported.json"
V1_CURRENT = FIXTURES / "manifest_v1_current.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _migrate(path: Path) -> tuple[dict, dict]:
    return migrate(_load(path), "0" * 64, now="2026-10-20T12:00:00Z")


# --------------------------------------------------------------------------
# la regla que bloquea la fase
# --------------------------------------------------------------------------

def test_la_migracion_no_fabrica_una_aprobacion_vigente() -> None:
    migrated, report = _migrate(V0_APPROVED)
    for approval in migrated["approvals"]:
        assert approval["stale"] is True
        assert approval["stale_reason"] == STALE_REASON
        assert approval["status"] != "valid"


def test_la_migracion_no_fabrica_una_decision_vigente() -> None:
    migrated, _ = _migrate(V0_APPROVED)
    for decision in migrated["decisions"]:
        assert decision["stale"] is True
        assert decision["stale_reason"] == STALE_REASON


def test_un_archivo_aprobado_baja_a_deterministic_pass() -> None:
    migrated, report = _migrate(V0_APPROVED)
    record = migrated["files"][0]
    assert record["current_state"] == "deterministic_pass"
    assert record["requires_revalidation"] == REVALIDATION
    assert record["path"] in report["downgraded_files"]


def test_un_archivo_exportado_tambien_baja() -> None:
    migrated, report = _migrate(V0_EXPORTED)
    assert migrated["files"][0]["current_state"] == "deterministic_pass"
    assert report["downgraded_files"] == ["docs/otra.md"]


def test_la_migracion_conserva_la_historia_y_la_amplia() -> None:
    original = _load(V0_APPROVED)
    migrated, report = _migrate(V0_APPROVED)
    history = migrated["files"][0]["state_history"]
    assert history[:len(original["files"][0]["state_history"])] == original["files"][0]["state_history"]
    assert history[-1]["reason"] == STALE_REASON
    assert report["preserved_history"] == len(original["files"][0]["state_history"])


def test_la_migracion_no_toca_created_at_ni_los_hashes() -> None:
    original = _load(V0_APPROVED)
    migrated, _ = _migrate(V0_APPROVED)
    assert migrated["created_at"] == original["created_at"]
    assert migrated["files"][0]["source_hash"] == original["files"][0]["source_hash"]
    assert migrated["skill_version"] == original["skill_version"]


# --------------------------------------------------------------------------
# procedimiento
# --------------------------------------------------------------------------

def test_el_manifiesto_migrado_declara_la_version_y_registra_la_migracion() -> None:
    migrated, _ = _migrate(V0_APPROVED)
    assert migrated["manifest_version"] == TARGET_VERSION
    entry = migrated["migrations"][-1]
    assert entry["from"] == "translate/v0"
    assert entry["to"] == TARGET_VERSION
    assert entry["source_sha256"] == "0" * 64
    assert entry["reason"] == STALE_REASON


def test_el_manifiesto_migrado_valida_contra_el_esquema() -> None:
    migrated, _ = _migrate(V0_APPROVED)
    assert schema_violations(migrated) == []


def test_la_migracion_es_idempotente() -> None:
    migrated_once, _ = _migrate(V0_APPROVED)
    migrated_twice, report = migrate(migrated_once, "1" * 64, now="2026-10-20T12:00:00Z")
    # las aprobaciones siguen obsoletas y el estado del archivo no sube
    assert migrated_twice["approvals"][0]["stale"] is True
    assert migrated_twice["files"][0]["current_state"] == "deterministic_pass"
    assert migrated_twice["files"][0]["requires_revalidation"] == REVALIDATION
    assert report["downgraded_files"] == []


def test_un_manifiesto_ya_vigente_no_se_reexporta() -> None:
    migrated, report = _migrate(V1_CURRENT)
    assert report["downgraded_files"] == []
    assert len(migrated["migrations"]) == 2


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def test_la_cli_rechaza_un_manifiesto_ilegible(tmp_path: Path) -> None:
    bogus = tmp_path / "manifest.json"
    bogus.write_text("{}", encoding="utf-8")
    assert main(["--in", str(bogus), "--out", str(tmp_path / "out.json")]) == 2


def test_la_cli_rechaza_un_hash_de_origen_distinto(tmp_path: Path) -> None:
    code = main([
        "--in", str(V0_APPROVED),
        "--out", str(tmp_path / "out.json"),
        "--expected-source-hash", "f" * 64,
    ])
    assert code == 4


def test_la_cli_rechaza_una_version_futura(tmp_path: Path) -> None:
    future = json.loads(V1_CURRENT.read_text(encoding="utf-8"))
    future["manifest_version"] = "translate/v9"
    path = tmp_path / "future.json"
    path.write_text(json.dumps(future), encoding="utf-8")
    assert main(["--in", str(path), "--out", str(tmp_path / "out.json")]) == 5


def test_la_cli_avisa_si_ya_esta_migrado(tmp_path: Path) -> None:
    assert main(["--in", str(V1_CURRENT), "--out", str(tmp_path / "out.json")]) == 6


def test_la_cli_en_sequillo_no_escribe(tmp_path: Path) -> None:
    out = tmp_path / "out.json"
    assert main(["--in", str(V0_APPROVED), "--out", str(out), "--dry-run"]) == 0
    assert not out.exists()


def test_la_cli_escribe_con_autorizacion(tmp_path: Path) -> None:
    out = tmp_path / "out.json"
    code = main([
        "--in", str(V0_APPROVED),
        "--out", str(out),
        "--apply",
        "--authorized-by", "tester",
    ])
    assert code == 0
    written = json.loads(out.read_text(encoding="utf-8"))
    assert written["manifest_version"] == TARGET_VERSION
    assert written["files"][0]["current_state"] == "deterministic_pass"


def test_la_cli_exige_autorizacion_para_escribir(tmp_path: Path) -> None:
    out = tmp_path / "out.json"
    code = main(["--in", str(V0_APPROVED), "--out", str(out), "--apply"])
    assert code == 3
    assert not out.exists()