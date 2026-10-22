"""Pruebas de la colisión de `document_id` (deuda de entrada de G-BETA).

`prepare.py` deriva `document_id` de los bytes del archivo:

    document_id = "doc-" + sha256(source_bytes)[:8]

Dos rutas con contenido byte a byte idéntico comparten `document_id`.
Medido sobre el corpus beta: 15 identificadores ambiguos, 214 rutas.

Con la traducción persistida en `translations/<document_id>.json`, dos de
esas rutas escribían sobre el mismo archivo y el parche de `assemble.py`
se aplicaba sobre el documento equivocado. Ningún validador por paquete
lo detectaba: cada paquete era correcto por separado.

Estas pruebas fijan la colisión real (los stubs de
`tailwindcss/installation/`) y comprueban que la remediación la separa
sin mover los archivos que ya no colisionan.
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

from translation_key import (  # noqa: E402
    ambiguous_documents,
    collision_report,
    index_by_document,
    normalize_path,
    resolve_file,
    resolve_key,
    translation_id,
)

RECEIVE = ROOT / "scripts" / "receive_translations.py"
ASSEMBLE = ROOT / "scripts" / "assemble.py"
INJECT = ROOT / "scripts" / "inject_translation_ids.py"

# Bytes exactos de las cuatro páginas stub de Tailwind medidas en el
# corpus: 15 bytes, idénticos en cuatro rutas distintas.
STUB = "\n# Hello world!"

STUB_PATHS = [
    "tailwindcss/installation/index.md",
    "tailwindcss/installation/tailwind-cli.md",
    "tailwindcss/installation/using-postcss.md",
    "tailwindcss/installation/using-vite.md",
]


def sha256_hex(data: bytes) -> str:
    import hashlib

    return hashlib.sha256(data).hexdigest()


STUB_DOC_ID = "doc-" + sha256_hex(STUB.encode("utf-8"))[:8]


def make_segments_doc(stub_paths: list[str] | None = None) -> dict:
    """segments.json con un `document_id` ambiguo y otro que no lo es."""
    paths = STUB_PATHS if stub_paths is None else stub_paths
    files = [
        {
            "document_id": STUB_DOC_ID,
            "path": p,
            "source_hash": sha256_hex(STUB.encode("utf-8")),
            "segments": [
                {"segment_id": "seg-h", "translatable_text": "Hello world!",
                 "byte_range": {"start": 3, "end": 15},
                 "protected_literals": []},
            ],
        }
        for p in paths
    ]
    files.append({
        "document_id": "doc-abcdef01",
        "path": "nextjs/messages/ejemplo.md",
        "source_hash": "a" * 64,
        "segments": [
            {"segment_id": "seg-p", "translatable_text": "Blocking prerender.",
             "byte_range": {"start": 0, "end": 19},
             "protected_literals": []},
        ],
    })
    return {"source_root": "/fuente", "files": files}


def make_packets_doc(segments_doc: dict) -> dict:
    packets = []
    for f in segments_doc["files"]:
        for seg in f["segments"]:
            packets.append({
                "packet_id": f"pack-{f['path']}-{seg['segment_id']}",
                "document_id": f["document_id"],
                "path": f["path"],
                "markers": "§§",
                "segments": [seg["segment_id"]],
                "translatable_text_with_markers": seg["translatable_text"],
            })
    return {"context_budget": 1500, "packets": packets}


# --------------------------------------------------------------------------
# translation_key
# --------------------------------------------------------------------------


def test_los_cuatro_stubs_de_tailwind_comparten_document_id() -> None:
    """La colisión es real y medible, no una hipótesis."""
    assert len(STUB.encode("utf-8")) == 15
    assert STUB_DOC_ID == "doc-085fb377"
    doc = make_segments_doc()
    ambiguous = ambiguous_documents(doc)
    assert list(ambiguous) == [STUB_DOC_ID]
    assert len(ambiguous[STUB_DOC_ID]) == 4


def test_la_clave_con_ruta_separa_los_stubs() -> None:
    doc = make_segments_doc()
    files_by_doc = index_by_document(doc)
    keys = {
        p: resolve_key(files_by_doc[STUB_DOC_ID], STUB_DOC_ID, p)
        for p in STUB_PATHS
    }
    assert len(set(keys.values())) == 4, keys
    assert all(k.startswith("trl-") for k in keys.values())


def test_la_clave_sin_ambiguedad_no_cambia() -> None:
    """El 99 % del corpus no se mueve: su clave sigue siendo document_id."""
    doc = make_segments_doc()
    files_by_doc = index_by_document(doc)
    assert resolve_key(files_by_doc["doc-abcdef01"], "doc-abcdef01", "nextjs/messages/ejemplo.md") == "doc-abcdef01"


def test_translation_id_es_estable_y_depende_de_la_ruta() -> None:
    a = translation_id(STUB_DOC_ID, "tailwindcss/installation/index.md")
    b = translation_id(STUB_DOC_ID, "tailwindcss/installation/tailwind-cli.md")
    assert a == translation_id(STUB_DOC_ID, "tailwindcss/installation/index.md")
    assert a != b


def test_la_ruta_se_normaliza_antes_de_entrar_en_la_clave() -> None:
    """`./a.md`, `a\\b.md` y `a/b.md` son el mismo archivo, no tres."""
    doc_id = "doc-01234567"
    assert translation_id(doc_id, "./a/b.md") == translation_id(doc_id, "a/b.md")
    assert translation_id(doc_id, "a\\b.md") == translation_id(doc_id, "a/b.md")
    assert normalize_path("./a//b.md") == "a/b.md"


def test_resolve_file_desambigua_por_ruta() -> None:
    doc = make_segments_doc()
    files = index_by_document(doc)[STUB_DOC_ID]
    found = resolve_file(files, STUB_DOC_ID, "tailwindcss/installation/using-vite.md")
    assert found is not None
    assert found["path"] == "tailwindcss/installation/using-vite.md"
    # Una ruta que no pertenece al grupo no resuelve a una de ellas:
    # elegir la primera sería el error que INV-09 prohíbe.
    assert resolve_file(files, STUB_DOC_ID, "otro/archivo.md") is None


def test_el_informe_de_colisiones_cuenta_lo_que_se_separa() -> None:
    report = collision_report(make_segments_doc())
    assert report["ambiguous_document_ids"] == 1
    assert report["paths_affected"] == 4
    assert report["files_total"] == 5
    assert report["files_unambiguous"] == 1


# --------------------------------------------------------------------------
# receive_translations
# --------------------------------------------------------------------------


def _run_receive(base: Path, segments_doc: dict, packets_doc: dict, responses: list[dict]):
    (base / "packets.json").write_text(json.dumps(packets_doc), encoding="utf-8")
    (base / "segments.json").write_text(json.dumps(segments_doc), encoding="utf-8")
    (base / "responses.json").write_text(json.dumps(responses), encoding="utf-8")
    out = base / "translations"
    proc = subprocess.run([
        sys.executable, str(RECEIVE),
        "--packets", str(base / "packets.json"),
        "--segments", str(base / "segments.json"),
        "--responses", str(base / "responses.json"),
        "--translations", str(out),
        "--apply",
    ], capture_output=True, text=True, check=False)
    return proc, out


def test_recibir_no_pisa_la_traduccion_de_otra_ruta_del_mismo_document_id(tmp_path: Path) -> None:
    """El defecto: dos stubs con el mismo document_id, un solo archivo."""
    segments_doc = make_segments_doc()
    packets_doc = make_packets_doc(segments_doc)
    target = packets_doc["packets"][0]
    assert target["document_id"] == STUB_DOC_ID

    proc, out = _run_receive(tmp_path, segments_doc, packets_doc, [{
        "packet_id": target["packet_id"],
        "translations": [{"segment_id": "seg-h", "translated_text": "¡Hola, mundo!"}],
    }])
    assert proc.returncode == 0, proc.stderr
    report = json.loads(proc.stdout)
    assert report["documents_written"] == 1

    # El documento inequívoco conserva su clave histórica.
    assert (out / "doc-abcdef01.json").exists() is False

    key_a = translation_id(STUB_DOC_ID, STUB_PATHS[0])
    key_b = translation_id(STUB_DOC_ID, STUB_PATHS[1])
    assert (out / f"{key_a}.json").exists()
    assert (out / "doc-1.json").exists() is False


def test_los_stubs_reciben_claves_distintas_y_conservan_su_ruta(tmp_path: Path) -> None:
    segments_doc = make_segments_doc()
    packets_doc = make_packets_doc(segments_doc)

    # Se entregan los cuatro stubs con traducciones distintas. Antes de la
    # remediación las cuatro escrituras se apilarían en un único archivo y
    # solo ganaría la última.
    responses = [
        {
            "packet_id": f"pack-{p}-seg-h",
            "translations": [{"segment_id": "seg-h",
                              "translated_text": f"¡Hola, mundo! ({i})"}],
        }
        for i, p in enumerate(STUB_PATHS)
    ]
    proc, out = _run_receive(tmp_path, segments_doc, packets_doc, responses)
    assert proc.returncode == 0, proc.stderr

    for i, p in enumerate(STUB_PATHS):
        key = translation_id(STUB_DOC_ID, p)
        written = json.loads((out / f"{key}.json").read_text(encoding="utf-8"))
        assert written["path"] == p
        assert written["document_id"] == STUB_DOC_ID
        assert written["entries"][0]["translated_text"] == f"¡Hola, mundo! ({i})"


def test_una_ruta_ambigua_que_no_pertenece_al_grupo_se_rechaza(tmp_path: Path) -> None:
    """Inventar una ruta no adivina: es un hallazgo, no una escritura."""
    segments_doc = make_segments_doc()
    packets_doc = make_packets_doc(segments_doc)
    target = dict(packets_doc["packets"][0])
    target["path"] = "tailwindcss/installation/inventada.md"
    packets_doc["packets"][0] = target

    proc, out = _run_receive(tmp_path, segments_doc, packets_doc, [{
        "packet_id": target["packet_id"],
        "translations": [{"segment_id": "seg-h", "translated_text": "¡Hola!"}],
    }])
    assert proc.returncode == 1
    report = json.loads(proc.stdout)
    assert "document_id_ambiguo" in report["findings_by_kind"]
    assert not out.exists() or not list(out.glob("*.json"))


def test_el_documento_inequivoco_sigue_usando_document_id(tmp_path: Path) -> None:
    segments_doc = make_segments_doc()
    packets_doc = make_packets_doc(segments_doc)
    target = next(p for p in packets_doc["packets"] if p["document_id"] == "doc-abcdef01")

    proc, out = _run_receive(tmp_path, segments_doc, packets_doc, [{
        "packet_id": target["packet_id"],
        "translations": [{"segment_id": "seg-p", "translated_text": "Prerenderizado bloqueante."}],
    }])
    assert proc.returncode == 0, proc.stderr
    assert (out / "doc-abcdef01.json").exists()
    assert not list(out.glob("trl-*.json"))


# --------------------------------------------------------------------------
# assemble
# --------------------------------------------------------------------------


def test_assemble_aplica_cada_traduccion_a_su_archivo(tmp_path: Path) -> None:
    """El segundo síntoma: el parche caía sobre el documento equivocado."""
    source_root = tmp_path / "fuente"
    (source_root / "tailwindcss" / "installation").mkdir(parents=True)
    for p in STUB_PATHS:
        (source_root / p).write_text(STUB, encoding="utf-8")

    segments_doc = make_segments_doc()
    packets_doc = make_packets_doc(segments_doc)

    responses = [
        {
            "packet_id": f"pack-{p}-seg-h",
            "translations": [{"segment_id": "seg-h",
                              "translated_text": f"¡Hola, mundo! ({i})"}],
        }
        for i, p in enumerate(STUB_PATHS)
    ]
    _, out = _run_receive(tmp_path, segments_doc, packets_doc, responses)

    (tmp_path / "segments.json").write_text(json.dumps(segments_doc), encoding="utf-8")
    for i, p in enumerate(STUB_PATHS):
        staged = tmp_path / "staged" / p
        proc = subprocess.run([
            sys.executable, str(ASSEMBLE),
            "--source", str(source_root / p),
            "--segments", str(tmp_path / "segments.json"),
            "--out", str(staged),
            "--translations", str(out),
        ], capture_output=True, text=True, check=False)
        assert proc.returncode == 0, proc.stderr
        assert staged.read_text(encoding="utf-8") == STUB.replace(
            "Hello world!", f"¡Hola, mundo! ({i})"
        )


def test_assemble_sin_traduccion_devuelve_el_archivo_intacto(tmp_path: Path) -> None:
    source_root = tmp_path / "fuente"
    (source_root / "tailwindcss" / "installation").mkdir(parents=True)
    (source_root / STUB_PATHS[0]).write_text(STUB, encoding="utf-8")
    segments_doc = make_segments_doc([STUB_PATHS[0]] + ["x.md", "y.md"])
    (tmp_path / "segments.json").write_text(json.dumps(segments_doc), encoding="utf-8")
    staged = tmp_path / "staged.md"
    proc = subprocess.run([
        sys.executable, str(ASSEMBLE),
        "--source", str(source_root / STUB_PATHS[0]),
        "--segments", str(tmp_path / "segments.json"),
        "--out", str(staged),
    ], capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr
    assert staged.read_bytes() == STUB.encode("utf-8")


def test_assemble_elige_por_ruta_y_no_por_nombre_suelto(tmp_path: Path) -> None:
    """Dos `index.md` en directorios distintos no son el mismo archivo."""
    source_root = tmp_path / "fuente"
    (source_root / "a").mkdir(parents=True)
    (source_root / "b").mkdir(parents=True)
    (source_root / "a" / "index.md").write_text("primero\n", encoding="utf-8")
    (source_root / "b" / "index.md").write_text("segundo\n", encoding="utf-8")

    segments_doc = {"files": [
        {"document_id": "doc-aaaaaaaa", "path": "a/index.md", "source_hash": "0" * 64,
         "segments": [{"segment_id": "seg-a", "translatable_text": "primero",
                       "byte_range": {"start": 0, "end": 7}}]},
        {"document_id": "doc-bbbbbbbb", "path": "b/index.md", "source_hash": "1" * 64,
         "segments": [{"segment_id": "seg-b", "translatable_text": "segundo",
                       "byte_range": {"start": 0, "end": 7}}]},
    ]}
    (tmp_path / "segments.json").write_text(json.dumps(segments_doc), encoding="utf-8")
    translations = tmp_path / "translations"
    translations.mkdir()
    (translations / "doc-bbbbbbbb.json").write_text(json.dumps({
        "document_id": "doc-bbbbbbbb", "path": "b/index.md",
        "entries": [{"segment_id": "seg-b", "translated_text": "SEGUNDO"}],
    }), encoding="utf-8")

    staged = tmp_path / "staged.md"
    proc = subprocess.run([
        sys.executable, str(ASSEMBLE),
        "--source", str(source_root / "a" / "index.md"),
        "--segments", str(tmp_path / "segments.json"),
        "--out", str(staged),
        "--translations", str(translations),
    ], capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr
    assert staged.read_text(encoding="utf-8") == "primero\n"


# --------------------------------------------------------------------------
# inject_translation_ids
# --------------------------------------------------------------------------


def test_inyectar_agrega_la_clave_solo_a_los_ambiguos(tmp_path: Path) -> None:
    segments_doc = make_segments_doc()
    packets_doc = make_packets_doc(segments_doc)
    proc = subprocess.run([
        sys.executable, str(INJECT),
        "--packets", _write(tmp_path / "p2.json", packets_doc),
        "--segments", _write(tmp_path / "s2.json", segments_doc),
        "--out", str(tmp_path / "p3.json"),
        "--report", str(tmp_path / "r.json"),
    ], capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr

    report = json.loads((tmp_path / "r.json").read_text(encoding="utf-8"))
    assert report["packets_with_new_key"] == 4
    assert report["packets_keeping_document_id_key"] == 1
    assert report["integrity_ok"] is True
    assert report["collisions"]["paths_affected"] == 4

    out = json.loads((tmp_path / "p3.json").read_text(encoding="utf-8"))
    by_path = {p["path"]: p for p in out["packets"]}
    assert by_path[STUB_PATHS[0]]["translation_id"] == translation_id(STUB_DOC_ID, STUB_PATHS[0])
    assert by_path["nextjs/messages/ejemplo.md"]["translation_id"] is None
    # El texto del paquete no se toca: no se reempaquetó nada.
    assert by_path[STUB_PATHS[0]]["translatable_text_with_markers"] == "Hello world!"


def test_inyectar_no_crea_doble_propietario_por_ruta(tmp_path: Path) -> None:
    """INV-03 se verifica sobre la identidad real del archivo."""
    segments_doc = make_segments_doc()
    packets_doc = make_packets_doc(segments_doc)
    # Duplica un paquete del grupo ambiguo para provocar doble propiedad.
    dup = dict(packets_doc["packets"][0])
    dup["packet_id"] = dup["packet_id"] + "-copia"
    packets_doc["packets"].append(dup)

    subprocess.run([
        sys.executable, str(INJECT),
        "--packets", _write(tmp_path / "p2.json", packets_doc),
        "--segments", _write(tmp_path / "s2.json", segments_doc),
        "--out", str(tmp_path / "p3.json"),
        "--report", str(tmp_path / "r.json"),
    ], capture_output=True, text=True, check=False)
    report = json.loads((tmp_path / "r.json").read_text(encoding="utf-8"))
    assert report["segments_with_duplicate_path_owner"] == 1
    assert report["integrity_ok"] is False


def test_inyectar_avisa_de_un_documento_que_segments_no_conoce(tmp_path: Path) -> None:
    segments_doc = make_segments_doc()
    packets_doc = make_packets_doc(segments_doc)
    packets_doc["packets"].append({
        "packet_id": "pack-fantasma", "document_id": "doc-99999999",
        "path": "fantasma.md", "markers": "§§", "segments": ["seg-z"],
        "translatable_text_with_markers": "nada",
    })
    subprocess.run([
        sys.executable, str(INJECT),
        "--packets", _write(tmp_path / "p2.json", packets_doc),
        "--segments", _write(tmp_path / "s2.json", segments_doc),
        "--out", str(tmp_path / "p3.json"),
        "--report", str(tmp_path / "r.json"),
    ], capture_output=True, text=True, check=False)
    report = json.loads((tmp_path / "r.json").read_text(encoding="utf-8"))
    assert report["integrity_ok"] is False
    assert report["unresolved"]


def _write(path: Path, payload: dict) -> str:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


# --------------------------------------------------------------------------
# packet_id: la misma raíz, un symptom más grave
# --------------------------------------------------------------------------


def test_packetize_no_repite_packet_id_entre_archivos_byte_identicos() -> None:
    """`packet_id` debe nombrar una unidad de trabajo, no un grupo de ellas.

    Se derivaba de `document_id` + `segment_id`, y ambos derivan de los
    bytes: dos archivos byte-idénticos producían el MISMO `packet_id`.
    Quien responde indexa los paquetes en un dict por id, así que el
    trabajo de todos menos el último se perdía sin aviso.
    """
    from packetize import pack_file

    seg = {"segment_id": "seg-h", "translatable_text": "Hello world!",
           "protected_literals": []}
    a, _ = pack_file({"document_id": STUB_DOC_ID, "path": STUB_PATHS[0],
                      "segments": [seg]}, 1500, "§§")
    b, _ = pack_file({"document_id": STUB_DOC_ID, "path": STUB_PATHS[1],
                      "segments": [dict(seg)]}, 1500, "§§")
    assert a and b
    assert a[0]["packet_id"] != b[0]["packet_id"]


def test_packetize_conserva_la_estabilidad_del_id_entre_ejecuciones() -> None:
    """Cambiar la fórmula no puede cambiar el id dos veces seguidas."""
    from packetize import pack_file

    f = {"document_id": "doc-abcdef01", "path": "nextjs/messages/x.md",
         "segments": [{"segment_id": "seg-1", "translatable_text": "Hola.",
                       "protected_literals": []}]}
    first, _ = pack_file(dict(f), 1500, "§§")
    second, _ = pack_file(dict(f), 1500, "§§")
    assert first[0]["packet_id"] == second[0]["packet_id"]


def test_inyectar_renombra_los_packet_id_duplicados(tmp_path: Path) -> None:
    segments_doc = make_segments_doc()
    packets_doc = make_packets_doc(segments_doc)
    # Dos stubs con el mismo document_id y el mismo segment_id: es
    # exactamente lo que packetize producía antes de la reparación.
    shared = segments_doc["files"][0]["segments"][0]["segment_id"]
    for i, p in enumerate(STUB_PATHS[:2]):
        pkt = {"packet_id": "pack-colision", "document_id": STUB_DOC_ID,
               "path": p, "markers": "§§", "segments": [shared],
               "translatable_text_with_markers": "Hello world!"}
        packets_doc["packets"][i] = pkt

    subprocess.run([
        sys.executable, str(INJECT),
        "--packets", _write(tmp_path / "p2.json", packets_doc),
        "--segments", _write(tmp_path / "s2.json", segments_doc),
        "--out", str(tmp_path / "p3.json"),
        "--report", str(tmp_path / "r.json"),
    ], capture_output=True, text=True, check=False)
    report = json.loads((tmp_path / "r.json").read_text(encoding="utf-8"))
    assert report["duplicate_packet_ids_before"] == 1
    assert report["duplicate_packet_ids_after"] == 0
    assert report["packets_renamed"] == 2
    assert report["integrity_ok"] is True

    out = json.loads((tmp_path / "p3.json").read_text(encoding="utf-8"))
    ids = [p["packet_id"] for p in out["packets"]]
    assert len(ids) == len(set(ids))
    assert set(report["packet_id_renames"]["pack-colision"]) == {
        p["packet_id"] for p in out["packets"] if p.get("previous_packet_id") == "pack-colision"
    }


def test_el_renombrado_conserva_la_posesion_de_segmentos(tmp_path: Path) -> None:
    segments_doc = make_segments_doc()
    packets_doc = make_packets_doc(segments_doc)
    shared = segments_doc["files"][0]["segments"][0]["segment_id"]
    for i, p in enumerate(STUB_PATHS[:2]):
        packets_doc["packets"][i] = {"packet_id": "pack-colision",
                                     "document_id": STUB_DOC_ID, "path": p,
                                     "markers": "§§", "segments": [shared],
                                     "translatable_text_with_markers": "Hello world!"}
    subprocess.run([
        sys.executable, str(INJECT),
        "--packets", _write(tmp_path / "p2.json", packets_doc),
        "--segments", _write(tmp_path / "s2.json", segments_doc),
        "--out", str(tmp_path / "p3.json"),
    ], capture_output=True, text=True, check=False)
    out = json.loads((tmp_path / "p3.json").read_text(encoding="utf-8"))
    by_path = {p["path"]: p for p in out["packets"]}
    for p in STUB_PATHS[:2]:
        assert by_path[p]["segments"] == [shared]
        assert by_path[p]["previous_packet_id"] == "pack-colision"


# --------------------------------------------------------------------------
# validate
# --------------------------------------------------------------------------


def test_validate_registra_colisiones_como_hallazgo_del_contrato() -> None:
    """El validador no puede arreglar la colisión, pero sí verla."""
    from validate import _identity_resolver, _translation_identity

    segments_doc = make_segments_doc()
    key_for = _identity_resolver(segments_doc)
    stub_key = key_for(STUB_DOC_ID, STUB_PATHS[0])
    plain_key = key_for("doc-abcdef01", "nextjs/messages/ejemplo.md")
    assert stub_key != plain_key
    assert stub_key.startswith("trl-")
    assert plain_key == "doc-abcdef01"


@pytest.mark.parametrize("idx", [0, 1, 2, 3])
def test_cada_stub_resuelve_a_su_propia_clave(tmp_path: Path, idx: int) -> None:
    from validate import _identity_resolver, _translation_identity

    segments_doc = make_segments_doc()
    key_for = _identity_resolver(segments_doc)
    path = STUB_PATHS[idx]
    key = translation_id(STUB_DOC_ID, path)
    f = tmp_path / f"{key}.json"
    f.write_text(json.dumps({
        "document_id": STUB_DOC_ID, "path": path, "translation_id": key,
        "entries": [],
    }), encoding="utf-8")
    assert _translation_identity(f, key_for) == (key, path)