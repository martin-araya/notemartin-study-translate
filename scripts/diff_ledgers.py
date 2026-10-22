"""Comparador de ledgers (fase 117 del roadmap).

Compara dos manifiestos y devuelve la lista de diferencias por
``segment_id``. Útil para verificar la equivalencia serie↔concurrente
(fase 120).

Uso::

    python3 scripts/diff_ledgers.py \\
        --a reports/serial/run/manifest.json \\
        --b reports/concurrent/run/manifest.json \\
        --out reports/diff.json

Sin ``--out``, vuelca el resumen en stdout.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="diff_ledgers.py")
    p.add_argument("--a", required=True)
    p.add_argument("--b", required=True)
    p.add_argument("--out", default=None)
    p.add_argument("--strict", action="store_true")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        a = json.loads(Path(args.a).read_text(encoding="utf-8"))
        b = json.loads(Path(args.b).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    a_ids = set(a.get("approved_segment_ids", []))
    b_ids = set(b.get("approved_segment_ids", []))

    a_state = {sid: "approved" for sid in a_ids}
    b_state = {sid: "approved" for sid in b_ids}

    only_in_a = sorted(a_ids - b_ids)
    only_in_b = sorted(b_ids - a_ids)
    both = sorted(a_ids & b_ids)

    state_dist_a = a.get("current_state_distribution", {})
    state_dist_b = b.get("current_state_distribution", {})

    diff = {
        "a_path": args.a,
        "b_path": args.b,
        "only_in_a": only_in_a,
        "only_in_b": only_in_b,
        "both_count": len(both),
        "state_distribution_a": state_dist_a,
        "state_distribution_b": state_dist_b,
    }

    if args.out:
        Path(args.out).write_text(
            json.dumps(diff, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    else:
        print(json.dumps(diff, indent=2, ensure_ascii=False))

    if args.strict and (only_in_a or only_in_b):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
