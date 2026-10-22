"""Invalidador transitivo del caché (fase 119 del roadmap).

Recorre el caché de traducción y determina qué entradas se han
invalidado por:

- cambio del ``glossary_hash`` (cambio de glosario).
- cambio de encabezados en ``anchors.json`` (las entradas cuyo
  segmento se reescribió y las de los documentos que apuntaban al
  encabezado afectado).

Uso::

    python3 scripts/invalidate_cache.py \\
        --cache-root reports/cache/ \\
        --glossary-old <sha256-antiguo> \\
        --glossary-new <sha256-nuevo> \\
        --out reports/cache/invalidation_plan.json

    # Sólo invalida entradas con glossary_hash incompatible:
    python3 scripts/invalidate_cache.py \\
        --cache-root reports/cache/ \\
        --glossary-old <sha256-antiguo> \\
        --glossary-new <sha256-nuevo>

    # Anclas:
    python3 scripts/invalidate_cache.py \\
        --cache-root reports/cache/ \\
        --anchors-old anchors_old.json \\
        --anchors-new anchors_new.json \\
        --out plan.json

Sin ``--out``, el script imprime el número de entradas afectadas
y sale con código 1 si hay invalideces. Con ``--out``, vuelca el
plan completo con cada entrada listada.
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


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="invalidate_cache.py")
    p.add_argument("--cache-root", required=True)
    p.add_argument("--glossary-old", default=None)
    p.add_argument("--glossary-new", default=None)
    p.add_argument("--anchors-old", default=None)
    p.add_argument("--anchors-new", default=None)
    p.add_argument("--out", default=None)
    return p.parse_args(argv)


def write_atomic(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def iter_cache(cache_root: Path):
    for f in cache_root.rglob("*.json"):
        try:
            yield f, json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue


def detect_glossary_changes(cache_root: Path,
                             glossary_old: str | None,
                             glossary_new: str | None) -> list[Path]:
    if not glossary_old or glossary_old == glossary_new:
        return []
    paths = []
    for f, entry in iter_cache(cache_root):
        if entry.get("glossary_hash") == glossary_new:
            continue
        paths.append(f)
    return paths


def detect_anchor_changes(cache_root: Path,
                          anchors_old_path: str | None,
                          anchors_new_path: str | None) -> list[Path]:
    if not anchors_old_path or not anchors_new_path:
        return []
    try:
        old = json.loads(Path(anchors_old_path).read_text(encoding="utf-8"))
        new = json.loads(Path(anchors_new_path).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    old_map = old.get("anchors") or {}
    new_map = new.get("anchors") or {}
    changed_anchors = set()
    for anchor, info in old_map.items():
        new_info = new_map.get(anchor)
        if new_info is None or new_info != info:
            changed_anchors.add(anchor)

    if not changed_anchors:
        return []

    # Encontrar las entradas de caché que se reescribieron con esos anchors.
    paths = []
    for f, entry in iter_cache(cache_root):
        meta = entry.get("anchors") or []
        if isinstance(meta, dict):
            meta_keys = set(meta.keys())
        else:
            meta_keys = set(meta) if isinstance(meta, list) else set()
        if changed_anchors & meta_keys:
            paths.append(f)
    return paths


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    cache_root = Path(args.cache_root)
    if not cache_root.exists():
        print("ok: vacío", file=sys.stderr)
        return 0

    direct = detect_glossary_changes(cache_root, args.glossary_old, args.glossary_new)
    transitive = detect_anchor_changes(cache_root, args.anchors_old, args.anchors_new)

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    plan = {
        "generated_at": now,
        "cache_root": str(cache_root),
        "inputs": {
            "glossary_old": args.glossary_old,
            "glossary_new": args.glossary_new,
            "anchors_old": args.anchors_old,
            "anchors_new": args.anchors_new,
        },
        "direct_invalidations": sorted(str(p) for p in direct),
        "transitive_invalidations": sorted(str(p) for p in transitive),
        "counts": {
            "direct": len(direct),
            "transitive": len(transitive),
            "total_unique": len(set(direct) | set(transitive)),
        },
    }

    if args.out:
        write_atomic(Path(args.out), plan)

    if plan["counts"]["total_unique"] > 0:
        print(
            f"invalidaciones: direct={plan['counts']['direct']}, "
            f"transitive={plan['counts']['transitive']}"
        )
        return 1

    print("ok: ninguna entrada afectada")
    return 0


if __name__ == "__main__":
    sys.exit(main())
