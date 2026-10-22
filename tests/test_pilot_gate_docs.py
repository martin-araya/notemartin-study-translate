"""El gate G-PILOT no puede volver a quedar en verde por inercia (fase 030).

Cada casilla de `### G-PILOT` del roadmap debe tener su artefacto de
evidencia. Si alguien borra un reporte, cambia el manifiesto aprobado o
revierte el estado del caso piloto, estas pruebas fallan.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ROADMAP = ROOT / "roadmap.md"
PILOT_CASE = ROOT / "evals" / "cases" / "pilot.md"
SUMMARY = ROOT / "reports" / "pilot" / "summary.md"
EVIDENCE = (
    "manifest.json",
    "glossary.json",
    "validate.json",
    "review.json",
    "profile.json",
    "classified.json",
    "inventory.json",
    "copy_resources.json",
)


def _gate_section() -> str:
    text = ROADMAP.read_text(encoding="utf-8")
    start = text.index("### G-PILOT, fase 030")
    end = text.index("### ", start + 10)
    return text[start:end]


def test_el_roadmap_tiene_la_seccion_de_g_pilot() -> None:
    assert "### G-PILOT, fase 030" in ROADMAP.read_text(encoding="utf-8")


def test_las_cuatro_casillas_de_g_pilot_estan_marcadas() -> None:
    section = _gate_section()
    boxes = [line for line in section.splitlines() if line.startswith("- [")]
    assert len(boxes) == 4, boxes
    pendientes = [line for line in boxes if line.startswith("- [ ]")]
    assert pendientes == [], pendientes


def test_cada_casilla_cita_su_evidencia() -> None:
    for line in _gate_section().splitlines():
        if line.startswith("- [x]"):
            assert "→" in line and "reports/pilot/" in line, line


def test_existen_todos_los_artefactos_de_evidencia() -> None:
    for name in EVIDENCE:
        path = ROOT / "reports" / "pilot" / name
        assert path.is_file(), f"falta {path.relative_to(ROOT)}"


def test_el_manifiesto_aprobado_esta_aprobado_y_vigente() -> None:
    manifest = json.loads((ROOT / "reports" / "pilot" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["manifest_version"] == "translate/v1"
    assert manifest["pilot_approved"] is True
    assert manifest["approved_by"]
    assert manifest["approved_at"]
    assert manifest["provenance_baseline"]["files_source"]
    assert len(manifest["files"]) == 9
    # `approve_pilot.py` escribía solo `state` y dejaba `current_state` en
    # `translated`: la aprobación quedaba invisible para todo gate que lee
    # `current_state`. El manifiesto del piloto se reparó con
    # `scripts/repair_state_field.py`; esta aserción fija el estado real.
    assert {f["current_state"] for f in manifest["files"]} == {"approved"}
    assert {f["state"] for f in manifest["files"]} == {"approved"}
    assert manifest["integrity_ok"] is True


def test_el_manifiesto_aprobar_cubre_los_nueve_documentos() -> None:
    manifest = json.loads((ROOT / "reports" / "pilot" / "manifest.json").read_text(encoding="utf-8"))
    baseline = manifest["provenance_baseline"]["files_source"]
    assert set(baseline) == {f["document_id"] for f in manifest["files"]}
    for record in manifest["files"]:
        assert baseline[record["document_id"]] == record["source_hash"]


def test_el_glosario_esta_congelado() -> None:
    glossary = json.loads((ROOT / "reports" / "pilot" / "glossary.json").read_text(encoding="utf-8"))
    assert glossary["frozen"] is True
    assert glossary["version"] >= 2
    assert glossary["approved_at"]
    assert len(glossary["entries"]) >= 14


def test_la_validacion_no_tiene_errores() -> None:
    report = json.loads((ROOT / "reports" / "pilot" / "validate.json").read_text(encoding="utf-8"))
    assert report["ok"] is True
    assert report["errors"] == []
    for check in ("structure", "protection", "destinations"):
        assert report["results"][check]["errors"] == [], check
    coverage = report["results"]["coverage"]["info"][0]
    assert coverage["integrity_ok"] is True
    assert coverage["coverage"]["integrated"] == 9
    assert coverage["coverage"]["blocked"] == 0


def test_la_revision_cubre_los_segmentos_del_piloto() -> None:
    review = json.loads((ROOT / "reports" / "pilot" / "review.json").read_text(encoding="utf-8"))
    assert review["segments_reviewed"] == 636
    assert sum(review["verdicts"].values()) == 636
    assert review["findings"], "una revisión sin hallazgos sobre 636 segmentos no es una revisión"
    for finding in review["findings"]:
        assert finding.get("status") == "resolved", finding["segment_id"]


def test_el_caso_piloto_declara_esta_aprobado() -> None:
    text = PILOT_CASE.read_text(encoding="utf-8")
    assert "Estado: **aprobado**" in text
    assert "pendiente de aprobación" not in text


def test_el_caso_piloto_documenta_las_limitaciones_abiertas() -> None:
    text = PILOT_CASE.read_text(encoding="utf-8")
    assert "Limitaciones que siguen abiertas" in text
    assert "cumplido parcial" in text
    assert "153" in text


def test_el_resumen_no_declara_lo_que_no_se_comprobo() -> None:
    text = SUMMARY.read_text(encoding="utf-8")
    assert "Qué este informe NO afirma" in text
    for frase in ("no una certificación humana", "No afirma"):
        assert frase in text


def test_la_cabecera_del_roadmap_no_dice_que_nada_esta_implementado() -> None:
    text = ROADMAP.read_text(encoding="utf-8")
    assert "implementación pendiente" not in text.split("## 1.")[0]
    assert "Ninguna fase está implementada" not in text.split("## 1.")[0]


def test_el_roadmap_aclara_que_significa_un_glifo_de_fase() -> None:
    text = ROADMAP.read_text(encoding="utf-8")
    assert "Un ✅ en la tabla de fases significa" in text
    assert "### G1. Estado de G-PILOT, fase 030" in text