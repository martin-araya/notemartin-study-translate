"""Caché contextual de traducción (fase 118 del roadmap).

Almacena y consulta traducciones previas por segmento. La clave
compuesta es ``(source_hash, glossary_hash, locale_variant,
segment_id)``: si difiere cualquiera, no se reutiliza. Esta es la
regla «no reutilizar texto con sentido incompatible» del lote 118.

Uso::

    python3 scripts/translation_cache.py lookup \\
        --segment seg-abc \\
        --source-hash <sha256> \\
        --glossary-hash <sha256> \\
        --locale es-ES \\
        --root reports/cache

    python3 scripts/translation_cache.py store \\
        --segment seg-abc \\
        --source-hash <sha256> \\
        --glossary-hash <sha256> \\
        --locale es-ES \\
        --content «Traducción propuesta.» \\
        --root reports/cache

    python3 scripts/translation_cache.py reset \\
        --root reports/cache
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def key_short(segment_id: str, source_hash: str, glossary_hash: str, locale_variant: str) -> str:
    payload = f"{segment_id}|{source_hash}|{glossary_hash}|{locale_variant}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def entry_path(root: Path, locale_variant: str, source_hash: str, glossary_hash: str, segment_id: str) -> Path:
    src_short = source_hash[:16]
    gls_short = glossary_hash[:16]
    safe_seg = segment_id.replace("/", "_").replace(":", "_")
    return (
        root
        / locale_variant
        / f"{src_short}__{gls_short}"
        / f"{safe_seg}.json"
    )


def write_atomic(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def lookup(segment_id: str, source_hash: str, glossary_hash: str, locale_variant: str,
           root: Path) -> dict | None:
    path = entry_path(root, locale_variant, source_hash, glossary_hash, segment_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def store(segment_id: str, source_hash: str, glossary_hash: str, locale_variant: str,
          content: str | None, root: Path, packet_id: str | None = None,
          anchors: list[str] | None = None) -> dict:
    """Guarda una entrada de caché.

    ``anchors`` es lo que permite a la fase 119 invalidar por cambio de
    títulos. Sin él, la entrada se puede reutilizar después de que el
    documento haya cambiado de anclas, que es exactamente el fallo que esa
    fase existe para evitar.
    """
    key = key_short(segment_id, source_hash, glossary_hash, locale_variant)
    payload = {
        "key": key,
        "segment_id": segment_id,
        "source_hash": source_hash,
        "glossary_hash": glossary_hash,
        "locale_variant": locale_variant,
        "content": content,
        "created_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    if packet_id:
        payload["packet_id"] = packet_id
    if anchors is not None:
        payload["anchors"] = sorted(set(anchors))
    path = entry_path(root, locale_variant, source_hash, glossary_hash, segment_id)
    write_atomic(path, payload)
    return payload


def reset(root: Path, locale_variant: str | None = None) -> int:
    if locale_variant:
        target = root / locale_variant
        if target.exists():
            count = sum(1 for _ in target.rglob("*.json"))
            for f in target.rglob("*.json"):
                f.unlink()
            return count
        return 0
    if not root.exists():
        return 0
    count = sum(1 for _ in root.rglob("*.json"))
    for f in root.rglob("*.json"):
        f.unlink()
    return count


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="translation_cache.py")
    sub = p.add_subparsers(dest="cmd", required=True)

    look = sub.add_parser("lookup", help="Buscar una entrada.")
    look.add_argument("--segment", required=True)
    look.add_argument("--source-hash", dest="source_hash", required=True)
    look.add_argument("--glossary-hash", dest="glossary_hash", required=True)
    look.add_argument("--locale", required=True)
    look.add_argument("--root", required=True)

    store_p = sub.add_parser("store", help="Almacenar una entrada.")
    store_p.add_argument("--segment", required=True)
    store_p.add_argument("--source-hash", dest="source_hash", required=True)
    store_p.add_argument("--glossary-hash", dest="glossary_hash", required=True)
    store_p.add_argument("--locale", required=True)
    store_p.add_argument("--content", default=None)
    store_p.add_argument("--root", required=True)
    store_p.add_argument("--packet-id", dest="packet_id", default=None)
    store_p.add_argument("--anchor", dest="anchors", action="append", default=None,
                         help="Ancla del documento usada por esta traducción. "
                              "Repetible: sin anclas, la invalidación por cambio "
                              "de títulos no puede alcanzar a esta entrada.")

    reset_p = sub.add_parser("reset", help="Borrar el caché.")
    reset_p.add_argument("--root", required=True)
    reset_p.add_argument("--locale", default=None)

    return p.parse_args(argv)


def _validate_hash(value: str, name: str) -> None:
    if not value or len(value) != 64 or not all(c in "0123456789abcdef" for c in value):
        raise SystemExit(f"{name}: debe ser SHA-256 hex (64 caracteres), recibido {value!r}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.cmd == "lookup":
        _validate_hash(args.source_hash, "--source-hash")
        _validate_hash(args.glossary_hash, "--glossary-hash")
        entry = lookup(args.segment, args.source_hash, args.glossary_hash, args.locale, Path(args.root))
        if entry is None:
            print("miss")
            return 1
        print(json.dumps(entry, ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "store":
        _validate_hash(args.source_hash, "--source-hash")
        _validate_hash(args.glossary_hash, "--glossary-hash")
        entry = store(args.segment, args.source_hash, args.glossary_hash, args.locale,
                      args.content, Path(args.root), args.packet_id, args.anchors)
        print(json.dumps(entry, ensure_ascii=False, indent=2))
        return 0
    if args.cmd == "reset":
        n = reset(Path(args.root), args.locale)
        print(f"ok: {n} entradas eliminadas")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
