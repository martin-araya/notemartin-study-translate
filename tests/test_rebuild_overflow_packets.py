"""Pruebas para scripts/rebuild_overflow_packets.py (fase 050).

Los paquetes con ``overflow: true`` del corpus beta contienen **un solo**
segmento, así que la partición tiene que ocurrir dentro del segmento, por
línea. Estas pruebas fijan los invariantes que la subdivisión no puede
romper:

- cada tramo cabe en el presupuesto del perfil;
- los tramos cubren el rango original sin huecos ni solapamientos, y los
  únicos huecos admisibles son saltos de línea, igual que en ``prepare``;
- ``assemble.py`` reproduce la fuente byte a byte con los tramos;
- ningún literal protegido se parte ni se duplica entre tramos;
- el texto de cada tramo relee exactamente su propio rango.

Cada prueba que fijó un defecto real lleva el motivo en el docstring.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "rebuild_overflow_packets.py"
TMP = Path(tempfile.gettempdir()) / "nst-tests-overflow"

sys.path.insert(0, str(ROOT / "scripts"))
import assemble  # noqa: E402


def load_module():
    spec = importlib.util.spec_from_file_location("rebuild_overflow_packets", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ROP = load_module()


def prose(lines: list[str]) -> bytes:
    return "\n".join(lines).encode("utf-8")


def test_trozos_caben_en_el_presupuesto() -> None:
    src = prose([f"linea numero {i} con texto suficiente" for i in range(40)])
    spans = ROP.split_segment_spans(src, 0, len(src), 60, [])
    assert len(spans) > 1, "una prosa larga debe partirse en varios trozos"
    for a, b in spans:
        assert len(src[a:b].decode("utf-8")) <= 60


def test_trozos_cubren_el_rango_sin_solapamientos() -> None:
    """Cobertura completa y sin solapes.

    Los tramos no son contiguos byte a byte: entre ellos queda el salto
    de línea que unía las líneas partidas, y ese salto queda fuera del
    rango a propósito para que ``assemble.py`` lo copie literal. Lo que
    no puede pasar es un solape, que reescribiría prosa, ni prosa
    perdida, que un hueco más ancho que un salto ocultaría.
    """
    src = prose([f"linea {i} del documento" for i in range(30)])
    spans = ROP.split_segment_spans(src, 0, len(src), 40, [])
    cursor = 0
    for a, b in spans:
        assert a >= cursor, f"solape: el tramo empieza en {a} antes de {cursor}"
        assert a - cursor <= 1, (
            f"hueco de {a - cursor} bytes: solo puede faltar el salto de línea"
        )
        cursor = b
    assert cursor == len(src), "el último trozo debe cerrar el rango"


def test_los_huecos_solo_son_saltos_de_linea() -> None:
    """Un hueco que no sea ``\\n`` perdería prosa al ensamblar.

    ``prepare.narrow_range_to_text`` deja el salto final fuera del rango
    y ``assemble.py`` lo copia literal. El splitter debe comportarse
    igual: los huecos entre trozos son exactamente los saltos que unían
    las líneas partidas, y nada más.
    """
    src = prose([f"contenido de la linea {i}" for i in range(20)])
    spans = ROP.split_segment_spans(src, 0, len(src), 35, [])
    for (_, prev_end), (next_start, _) in zip(spans, spans[1:]):
        gap = src[prev_end:next_start]
        assert gap in (b"", b"\n"), f"hueco inesperado: {gap!r}"


def test_ningun_trozo_empieza_o_termina_en_salto_de_linea() -> None:
    src = prose([f"linea {i} con contenido" for i in range(20)])
    spans = ROP.split_segment_spans(src, 0, len(src), 40, [])
    for a, b in spans:
        text = src[a:b].decode("utf-8")
        assert not text.startswith("\n")
        assert not text.endswith("\n")


def test_assemble_reproduce_la_fuente_byte_a_byte() -> None:
    """La prueba base: sustituir cada tramo por sí mismo devuelve el original."""
    src = prose([f"linea {i} con un poco de texto" for i in range(50)])
    spans = ROP.split_segment_spans(src, 0, len(src), 55, [])
    segments = [
        {"segment_id": f"s{i}", "byte_range": {"start": a, "end": b}}
        for i, (a, b) in enumerate(spans)
    ]
    assert assemble.assemble(src, {"segments": segments}, identity=True) == src


def test_assemble_con_traduccion_identidad_por_trozo() -> None:
    """Cada tramo recibe su propio texto y el documento vuelve a ser la fuente."""
    src = prose([f"linea {i} con texto" for i in range(30)])
    spans = ROP.split_segment_spans(src, 0, len(src), 40, [])
    segments = [
        {"segment_id": f"s{i}", "byte_range": {"start": a, "end": b}}
        for i, (a, b) in enumerate(spans)
    ]
    lookup = {
        f"s{i}": src[a:b].decode("utf-8") for i, (a, b) in enumerate(spans)
    }
    out = assemble.assemble(src, {"segments": segments}, identity=False,
                            translations_lookup=lookup)
    assert out == src


def test_no_parte_un_literal_protegido() -> None:
    value = '{"clave": "valor"}'
    src = prose([
        f"primera linea con {value} dentro",
        "segunda linea sin nada",
        f"tercera linea con {value} otra vez",
        "cuarta linea de cierre",
    ])
    lits = [
        {"type": "code_inline", "value": value, "byte_range": {"start": src.index(value.encode()), "end": src.index(value.encode()) + len(value)}},
        {"type": "code_inline", "value": value, "byte_range": {"start": src.rindex(value.encode()), "end": src.rindex(value.encode()) + len(value)}},
    ]
    spans = ROP.split_segment_spans(src, 0, len(src), 45, lits)
    holders = [i for i, (a, b) in enumerate(spans) if value.encode() in src[a:b]]
    assert len(holders) == 2, f"el literal aparece en dos trozos, no en {len(holders)}"
    for i in holders:
        assert src[spans[i][0]:spans[i][1]].decode("utf-8").count(value) == 1


def test_literal_repetido_no_se_declara_dos_veces_en_el_mismo_trozo() -> None:
    """Defecto real: al buscar por valor, un literal repetido se duplicaba.

    ``protected_literals`` puede traer dos entradas con el mismo valor y
    rangos distintos. Buscar por texto declaraba las dos en el primer
    trozo, generaba marcadores repetidos y ``validate_packet`` rechazaba
    el paquete con «literales extra».
    """
    value = "ViewEncapsulation.ShadowDom"
    src = prose([
        "primera seccion con la primera aparicion",
        f"linea con {value} en medio",
        "seccion intermedia sin nada",
        f"otra linea con {value} repetida",
        "cierre del documento",
    ])
    first = src.index(value.encode())
    second = src.rindex(value.encode())
    lits = [
        {"type": "code_inline", "value": value, "byte_range": {"start": first, "end": first + len(value)}},
        {"type": "code_inline", "value": value, "byte_range": {"start": second, "end": second + len(value)}},
    ]
    spans = ROP.split_segment_spans(src, 0, len(src), 45, lits)
    # Asignación por rango: cada entrada cae en el trozo que la contiene.
    lit_spans = [
        (len(src[:first].decode("utf-8")), len(src[:first].decode("utf-8")) + len(value), lits[0]),
        (len(src[:second].decode("utf-8")), len(src[:second].decode("utf-8")) + len(value), lits[1]),
    ]
    per_piece = []
    for a, b in spans:
        piece = src[a:b].decode("utf-8")
        ps = len(src[:a].decode("utf-8"))
        per_piece.append(ROP.literals_in_range(lit_spans, ps, ps + len(piece)))
    counts = [len(p) for p in per_piece]
    assert counts.count(2) == 0, f"un trozo declara dos veces el mismo literal: {counts}"
    assert sum(counts) == 2, f"se esperaban 2 declaraciones, hay {sum(counts)}"
    for a, b in spans:
        piece = src[a:b].decode("utf-8")
        if value in piece:
            ps = len(src[:a].decode("utf-8"))
            assert len(ROP.literals_in_range(lit_spans, ps, ps + len(piece))) == 1


def test_los_cortes_caen_en_limites_utf8_validos() -> None:
    """Un corte a mitad de un multibyte produciría un tramo ilegible."""
    src = prose([
        "sección uno con ñandú y águila",
        "sección dos con über y más",
        "sección tres con 🔥 y emoji",
        "sección cuatro de cierre",
    ])
    spans = ROP.split_segment_spans(src, 0, len(src), 32, [])
    for a, b in spans:
        src[a:b].decode("utf-8")  # lanza si el corte parte un carácter


def test_una_fila_de_tabla_no_separte() -> None:
    table = prose([
        "| columna uno | columna dos |",
        "| --- | --- |",
        "| celda a | celda b |",
        "| celda c | celda d |",
        "| celda e | celda f |",
    ])
    spans = ROP.split_segment_spans(table, 0, len(table), 24, [])
    for a, b in spans:
        piece = table[a:b].decode("utf-8")
        if piece.startswith("|"):
            assert piece.rstrip("\n").endswith("|"), (
                f"una fila de tabla quedó partida: {piece!r}"
            )


def test_identificadores_de_trozo_son_estables_y_unicos() -> None:
    a = ROP.split_segment_id("seg-abc123", 0, 4)
    b = ROP.split_segment_id("seg-abc123", 0, 4)
    c = ROP.split_segment_id("seg-abc123", 1, 4)
    assert a == b, "el mismo trozo debe dar el mismo id entre ejecuciones"
    assert a != c, "trozos distintos deben tener ids distintos"
    assert a.startswith("seg-") and len(a) == len("seg-") + 8


def test_split_file_segments_marca_el_padre_como_superado() -> None:
    """El rango original conserva un propietario explícito (INV-03)."""
    src = prose([f"contenido largo de la linea {i}" for i in range(30)])
    text = src.decode("utf-8")
    file_doc = {
        "document_id": "doc-test",
        "path": "x.md",
        "segments": [{
            "segment_id": "seg-padre",
            "structural_type": "paragraph",
            "byte_range": {"start": 0, "end": len(src)},
            "translatable_text": text,
            "protected_literals": [],
            "language": "en",
        }],
    }
    segments, warnings = ROP.split_file_segments(file_doc, src, 40)
    assert warnings == []
    pieces = [s for s in segments if s.get("split_parent") == "seg-padre"]
    parent = [s for s in segments if s["segment_id"] == "seg-padre"]
    assert len(pieces) > 1
    assert len(parent) == 1
    assert parent[0]["disposition"] == "superseded_by_split"
    assert parent[0]["superseded_by"] == [p["segment_id"] for p in pieces]


def test_segmento_que_ya_cabe_no_se_toca() -> None:
    src = b"una linea corta\n"
    text = src.decode("utf-8")
    file_doc = {
        "document_id": "doc-test",
        "path": "x.md",
        "segments": [{
            "segment_id": "seg-corto",
            "byte_range": {"start": 0, "end": len(src) - 1},
            "translatable_text": "una linea corta",
            "protected_literals": [],
        }],
    }
    segments, warnings = ROP.split_file_segments(file_doc, src, 100)
    assert warnings == []
    assert len(segments) == 1
    assert segments[0]["segment_id"] == "seg-corto"
    assert "split_parent" not in segments[0]


def test_sin_corte_seguro_se_conserva_y_se_avisa() -> None:
    """No se pierde un segmento porque no haya por dónde cortarlo."""
    table = prose([
        "| aaaa | bbbb | cccc | dddd |",
        "| eeee | ffff | gggg | hhhh |",
        "| iiii | jjjj | kkkk | llll |",
    ])
    file_doc = {
        "document_id": "doc-test",
        "path": "x.md",
        "segments": [{
            "segment_id": "seg-tabla",
            "byte_range": {"start": 0, "end": len(table)},
            "translatable_text": table.decode("utf-8"),
            "protected_literals": [],
        }],
    }
    segments, warnings = ROP.split_file_segments(file_doc, table, 10)
    assert len(warnings) == 1, "un segmento indivisible debe quedar reportado"
    assert "sin corte seguro" in warnings[0]
    assert len(segments) == 1
    assert segments[0]["segment_id"] == "seg-tabla"


def test_reempaquetar_no_deja_ningun_segmento_sin_propietario_unico() -> None:
    """Defecto real: se conservaban los paquetes no-overflow del documento.

    Al reempaquetar un documento se retiraban solo sus paquetes con
    ``overflow``, y se añadía el reempaquetado completo. Los segmentos
    que no habían cambiado quedaban en dos paquetes a la vez, con dos
    propietarios, rompiendo INV-03 sin que ningún validador por paquete
    lo notara.
    """
    source = TMP / "src3"
    source.mkdir(parents=True, exist_ok=True)
    doc = source / "doc.md"
    # Una prosa larga (se parte) y una corta (no se parte) conviven en
    # el mismo documento: es justo el caso que duplicaba la propiedad.
    short = "parrafo corto que ya cabe."
    body = "\n".join(f"linea larga {i} con contenido" for i in range(40)) + "\n" + short
    doc.write_text(body, encoding="utf-8")

    raw = doc.read_bytes()
    long_end = raw.index(b"\n" + short.encode())
    segments_doc = {
        "source_root": str(source),
        "files": [{
            "document_id": "doc-1", "path": "doc.md",
            "segments": [
                {
                    "segment_id": "seg-largo",
                    "structural_type": "paragraph",
                    "byte_range": {"start": 0, "end": long_end},
                    "translatable_text": raw[:long_end].decode("utf-8"),
                    "protected_literals": [],
                },
                {
                    "segment_id": "seg-corto",
                    "structural_type": "paragraph",
                    "byte_range": {"start": long_end + 1, "end": len(raw)},
                    "translatable_text": short,
                    "protected_literals": [],
                },
            ],
        }],
    }
    packets_doc = {
        "source_root": str(source), "markers": "§§", "total_packets": 2,
        "packets": [
            {"packet_id": "pack-1", "document_id": "doc-1", "path": "doc.md",
             "owner": "pack-1", "markers": "§§", "segments": ["seg-largo"],
             "source_language": "en", "non_emitible_context": [],
             "total_chars": len(segments_doc["files"][0]["segments"][0]["translatable_text"]),
             "translatable_text": "", "translatable_text_with_markers": "",
             "overflow": True},
            {"packet_id": "pack-2", "document_id": "doc-1", "path": "doc.md",
             "owner": "pack-2", "markers": "§§", "segments": ["seg-corto"],
             "source_language": "en", "non_emitible_context": [],
             "total_chars": len(short),
             "translatable_text": short, "translatable_text_with_markers": short,
             "overflow": False},
        ],
    }
    TMP.mkdir(parents=True, exist_ok=True)
    (TMP / "s3.json").write_text(json.dumps(segments_doc), encoding="utf-8")
    (TMP / "p3.json").write_text(json.dumps(packets_doc), encoding="utf-8")
    (TMP / "prof3.json").write_text(json.dumps({"context_budget": 60}), encoding="utf-8")

    proc = subprocess.run([
        sys.executable, str(SCRIPT),
        "--source-root", str(source),
        "--packets", str(TMP / "p3.json"),
        "--segments", str(TMP / "s3.json"),
        "--profile", str(TMP / "prof3.json"),
        "--out-packets", str(TMP / "p3_v2.json"),
        "--out-segments", str(TMP / "s3_v2.json"),
    ], capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr

    out = json.loads((TMP / "p3_v2.json").read_text(encoding="utf-8"))
    counts: dict[str, int] = {}
    for packet in out["packets"]:
        for sid in packet["segments"]:
            counts[sid] = counts.get(sid, 0) + 1
    assert "pack-2" not in {p["packet_id"] for p in out["packets"]}, (
        "el paquete previo del documento no debe sobrevivir al reempaquetado"
    )
    assert [v for v in counts.values() if v > 1] == [], (
        f"algún segmento quedó en dos paquetes: {counts}"
    )


def test_count_collisions_mide_la_deuda_de_entrada() -> None:
    """Las colisiones heredadas se miden, no se reparan en silencio."""
    packets = [
        {"packet_id": "pack-a", "document_id": "doc-x", "path": "a.md", "segments": ["seg-1"]},
        {"packet_id": "pack-b", "document_id": "doc-x", "path": "b.md", "segments": ["seg-1"]},
        {"packet_id": "pack-c", "document_id": "doc-y", "path": "c.md", "segments": ["seg-2"]},
    ]
    data = ROP.count_collisions(packets)
    assert data["segments_in_multiple_packets"] == 1
    assert data["document_ids_reused_across_paths"] == 1
    assert data["paths_involved"] == 2


def test_assert_single_owner_aborta_con_segmento_duplicado() -> None:
    try:
        ROP._assert_single_owner([
            {"packet_id": "pack-a", "segments": ["seg-1"]},
            {"packet_id": "pack-b", "segments": ["seg-1"]},
        ])
    except SystemExit as exc:
        assert "dos paquetes" in str(exc)
    else:
        raise AssertionError("un segmento en dos paquetes debe abortar")


def test_check_coverage_detecta_hueco() -> None:
    """``check_coverage`` exige cubrir el rango y aborta si falta."""
    src = b"contenido\n"
    try:
        ROP.check_coverage(src, [(0, 5)], 0, len(src))
    except SystemExit as exc:
        assert "cobertura" in str(exc)
    else:
        raise AssertionError("un rango incompleto debe abortar")


def test_no_toca_la_fuente_ni_el_gsource() -> None:
    """INV-01: el script solo escribe ficheros nuevos."""
    source = TMP / "src"
    source.mkdir(parents=True, exist_ok=True)
    doc = source / "doc.md"
    body = "\n".join(f"linea {i} con texto" for i in range(40))
    doc.write_text(body, encoding="utf-8")
    original_bytes = doc.read_bytes()

    segments_doc = {
        "source_root": str(source),
        "files": [{
            "document_id": "doc-1",
            "path": "doc.md",
            "segments": [{
                "segment_id": "seg-1",
                "structural_type": "paragraph",
                "byte_range": {"start": 0, "end": len(body.encode("utf-8"))},
                "translatable_text": body,
                "protected_literals": [],
            }],
        }],
    }
    packets_doc = {
        "source_root": str(source),
        "markers": "§§",
        "total_packets": 1,
        "packets": [{
            "packet_id": "pack-1", "document_id": "doc-1", "path": "doc.md",
            "owner": "pack-1", "markers": "§§", "segments": ["seg-1"],
            "source_language": "en", "non_emitible_context": [],
            "total_chars": len(body), "translatable_text": body,
            "translatable_text_with_markers": body, "overflow": True,
        }],
    }
    profile = {"context_budget": 40}
    TMP.mkdir(parents=True, exist_ok=True)
    (TMP / "segments.json").write_text(json.dumps(segments_doc), encoding="utf-8")
    (TMP / "packets.json").write_text(json.dumps(packets_doc), encoding="utf-8")
    (TMP / "profile.json").write_text(json.dumps(profile), encoding="utf-8")
    before = {p.name: p.read_bytes() for p in (TMP / "segments.json", TMP / "packets.json")}

    proc = subprocess.run([
        sys.executable, str(SCRIPT),
        "--source-root", str(source),
        "--packets", str(TMP / "packets.json"),
        "--segments", str(TMP / "segments.json"),
        "--profile", str(TMP / "profile.json"),
        "--out-packets", str(TMP / "packets_v2.json"),
        "--out-segments", str(TMP / "segments_v2.json"),
        "--report", str(TMP / "report.json"),
    ], capture_output=True, text=True, check=False)

    assert proc.returncode == 0, proc.stderr
    assert doc.read_bytes() == original_bytes, "la fuente no puede cambiar (INV-01)"
    for name, content in before.items():
        assert (TMP / name).read_bytes() == content, f"{name} no debe modificarse"

    report = json.loads((TMP / "report.json").read_text(encoding="utf-8"))
    assert report["validation_errors"] == []
    assert report["overflow_remaining"] == 0
    assert report["documents_rewritten"] == 1


def test_dry_run_no_escribe() -> None:
    source = TMP / "src2"
    source.mkdir(parents=True, exist_ok=True)
    doc = source / "doc.md"
    doc.write_text("\n".join(f"linea {i}" for i in range(30)), encoding="utf-8")
    body = doc.read_text(encoding="utf-8")
    segments_doc = {
        "source_root": str(source),
        "files": [{
            "document_id": "doc-1", "path": "doc.md",
            "segments": [{
                "segment_id": "seg-1", "byte_range": {"start": 0, "end": len(body.encode())},
                "translatable_text": body, "protected_literals": [],
            }],
        }],
    }
    packets_doc = {
        "source_root": str(source), "markers": "§§", "total_packets": 1,
        "packets": [{
            "packet_id": "pack-1", "document_id": "doc-1", "path": "doc.md",
            "owner": "pack-1", "markers": "§§", "segments": ["seg-1"],
            "source_language": "en", "non_emitible_context": [],
            "total_chars": len(body), "translatable_text": body,
            "translatable_text_with_markers": body, "overflow": True,
        }],
    }
    TMP.mkdir(parents=True, exist_ok=True)
    (TMP / "s2.json").write_text(json.dumps(segments_doc), encoding="utf-8")
    (TMP / "p2.json").write_text(json.dumps(packets_doc), encoding="utf-8")
    (TMP / "prof2.json").write_text(json.dumps({"context_budget": 40}), encoding="utf-8")
    out = TMP / "nunca_v2.json"
    if out.exists():
        out.unlink()

    proc = subprocess.run([
        sys.executable, str(SCRIPT),
        "--source-root", str(source),
        "--packets", str(TMP / "p2.json"),
        "--segments", str(TMP / "s2.json"),
        "--profile", str(TMP / "prof2.json"),
        "--out-packets", str(out),
        "--out-segments", str(TMP / "nunca_seg_v2.json"),
        "--dry-run",
    ], capture_output=True, text=True, check=False)

    assert proc.returncode == 0, proc.stderr
    assert not out.exists(), "--dry-run no debe escribir la salida"