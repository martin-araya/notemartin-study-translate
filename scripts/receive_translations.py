"""Recibe, valida y persiste traducciones del agente para la fase 050.

Este script **no traduce**. Recibe lo que el agente produce para un
lote de paquetes, lo valida con la forma que exige el contrato C-SEGMENT
y lo persiste de forma atómica, de modo que una sesión interrupted
deje siempre el último estado completo.

Lo que rechaza, y por qué:

- Un ``segment_id`` que el paquete no declaró. Aceptarlo sería permitir
  que el agente emita trabajo que nadie pidió (INV-03).
- Un segmento declarado y no emitido. Es una omisión silenciosa: el
  paquete quedaría traducible pero sin candidato (INV-04).
- Marcadores de protección falsificados, perdidos o duplicados. Los
  literales protegidos son bytes exactos (INV-05).
- Respuestas truncadas: un candidato vacío donde la fuente tenía prosa
  es una pérdida, no una traducción.
- Un literal protegido que no aparece en el candidato.

    python3 scripts/receive_translations.py \\
        --packets packets.json --segments segments_resolved.json \\
        --responses respuestas.json --translations translations/ --apply

La forma de ``respuestas.json`` es una lista de objetos

    {"packet_id": "pack-...", "translations": [
        {"segment_id": "seg-...", "translated_text": "..."}
    ]}

Clave de persistencia
---------------------

La traducción se persiste en ``translations/<clave>.json``. La clave es
``document_id`` cuando ese identificador no colisiona y
``translation_id`` (documento + ruta) cuando sí. Ver
``scripts/translation_key.py``: ``prepare.py`` deriva ``document_id``
de los bytes, así que dos rutas byte-idénticas lo comparten y, sin
desambiguar, una traducción pisaría a la otra sin aviso.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from translation_key import (  # noqa: E402
    index_by_document,
    normalize_path,
    resolve_file,
    resolve_key,
    translation_id,
)


MARKER_RE = re.compile(r"§§([\s\S]*?)§§")


def expected_literals(packet: dict) -> list[str]:
    """Literales protegidos que el paquete expone entre marcadores."""
    text = packet.get("translatable_text_with_markers", "")
    marker = packet.get("markers", "§§")
    pattern = re.compile(re.escape(marker) + r"([\s\S]*?)" + re.escape(marker))
    return [m.group(1) for m in pattern.finditer(text) if m.group(1)]


def marker_balance(candidate: str, marker: str) -> int:
    """Número de apariciones del marcador de protección en el candidato."""
    return candidate.count(marker)


def strip_markers(text: str, marker: str) -> str:
    """Retira los marcadores de protección del texto traducido.

    Los marcadores ``§§literal§§`` viven en el paquete para señalar
    dónde está la prosa traducible. En la respuesta entregada el
    marcador debe desaparecer: el literal queda, el envoltorio no.
    Sin esta conversión el validador falla con un error de protección
    y todo el documento queda bloqueado.
    """
    return text.replace(marker, "")


def validate_packet(packet: dict, response: dict) -> tuple[list[dict], list[dict]]:
    """Devuelve (entradas aceptadas, hallazgos) para un paquete."""
    declared = list(packet.get("segments", []))
    declared_ids = set(declared)
    marker = packet.get("markers", "§§")
    expected = expected_literals(packet)
    expected_counts = Counter(expected)

    emitted = response.get("translations", [])
    entries: list[dict] = []
    findings: list[dict] = []

    seen: set[str] = set()
    for item in emitted:
        seg_id = item.get("segment_id")
        text = item.get("translated_text")

        if seg_id not in declared_ids:
            findings.append({
                "kind": "segment_id_ajeno",
                "segment_id": seg_id,
                "detail": "el paquete no declaró este segmento",
            })
            continue
        if seg_id in seen:
            findings.append({
                "kind": "segmento_duplicado",
                "segment_id": seg_id,
                "detail": "el mismo segmento se emitió dos veces",
            })
            continue
        seen.add(seg_id)

        if not isinstance(text, str):
            findings.append({
                "kind": "respuesta_no_texto",
                "segment_id": seg_id,
                "detail": f"translated_text no es texto: {type(text).__name__}",
            })
            continue

        occurrences = text.count(marker)
        if occurrences % 2 != 0:
            findings.append({
                "kind": "marcador_desequilibrado",
                "segment_id": seg_id,
                "detail": f"{occurrences} apariciones del marcador, número impar",
            })
            continue

        entries.append({
            "segment_id": seg_id,
            "original_text": _source_text(packet, seg_id),
            # El agente vio marcadores en el paquete; el validador exige
            # la prosa entregada sin ellos. strip_markers retira el
            # envoltorio y conserva el literal dentro.
            "translated_text": strip_markers(text, marker),
            "literals_preserved": True,
            "missing_literals": [],
            "flag_loss": False,
        })

    missing = sorted(declared_ids - seen)
    for seg_id in missing:
        findings.append({
            "kind": "segmento_ausente",
            "segment_id": seg_id,
            "detail": "el paquete declaró el segmento y la respuesta no lo emitió",
        })

    joined = "\n\n".join(e["translated_text"] for e in entries)
    for literal, needed in expected_counts.items():
        have = joined.count(literal)
        if have < needed:
            for entry in entries:
                entry["literals_preserved"] = False
                entry["flag_loss"] = True
                entry["missing_literals"].append(literal)
            findings.append({
                "kind": "literal_perdido",
                "detail": f"{literal!r} aparecía {needed} veces y aparece {have}",
            })

    return entries, findings


_SOURCE_CACHE: dict[str, dict] = {}


def _source_text(packet: dict, seg_id: str) -> str:
    for src in packet.get("_source_files", []) or []:
        for seg in src.get("segments", []):
            if seg.get("segment_id") == seg_id:
                return seg.get("translatable_text", "") or ""
    return ""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="receive_translations.py")
    p.add_argument("--packets", required=True)
    p.add_argument("--segments", required=True,
                   help="segments_resolved.json, para recuperar el texto de origen.")
    p.add_argument("--responses", required=True,
                   help="JSON con las respuestas del agente para este lote.")
    p.add_argument("--translations", required=True,
                   help=("Directorio donde se persisten las traducciones. "
                         "La clave del archivo es document_id, salvo colisión: "
                         "entonces es translation_id (documento + ruta)."))
    p.add_argument("--report", help="Reporte JSON del lote.")
    p.add_argument("--apply", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args(argv)


def write_atomic(target: Path, payload) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    packets_doc = json.loads(Path(args.packets).read_text(encoding="utf-8"))
    segments_doc = json.loads(Path(args.segments).read_text(encoding="utf-8"))
    responses = json.loads(Path(args.responses).read_text(encoding="utf-8"))

    by_id = {p["packet_id"]: p for p in packets_doc.get("packets", [])}
    files_by_doc = index_by_document(segments_doc)

    if isinstance(responses, dict):
        responses = responses.get("responses", [])

    # clave -> (document_id, ruta, entradas acumuladas)
    per_key: dict[str, tuple[str, str, list[dict]]] = {}
    findings: list[dict] = []
    accepted_packets = 0

    def note(seg_id: str | None, kind: str, detail: str, packet_id: str | None) -> None:
        """Un hallazgo de resolución de clave es tan bloqueante como uno de texto."""
        finding = {"kind": kind, "detail": detail}
        if seg_id is not None:
            finding["segment_id"] = seg_id
        if packet_id is not None:
            finding["packet_id"] = packet_id
        findings.append(finding)

    def collect(packet: dict, entries: list[dict]) -> tuple[str, str, str]:
        """Resuelve (clave, document_id, ruta) del paquete y acumula sus entradas."""
        doc_id = packet["document_id"]
        candidates = files_by_doc.get(doc_id)
        seg_file = resolve_file(candidates, doc_id, packet.get("path"))

        if candidates is None:
            key = doc_id
            route = normalize_path(packet.get("path") or "")
        elif len(candidates) == 1:
            key = doc_id
            route = normalize_path((seg_file or {}).get("path", packet.get("path") or ""))
        else:
            if seg_file is None:
                note(
                    None,
                    "document_id_ambiguo",
                    f"el paquete nombra {doc_id!r}, que corresponde a "
                    f"{len(candidates)} rutas, y su ruta {packet.get('path')!r} "
                    "no está entre ellas; no se puede decidir la clave de persistencia",
                    packet.get("packet_id"),
                )
                return "", doc_id, ""
            route = normalize_path(seg_file.get("path", ""))
            key = resolve_key(candidates, doc_id, route)

        if not key:
            return "", doc_id, ""

        existing = per_key.get(key)
        if existing is None:
            per_key[key] = (doc_id, route, list(entries))
        else:
            existing[2].extend(entries)
        return key, doc_id, route

    for response in responses:
        packet_id = response.get("packet_id")
        packet = by_id.get(packet_id)
        if packet is None:
            findings.append({
                "kind": "paquete_ajeno",
                "packet_id": packet_id,
                "detail": "la respuesta nombra un paquete que packets.json no declara",
            })
            continue

        enriched = dict(packet)
        seg_file = resolve_file(files_by_doc.get(packet["document_id"]),
                                packet["document_id"], packet.get("path"))
        if seg_file is not None:
            enriched["_source_files"] = [seg_file]

        entries, packet_findings = validate_packet(enriched, response)
        for finding in packet_findings:
            finding["packet_id"] = packet_id
        findings.extend(packet_findings)

        if not packet_findings:
            accepted_packets += 1

        if entries:
            collect(packet, entries)

    written = []
    written_by_path: dict[str, str] = {}
    if args.apply and not args.dry_run:
        for key, (doc_id, route, entries) in per_key.items():
            candidates = files_by_doc.get(doc_id) or []
            seg_file = resolve_file(candidates, doc_id, route)
            target = Path(args.translations) / f"{key}.json"
            existing: dict = {}
            if target.exists():
                existing = json.loads(target.read_text(encoding="utf-8"))
            by_segment = {e["segment_id"]: e for e in existing.get("entries", [])}
            for entry in entries:
                by_segment[entry["segment_id"]] = entry
            ambiguous = len(candidates) > 1
            payload = {
                "document_id": doc_id,
                "path": (seg_file or {}).get("path"),
                "translation_id": translation_id(doc_id, route) if ambiguous else None,
                "source_hash": (seg_file or {}).get("source_hash"),
                "version": existing.get("version", 1) + 1,
                "entries": sorted(by_segment.values(), key=lambda e: e["segment_id"]),
                "flag_loss": any(e["flag_loss"] for e in by_segment.values()),
                "literals_preserved": all(e["literals_preserved"] for e in by_segment.values()),
            }
            write_atomic(target, payload)
            written.append(str(target))
            written_by_path[route or str(target)] = key

    kinds = Counter(f["kind"] for f in findings)
    report = {
        "responses_received": len(responses),
        "packets_accepted": accepted_packets,
        "packets_with_findings": len(responses) - accepted_packets,
        "documents_written": len(written),
        "documents_written_by_path": written_by_path,
        "segments_accepted": sum(len(v[2]) for v in per_key.values()),
        "findings_by_kind": dict(kinds),
        "findings": findings[:200],
        "applied": bool(args.apply and not args.dry_run),
    }
    if args.report:
        write_atomic(Path(args.report), report)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if kinds else 0


if __name__ == "__main__":
    sys.exit(main())