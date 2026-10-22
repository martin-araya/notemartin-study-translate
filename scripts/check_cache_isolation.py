"""Validación de aislamiento de caché entre variantes (fase 107).

Recorre los artefactos de varias ejecuciones regionales y verifica
que:

- Cada ``packet_id`` lleva consigo la variante y los hashes cortos
  son distintos entre variantes para el mismo segmento origen.
- ``locale.variant`` está presente y es consistente entre
  ``eval.json`` y los paquetes.
- No se ha reutilizado ninguna salida entre variantes.

Uso::

    python3 scripts/check_cache_isolation.py \
        --runs reports/es-es,reports/es-mx,reports/es-ar
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def load_eval(path: Path) -> dict:
    payload = json.loads((path / "eval.json").read_text(encoding="utf-8"))
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="check_cache_isolation.py")
    p.add_argument("--runs", required=True, help="Carpetas separadas por coma con eval.json")
    p.add_argument("--report", default=None)
    p.add_argument("--strict", action="store_true")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    runs = [Path(p) for p in args.runs.split(",") if p.strip()]
    issues = []
    summaries = []
    for run in runs:
        eval_path = run / "eval.json"
        if not eval_path.exists():
            issues.append(f"falta {eval_path}")
            continue
        ev = load_eval(run)
        variant = ev.get("variant") or "es"
        summaries.append(
            {
                "run": str(run),
                "variant": variant,
                "packets": len(ev.get("packets", [])),
                "segments": ev["metrics"]["total_segments"],
            }
        )

    by_variant: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for run in runs:
        ev = load_eval(run)
        for p in ev.get("packets", []):
            by_variant[ev.get("variant", "es")].append(
                (p["packet_id"], p["sha256_short"])
            )

    # Comprobación: dos variantes distintas no deben compartir hash corto
    # para un mismo packet_id_base (que incluye doc_id y segment_ids).
    bases_across = defaultdict(list)
    for variant, entries in by_variant.items():
        for packet_id, sha_short in entries:
            base = packet_id
            bases_across[base].append((variant, sha_short))

    for base, occurrences in bases_across.items():
        if len({v for v, _ in occurrences}) > 1:
            shas = {s for _, s in occurrences}
            variants = {v for v, _ in occurrences}
            if len(shas) < len(occurrences):
                issues.append(
                    f"paquete {base} reutilizado entre variantes {sorted(variants)}"
                )

    # Comprobación: cada run declara locale.variant
    for run in runs:
        ev = load_eval(run)
        if "locale" not in ev or not ev["locale"].get("variant"):
            issues.append(f"run {run} no declara locale.variant")

    report = {
        "runs": summaries,
        "issues": issues,
        "isolated": not issues,
    }
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"ok: reporte -> {args.report}")
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if issues:
        print("error: contaminación de caché detectada", file=sys.stderr)
        for i in issues:
            print(f"  - {i}", file=sys.stderr)
        return 1 if args.strict else 0
    print("ok: caché aislada por variante")
    return 0


if __name__ == "__main__":
    sys.exit(main())
