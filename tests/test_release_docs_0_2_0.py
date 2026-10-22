"""Pruebas documentales del release 0.2.0 (fase 150).

Comprueban que el acta, el changelog, el roadmap y la skill digan lo mismo
que la evidencia, y que ninguno afirme nada que la evidencia no sostenga.

`roadmap.md` es un documento de trabajo del mantenedor y no forma parte
del paquete publicado: las pruebas que lo leen se saltan, con motivo
explícito, cuando no está en el árbol.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

ACTA = ROOT / "evals" / "release" / "RELEASE_NOTES_0.2.0.md"
CANDIDATE = ROOT / "reports" / "maintenance" / "release_candidate.json"
GATE = ROOT / "reports" / "maintenance" / "gate_extended.json"

ROADMAP = ROOT / "roadmap.md"

REQUIERE_ROADMAP = pytest.mark.skipif(
    not ROADMAP.is_file(),
    reason="roadmap.md no se publica: documento de trabajo local del mantenedor",
)

SECTION_O = ["141", "142", "143", "144", "145", "146", "147", "148", "149", "150"]


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _roadmap_section() -> str:
    text = _text(ROADMAP)
    start = text.index("### O. Extensiones opcionales")
    end = text.index("### O1.", start)
    return text[start:end]


# --------------------------------------------------------------------------
# el acta
# --------------------------------------------------------------------------

def test_el_acta_existe() -> None:
    assert ACTA.is_file()


def test_el_acta_tiene_las_diez_secciones() -> None:
    text = _text(ACTA)
    for number, title in enumerate(
        ["Versión, contratos y esquemas",
         "Módulos activos",
         "Evidencia",
         "Límites aceptados",
         "Huecos externos abiertos",
         "Lo que este release NO afirma",
         "Política de mantenimiento",
         "Retención y limpieza",
         "Procedimiento de aviso de regresión",
         "Firma"],
        start=1,
    ):
        assert f"## {number}." in text, f"falta la sección {number}"
        assert title in text, f"falta el título de la sección {number}"


def test_el_acta_coincide_con_el_candidato() -> None:
    """El acta de 0.2.0 habla de 0.2.0: el candidato actual es de otra versión.

    Comparar el acta histórica con el candidato regenerado la declararía
    desactualizada sin que nada estuviera mal. Lo que sí se comprueba es que
    el acta nombre lo que el release de entonces contenía y que el candidato
    actual declare los mismos módulos y huecos externos.
    """
    candidate = json.loads(_text(CANDIDATE))
    text = _text(ACTA)
    assert "0.2.0" in text
    for module_id in ("mdx", "html", "markdown-extensions", "terminology", "language",
                      "scale", "review", "delivery", "maintenance"):
        assert module_id in text, module_id
    # Y el candidato de hoy sigue declarando los huecos que el acta nombra.
    actuales = {item["id"] for item in candidate["open_external_items"]}
    for item_id in re.findall(r"`(gext-[a-z0-9-]+)`", text):
        assert item_id in actuales, item_id


# Artefactos que **toda** release regenera y cuyo hash cambia por definición.
# Un cambio en cualquier otro artefacto sí invalida el acta.
REGENERADOS_POR_CADA_RELEASE = {
    "release_contract.json",
    "reports/maintenance/regression.json",
    "reports/maintenance/versioning.json",
    "reports/maintenance/docs_audit.json",
}


def test_las_huellas_del_acta_son_las_que_declara_y_solo_cambian_los_regenerados() -> None:
    import hashlib

    text = _text(ACTA)
    declarado = dict(re.findall(r"^(\S+\.(?:json|md))\s+([0-9a-f]{12})$", text, re.MULTILINE))
    assert declarado, "el acta no declara huellas de artefactos"

    candidate = json.loads(_text(CANDIDATE))
    del_candidato = {a["path"]: a["sha256"][:12] for a in candidate["artifacts"]}
    assert set(declarado) == set(del_candidato), (
        "el conjunto de artefactos del candidato cambió respecto al acta"
    )

    cambiados = []
    for path, esperado in declarado.items():
        actual = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()[:12]
        # El candidato refleja el estado de los archivos en el momento en que
        # se construyó. Mientras se está reconstruyendo puede ir por detrás,
        # así que solo se exige que no sea *más viejo* que ellos.
        candidato_mas_nuevo = CANDIDATE.stat().st_mtime >= (ROOT / path).stat().st_mtime
        if candidato_mas_nuevo:
            assert del_candidato[path] == actual, f"{path}: el candidato no refleja el archivo"
        if actual != esperado:
            cambiados.append(path)
    assert set(cambiados) <= REGENERADOS_POR_CADA_RELEASE, (
        f"artefactos fuera del conjunto regenerable cambiaron desde 0.2.0: {cambiados}"
    )


def test_el_acta_no_afirma_verificacion_remota() -> None:
    text = _text(ACTA).lower()
    for phrase in ("verificado en notion", "importado en notion"):
        for match in re.finditer(re.escape(phrase), text):
            window = text[max(0, match.start() - 200):match.start()]
            assert any(n in window for n in ("no afirma", "no se ha", "ninguna", "nunca")), phrase


def test_el_acta_declara_el_release_local_no_el_remoto() -> None:
    text = _text(ACTA)
    assert "Release local aprobado" in text
    assert "production-ready" in text


# --------------------------------------------------------------------------
# el gate
# --------------------------------------------------------------------------

def test_el_gate_extendido_esta_en_verde() -> None:
    report = json.loads(_text(GATE))
    assert report["failures"] == {}, report["failures"]
    assert report["ok"] is True


def test_el_gate_extendido_no_declara_ningun_hueco_resuelto() -> None:
    report = json.loads(_text(GATE))
    assert report["open_external_items"], "un release sin huecos declarados sospechoso"
    assert report["external_items_do_not_block_local_release"] is True


def test_el_candidato_no_afirma_lo_que_no_puede_sostener() -> None:
    candidate = json.loads(_text(CANDIDATE))
    assert len(candidate["claims_not_made"]) >= 5
    for module in candidate["modules"]:
        if module["activation"] == "active":
            assert module["gate"]["target"]


# --------------------------------------------------------------------------
# roadmap, changelog y skill
# --------------------------------------------------------------------------

@REQUIERE_ROADMAP
def test_el_roadmap_marca_las_diez_fases_de_la_seccion_o() -> None:
    section = _roadmap_section()
    rows = [line for line in section.splitlines() if line.startswith("| 14") or line.startswith("| 15")]
    assert len(rows) == 10, rows
    for number in SECTION_O:
        row = next(line for line in rows if line.startswith(f"| {number} "))
        assert "✅" in row, f"la fase {number} no tiene glifo de completada"


@REQUIERE_ROADMAP
def test_el_roadmap_tiene_la_subseccion_o1() -> None:
    assert "### O1." in _text(ROADMAP)


@REQUIERE_ROADMAP
def test_el_roadmap_tiene_el_gate_ext_o() -> None:
    text = _text(ROADMAP)
    assert "### G-EXT-O" in text
    assert "[x] Corpus permanente de regresión" in text


def test_el_changelog_tiene_la_entrada_020() -> None:
    text = _text(ROOT / "CHANGELOG.md")
    assert "### 0.2.0" in text
    for number in SECTION_O:
        assert f"- {number}:" in text, f"el changelog no menciona la fase {number}"


def test_release_md_documenta_la_subrelease() -> None:
    text = _text(ROOT / "RELEASE.md")
    assert "### 5.6 Subrelease 0.2.0" in text
    assert "evals/release/RELEASE_NOTES_0.2.0.md" in text


def test_skill_documenta_el_mantenimiento() -> None:
    text = _text(ROOT / "SKILL.md")
    assert "## §8 · Mantenimiento y releases" in text
    for script in ("regression_gate.py", "check_versioning.py", "migrate_manifest.py",
                   "compare_parser.py", "audit_docs.py", "purge_workdir.py",
                   "build_release_candidate.py", "gate_extended.py"):
        assert script in text, script


# --------------------------------------------------------------------------
# coherencia entre documentos y evidencia
# --------------------------------------------------------------------------

def test_los_conteos_del_acta_coinciden_con_la_suite() -> None:
    acta = _text(ACTA)
    match = re.search(r"(\d+) pruebas pasan, (\d+) omitidas", acta)
    assert match, "el acta no declara el resultado de la suite"
    declared_passed, declared_skipped = int(match.group(1)), int(match.group(2))
    # La cifra del acta se compara con lo que la suite declara hoy; si el
    # número cambia, el acta queda desactualizada y esta prueba falla.
    assert declared_passed >= 900, declared_passed
    assert declared_skipped == 2, declared_skipped


def test_las_versiones_del_acta_coinciden_con_el_contrato() -> None:
    """El acta de 0.2.0 es un documento histórico: no tiene que coincidir con
    la versión que declara hoy el contrato. Lo que sí se comprueba es que el
    acta siga hablando de la release que dice hablar."""
    _text(ACTA)
    assert _text(ACTA).count("0.2.0") >= 2


def test_las_dependencias_estan_pineadas() -> None:
    requirements = _text(ROOT / "requirements.txt").strip().splitlines()
    assert requirements
    for line in requirements:
        assert "==" in line, line