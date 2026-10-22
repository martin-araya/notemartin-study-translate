"""Pruebas de verify_already_target.py (paso 3 del cierre de G-BETA).

Un segmento `already_target` no se reescribe: se **comprueba** que esté
en el idioma de destino. Declararlo sin comprobar reduce el denominador
para mejorar una métrica, que es lo que INV-04 prohíbe.

El riesgo real de este script no es quedarse corto: es dar positivo en
prosa española corriente. El corpus beta mide las tres iteraciones del
detector: 884 → 386 → 147 hallazgos sobre 1 297 segmentos, y cada
descenso salió de medir un caso concreto en lugar de subir umbrales a
ojo. Estas pruebas fijan los tres filtros para que no vuelvan a
relajarse.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from verify_already_target import (  # noqa: E402
    classify,
    load_preserve_terms,
    looks_like_proper_noun_run,
    render_markdown,
    scan,
    segment_kind,
    spanish_share,
    strip_quoted_spans,
)

SCRIPT = ROOT / "scripts" / "verify_already_target.py"


# --------------------------------------------------------------------------
# Formas
# --------------------------------------------------------------------------


def test_la_forma_se_clasifica_segun_estructura_no_segun_idioma() -> None:
    assert segment_kind("") == "empty"
    assert segment_kind("[Sequence](#Sequence)") == "link_only"
    assert segment_kind("**Code**") == "label"
    assert segment_kind("El tipo `VECTOR` es la base.") == "prose"


# --------------------------------------------------------------------------
# El error que ya se cometió: falsos positivos sobre prosa española
# --------------------------------------------------------------------------


def test_una_palestra_con_guion_no_es_ingles() -> None:
    """«sub-sección» y «auto-completado» no son evidencia de inglés."""
    v, _ = classify("Esta sub-sección detalla las tablas auxiliares del índice.", set())
    assert v == "spanish_prose"


def test_un_nombre_propio_no_es_prosa_sin_traducir() -> None:
    assert looks_like_proper_noun_run(["Oracle", "AI", "Vector", "Search"])
    assert not looks_like_proper_noun_run(["release", "update", "notes"])
    v, _ = classify("Esta sección cubre las novedades de Oracle AI Vector Search.", set())
    assert v == "spanish_prose"


def test_una_frase_inglesa_no_se_escapa_al_filtro_de_propia_nombre() -> None:
    """El filtro no puede tapar una frase que sí está sin traducir."""
    v, ev = classify("Create and Use a custom Vocabulary for the index.", set())
    assert v == "english_prose"
    assert ev


# --------------------------------------------------------------------------
# Citas textuales
# --------------------------------------------------------------------------


def test_una_cita_del_pdf_en_ingles_no_es_una_entence_sin_traducir() -> None:
    texto = (
        "Última sección del capítulo. Recoge las **features deprecadas**. "
        'El propio texto del PDF declara: *"Included are some notable Oracle '
        'AI Vector Search updates with Oracle Database"* y las reproduce aquí.'
    )
    # La cita se retira ANTES de medir: si se midiera dentro, el detector
    # vería quince palabras inglesas seguidas y acusaría el segmento.
    assert "Included are some notable" not in strip_quoted_spans(texto)
    v, _ = classify(texto, set())
    assert v == "spanish_prose"


# --------------------------------------------------------------------------
# Densidad de español
# --------------------------------------------------------------------------


def test_la_densidad_de_espanol_separa_las_dos_casos() -> None:
    assert spanish_share("El tipo VECTOR es la base del almacenamiento") >= 0.15
    assert spanish_share("The vector type is the basis for storage") == 0.0


def test_una_frase_inglesa_entera_se_reporta() -> None:
    v, ev = classify(
        "Guidelines for Vector Indexes describe how the index is built.", set()
    )
    assert v == "english_prose"
    assert ev and ev[0]


# --------------------------------------------------------------------------
# Etiquetas de interfaz generada
# --------------------------------------------------------------------------


def test_una_etiqueta_de_la_referencia_generada_se_reporta() -> None:
    for texto in ["Type Alias\nstable", "function", "experimental",
                  "deprecated", "read-only"]:
        v, _ = classify(texto, set())
        assert v == "english_label", texto


def test_una_etiqueta_de_enlace_va_a_la_reecritura_de_anclas() -> None:
    """`[destroy](#destroy)` no se juzga por idioma: su idioma lo decide
    el encabezado de destino, que es lo que INV-09 obliga a reescribir."""
    v, _ = classify("[destroy](#destroy)", set())
    assert v == "link_label_pending"


def test_una_etiqueta_en_espanol_no_se_reporta() -> None:
    """«alias» y «type» existen también en español: no bastan solos."""
    for texto in ["Tipo alias", "Alias de tipo", "Valor de entrada", "Código"]:
        v, _ = classify(texto, set())
        assert v != "english_label", texto


# --------------------------------------------------------------------------
# Glosario
# --------------------------------------------------------------------------


def test_los_terminos_del_glosario_no_cuentan_como_residuo(tmp_path: Path) -> None:
    glosario = tmp_path / "glossary.json"
    glosario.write_text(json.dumps({"entries": [
        {"source_term": "component", "preservation_policy": "keep-original",
         "preferred": {"lang": "es", "term": "componente"}},
        {"source_term": "binding", "preservation_policy": "translate",
         "preferred": {"lang": "es", "term": "enlace"}},
    ]}), encoding="utf-8")
    preserve = load_preserve_terms(str(glosario))
    assert preserve == {"component", "componente"}
    v, _ = classify("The component reads the property and returns nothing else.", preserve)
    assert v != "english_prose" or "component" not in " ".join(v)


def test_un_glosario_inexistente_no_rompe_la_verificacion(tmp_path: Path) -> None:
    assert load_preserve_terms(str(tmp_path / "no-existe.json")) == set()
    assert load_preserve_terms(None) == set()


# --------------------------------------------------------------------------
# Recorrido completo
# --------------------------------------------------------------------------


def _segments_doc() -> dict:
    return {"files": [
        {"document_id": "doc-1", "path": "oracle/resúmenes/01.md", "segments": [
            {"segment_id": "seg-1", "disposition": "already_target",
             "translatable_text": "El tipo VECTOR es la base para almacenar embeddings vectoriales."},
            {"segment_id": "seg-2", "disposition": "already_target",
             "translatable_text": "Guidelines for Vector Indexes"},
        ]},
        {"document_id": "doc-2", "path": "angular/api/x.md", "segments": [
            {"segment_id": "seg-3", "disposition": "already_target",
             "translatable_text": "Type Alias\nstable"},
        ]},
        {"document_id": "doc-3", "path": "nextjs/y.md", "segments": [
            {"segment_id": "seg-4", "disposition": "translatable",
             "translatable_text": "This paragraph is English and must be translated."},
        ]},
    ]}


def test_el_recorrido_solo_mira_la_disposicion_pedida() -> None:
    payload = scan(_segments_doc(), "already_target")
    assert payload["total"] == 3
    assert {s["segment_id"] for s in payload["all_segments"]} == {"seg-1", "seg-2", "seg-3"}


def test_el_recorrido_desglosa_por_directorio() -> None:
    payload = scan(_segments_doc(), "already_target")
    assert set(payload["by_directory"]) == {"oracle", "angular"}
    assert payload["needs_translation_count"] == 2


def test_la_verificacion_no_reescribe_nada(tmp_path: Path) -> None:
    """El script no abre el documento fuente: solo lee el JSON de segmentos."""
    out = tmp_path / "out.json"
    proc = subprocess.run([
        sys.executable, str(SCRIPT),
        "--segments", str(ROOT / "tests" / "fixtures" / "already_target" / "segments.json"),
        "--out", str(out),
    ], capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["total"] == 3
    # Los identificadores de archivo escritos son solo el informe.
    assert sorted(p.name for p in tmp_path.iterdir()) == ["out.json"]


def test_el_informe_markdown_declara_lo_que_no_afirma() -> None:
    md = render_markdown(scan(_segments_doc(), "already_target"))
    assert "Lo que este informe no afirma" in md
    assert "No** demuestra que la prosa en español sea una traducción fiel" in md
    assert "reduce el denominador por su cuenta" in md