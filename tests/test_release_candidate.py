"""Pruebas del candidato de release ampliado y de su gate (fase 149).

El candidato se construye sobre un árbol temporal mínimo para que las
pruebas no dependan del estado real del repositorio, y sobre el repositorio
real para comprobar la coherencia del inventario de módulos.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from build_release_candidate import (  # noqa: E402
    MODULE_INVENTORY,
    NOT_REQUIRED,
    OPEN_EXTERNAL,
    build,
    schema_violations,
)
from gate_extended import exit_code_for, gate  # noqa: E402

CANDIDATE_PATH = ROOT / "reports" / "maintenance" / "release_candidate.json"


def _candidate() -> dict:
    return json.loads(CANDIDATE_PATH.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# inventario
# --------------------------------------------------------------------------

def test_el_inventario_cubre_los_nueve_modulos_mas_mantenimiento() -> None:
    ids = {entry["module_id"] for entry in MODULE_INVENTORY}
    assert ids == {
        "core", "mdx", "html", "markdown-extensions", "terminology",
        "language", "scale", "review", "delivery", "maintenance",
    }


def test_todo_modulo_activo_declara_su_gate() -> None:
    for entry in MODULE_INVENTORY:
        assert entry["gate"]["kind"] in ("command", "pytest", "report")
        assert entry["gate"]["target"]


def test_las_pruebas_excluidas_de_un_gate_declaran_motivo() -> None:
    """Excluir una prueba del gate es legítimo; excluirla en silencio, no.

    La única exclusión admitida es la que impide la autorreferencia: las
    pruebas que leen el candidato que el propio script está construyendo.
    """
    for entry in MODULE_INVENTORY:
        excluded = entry["gate"].get("excluded_tests", [])
        for item in excluded:
            assert len(item["reason"]) >= 20, item
            assert "candidato" in item["reason"], item
        if excluded:
            command = entry["gate"]["command"]
            for item in excluded:
                assert Path(item["path"]).name not in command, item["path"]


def test_las_fases_de_cada_modulo_cubren_su_rango() -> None:
    for entry in MODULE_INVENTORY:
        phases = entry["phases"]
        assert phases == list(range(phases[0], phases[-1] + 1)), entry["module_id"]


def test_los_huecos_externos_declaran_responsable_y_procedimiento() -> None:
    assert OPEN_EXTERNAL
    for item in OPEN_EXTERNAL:
        assert item["owner"] and item["procedure"] and item["reason"]
        assert item["blocking_scope"] in ("remote_verification_claim", "human_signature")


def test_las_opciones_desactivadas_explican_por_que_no_son_requisito() -> None:
    options = {item["option"] for item in NOT_REQUIRED}
    assert {"delivery.enabled", "html.enabled", "mixed_profile.enabled", "rtl.enabled"} <= options
    for item in NOT_REQUIRED:
        assert len(item["reason"]) > 20, item


# --------------------------------------------------------------------------
# candidato real
# --------------------------------------------------------------------------

def test_el_candidato_real_valida_contra_el_esquema() -> None:
    assert schema_violations(_candidate()) == []


def test_el_candidato_real_tiene_todos_los_modulos_en_verde() -> None:
    failed = [m["module_id"] for m in _candidate()["modules"] if not m["ok"]]
    assert failed == [], failed


def test_el_candidato_real_declara_lo_que_no_afirma() -> None:
    claims = " ".join(_candidate()["claims_not_made"]).lower()
    assert "notion" in claims
    assert "semántica" in claims


# --------------------------------------------------------------------------
# gate
# --------------------------------------------------------------------------

def _minimal_root(tmp_path: Path) -> Path:
    (tmp_path / "reports" / "maintenance").mkdir(parents=True)
    (tmp_path / "reports" / "maintenance" / "regression.json").write_text(json.dumps({
        "ok": True, "failures": {}, "gaps": [], "reproduce": {"exit_code": 0},
    }), encoding="utf-8")
    (tmp_path / "reports" / "maintenance" / "versioning.json").write_text(json.dumps({
        "ok": True, "failures": {},
    }), encoding="utf-8")
    (tmp_path / "reports" / "maintenance" / "docs_audit.json").write_text(json.dumps({
        "ok": True, "failures": {},
    }), encoding="utf-8")
    (tmp_path / "reports" / "maintenance" / "parser_comparison.json").write_text(json.dumps({
        "promotion": "allowed", "dependents_to_migrate": [],
    }), encoding="utf-8")
    (tmp_path / "reports" / "maintenance" / "portability_matrix.json").write_text(json.dumps({
        "rows": [{"system_id": "linux-cpython", "status": "verified",
                  "evidence": {"platform": "linux"}, "executed_at": "2026-10-20T00:00:00Z"}],
    }), encoding="utf-8")
    (tmp_path / "references").mkdir(exist_ok=True)
    (tmp_path / "references" / "workdir-retention.md").write_text("política\n", encoding="utf-8")
    return tmp_path


def _clean_candidate() -> dict:
    return {
        "candidate_version": "0.2.0",
        "modules": [{"module_id": "core", "exit_code": 0, "ok": True}],
        "open_external_items": [],
        "claims_not_made": ["no se afirma nada remoto"],
    }


def test_un_candidato_limpio_pasa_el_gate(tmp_path: Path) -> None:
    report = gate(_clean_candidate(), _minimal_root(tmp_path), core_exit_code=0)
    assert report["failures"] == {}, report["failures"]
    assert exit_code_for(report) == 0
    assert report["external_items_do_not_block_local_release"] is True


def test_un_hueco_externo_no_hace_fallar_el_gate(tmp_path: Path) -> None:
    candidate = _clean_candidate()
    candidate["open_external_items"] = OPEN_EXTERNAL
    report = gate(candidate, _minimal_root(tmp_path), core_exit_code=0)
    assert exit_code_for(report) == 0
    assert len(report["open_external_items"]) == len(OPEN_EXTERNAL)


def test_afirmar_notion_fuera_de_la_lista_de_huecos_falla(tmp_path: Path) -> None:
    candidate = _clean_candidate()
    candidate["claims_not_made"] = ["La entrega está soportado en Notion."]
    report = gate(candidate, _minimal_root(tmp_path), core_exit_code=0)
    assert report["failures"]["5"], report["failures"]
    assert exit_code_for(report) == 5


def test_verificar_una_firma_que_no_existe_falla(tmp_path: Path) -> None:
    candidate = _clean_candidate()
    candidate["claims_not_made"] = ["El documento está revisado por una persona."]
    report = gate(candidate, _minimal_root(tmp_path), core_exit_code=0)
    assert report["failures"]["5"], report["failures"]


def test_un_verified_sin_evidencia_falla(tmp_path: Path) -> None:
    root = _minimal_root(tmp_path)
    matrix = json.loads((root / "reports/maintenance/portability_matrix.json").read_text("utf-8"))
    matrix["rows"][0]["evidence"] = None
    (root / "reports/maintenance/portability_matrix.json").write_text(json.dumps(matrix), "utf-8")
    report = gate(_clean_candidate(), root, core_exit_code=0)
    assert report["failures"]["7"], report["failures"]
    assert exit_code_for(report) == 7


def test_una_auditoria_con_hallazgos_falla(tmp_path: Path) -> None:
    root = _minimal_root(tmp_path)
    (root / "reports/maintenance/docs_audit.json").write_text(json.dumps({
        "ok": False, "failures": {"1": ["ruta inexistente"]},
    }), encoding="utf-8")
    report = gate(_clean_candidate(), root, core_exit_code=0)
    assert report["failures"]["6"], report["failures"]
    assert exit_code_for(report) == 6


def test_un_registro_de_regresion_sin_reproducir_falla(tmp_path: Path) -> None:
    root = _minimal_root(tmp_path)
    (root / "reports/maintenance/regression.json").write_text(json.dumps({
        "ok": True, "failures": {}, "gaps": [],
    }), encoding="utf-8")
    report = gate(_clean_candidate(), root, core_exit_code=0)
    assert report["failures"]["1"], report["failures"]
    assert exit_code_for(report) == 1


def test_un_manifiesto_sin_version_falla(tmp_path: Path) -> None:
    root = _minimal_root(tmp_path)
    (root / "reports" / "manifiesto.json").write_text(json.dumps({
        "run_id": "run-0000aaaa", "files": [{"path": "a.md", "current_state": "translated"}],
    }), encoding="utf-8")
    report = gate(_clean_candidate(), root, core_exit_code=0)
    assert report["failures"]["3"], report["failures"]
    assert exit_code_for(report) == 3


def test_una_aprobacion_vigente_tras_migrar_falla(tmp_path: Path) -> None:
    root = _minimal_root(tmp_path)
    (root / "reports" / "manifiesto.json").write_text(json.dumps({
        "run_id": "run-0000aaaa",
        "manifest_version": "translate/v1",
        "files": [{"path": "a.md", "current_state": "translated"}],
        "approvals": [{"approval_id": "app-0000aaaa", "status": "valid"}],
        "migrations": [{"from": "translate/v0", "to": "translate/v1",
                        "applied_at": "2026-10-20T00:00:00Z", "tool_version": "1.0.0",
                        "source_sha256": "0" * 64, "reason": "manifest_migration"}],
    }), encoding="utf-8")
    report = gate(_clean_candidate(), root, core_exit_code=0)
    assert report["failures"]["3"], report["failures"]


def test_el_nucleo_en_rojo_falla(tmp_path: Path) -> None:
    report = gate(_clean_candidate(), _minimal_root(tmp_path), core_exit_code=9)
    assert report["failures"]["9"], report["failures"]
    assert exit_code_for(report) == 9


def test_una_purga_sin_autorizacion_falla(tmp_path: Path) -> None:
    root = _minimal_root(tmp_path)
    (root / "reports" / "maintenance" / "purge_log.json").write_text(json.dumps({
        "generated_at": "2026-10-20T00:00:00Z", "dry_run": False, "authorized_by": None,
    }), encoding="utf-8")
    report = gate(_clean_candidate(), root, core_exit_code=0)
    assert report["failures"]["8"], report["failures"]


def test_la_politica_de_retencion_ausente_falla(tmp_path: Path) -> None:
    root = _minimal_root(tmp_path)
    (root / "references" / "workdir-retention.md").unlink()
    report = gate(_clean_candidate(), root, core_exit_code=0)
    assert report["failures"]["8"], report["failures"]


def test_construir_el_candidato_sobre_el_repo_real_es_valido(tmp_path: Path) -> None:
    candidate = build(ROOT, "0.2.0", skip_gates=True)
    assert schema_violations(candidate) == []
    assert len(candidate["modules"]) == len(MODULE_INVENTORY)
    assert candidate["artifacts"], "el candidato debe llevar huellas de sus artefactos"