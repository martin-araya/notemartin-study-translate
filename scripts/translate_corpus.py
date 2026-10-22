"""Traduce el corpus completo en orden controlado.

Recorre ``packets.json`` generado por ``scripts/build_packets.py``
sobre el alcance completo (no solo el piloto), agrupa los paquetes por
``document_id`` y aplica ``translate_packet`` de
``scripts/translate_pilot.py`` sobre cada uno. Persiste el resultado
en ``translations/<doc_id>.json``.

Si un ``document_id`` del alcance no tiene paquetes asociados, lo
registra como ``skipped: no_packets`` en stdout sin abortar. No salta
archivos largos: procesa todos los paquetes por documento en orden
de ``packet_id``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="translate_corpus.py")
    p.add_argument("--packets", required=True)
    p.add_argument("--segments", required=True)
    p.add_argument("--translations", required=True)
    p.add_argument("--mode", choices=["identity", "glossary"], default="identity")
    p.add_argument("--glossary")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from translate_pilot import translate_packet, write_atomic

    packets_doc = json.loads(Path(args.packets).read_text(encoding="utf-8"))
    segments_doc = json.loads(Path(args.segments).read_text(encoding="utf-8"))
    glossary = json.loads(Path(args.glossary).read_text(encoding="utf-8")) if args.glossary else None

    files_index = {f["document_id"]: f for f in segments_doc.get("files", [])}
    in_scope = set(files_index)

    by_doc: dict[str, dict] = {doc_id: {
        "document_id": doc_id,
        "path": f["path"],
        "source_hash": f["source_hash"],
        "version": 1,
        "entries": [],
        "flag_loss": False,
        "literals_preserved": True,
    } for doc_id, f in files_index.items()}

    seen_packets: set[str] = set()
    for pkt in packets_doc.get("packets", []):
        doc_id = pkt["document_id"]
        if doc_id not in in_scope:
            continue
        seg_file = files_index.get(doc_id)
        if seg_file is None:
            continue
        if pkt["packet_id"] in seen_packets:
            continue
        seen_packets.add(pkt["packet_id"])
        pkt_with_source = dict(pkt)
        pkt_with_source["_source_files"] = [seg_file]
        result = translate_packet(pkt_with_source, glossary, args.mode)
        target = by_doc[doc_id]
        target["entries"].extend(result["translations"])
        if result["flag_loss"]:
            target["flag_loss"] = True
            target["literals_preserved"] = False

    out_dir = Path(args.translations)
    written = 0
    for doc_id, payload in by_doc.items():
        write_atomic(out_dir / f"{doc_id}.json", payload)
        written += 1

    skipped = sorted(in_scope - set(p["document_id"] for p in packets_doc.get("packets", []) if p["document_id"] in in_scope))
    coverage = written / max(len(in_scope), 1)
    print(f"ok: {written} documentos, cobertura {coverage:.0%}, skipped: {skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())