"""Subdivide paquetes que exceden el presupuesto del perfil (fase 050).

Un paquete se marca ``overflow: true`` cuando sus segmentos no caben
en ``context_budget``. En el corpus beta los 191 paquetes con
``overflow`` contienen **un solo segmento** cada uno, y ese segmento es
una prosa larga: partir por segmento no las divide, porque no hay más
segmentos que repartir.

La unidad de corte correcta es la **línea**, no el segmento. Este script
parte el ``byte_range`` del segmento en trozos consecutivos que:

- respetan el presupuesto del perfil;
- no cortan un literal protegido por la mitad;
- no cortan una fila de tabla por la mitad;
- no separan una celda de su fila;
- conservan los rangos de bytes de la fuente, sin huecos ni solapamientos.

Cada trozo se emite como un segmento nuevo con su propio ``segment_id``
derivado del original, y los segmentos originales se conservan con
``disposition: superseded_by_split`` para que el rango original conserve
un propietario explícito (INV-03).

Los trozos se vuelven a empaquetar con ``packetize.pack_file``, de modo
que heredan el mismo contrato que el resto del corpus: marcadores de
protección, ``owner``, ``non_emitible_context`` y validación de
literales.

No modifica la fuente (INV-01), ni ``segments_resolved.json``, ni el
glosario. Escribe ficheros nuevos y deja el original intacto.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from packetize import build_packet_markers, pack_file, validate_packet  # noqa: E402


# Una fila de tabla GFM es una línea que empieza y termina en ``|``.
_TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")
# Una celda suelta no debe quedar sin su fila.
_TABLE_CELL_RE = re.compile(r"^\s*\|")


def split_segment_id(parent_id: str, index: int, total: int) -> str:
    """Identificador estable y determinista para un trozo."""
    payload = f"{parent_id}:{index}:{total}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:8]
    return f"seg-{digest}"


def byte_offsets(raw: bytes, text: str) -> list[int]:
    """``offsets[i]`` es el offset de byte del carácter ``i`` en ``raw``.

    ``offsets[len(text)]`` es ``len(raw)``. Construido con el
    desplazamiento real de cada carácter, no con una suma de longitudes,
    para que un multibyte no desplace los cortes.
    """
    offsets = [0] * (len(text) + 1)
    b = 0
    for i, ch in enumerate(text):
        offsets[i] = b
        b += len(ch.encode("utf-8"))
    offsets[len(text)] = b
    return offsets


def _drop_empty(spans: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Quita tramos vacíos sin fusionar los contiguos.

    Fusionar vecinos volvería a reconstruir el segmento original y
    anularía la partición, así que aquí solo se descartan los tramos de
    longitud cero.
    """
    return [(a, b) for a, b in spans if b > a]


def literals_in_range(
    literal_char_spans: list[tuple[int, int, dict]],
    piece_start_char: int,
    piece_end_char: int,
) -> list[dict]:
    """Literales protegidos que caen enteros dentro de este trozo.

    Cada entrada se asigna al tramo que contiene **su propio** rango, no
    al primero que contenga ese texto. Un mismo literal puede repetirse
    en un segmento, y dos entradas con el mismo valor tienen rangos
    distintos: buscar por valor declararía ambas en el primer tramo,
    duplicaría los marcadores y el segundo tramo se quedaría sin
    declarar su copia.
    """
    out: list[dict] = []
    for start_char, end_char, lit in literal_char_spans:
        if start_char >= piece_start_char and end_char <= piece_end_char:
            out.append(lit)
    return out


def split_file_segments(
    file_doc: dict,
    source_bytes: bytes,
    budget: int,
) -> tuple[list[dict], list[str]]:
    """Divide los segmentos sobredimensionados de un documento.

    Devuelve ``(segmentos_nuevos, avisos)``. Los segmentos que ya caben
    se devuelven intactos.
    """
    new_segments: list[dict] = []
    warnings: list[str] = []

    for seg in file_doc.get("segments", []):
        text = seg.get("translatable_text") or ""
        br = seg.get("byte_range") or {}
        if not text or "start" not in br or len(text) <= budget:
            new_segments.append(seg)
            continue

        start, end = br["start"], br["end"]
        spans = split_segment_with_budget(
            source_bytes, start, end, budget, seg.get("protected_literals") or []
        )
        check_coverage(source_bytes, spans, start, end)

        if len(spans) <= 1:
            # No se pudo partir sin romper estructura. Se conserva y se
            # avisa: no se pierde el segmento ni se inventa un corte.
            new_segments.append(seg)
            warnings.append(
                f"{seg['segment_id']}: {len(text)} chars sin corte seguro; conservado"
            )
            continue

        # Cada literal se sitúa en caracteres del segmento a partir de su
        # propio byte_range. La conversión pasa por los bytes reales
        # porque el offset del literal es de bytes y el corte se mide en
        # caracteres.
        literal_spans = []
        for lit in seg.get("protected_literals") or []:
            lbr = lit.get("byte_range") or {}
            if "start" not in lbr or "end" not in lbr:
                continue
            lit_start_char = len(source_bytes[start:lbr["start"]].decode("utf-8"))
            lit_end_char = len(source_bytes[start:lbr["end"]].decode("utf-8"))
            literal_spans.append((lit_start_char, lit_end_char, lit))

        total = len(spans)
        for idx, (sub_start, sub_end) in enumerate(spans):
            sub_text = source_bytes[sub_start:sub_end].decode("utf-8")
            if not sub_text.strip():
                continue
            piece_start_char = len(source_bytes[start:sub_start].decode("utf-8"))
            piece_end_char = piece_start_char + len(sub_text)
            piece = dict(seg)
            piece["segment_id"] = split_segment_id(seg["segment_id"], idx, total)
            piece["byte_range"] = {"start": sub_start, "end": sub_end}
            piece["translatable_text"] = sub_text
            piece["protected_literals"] = literals_in_range(
                literal_spans, piece_start_char, piece_end_char
            )
            piece["split_parent"] = seg["segment_id"]
            piece["split_index"] = idx
            piece["split_total"] = total
            new_segments.append(piece)

        new_segments.append({
            "segment_id": seg["segment_id"],
            "disposition": "superseded_by_split",
            "language": seg.get("language"),
            "confidence": seg.get("confidence"),
            "byte_range": {"start": start, "end": end},
            "translatable_text": "",
            "protected_literals": [],
            "superseded_by": [split_segment_id(seg["segment_id"], i, total) for i in range(total)],
            "structural_type": seg.get("structural_type"),
        })

    return new_segments, warnings


def split_segment_with_budget(
    source_bytes: bytes,
    start: int,
    end: int,
    budget: int,
    protected: list[dict],
) -> list[tuple[int, int]]:
    """Trocea ``[start, end)`` en tramos que caben en ``budget``.

    Punto de entrada usado por ``split_file_segments``. Los tramos son
    consecutivos, no se solapan y cubren todo el rango original salvo, si
    el último punto seguro lo impide, una cola que se reporta aparte.
    """
    return split_segment_spans(source_bytes, start, end, budget, protected)


def split_segment_spans(
    source_bytes: bytes,
    start: int,
    end: int,
    budget: int,
    protected: list[dict],
) -> list[tuple[int, int]]:
    """Trocea ``[start, end)`` en tramos consecutivos dentro de ``budget``.

    Convención alineada con ``prepare.narrow_range_to_text``: el texto de
    un segmento **no** incluye el salto de línea final. Por eso cada
    tramo acaba en el último carácter de su última línea y el ``\\n``
    que la sigue queda fuera del rango, como ya ocurre en el corpus.
    """
    raw = source_bytes[start:end]
    text = raw.decode("utf-8")
    offsets = byte_offsets(raw, text)

    protected_spans: list[tuple[int, int]] = []
    for lit in protected:
        value = lit.get("value") or ""
        if not value:
            continue
        for m in re.finditer(re.escape(value), text):
            protected_spans.append((m.start(), m.end()))
    protected_spans.sort()

    lines = text.split("\n")
    # (inicio_char, fin_char) de cada línea, sin el salto que la sigue.
    line_spans: list[tuple[int, int]] = []
    cursor = 0
    for line in lines:
        line_spans.append((cursor, cursor + len(line)))
        cursor += len(line) + 1

    def is_safe(line_idx: int) -> bool:
        """La línea puede cerrar un tramo sin partir nada protegido.

        No se corta en mitad de un literal protegido ni dentro de una
        fila de tabla GFM. Una celda suelta tampoco cierra un tramo:
        una tabla debe Viajar completa o partirse por filas, no por
        celdas sueltas.
        """
        a, b = line_spans[line_idx]
        for ps, pe in protected_spans:
            if ps < b < pe:
                return False
        line = lines[line_idx]
        if _TABLE_ROW_RE.match(line) or _TABLE_CELL_RE.match(line):
            return False
        return True

    spans: list[tuple[int, int]] = []
    cur_start = 0          # inicio del tramo en curso, en caracteres
    first_line = 0         # primera línea que pertenece al tramo
    cur_chars = 0          # prosa acumulada del tramo, saltos incluidos
    last_safe_idx: int | None = None

    for idx, (a, b) in enumerate(line_spans):
        line_chars = b - a

        # El salto que une esta línea con la anterior solo cuenta si esa
        # línea anterior ya estaba dentro del tramo en curso.
        separator = 1 if idx > first_line else 0

        if cur_chars + separator + line_chars > budget and last_safe_idx is not None:
            cut_end = line_spans[last_safe_idx][1]
            spans.append((start + offsets[cur_start], start + offsets[cut_end]))
            # El salto tras la última línea del tramo queda fuera del
            # rango: es un hueco que ``assemble.py`` copia literal.
            cur_start = cut_end + 1
            first_line = idx
            cur_chars = 0
            last_safe_idx = None
            separator = 0

        cur_chars += separator + line_chars
        if is_safe(idx):
            last_safe_idx = idx

    spans.append((start + offsets[cur_start], start + offsets[len(text)]))
    return _drop_empty(spans)


def _drop_empty(spans: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """Quita tramos vacíos sin fusionar los contiguos.

    Fusionar vecinos volvería a reconstruir el segmento original y
    anularía la partición, así que aquí solo se descartan los tramos de
    longitud cero, que pueden aparecer cuando el corte cae al final.
    """
    return [(a, b) for a, b in spans if b > a]


def check_coverage(
    source_bytes: bytes, spans: list[tuple[int, int]], start: int, end: int
) -> None:
    """Verifica que los tramos cubren el rango sin solapes ni prosa perdida.

    Los tramos no son contiguos: entre dos consecutivos queda el salto de
    línea que unía las líneas partidas. Ese hueco mide exactamente un
    byte y contiene solo ``\\n``. Cualquier hueco más ancho significaría
    prosa fuera del rango de todo segmento, y cualquier solape
    reescribiría prosa ya cubierta.
    """
    if not spans:
        raise SystemExit(f"cobertura rota: no hay tramos para el rango {start}-{end}")

    cursor = start
    for a, b in spans:
        if a < cursor:
            raise SystemExit(
                f"solape: el tramo empieza en {a} y el anterior acaba en {cursor}"
            )
        gap = source_bytes[cursor:a]
        if gap not in (b"", b"\n"):
            raise SystemExit(
                f"hueco de {len(gap)} bytes entre {cursor} y {a}: solo puede faltar un salto"
            )
        cursor = b

    if cursor != end:
        raise SystemExit(
            f"cobertura incompleta: último tramo acaba en {cursor}, esperaba {end}"
        )


def _assert_single_owner(packets: list[dict]) -> None:
    """Cada segmento puede pertenecer a un solo paquete (INV-03).

    Reempaquetar un documento sin retirar sus paquetes anteriores
    duplicaría la propiedad de los segmentos que no cambian. Es un
    fallo silencioso: los validadores por paquete seguirían en verde
    porque cada paquete es válido por separado.
    """
    seen: dict[str, str] = {}
    for packet in packets:
        pid = packet["packet_id"]
        for sid in packet.get("segments", []):
            if sid in seen:
                raise SystemExit(
                    f"segmento {sid} en dos paquetes: {seen[sid]} y {pid}"
                )
            seen[sid] = pid


def count_collisions(packets: list[dict]) -> dict:
    """Segmentos que aparecen en más de un paquete, por id y por valor.

    El corpus beta ya traía esta condición antes de cualquier subdivisión:
    ``prepare`` reutiliza ``document_id`` entre archivos casi idénticos
    (páginas stub de tailwindcss y faq de Angular), de modo que un mismo
    ``segment_id`` pertenece a varios documentos. Se mide y se reporta;
    no lo arregla este script, porque rehacer los identificadores
    invalidaría el manifiesto y el trabajo ya traducido.
    """
    by_segment: dict[str, list[str]] = {}
    by_document: dict[str, set[str]] = {}
    for packet in packets:
        for sid in packet.get("segments", []):
            by_segment.setdefault(sid, []).append(packet["packet_id"])
            by_document.setdefault(packet["document_id"], set()).add(sid)
    shared = {sid: pids for sid, pids in by_segment.items() if len(pids) > 1}
    docs_with_paths: dict[str, set[str]] = {}
    for packet in packets:
        docs_with_paths.setdefault(packet["document_id"], set()).add(packet["path"])
    reused_docs = {d: sorted(p) for d, p in docs_with_paths.items() if len(p) > 1}
    return {
        "segments_in_multiple_packets": len(shared),
        "document_ids_reused_across_paths": len(reused_docs),
        "paths_involved": sum(len(p) for p in reused_docs.values()),
        "examples": sorted(shared)[:5],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="rebuild_overflow_packets.py")
    p.add_argument("--source-root", required=True)
    p.add_argument("--packets", required=True, help="packets.json con overflow: true")
    p.add_argument("--segments", required=True, help="segments_resolved.json")
    p.add_argument("--profile", required=True)
    p.add_argument("--out-packets", required=True, help="packets_v2.json a escribir")
    p.add_argument("--out-segments", required=True, help="segments_v2.json a escribir")
    p.add_argument("--report", help="Reporte JSON de la subdivisión.")
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args(argv)


def load_budget(profile_path: Path) -> int:
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    return int(profile.get("context_budget", 8000))


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source_root = Path(args.source_root)
    budget = load_budget(Path(args.profile))

    packets_doc = json.loads(Path(args.packets).read_text(encoding="utf-8"))
    segments_doc = json.loads(Path(args.segments).read_text(encoding="utf-8"))
    markers = packets_doc.get("markers", "§§")

    overflow_docs = {
        p["document_id"] for p in packets_doc.get("packets", []) if p.get("overflow")
    }

    new_files: list[dict] = []
    warnings: list[str] = []
    split_count = 0
    piece_count = 0
    verified_docs = 0

    for file_doc in segments_doc.get("files", []):
        if file_doc["document_id"] not in overflow_docs:
            new_files.append(file_doc)
            continue

        source_path = source_root / file_doc["path"]
        source_bytes = source_path.read_bytes()

        new_segments, doc_warnings = split_file_segments(file_doc, source_bytes, budget)
        warnings.extend(f"{file_doc['path']}: {w}" for w in doc_warnings)
        split_count += sum(
            1 for s in new_segments if s.get("split_parent")
        )
        piece_count += len(new_segments)

        # Verificación de identidad por documento: cada trozo releído
        # debe ser exactamente el tramo que sustituye.
        for seg in new_segments:
            if not seg.get("split_parent"):
                continue
            br = seg["byte_range"]
            piece = source_bytes[br["start"]:br["end"]].decode("utf-8").rstrip("\n")
            if piece != seg["translatable_text"]:
                raise SystemExit(
                    f"identidad rota en {seg['segment_id']}: el trozo no relee su rango"
                )
        verified_docs += 1

        rebuilt_doc = dict(file_doc)
        rebuilt_doc["segments"] = new_segments
        new_files.append(rebuilt_doc)

    out_segments = dict(segments_doc)
    out_segments["files"] = new_files
    out_segments["split_by"] = {
        "script": "rebuild_overflow_packets.py",
        "source_packets": str(args.packets),
        "budget": budget,
    }

    # Reempaquetar los documentos tocados con el mismo contrato.
    touched = {
        f["document_id"] for f in new_files
        if any(s.get("split_parent") for s in f.get("segments", []))
    }

    # Un documento reescrito se reempaqueta entero: se retiran TODOS sus
    # paquetes previos, no solo los que tenían overflow. Conservar los
    # no-overflow junto a los nuevos dejaría el mismo segmento en dos
    # paquetes, con dos propietarios, y rompe INV-03.
    new_packets: list[dict] = [
        p for p in packets_doc.get("packets", [])
        if p["document_id"] not in touched
    ]

    files_by_id = {f["document_id"]: f for f in new_files}
    validation_errors: list[dict] = []
    rebuilt_packets: list[dict] = []
    for doc_id in sorted(touched):
        pkts, errs = pack_file(files_by_id[doc_id], budget, markers)
        rebuilt_packets.extend(pkts)
        validation_errors.extend(errs)
    new_packets.extend(rebuilt_packets)

    # El guard solo vigila lo que este script genera. Las colisiones que
    # ya trae el corpus se miden aparte: son una deuda de entrada que
    # este script no puede corregir sin invalidar el manifiesto.
    _assert_single_owner(rebuilt_packets)
    collisions = count_collisions(new_packets)
    collisions["pre_existing"] = count_collisions(packets_doc.get("packets", []))

    out_packets = {
        "source_root": packets_doc.get("source_root"),
        "context_budget": budget,
        "markers": markers,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        "derived_from": str(args.packets),
        "total_packets": len(new_packets),
        "validation_errors": validation_errors,
        "packets": new_packets,
    }

    remaining_overflow = [p for p in new_packets if p.get("overflow")]
    by_packet_chars = sorted(p["total_chars"] for p in new_packets)

    report = {
        "budget": budget,
        "documents_rewritten": len(touched),
        "documents_verified_identity": verified_docs,
        "split_pieces": split_count,
        "warnings": warnings,
        "validation_errors": validation_errors,
        "packets_before": packets_doc.get("total_packets"),
        "packets_after": len(new_packets),
        "overflow_remaining": len(remaining_overflow),
        "overflow_packet_ids": [p["packet_id"] for p in remaining_overflow][:50],
        "median_packet_chars": by_packet_chars[len(by_packet_chars) // 2] if by_packet_chars else 0,
        "max_packet_chars": by_packet_chars[-1] if by_packet_chars else 0,
        "collisions": collisions,
        "applied": not args.dry_run,
    }

    if not args.dry_run:
        for target, payload in ((Path(args.out_packets), out_packets),
                                (Path(args.out_segments), out_segments),
                                (Path(args.report), report) if args.report else (None, None)):
            if target is None:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp = target.with_suffix(target.suffix + ".tmp")
            tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
            os.replace(tmp, target)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if validation_errors else 0


if __name__ == "__main__":
    sys.exit(main())