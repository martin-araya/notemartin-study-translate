"""Pruebas de consistencia documental del lote de entrega (fases 131-140).

Comprueba que el cierre documental del lote existe y es coherente:

- Las cuatro referencias nuevas están en el árbol y en la tabla §6 de
  `SKILL.md`.
- Todo `scripts/*.py` mencionado en ellas existe.
- `CHANGELOG.md` trae la entrada 0.1.5 y `RELEASE.md` la subsección 5.5
  con su bloque de lo que no afirma.
- `roadmap.md` marca las diez fases de la sección N y documenta el
  lote en N1 con el gate G-EXT-N.
- Ningún documento afirma verificación remota que no exista.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "SKILL.md"
CHANGELOG = ROOT / "CHANGELOG.md"
RELEASE = ROOT / "RELEASE.md"
ROADMAP = ROOT / "roadmap.md"
HANDOFF = ROOT / "references" / "notion-handoff.md"

NEW_REFERENCES = (
    "references/delivery-notion-checklist.md",
    "references/delivery-contract.md",
    "references/delivery-matrix.md",
    "references/delivery-gate.md",
)

NEW_SCRIPTS = (
    "scripts/record_import_evidence.py",
    "scripts/adapt_delivery.py",
    "scripts/export_zip.py",
    "scripts/validate_zip_package.py",
    "scripts/render_delivery_guide.py",
    "scripts/compare_delivery.py",
    "scripts/delivery_matrix.py",
    "scripts/gate_delivery.py",
    "scripts/delivery_common.py",
)

NEW_SCHEMAS = (
    "schemas/import_evidence.schema.json",
    "schemas/delivery_profile.schema.json",
    "schemas/delivery_package.schema.json",
)


def test_las_referencias_nuevas_existen() -> None:
    for rel in NEW_REFERENCES:
        assert (ROOT / rel).exists(), rel


def test_los_scripts_y_esquemas_nuevos_existen() -> None:
    for rel in NEW_SCRIPTS + NEW_SCHEMAS:
        assert (ROOT / rel).exists(), rel


def test_skill_lista_las_referencias_nuevas() -> None:
    text = SKILL.read_text(encoding="utf-8")
    for rel in NEW_REFERENCES:
        assert f"`{rel}`" in text, f"SKILL.md §6 no lista {rel}"


def test_los_scripts_mencionados_en_las_referencias_existen() -> None:
    pattern = re.compile(r"`scripts/([a-zA-Z0-9_.\-]+\.py)`")
    for rel in NEW_REFERENCES:
        text = (ROOT / rel).read_text(encoding="utf-8")
        for name in pattern.findall(text):
            assert (ROOT / "scripts" / name).exists(), f"{rel} cita un script inexistente: {name}"


def test_changelog_trae_la_subrelease() -> None:
    text = CHANGELOG.read_text(encoding="utf-8")
    assert "0.1.5" in text
    for phase in ("131", "134", "135", "136", "137", "138", "139", "140"):
        assert phase in text, phase
    assert "723 tests" in text


def test_release_documenta_lo_que_no_afirma() -> None:
    text = RELEASE.read_text(encoding="utf-8")
    assert "5.5" in text or "### 5.5" in text
    assert "Lo que esta subrelease **no** afirma" in text
    assert "no verificada" in text.lower() or "no_verificado" in text
    assert "real_app_evidence: false" in text


def test_roadmap_marca_las_diez_fases_de_la_seccion_n() -> None:
    text = ROADMAP.read_text(encoding="utf-8")
    for phase in range(131, 141):
        pattern = rf"\| {phase} (✅|✅ ⚠)"
        assert re.search(pattern, text), f"la fase {phase} no tiene glifo en la sección N"


def test_roadmap_documenta_la_ejecucion_n1_y_su_gate() -> None:
    text = ROADMAP.read_text(encoding="utf-8")
    assert "### N1. Implementación 131–140" in text
    assert "G-EXT-N" in text
    assert "no_verificado" in text


def test_ningun_documento_afirma_importacion_verificada() -> None:
    handoff = HANDOFF.read_text(encoding="utf-8")
    assert "no verificado" in handoff
    assert "Estado actual de la verificación remota" in handoff

    forbidden = ("importación verificada en Notion", "soportado en Notion")
    for rel in NEW_REFERENCES + ("RELEASE.md", "CHANGELOG.md", "roadmap.md"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        for phrase in forbidden:
            assert phrase not in text, f"{rel} afirma {phrase!r}"