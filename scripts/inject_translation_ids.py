"""Inyecta `translation_id` y repara los `packet_id` duplicados.

`packets_v2.json` se construyó antes de detectar que `document_id`
colisiona (ver `scripts/translation_key.py`). Los paquetes ya llevan
`path`, de modo que la clave de persistencia se puede calcular sin
volver a empaquetar 6 927 paquetes: el texto de cada paquete no cambia,
no se vuelve a leer la fuente y no se regenera ningún `segment_id`.

Repara además una segunda colisión, de la misma raíz: `packet_id` se
derivaba de `document_id` + `segment_id`, y ambos derivan de los bytes.
Dos archivos byte-idénticos producían el mismo `packet_id`, de modo que
`receive_translations.py`, que indexa los paquetes en un dict por id,
resolvía una respuesta al último del grupo y perdía el trabajo de los
demás sin emitir ningún hallazgo. `scripts/packetize.py` ya no genera
esa colisión; aquí solo se reparan los paquetes existentes.

    python3 scripts/inject_translation_ids.py \\
        --packets packets_v2.json --segments segments_v2.json \\
        --out packets_v3.json --report reports/inject.json

Salida:

- ``packets_v3.json`` con ``translation_id`` y ``path`` por paquete, y
  con ``packet_id`` rehashed en los que colisionaban. Los paquetes no
  ambiguos llevan ``translation_id: null``, porque su clave de
  persistencia sigue siendo ``document_id``.
- ``packet_id_renames``: mapa ``id_viejo -> id_nuevo`` para las respuestas
  ya escritas contra el id anterior.
- Un informe con las colisiones medidas y dos comprobaciones de
  integridad que declaran fallo si queda alguna.

El original no se toca (INV-01 aplicado a los artefactos de trabajo).
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from translation_key import (  # noqa: E402
    collision_report,
    index_by_document,
    normalize_path,
    resolve_file,
    resolve_key,
    translation_id,
)


def inject(packets_doc: dict, segments_doc: dict) -> tuple[dict, dict]:
    """Devuelve (paquetes anotados, informe)."""
    files_by_doc = index_by_document(segments_doc)
    out_packets: list[dict] = []
    unresolved: list[dict] = []
    remapped = 0
    unchanged = 0

    for pkt in packets_doc.get("packets", []):
        doc_id = pkt.get("document_id", "")
        candidates = files_by_doc.get(doc_id) or []
        seg_file = resolve_file(candidates, doc_id, pkt.get("path"))

        if not candidates:
            # El paquete nombra un documento que segments no conoce.
            # Se conserva el `document_id` como clave y se avisa: es
            # mejor un aviso que un cambio silencioso de nombre.
            unresolved.append({
                "packet_id": pkt.get("packet_id"),
                "document_id": doc_id,
                "path": pkt.get("path"),
                "detail": "document_id ausente de segments; se conserva document_id como clave",
            })
            annotated = dict(pkt)
            annotated.setdefault("path", "")
            annotated["translation_id"] = None
        elif seg_file is None:
            unresolved.append({
                "packet_id": pkt.get("packet_id"),
                "document_id": doc_id,
                "path": pkt.get("path"),
                "detail": f"document_id ambiguo entre {len(candidates)} rutas; la ruta del paquete no está entre ellas",
            })
            annotated = dict(pkt)
            annotated["translation_id"] = None
        elif len(candidates) == 1:
            annotated = dict(pkt)
            annotated["path"] = seg_file.get("path", pkt.get("path", ""))
            annotated["translation_id"] = None
            unchanged += 1
        else:
            annotated = dict(pkt)
            annotated["path"] = seg_file.get("path", pkt.get("path", ""))
            annotated["translation_id"] = translation_id(doc_id, annotated["path"])
            remapped += 1

        out_packets.append(annotated)

    # packet_id duplicado: dos paquetes con el mismo id son la misma
    # unidad de trabajo para quien responde. Se rehashean usando la clave
    # que ya distingue la ruta, de modo que la fórmula queda libre de
    # colisión por construcción.
    by_packet_id: dict[str, list[dict]] = {}
    for pkt in out_packets:
        by_packet_id.setdefault(pkt.get("packet_id", ""), []).append(pkt)

    renames: dict[str, list[str]] = {}
    renamed_packets = 0
    for packet_id, group in by_packet_id.items():
        if len(group) < 2:
            continue
        for pkt in group:
            key = pkt.get("translation_id") or pkt.get("path") or ""
            new_id = "pack-" + hashlib.sha256(
                f"{key}|{','.join(pkt.get('segments', []))}".encode("utf-8")
            ).hexdigest()[:8]
            old_id = pkt.get("packet_id")
            pkt["previous_packet_id"] = old_id
            pkt["packet_id"] = new_id
            if new_id != old_id:
                # Un id viejo puede renombrarse a varios: doce stubs
                # compartían `pack-13a84a72`. Un mapa de uno a uno
                # perdería doce de esos doce.
                renames.setdefault(old_id, []).append(new_id)
                renamed_packets += 1

    duplicate_packet_ids = {
        pid: [p.get("path") for p in group]
        for pid, group in by_packet_id.items() if len(group) > 1
    }

    # Invariante de propietario único (INV-03) sobre las claves nuevas:
    # un (translation_id, segment_id) no puede aparecer en dos paquetes.
    owners: dict[tuple[str, str], list[str]] = {}
    for pkt in out_packets:
        key = pkt.get("translation_id") or pkt.get("document_id")
        for sid in pkt.get("segments", []):
            owners.setdefault((key, sid), []).append(pkt.get("packet_id", "?"))
    duplicated = {k: v for k, v in owners.items() if len(v) > 1}

    # Y sobre (path, segment_id), que es la identidad real del archivo.
    owners_by_path: dict[tuple[str, str], list[str]] = {}
    for pkt in out_packets:
        route = normalize_path(pkt.get("path", ""))
        for sid in pkt.get("segments", []):
            owners_by_path.setdefault((route, sid), []).append(pkt.get("packet_id", "?"))
    duplicated_by_path = {k: v for k, v in owners_by_path.items() if len(v) > 1}

    # Y el id de paquete, que es la unidad de trabajo que nombra el agente.
    id_counts = Counter(p.get("packet_id", "") for p in out_packets)
    remaining_duplicate_ids = {pid: n for pid, n in id_counts.items() if n > 1}

    out_doc = dict(packets_doc)
    out_doc["packets"] = out_packets
    out_doc["translation_id_injected_at"] = datetime.datetime.now(
        datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out_doc["packet_id_renames"] = renames
    out_doc["derived_from"] = packets_doc.get("derived_from") or {
        "tool": "inject_translation_ids.py",
        "packets_injected": None,
        "reason": (
            "Los paquetes no se reempaquetaron: ya declaraban la ruta y el "
            "texto, y la colisión de document_id se resuelve solo en la "
            "clave de persistencia. Reempaquetar habría regenerado packet_id "
            "sin ganancia. Los packet_id duplicados sí se renombraron, y "
            "packet_id_renames registra el cambio."
        ),
    }

    collisions = collision_report(segments_doc)
    report = {
        "packets_in": len(packets_doc.get("packets", [])),
        "packets_out": len(out_packets),
        "packets_with_new_key": remapped,
        "packets_keeping_document_id_key": unchanged,
        "unresolved": unresolved,
        "duplicate_packet_ids_before": len(duplicate_packet_ids),
        "duplicate_packet_ids_after": len(remaining_duplicate_ids),
        "packets_renamed": renamed_packets,
        "packet_id_renames": {k: sorted(v) for k, v in sorted(renames.items())},
        "duplicate_packet_id_samples": dict(list(duplicate_packet_ids.items())[:10]),
        "segments_with_duplicate_key_owner": len(duplicated),
        "segments_with_duplicate_path_owner": len(duplicated_by_path),
        "duplicate_samples": [
            {"key": f"{k[0]}|{k[1]}", "packets": v} for k, v in list(duplicated.items())[:20]
        ],
        "collisions": {
            "ambiguous_document_ids": collisions["ambiguous_document_ids"],
            "paths_affected": collisions["paths_affected"],
            "files_total": collisions["files_total"],
            "files_unambiguous": collisions["files_unambiguous"],
        },
        "collision_detail": collisions["collisions"],
        "integrity_ok": not unresolved and not duplicated_by_path and not remaining_duplicate_ids,
    }
    return out_doc, report


def write_atomic(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="inject_translation_ids.py")
    p.add_argument("--packets", required=True, help="packets_v2.json produced por rebuild_overflow_packets.py")
    p.add_argument("--segments", required=True, help="segments_v2.json")
    p.add_argument("--out", required=True, help="packets_v3.json")
    p.add_argument("--report", help="Informe JSON de la inyección.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    packets_doc = json.loads(Path(args.packets).read_text(encoding="utf-8"))
    segments_doc = json.loads(Path(args.segments).read_text(encoding="utf-8"))

    out_doc, report = inject(packets_doc, segments_doc)
    kinds = Counter(u["detail"].split(":")[0] for u in report["unresolved"])
    report["unresolved_by_kind"] = dict(kinds)

    if args.report:
        write_atomic(Path(args.report), report)

    write_atomic(Path(args.out), out_doc)

    print(json.dumps({k: v for k, v in report.items() if k != "collision_detail"},
                     ensure_ascii=False, indent=2))
    return 0 if report["integrity_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())