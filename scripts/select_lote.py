"""Selecciona el siguiente lote de paquetes traducibles, por orden de riesgo.

La traducción del corpus beta son 44 293 segmentos y unos 2,4 millones de
tokens de salida: no caben en una sesión (`AGENTS.md` §11). El trabajo se
hace por lotes, con checkpoint, y el estado vive en el manifiesto.

Este script **no traduce**. Prepara el sobre de un lote y dice cuál es el
siguiente, de modo que reanudar una sesión sea leer un archivo y no
reconstruir decisiones. El orden es de menor a mayor riesgo:

1. `tailwindcss/`: 132 segmentos, tablas densas, corpus pequeño. Donde
   además están las 214 rutas con `document_id` colisionado, que el lote
   expone primero para comprobar que la remediación aguanta.
2. `oracle/resúmenes/`: ya en español (`already_target`), se verifican,
   no se reescriben.
3. `angular/`: tablas de parámetros, donde se concentran las regresiones
   de cifras y valores por defecto.
4. `nextjs/`: encabezados que se autolinkean y rutas escapadas.

    python3 scripts/select_lote.py --packets packets_v3.json \\
        --segments segments_v2.json --translations translations/ \\
        --size 6000 --out lotes/lote-0001.json

`--order` imprime el plan completo sin escribir nada, para auditarlo.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from translation_key import index_by_document, resolve_key  # noqa: E402

# Orden deliberado: menor riesgo primero. `tailwindcss` antes que
# `angular` porque sus tablas densas fallan pronto y en poco texto; el
# error se detecta en la primera sesión en lugar de la décima.
DIRECTORY_ORDER = ["tailwindcss", "oracle", "angular", "nextjs"]


def translation_files(translations: str | None) -> set[str]:
    """Claves ya escritas en `translations/`."""
    if not translations:
        return set()
    d = Path(translations)
    if not d.exists():
        return set()
    return {p.stem for p in d.glob("*.json")}


class Tradable:
    """Índice de segmentos traducibles por clave de persistencia.

    Guarda el índice de rutas por `document_id` para que `key_of` pueda
    resolver la clave de un paquete **sin** depender de que el paquete
    la declare. La primera versión leía `translation_id` del paquete y,
    en un `packets.json` sin ese campo, el sobre salía vacío sin error:
    una tanda sin trabajo es indistinguible de una tanda correcta.
    """

    def __init__(self, segments_doc: dict) -> None:
        self.files_by_doc = index_by_document(segments_doc)
        self.by_key: dict[str, list[str]] = {}
        for f in segments_doc.get("files", []):
            key = self.key_of(f.get("document_id", ""), f.get("path"))
            ids = [
                s["segment_id"] for s in f.get("segments", [])
                if s.get("disposition") == "translatable"
            ]
            if ids:
                self.by_key.setdefault(key, []).extend(ids)

    def key_of(self, doc_id: str, path: str | None) -> str:
        return resolve_key(self.files_by_doc.get(doc_id), doc_id, path)

    def ids_for(self, pkt: dict) -> list[str]:
        doc_id = pkt.get("document_id") or ""
        key = self.key_of(doc_id, pkt.get("path"))
        if key not in self.by_key:
            key = pkt.get("translation_id") or doc_id
        wanted = set(self.by_key.get(key, []))
        return [sid for sid in pkt.get("segments", []) if sid in wanted]

    def total(self) -> int:
        return sum(len(v) for v in self.by_key.values())

    def __len__(self) -> int:
        return len(self.by_key)


def packet_key(pkt: dict, tradable: Tradable) -> str:
    doc_id = pkt.get("document_id") or ""
    key = tradable.key_of(doc_id, pkt.get("path"))
    if key not in tradable.by_key:
        key = pkt.get("translation_id") or doc_id
    return key


def plan(packets_doc: dict, segments_doc: dict, translations: str | None) -> dict:
    """Estado medido: qué falta, por directorio, en qué orden."""
    done = translation_files(translations)
    tradable = Tradable(segments_doc)

    per_dir: dict[str, dict] = defaultdict(
        lambda: {"packets": 0, "pending": 0, "pending_chars": 0, "documents": set()}
    )
    pending: list[dict] = []
    for pkt in packets_doc.get("packets", []):
        top = (pkt.get("path") or "").split("/")[0]
        key = packet_key(pkt, tradable)
        bucket = per_dir[top]
        bucket["packets"] += 1
        bucket["documents"].add(pkt.get("path"))
        if key in done:
            continue
        bucket["pending"] += 1
        bucket["pending_chars"] += int(pkt.get("total_chars") or 0)
        pending.append(pkt)

    order = [d for d in DIRECTORY_ORDER if d in per_dir]
    order += [d for d in sorted(per_dir) if d not in DIRECTORY_ORDER]

    summary = []
    for d in order:
        b = per_dir[d]
        summary.append({
            "directory": d,
            "packets": b["packets"],
            "pending_packets": b["pending"],
            "pending_chars": b["pending_chars"],
            "documents": len(b["documents"]),
        })

    return {
        "documents_total": len(segments_doc.get("files", [])),
        "translatable_segments_total": tradable.total(),
        "documents_already_written": len(done),
        "packets_total": len(packets_doc.get("packets", [])),
        "packets_pending": len(pending),
        "pending_chars": sum(int(p.get("total_chars") or 0) for p in pending),
        "by_directory": summary,
        "_pending": pending,
        "_tradable": tradable,
    }


def build_lote(state: dict, size: int, prefix: str = "angular") -> dict:
    """Arma un lote de `size` caracteres, sin cruzar directorios.

    Un lote no cruza directorio a propósito: cada uno tiene su propia
    terminología y sus propios riesgos, y mezclarlos haría que un fallo
    en tablas de `angular/api/` contaminara el diagnóstico de
    `nextjs/messages/`.
    """
    pending = list(state["_pending"])
    prefix = prefix or None
    chosen: list[dict] = []
    used = 0
    for pkt in pending:
        if prefix and not (pkt.get("path") or "").startswith(prefix + "/"):
            continue
        chars = int(pkt.get("total_chars") or 0)
        if chosen and used + chars > size:
            break
        chosen.append(pkt)
        used += chars

    tradable: Tradable = state["_tradable"]
    envelopes = []
    for pkt in chosen:
        key = packet_key(pkt, tradable)
        wanted = tradable.ids_for(pkt)
        if not wanted:
            continue
        envelopes.append({
            "packet_id": pkt["packet_id"],
            "document_id": pkt.get("document_id"),
            # Se emite la clave **resuelta**, no la declarada: quien
            # responde y quien reciben tienen que nombrar lo mismo.
            "translation_id": key,
            "path": pkt.get("path"),
            "markers": pkt.get("markers", "§§"),
            "segments": wanted,
            "translatable_text_with_markers": pkt.get("translatable_text_with_markers", ""),
            "non_emitible_context": pkt.get("non_emitible_context", []),
        })

    return {
        "lote_id": None,
        "directory": prefix,
        "packets": envelopes,
        "packets_count": len(envelopes),
        "segments_requested": sum(len(e["segments"]) for e in envelopes),
        "chars": used,
        "note": (
            "Sobre de traducción. Responder por `segment_id` con "
            "`translated_text`. Los literales entre `§§` se devuelven "
            "intactos y el envoltorio se retira: el marcador es "
            "instrumental del paquete, no parte de la entrega."
        ),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="select_lote.py")
    p.add_argument("--packets", required=True, help="packets_v3.json")
    p.add_argument("--segments", required=True, help="segments_v2.json")
    p.add_argument("--translations", help="Directorio translations/, para saltar lo ya entregado.")
    p.add_argument("--size", type=int, default=6000,
                   help="Caracteres de prosa aproximados por lote.")
    p.add_argument("--prefix", default="",
                   help="Directorio del lote. Vacío usa el primero con trabajo pendiente.")
    p.add_argument("--out", help="Sobre del lote. Sin él solo se imprime el plan.")
    p.add_argument("--lote-id", help="Identificador del lote, por ejemplo 0001.")
    p.add_argument("--order", action="store_true",
                   help="Imprime el plan por directorio y no escribe el lote.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    packets_doc = json.loads(Path(args.packets).read_text(encoding="utf-8"))
    segments_doc = json.loads(Path(args.segments).read_text(encoding="utf-8"))
    state = plan(packets_doc, segments_doc, args.translations)

    if args.order:
        rows = [
            "| Directorio | Paquetes | Pendientes | Caracteres | Documentos |",
            "|---|---|---|---|---|",
        ]
        for s in state["by_directory"]:
            rows.append(
                f"| `{s['directory']}` | {s['packets']} | {s['pending_packets']} | "
                f"{s['pending_chars']:,} | {s['documents']} |".replace(",", ".")
            )
        print("\n".join(rows))
        print()
        print(json.dumps({k: v for k, v in state.items()
                          if not k.startswith("_")}, ensure_ascii=False, indent=2))
        return 0

    prefix = args.prefix
    if not prefix:
        first = next((s["directory"] for s in state["by_directory"] if s["pending_packets"]), "")
        if not first:
            print(json.dumps({"ok": True, "message": "no queda trabajo pendiente"}, ensure_ascii=False))
            return 0
        prefix = first

    lote = build_lote(state, args.size, prefix)
    lote["lote_id"] = args.lote_id
    lote["packets_total_pending"] = state["packets_pending"]
    lote["packets_total"] = state["packets_total"]

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(lote, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({k: v for k, v in lote.items() if k != "packets"},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())