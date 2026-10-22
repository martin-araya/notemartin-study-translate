"""Matriz lingüística de pares verificados (fase 110).

Vuelca ``reports/language_matrix.json`` con un objeto por par
declarado en el sistema. La rúbrica combina:

- ``evaluation_kind`` ∈ ``{human_approved, assisted, experimental, not_started}``
- ``reviewer_status`` ∈ ``{human_approved, assisted_only_pending_human, not_applicable}``
- ``human_reviewer``: nombre o ``null``.

El módulo es invocable como script::

    python3 scripts/language_matrix.py --out reports/language_matrix.json

El umbral para considerar la matriz estable es 3 pares con
``evaluation_kind: human_approved``. Eso se valida con
``tests/test_language_matrix.py``.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PAIRS = [
    {
        "pair": "en-es",
        "locale": "es",
        "evaluation_kind": "human_approved",
        "reviewer_status": "human_approved",
        "human_reviewer": "núcleo-0.1.0",
        "corpus": "tests/fixtures/pilot/",
        "limits": ["CommonMark + GFM básico", "Mermaid preservado"],
        "policy_path": None,
        "rtl": False,
    },
    {
        "pair": "fr-es",
        "locale": "es",
        "evaluation_kind": "assisted",
        "reviewer_status": "assisted_only_pending_human",
        "human_reviewer": None,
        "corpus": "tests/fixtures/pilot-fr/",
        "limits": ["revisión asistida pendiente de firma humana nativa en fr",
                   "corpus derivado CC0 (sustitución cuando se activen 071-080)"],
        "policy_path": "references/source-language-policy-fr.md",
        "rtl": False,
    },
    {
        "pair": "en-es-ES",
        "locale": "es-ES",
        "evaluation_kind": "assisted",
        "reviewer_status": "assisted_only_pending_human",
        "human_reviewer": None,
        "corpus": "tests/fixtures/es-es/",
        "limits": ["voseo desactivado, vosotros activo", "firma humana nativa pendiente"],
        "policy_path": "references/locale-policy.md",
        "rtl": False,
    },
    {
        "pair": "en-es-MX",
        "locale": "es-MX",
        "evaluation_kind": "assisted",
        "reviewer_status": "assisted_only_pending_human",
        "human_reviewer": None,
        "corpus": "tests/fixtures/es-mx/",
        "limits": ["usted por defecto, sin vosotros", "firma humana nativa pendiente",
                   "corpus derivado CC0"],
        "policy_path": "references/locale-policy.md",
        "rtl": False,
    },
    {
        "pair": "en-es-AR",
        "locale": "es-AR",
        "evaluation_kind": "assisted",
        "reviewer_status": "assisted_only_pending_human",
        "human_reviewer": None,
        "corpus": "tests/fixtures/es-ar/",
        "limits": ["voseo rioplatense", "firma humana nativa pendiente",
                   "corpus derivado CC0"],
        "policy_path": "references/locale-policy.md",
        "rtl": False,
    },
    {
        "pair": "ar-es",
        "locale": "es",
        "evaluation_kind": "assisted",
        "reviewer_status": "assisted_only_pending_human",
        "human_reviewer": None,
        "corpus": "tests/fixtures/rtl/",
        "limits": ["RTL preservado byte-a-byte",
                   "render no comprobado por el importador",
                   "firma humana nativa pendiente"],
        "policy_path": "references/rtl-policy.md",
        "rtl": True,
    },
]


PLANNED_PAIRS = [
    {"pair": "en-es-CL", "locale": "es-CL", "rationale": "Chile pendiente del lote 110+"},
    {"pair": "en-es-CO", "locale": "es-CO", "rationale": "Colombia pendiente del lote 110+"},
    {"pair": "he-es", "locale": "es", "rationale": "Hebreo→Español pendiente"},
    {"pair": "pt-es", "locale": "es", "rationale": "Portugués→Español pendiente"},
    {"pair": "en-pt-BR", "locale": "pt-BR", "rationale": "Salida en portugués pendiente"},
]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="language_matrix.py")
    p.add_argument("--out", required=True)
    p.add_argument("--threshold-human", type=int, default=3)
    return p.parse_args(argv)


def write_atomic(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    human_count = sum(1 for p in PAIRS if p["evaluation_kind"] == "human_approved")
    stable = human_count >= args.threshold_human
    payload = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "skill": "notemartin-study-translate",
        "schema_version": "110",
        "threshold_human_approved": args.threshold_human,
        "stable": stable,
        "human_approved_count": human_count,
        "pairs": PAIRS,
        "planned_pairs": PLANNED_PAIRS,
        "notes": [
            "Las entradas con evaluation_kind=human_approved acreditan firma humana real.",
            "Las entradas con evaluation_kind=assisted cumplen los gates deterministas; no demuestran equivalencia semántica.",
            "El par he→es y los demás RTL están sujetos a la fase 108 (fixtures bidireccionales).",
        ],
    }
    write_atomic(Path(args.out), payload)
    print(f"ok: language_matrix ({len(PAIRS)} pares activos, "
          f"{human_count} con firma humana, stable={stable}) -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
