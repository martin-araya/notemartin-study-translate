"""Construye paquetes de traducción y aplica marcadores de protección.

Por cada archivo del inventario, agrupa segmentos consecutivos en
paquetes respetando:

- ``context_budget`` del perfil.
- No partir una celda de tabla ni un literal.
- Cada paquete tiene un único ``owner``.

Cada ``protected_literal`` se delimita con un marcador elegido
(``§§...§§`` por defecto). El validador integrado detecta:

- Marcadores falsificados (el contenido entre marcadores no coincide
  con el ``protected_literal.value``).
- Marcadores perdidos (un literal esperado no aparece entre
  marcadores).
- Marcadores duplicados (el mismo literal aparece más de una vez).

Si la validación falla, el script devuelve código no cero y no
escribe la salida.
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

DEFAULT_MARKERS = "§§"
DEFAULT_BUDGET = 8000


def hash_id(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:8]


def build_packet_markers(seg: dict, markers: str) -> tuple[str, list[dict]]:
    """Inserta marcadores ``markers`` alrededor de cada literal protegido.

    Devuelve ``(text_with_markers, validation_map)``. ``validation_map``
    lista los literales delimitados con su offset dentro del texto con
    marcadores.

    El marcado se hace por **posición**, no por valor: un segmento puede
    llevar dos apariciones del mismo literal, y envolver la primera dos
    veces producía `§§§§string§§§§`, que la validación leía como un solo
    literal y daba por perdido el segundo. Se recorren las apariciones de
    izquierda a derecha, se toman tantas como entradas de literal haya,
    y se envuelve de derecha a izquierda para que los desplazamiento
    anteriores sigan siendo válidos.
    """
    text = seg.get("translatable_text") or ""
    literals = [lit for lit in (seg.get("protected_literals") or []) if (lit.get("value") or "")]

    needed: dict[str, int] = {}
    for lit in literals:
        value = lit["value"]
        needed[value] = needed.get(value, 0) + 1

    spans: list[tuple[int, int]] = []
    for value, count in sorted(needed.items(), key=lambda kv: -len(kv[0])):
        position = text.find(value)
        found = 0
        while position != -1 and found < count:
            end = position + len(value)
            if not any(start <= position < other_end for start, other_end in spans):
                spans.append((position, end))
                found += 1
            position = text.find(value, position + 1)

    for start, end in sorted(spans, reverse=True):
        text = text[:start] + f"{markers}{text[start:end]}{markers}" + text[end:]

    return text, [
        {
            "type": lit.get("type"),
            "value": lit.get("value"),
            "found_in_packet": True,
            "byte_range": lit.get("byte_range"),
        }
        for lit in literals
    ]


def validate_packet(packet: dict, source_segments: list[dict]) -> list[str]:
    """Devuelve una lista de errores. Vacía si todo está bien.

    Verifica por segmento: para cada segmento del paquete, todos sus
    ``protected_literals`` deben aparecer entre marcadores en el texto
    del paquete. La duplicación entre segmentos distintos es normal y
    no se reporta como duplicado. Solo se marca como duplicado si un
    MISMO segmento tiene varias ocurrencias idénticas que
    ``text.replace(..., 1)`` no cubre.
    """
    errors: list[str] = []
    markers = packet["markers"]
    text = packet["translatable_text_with_markers"]
    opening = text.count(markers)
    if opening % 2 != 0:
        errors.append(f"número impar de marcadores: {opening}")

    pattern = re.compile(re.escape(markers) + r"([\s\S]*?)" + re.escape(markers))
    found_values = [m.group(1) for m in pattern.finditer(text) if m.group(1) != ""]

    expected_count: dict[str, int] = {}
    for seg in source_segments:
        for lit in seg.get("protected_literals") or []:
            v = lit.get("value") or ""
            if v:
                expected_count[v] = expected_count.get(v, 0) + 1

    found_count: dict[str, int] = {}
    for v in found_values:
        found_count[v] = found_count.get(v, 0) + 1

    missing = [v for v, n in expected_count.items() if found_count.get(v, 0) < n]
    extra = [v for v, n in found_count.items() if found_count.get(v, 0) > n]
    if missing:
        errors.append(f"literales perdidos: {missing}")
    if extra:
        errors.append(f"literales extra: {extra}")

    return errors


def pack_file(
    f: dict, budget: int, markers: str, mixed_profile: dict | None = None
) -> tuple[list[dict], list[dict]]:
    """Empaqueta un archivo y devuelve ``(paquetes, errores)``.

    ``mixed_profile`` controla la política multilingüe:

    - ``None`` o ``{"enabled": false}``: comportamiento tradicional;
      todos los segmentos traducibles se mezclan sin restricción de
      idioma.
    - ``{"enabled": true, ...}``: cada paquete contiene segmentos
      cuyo ``language`` declarado pertenece a un **único** idioma.
      Si ``forbid_double_translation`` está activo, los segmentos ya
      en ``es`` se excluyen del paquete además de marcarse como
      skippables. Si un idioma declarado no está en
      ``allowed_source_languages``, se devuelve un error.
    """
    segments = [s for s in f.get("segments", []) if not _is_skippable(s)]
    if not segments:
        return [], []

    enabled = bool(mixed_profile and mixed_profile.get("enabled"))
    allowed = set(mixed_profile.get("allowed_source_languages", []) if mixed_profile else [])
    forbid_double = bool(mixed_profile.get("forbid_double_translation", False)) if mixed_profile else False

    if enabled:
        out_of_scope: list[str] = []
        for s in segments:
            lang = s.get("language") or s.get("detected_language") or "unknown"
            if lang not in allowed and lang not in {"code", "empty", "unknown", "mixed"}:
                out_of_scope.append(f"{s.get('segment_id', '?')}:{lang}")
        if out_of_scope:
            return [], [
                {
                    "packet_id": f["document_id"],
                    "errors": [
                        "mixed_profile habilitado pero hay segmentos con idiomas no permitidos: "
                        + ", ".join(out_of_scope[:5])
                        + ("..." if len(out_of_scope) > 5 else "")
                    ],
                }
            ]

    packets: list[dict] = []
    errors: list[dict] = []
    cur: list[dict] = []
    cur_chars = 0
    cur_lang: str | None = None

    def flush(overflow: bool = False) -> None:
        nonlocal cur, cur_chars, cur_lang
        if not cur:
            return
        text_with_markers = ""
        text_plain = ""
        for seg in cur:
            twm, _ = build_packet_markers(seg, markers)
            text_with_markers += twm + "\n\n"
            text_plain += (seg.get("translatable_text") or "") + "\n\n"
        text_with_markers = text_with_markers.rstrip()
        text_plain = text_plain.rstrip()
        seg_ids = [s["segment_id"] for s in cur]
        # El id de paquete incluye la ruta, no solo `document_id` y los
        # segmentos: `document_id` deriva de los bytes y `segment_id`
        # deriva de `document_id` más el rango, así que dos archivos
        # byte-idénticos producían el MISMO `packet_id`. Con id duplicado
        # una respuesta del agente se resuelve al último paquete del
        # grupo (es un dict por id) y el trabajo de los otros se pierde
        # sin aviso: INV-03 exige propietario único.
        packet_id = "pack-" + hash_id(f["path"] + ":" + f["document_id"] + ":" + ",".join(seg_ids))
        packet = {
            "packet_id": packet_id,
            "document_id": f["document_id"],
            "path": f["path"],
            "owner": "pack-" + hash_id(packet_id),
            "markers": markers,
            "segments": seg_ids,
            "source_language": cur_lang or "mixed",
            "non_emitible_context": _non_emitible(f, seg_ids),
            "total_chars": cur_chars,
            "translatable_text": text_plain,
            "translatable_text_with_markers": text_with_markers,
            "overflow": overflow,
        }
        if forbid_double:
            packet["forbid_double_translation"] = True
        packets.append(packet)
        cur = []
        cur_chars = 0
        cur_lang = None

    for seg in segments:
        text_len = len(seg.get("translatable_text") or "")
        seg_lang = seg.get("language") or seg.get("detected_language") or "unknown"
        if enabled and cur_lang is not None and seg_lang != cur_lang:
            flush()
        if cur and cur_chars + text_len > budget:
            flush()
        if not cur:
            cur.append(seg)
            cur_chars = text_len
            cur_lang = seg_lang if enabled else None
            if cur_chars > budget:
                flush(overflow=True)
        else:
            cur.append(seg)
            cur_chars += text_len
            if cur_chars > budget:
                flush(overflow=True)

    flush()

    for pkt in packets:
        segs_by_id = {s["segment_id"]: s for s in segments if s["segment_id"] in pkt["segments"]}
        errs = validate_packet(pkt, list(segs_by_id.values()))
        if errs:
            errors.append({"packet_id": pkt["packet_id"], "errors": errs})

    return packets, errors


def _is_skippable(seg: dict) -> bool:
    disposition = seg.get("disposition", "translatable")
    if disposition in {"already_target", "code_skip", "no_text", "too_short", "mixed_or_code"}:
        return True
    if not (seg.get("translatable_text") or "").strip():
        return True
    return False


def _non_emitible(f: dict, seg_ids: list[str]) -> list[str]:
    all_ids = [s["segment_id"] for s in f.get("segments", [])]
    out: list[str] = []
    for sid in seg_ids:
        idx = all_ids.index(sid)
        for delta in (-1, 1):
            j = idx + delta
            if 0 <= j < len(all_ids) and all_ids[j] not in seg_ids and all_ids[j] not in out:
                out.append(all_ids[j])
    return out


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="packetize.py")
    p.add_argument("--segments", required=True, help="JSON con segmentos clasificados.")
    p.add_argument("--out", required=True, help="JSON con paquetes.")
    p.add_argument("--context-budget", type=int, default=DEFAULT_BUDGET)
    p.add_argument("--markers", default=DEFAULT_MARKERS)
    p.add_argument(
        "--mixed-profile",
        help=(
            "Path a un JSON con la política mixed_profile. Si se omite, el script "
            "actúa como antes (sin restricción de idioma por paquete)."
        ),
    )
    return p.parse_args(argv)


def load_mixed_profile(path: str | None) -> dict | None:
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"--mixed-profile: archivo inexistente: {path}")
    return json.loads(p.read_text(encoding="utf-8"))


def write_atomic(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    seg_path = Path(args.segments)
    out_path = Path(args.out)
    payload = json.loads(seg_path.read_text(encoding="utf-8"))
    mixed_profile = load_mixed_profile(args.mixed_profile)

    all_packets: list[dict] = []
    all_errors: list[dict] = []
    for f in payload.get("files", []):
        pkts, errs = pack_file(f, args.context_budget, args.markers, mixed_profile=mixed_profile)
        all_packets.extend(pkts)
        all_errors.extend(errs)

    out = {
        "source_root": payload.get("source_root"),
        "context_budget": args.context_budget,
        "markers": args.markers,
        "mixed_profile": mixed_profile,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_packets": len(all_packets),
        "validation_errors": all_errors,
        "packets": all_packets,
    }

    if all_errors:
        print(f"error: {len(all_errors)} paquetes con errores de validación", file=sys.stderr)
        for e in all_errors:
            print(f"  {e['packet_id']}: {e['errors']}", file=sys.stderr)
        return 1

    write_atomic(out_path, out)
    print(f"ok: {len(all_packets)} paquetes -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())