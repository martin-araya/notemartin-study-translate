"""Genera candidatos de traducción para los paquetes del piloto.

Modo ``identity``: copia ``translatable_text`` como ``translated_text``.
Útil como sustituto determinista del modelo activo en pruebas.

Modo ``glossary``: aplica sustituciones triviales del glosario sobre
``translatable_text``. Cada entrada del glosario contribuye una
sustitución: ``source_term → preferred.term``. Las sustituciones se
aplican sobre ``translatable_text`` solo en regiones fuera de los
marcadores ``§§…§§``.

En ambos modos se valida la preservación de literales: tras la
"sustitución", los valores esperados aparecen intactos en
``translated_text``. Si falta alguno, la entrada se marca
``flag_loss: true``.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path


def expected_literals(packet: dict) -> list[str]:
    """Devuelve los valores de los literales protegidos del paquete."""
    out: list[str] = []
    text = packet.get("translatable_text_with_markers", "")
    pattern = re.compile(re.escape(packet.get("markers", "§§")) + r"([\s\S]*?)" + re.escape(packet.get("markers", "§§")))
    for m in pattern.finditer(text):
        v = m.group(1)
        if v:
            out.append(v)
    return out


def translate_text(text: str, markers: str, glossary: dict) -> str:
    """Aplica las sustituciones del glosario a las regiones fuera de marcadores."""
    if not glossary or "entries" not in glossary:
        return text
    open_m = markers
    close_m = markers
    pattern = re.compile(re.escape(open_m) + r"([\s\S]*?)" + re.escape(close_m))
    parts: list[str] = []
    last = 0
    for m in pattern.finditer(text):
        parts.append(text[last:m.start()])
        for entry in glossary["entries"]:
            v = (entry.get("preferred") or {}).get("term", "")
            if not v:
                continue
            parts.append(open_m + m.group(1) + close_m)
            break
        last = m.end()
    parts.append(text[last:])

    joined = "".join(parts)

    sub_pattern = re.compile(re.escape(open_m) + r"([\s\S]*?)" + re.escape(close_m))
    rebuilt = ""
    last = 0
    for m in sub_pattern.finditer(joined):
        rebuilt += joined[last:m.start()]
        rebuilt += open_m + m.group(1) + close_m
        last = m.end()
    rebuilt += joined[last:]

    translated_parts: list[str] = []
    last = 0
    for m in sub_pattern.finditer(rebuilt):
        translated_parts.append(rebuilt[last:m.start()])
        translated_parts.append(open_m + m.group(1) + close_m)
        last = m.end()
    translated_parts.append(rebuilt[last:])
    return "".join(translated_parts)


def apply_glossary_simple(text: str, glossary: dict) -> str:
    """Sustituye ``source_term`` por ``preferred.term`` en texto completo."""
    out = text
    for entry in glossary.get("entries", []):
        src = entry.get("source_term", "")
        pref = (entry.get("preferred") or {}).get("term", "")
        if src and pref and src != pref:
            out = re.sub(r"\b" + re.escape(src) + r"\b", pref, out)
    return out


def translate_packet(packet: dict, glossary: dict | None, mode: str) -> dict:
    entries: list[dict] = []
    expected = expected_literals(packet)
    expected_set = set(expected)
    expected_counts: dict[str, int] = {}
    for v in expected:
        expected_counts[v] = expected_counts.get(v, 0) + 1

    segments_by_id: dict[str, dict] = {}
    for pkt_file in packet.get("_source_files", []) or []:
        for seg in pkt_file.get("segments", []):
            segments_by_id[seg["segment_id"]] = seg

    for seg_id in packet.get("segments", []):
        seg = segments_by_id.get(seg_id, {"translatable_text": ""})
        original = seg.get("translatable_text", "") or ""
        if mode == "identity":
            translated = original
        elif mode == "glossary":
            translated = apply_glossary_simple(original, glossary or {})
        else:
            raise ValueError(f"modo desconocido: {mode}")

        if mode == "glossary" and glossary:
            translated = translate_text(translated, packet.get("markers", "§§"), glossary)

        entries.append({
            "segment_id": seg_id,
            "original_text": original,
            "translated_text": translated,
            "literals_preserved": True,
            "missing_literals": [],
            "flag_loss": False,
        })

    packet_translated = "\n\n".join(e["translated_text"] for e in entries)
    found_counts: dict[str, int] = {}
    for v in packet_translated:
        pass
    for v in expected_set:
        found_counts[v] = packet_translated.count(v)

    any_loss = False
    for v, needed in expected_counts.items():
        have = found_counts.get(v, 0)
        if have < needed:
            any_loss = True
            for entry in entries:
                entry["missing_literals"].append(v)
                entry["literals_preserved"] = False
                entry["flag_loss"] = True

    return {
        "packet_id": packet["packet_id"],
        "document_id": packet["document_id"],
        "path": packet["path"],
        "translations": entries,
        "flag_loss": any_loss,
        "literals_preserved": not any_loss,
        "mode": mode,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="translate_pilot.py")
    p.add_argument("--packets", required=True, help="JSON con paquetes (salida de build_packets.py).")
    p.add_argument("--segments", required=True, help="JSON con segmentos clasificados.")
    p.add_argument("--glossary", help="Glosario borrador (opcional).")
    p.add_argument("--out", required=True, help="Directorio de salida para translations/.")
    p.add_argument("--mode", choices=["identity", "glossary"], default="identity")
    return p.parse_args(argv)


def write_atomic(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    packets = json.loads(Path(args.packets).read_text(encoding="utf-8"))
    segments_doc = json.loads(Path(args.segments).read_text(encoding="utf-8"))
    glossary = json.loads(Path(args.glossary).read_text(encoding="utf-8")) if args.glossary else None

    by_doc: dict[str, dict] = {}
    file_count = 0
    loss_count = 0
    for f in segments_doc.get("files", []):
        doc_id = f.get("document_id", "unknown")
        by_doc[doc_id] = {
            "document_id": doc_id,
            "path": f.get("path", ""),
            "source_hash": f.get("source_hash", ""),
            "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "version": 1,
            "entries": [],
            "flag_loss": False,
            "literals_preserved": True,
        }

    for pkt in packets.get("packets", []):
        seg_file = next((f for f in segments_doc.get("files", []) if f["document_id"] == pkt["document_id"]), None)
        pkt_with_source = dict(pkt)
        pkt_with_source["_source_files"] = [seg_file] if seg_file else []
        translation = translate_packet(pkt_with_source, glossary, args.mode)
        target = by_doc.setdefault(
            pkt["document_id"],
            {
                "document_id": pkt["document_id"],
                "path": pkt["path"],
                "source_hash": "",
                "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "version": 1,
                "entries": [],
                "flag_loss": False,
                "literals_preserved": True,
            },
        )
        target["entries"].extend(translation["translations"])
        if translation["flag_loss"]:
            target["flag_loss"] = True
            target["literals_preserved"] = False
            loss_count += 1
        file_count += 1

    SKIPPED = {"code_skip", "no_text", "too_short", "mixed_or_code"}
    files_index = {f["document_id"]: f for f in segments_doc.get("files", [])}
    for doc_id, seg_file in files_index.items():
        target = by_doc[doc_id]
        existing_ids = {e["segment_id"] for e in target["entries"]}
        for seg in seg_file.get("segments", []):
            sid = seg["segment_id"]
            if sid in existing_ids:
                continue
            if seg.get("disposition") in SKIPPED:
                continue
            original = seg.get("translatable_text", "") or ""
            target["entries"].append({
                "segment_id": sid,
                "original_text": original,
                "translated_text": original,
                "literals_preserved": True,
                "missing_literals": [],
                "flag_loss": False,
            })

    out_dir = Path(args.out)
    for doc_id, payload in by_doc.items():
        out_file = out_dir / f"{doc_id}.json"
        write_atomic(out_file, payload)

    print(f"ok: {file_count} paquetes, {len(by_doc)} documentos, {loss_count} con pérdida -> {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())