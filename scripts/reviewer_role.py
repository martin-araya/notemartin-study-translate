"""Rol de revisor (separación autor/revisor, fase 115).

Toma un ``candidate.json`` producido por un worker (fase 113) y
genera un JSONL de veredictos vacíos para que un humano o un modelo
distinto del autor lo rellene.

Verifica que el input **no** contiene campos prohibidos:

- ``author_notes``
- ``tokens_estimated``
- ``metadata.author``
- ``cost_estimated_usd``

Si los contiene, aborta con código no cero. Esa es la guarda
principal de la separación autor/revisor.

Uso::

    python3 scripts/reviewer_role.py \\
        --reviewer-id R1 \\
        --input work_root/workers/W1/candidate-ok.json \\
        --rubric evals/rubric-distributed.md \\
        --source-path tests/fixtures/scale/foo.md \\
        --out work_root/reviews/R1.jsonl
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FORBIDDEN_KEYS = (
    "author_notes",
    "tokens_estimated",
    "cost_estimated_usd",
    "metadata",
)

VALID_VERDICTS = ("accept", "reject_with_reason", "needs_human")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="reviewer_role.py")
    p.add_argument("--reviewer-id", dest="reviewer_id", required=True)
    p.add_argument("--input", required=True)
    p.add_argument("--rubric", required=True)
    p.add_argument("--source-path", dest="source_path", required=True)
    p.add_argument("--out", required=True, help="JSONL de salida (un segmento por línea).")
    return p.parse_args(argv)


def check_pollution(payload: dict) -> list[str]:
    """Devuelve la lista de claves prohibidas encontradas."""
    pollution = []
    keys = set(payload.keys())
    for forbidden in FORBIDDEN_KEYS:
        if forbidden in keys:
            pollution.append(forbidden)
        # metadata.author específicamente prohibido aunque metadata esté permitido.
        meta = payload.get("metadata")
        if isinstance(meta, dict) and "author" in meta:
            pollution.append("metadata.author")
    return pollution


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    in_path = Path(args.input)
    out_path = Path(args.out)
    rubric_path = Path(args.rubric)
    source_path = Path(args.source_path)

    if not in_path.exists():
        print(f"error: --input no existe: {in_path}", file=sys.stderr)
        return 2
    if not rubric_path.exists():
        print(f"error: --rubric no existe: {rubric_path}", file=sys.stderr)
        return 2
    if not source_path.exists():
        print(f"error: --source-path no existe: {source_path}", file=sys.stderr)
        return 2

    try:
        payload = json.loads(in_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"error: --input no es JSON válido: {e}", file=sys.stderr)
        return 2

    pollution = check_pollution(payload)
    if pollution:
        print(f"error: input contaminado con claves prohibidas: {pollution}", file=sys.stderr)
        return 3

    # Aceptar tanto un candidate individual (packet_id + content) como un
    # lote con varios `packets`.
    candidates = []
    if "packet_id" in payload and "content" in payload:
        candidates.append(payload)
    elif "packets" in payload and isinstance(payload["packets"], list):
        for sub in payload["packets"]:
            if isinstance(sub, dict) and "packet_id" in sub:
                candidates.append(sub)
    else:
        print("error: --input no contiene ni 'packet_id' ni 'packets'", file=sys.stderr)
        return 2

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fp:
        for cand in candidates:
            entry = {
                "reviewer_id": args.reviewer_id,
                "packet_id": cand.get("packet_id"),
                "segment_id": cand.get("segment_id") or cand.get("packet_id"),
                "verdict": None,
                "rubric_checks": {},
                "reason": None,
                "reviewed_at": None,
                "schema_notes": (
                    "rellenar verdict ∈ "
                    + "|".join(VALID_VERDICTS)
                    + " y rubric_checks con la rúbrica"
                ),
            }
            fp.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")

    print(f"ok: {len(candidates)} veredictos (vacíos) -> {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
