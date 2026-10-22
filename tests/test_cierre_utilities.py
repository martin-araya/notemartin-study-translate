"""Pruebas de las utilidades de cierre: selección de lote y colisiones de anclas.

`select_lote.py` decide qué se traduce a continuación; `dump_anchor_collisions.py`
distingue la colisión que rompe la navegación de la que no. Los dos errores
que Importan aquí son silenciosos: elegir el trabajo equivocado, o dar por
bloqueante un recuento que no lo es.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from dump_anchor_collisions import (  # noqa: E402
    intra_document_collisions,
    load_collisions,
    render,
)
from select_lote import Tradable, build_lote, plan  # noqa: E402

SELECT = ROOT / "scripts" / "select_lote.py"
DUMP = ROOT / "scripts" / "dump_anchor_collisions.py"

STUB_A = "tailwindcss/installation/index.md"
STUB_B = "tailwindcss/installation/tailwind-cli.md"
DOC_COLLIDED = "doc-085fb377"


def segments_doc() -> dict:
    return {"source_root": "/f", "files": [
        {"document_id": DOC_COLLIDED, "path": STUB_A, "segments": [
            {"segment_id": "seg-a", "disposition": "translatable", "translatable_text": "Hello world!"}]},
        {"document_id": DOC_COLLIDED, "path": STUB_B, "segments": [
            {"segment_id": "seg-b", "disposition": "translatable", "translatable_text": "Hello world!"}]},
        {"document_id": "doc-2", "path": "angular/api/x.md", "segments": [
            {"segment_id": "seg-c", "disposition": "translatable", "translatable_text": "Una tabla."},
            {"segment_id": "seg-d", "disposition": "code_skip", "translatable_text": ""}]},
    ]}


def packets_doc() -> dict:
    def pkt(packet_id, doc_id, path, seg, chars=100):
        return {"packet_id": packet_id, "document_id": doc_id, "path": path,
                "markers": "§§", "segments": [seg], "total_chars": chars,
                "translatable_text_with_markers": "Hello world!"}

    return {"packets": [
        pkt("pack-1", DOC_COLLIDED, STUB_A, "seg-a"),
        pkt("pack-2", DOC_COLLIDED, STUB_B, "seg-b"),
        pkt("pack-3", "doc-2", "angular/api/x.md", "seg-c", 500),
        pkt("pack-4", "doc-2", "angular/api/x.md", "seg-d", 500),
    ]}


# --------------------------------------------------------------------------
# select_lote
# --------------------------------------------------------------------------


def test_el_plan_mide_lo_que_falta_por_directorio() -> None:
    state = plan(packets_doc(), segments_doc(), None)
    dirs = {s["directory"]: s for s in state["by_directory"]}
    assert set(dirs) == {"tailwindcss", "angular"}
    assert dirs["tailwindcss"]["pending_packets"] == 2
    assert state["translatable_segments_total"] == 3


def test_un_documento_ya_escrito_no_vuelve_al_plan() -> None:
    t = segments_doc()
    done = Path(__import__("tempfile").gettempdir()) / "nst-lote-done"
    done.mkdir(parents=True, exist_ok=True)
    (done / "doc-2.json").write_text("{}", encoding="utf-8")
    state = plan(packets_doc(), t, str(done))
    assert state["packets_pending"] == 2  # solo los dos stubs


def test_el_sobre_solo_pide_segmentos_traducibles() -> None:
    """Pedir un `code_skip` sería exigir una traducción que no existe."""
    state = plan(packets_doc(), segments_doc(), None)
    lote = build_lote(state, 6000, "angular")
    assert lote["packets_count"] == 1
    assert lote["packets"][0]["segments"] == ["seg-c"]
    assert lote["segments_requested"] == 1


def test_el_sobre_lleva_la_clave_que_desambigua_la_ruta() -> None:
    state = plan(packets_doc(), segments_doc(), None)
    lote = build_lote(state, 6000, "tailwindcss")
    claves = {p["path"]: p["translation_id"] for p in lote["packets"]}
    assert len(set(claves.values())) == 2, claves
    assert all(k and k.startswith("trl-") for k in claves.values())


def test_un_lote_no_cruza_de_directorio() -> None:
    """Mezclar `angular/api/` y `nextjs/messages/` en un lote impide
    diagnosticar un fallo: no se sabe a qué término pertenece."""
    state = plan(packets_doc(), segments_doc(), None)
    lote = build_lote(state, 6000, "tailwindcss")
    assert {p["path"].split("/")[0] for p in lote["packets"]} == {"tailwindcss"}


def test_el_orden_de_directorios_es_el_de_menor_riesgo() -> None:
    state = plan(packets_doc(), segments_doc(), None)
    order = [s["directory"] for s in state["by_directory"]]
    assert order.index("tailwindcss") < order.index("angular")


def test_los_segmentos_traducibles_se_indexan_por_clave_resuelta() -> None:
    idx = Tradable(segments_doc())
    assert idx.total() == 3          # dos stubs con claves distintas + doc-2
    assert len(idx) == 3
    assert any(k.startswith("trl-") for k in idx.by_key)


def test_el_cli_orden_no_escribe_nada(tmp_path: Path) -> None:
    seg = tmp_path / "s.json"
    pkt = tmp_path / "p.json"
    seg.write_text(json.dumps(segments_doc()), encoding="utf-8")
    pkt.write_text(json.dumps(packets_doc()), encoding="utf-8")
    proc = subprocess.run([
        sys.executable, str(SELECT), "--packets", str(pkt), "--segments", str(seg), "--order",
    ], capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr
    assert "tailwindcss" in proc.stdout
    assert sorted(p.name for p in tmp_path.iterdir()) == ["p.json", "s.json"]


# --------------------------------------------------------------------------
# dump_anchor_collisions
# --------------------------------------------------------------------------


def test_la_colision_intra_documento_se_detecta() -> None:
    tmp = Path(__import__("tempfile").gettempdir()) / "nst-anchors-intra"
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp / "doc-1.json").write_text(json.dumps({
        "document_id": "doc-1", "path": "a.md",
        "anchors": [
            {"new_slug": "api-api", "new_text": "API"},
            {"new_slug": "api-api", "new_text": "API otra vez"},
            {"new_slug": "guia", "new_text": "Guía"},
        ],
    }), encoding="utf-8")
    found = intra_document_collisions(tmp)
    assert len(found) == 1
    assert found[0]["slug"] == "api-api"
    assert found[0]["occurrences"] == 2


def test_un_slug_repetido_entre_documentos_no_es_colision() -> None:
    """El fragmento se resuelve dentro del documento. Reutilizarlo entre
    rutas no rompe nada: por eso los 3 110 de `_collisions.json` no
    bloquean la reescritura."""
    tmp = Path(__import__("tempfile").gettempdir()) / "nst-anchors-cross"
    tmp.mkdir(parents=True, exist_ok=True)
    for i in (1, 2):
        (tmp / f"doc-{i}.json").write_text(json.dumps({
            "document_id": f"doc-{i}", "path": f"d{i}.md",
            "anchors": [{"new_slug": "api-api", "new_text": "API"}],
        }), encoding="utf-8")
    assert intra_document_collisions(tmp) == []


def test_una_anchora_explicita_se_registra_como_esta() -> None:
    """`<a id="…">` no se reescribe (INV-09); el mapa lo marca `explicit`."""
    tmp = Path(__import__("tempfile").gettempdir()) / "nst-anchors-explicit"
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp / "doc-1.json").write_text(json.dumps({
        "document_id": "doc-1", "path": "a.md",
        "anchors": [
            {"new_slug": "api", "new_text": "API", "source": "explicit"},
            {"new_slug": "api", "new_text": "API", "source": "implicit"},
        ],
    }), encoding="utf-8")
    found = intra_document_collisions(tmp)
    assert len(found) == 1
    assert found[0]["occurrences"] == 2


def test_una_anchora_repetida_dentro_del_documento_bloquea_la_aprobacion() -> None:
    md = render({}, 10, [{
        "path": "a.md", "document_id": "doc-1", "slug": "api-api",
        "occurrences": 2, "titles": ["API", "API"],
    }])
    assert "bloqueantes" in md
    assert "no bloqueantes" in md
    assert "api-api" in md
    assert "No** reescribe nada" in md


def test_lectura_del_archivo_de_colisiones_de_build_anchors(tmp_path: Path) -> None:
    f = tmp_path / "_collisions.json"
    f.write_text(json.dumps({
        "kind": "cross_doc_collision", "total": 2,
        "collisions": [{"slug": "api-api", "documents": [
            {"path": "a.md", "heading": "API"},
            {"path": "b.md", "heading": "API"},
        ]}],
    }), encoding="utf-8")
    groups, documents = load_collisions(str(f))
    assert "api-api" in groups
    assert len(groups["api-api"]) == 2
    assert documents == 0


def test_el_cli_acepta_el_directorio_de_anchors(tmp_path: Path) -> None:
    d = tmp_path / "anchors.json"
    d.mkdir()
    (d / "_collisions.json").write_text(json.dumps({
        "collisions": [{"slug": "s", "documents": [{"path": "a.md"}, {"path": "b.md"}]}],
    }), encoding="utf-8")
    (d / "doc-1.json").write_text(json.dumps({
        "document_id": "doc-1", "path": "a.md",
        "anchors": [{"new_slug": "x", "new_text": "X"}],
    }), encoding="utf-8")
    out = tmp_path / "r.md"
    proc = subprocess.run([
        sys.executable, str(DUMP), "--anchors", str(d), "--out", str(out),
    ], capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr
    md = out.read_text(encoding="utf-8")
    assert "0 colisiones intra-documento" in proc.stdout
    assert "| Documentos con mapa de anclas | 1 |" in md