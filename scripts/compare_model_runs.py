"""Compara dos ejecuciones reales de traducción (fase 145).

La aceptación de la fase tiene dos mitades: registrar ejecuciones reales y
**no** comparar respuestas sintéticas con producción. Este comparador
aplica las dos:

- rechaza cualquier registro cuyo `evidence_kind` no sea `real_runs` (código 3),
- rechaza pares no comparables por Procedencia distinta (códigos 4 y 5).

Calcula, por segmento, si la respuesta es idéntica, divergente o falta en
alguno de los dos lados; quantify marcadores de protección y razón de
longitudes. La razón de longitudes se marca siempre `signal_only`: no
demuestra nada sobre el significado.

    0 = comparación hecha
    2 = un registro no es legible
    3 = algún registro no es una ejecución real
    4 = los dos runs son comparables pero no entre sí
    5 = difieren el prompt, el glosario, el perfil, el parser o los hashes
        de fuente

Uso::

    python scripts/compare_model_runs.py \\
        --run-a reports/maintenance/model_runs/run-a.json \\
        --run-b reports/maintenance/model_runs/run-b.json \\
        --out reports/maintenance/model_variation.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from delivery_common import now_iso, write_atomic  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="compare_model_runs.py")
    p.add_argument("--run-a", required=True)
    p.add_argument("--run-b", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--out-detail", default=None,
                   help="Fichero con el texto comparado. Por defecto no se escribe.")
    return p.parse_args(argv)


def load_json(path: str) -> dict | None:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def compatibility(left: dict, right: dict) -> list[str]:
    """Motivos por los que dos ejecuciones no son comparables."""
    reasons: list[str] = []
    for field in ("prompt_version", "glossary_hash", "profile_hash"):
        if left.get(field) != right.get(field):
            reasons.append(f"{field} distinto: {left.get(field)} vs {right.get(field)}")
    for field in ("parser", "anchor_policy", "skill_version"):
        if left.get(field) != right.get(field):
            reasons.append(f"{field} distinto: {left.get(field)} vs {right.get(field)}")
    if left.get("source_hashes") != right.get("source_hashes"):
        reasons.append("los hashes de fuente no coinciden")
    return reasons


def compare(left: dict, right: dict) -> dict:
    left_segments = left.get("segments") or {}
    right_segments = right.get("segments") or {}
    shared = sorted(set(left_segments) & set(right_segments))
    identical = [s for s in shared
                 if left_segments[s]["sha256"] == right_segments[s]["sha256"]]
    diverged = [s for s in shared if s not in identical]
    missing_in_b = sorted(set(left_segments) - set(right_segments))
    missing_in_a = sorted(set(right_segments) - set(left_segments))

    ratios = []
    for sid in shared:
        a, b = left_segments[sid], right_segments[sid]
        if a["chars"] and b["chars"]:
            ratios.append(abs(a["chars"] - b["chars"]) / max(a["chars"], b["chars"]))
    mean_ratio = sum(ratios) / len(ratios) if ratios else 0.0

    compared = len(shared)
    variation = (len(diverged) + len(missing_in_a) + len(missing_in_b)) / compared if compared else 0.0

    return {
        "generated_at": now_iso(),
        "models": {
            "a": {"run_id": left.get("run_id"), "model": left.get("model"),
                  "provider": left.get("provider"), "prompt_version": left.get("prompt_version")},
            "b": {"run_id": right.get("run_id"), "model": right.get("model"),
                  "provider": right.get("provider"), "prompt_version": right.get("prompt_version")},
        },
        "same_model": left.get("model") == right.get("model"),
        "comparable": True,
        "segments_compared": compared,
        "identical": len(identical),
        "diverged": len(diverged),
        "diverged_segments": diverged,
        "missing_in_b": missing_in_b,
        "missing_in_a": missing_in_a,
        "variation_rate": round(variation, 4),
        "marker_totals": {
            "a": sum(s.get("markers", 0) for s in left_segments.values()),
            "b": sum(s.get("markers", 0) for s in right_segments.values()),
        },
        "length_ratio": {
            "signal_only": True,
            "mean_abs_delta_ratio": round(mean_ratio, 4),
            "meaning": "una razón de longitud no demuestra equivalencia semántica",
        },
        "no_semantic_claim": True,
        "two_real_runs": True,
        "texts_compared": False,
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    left = load_json(args.run_a)
    right = load_json(args.run_b)
    if left is None or right is None:
        print("error: alguno de los registros no es legible", file=sys.stderr)
        return 2

    out_path = Path(args.out)
    for side, recording in (("a", left), ("b", right)):
        if recording.get("evidence_kind") != "real_runs" or recording.get("synthetic"):
            report = {
                "generated_at": now_iso(),
                "comparable": False,
                "reason": f"el run {side} no es una ejecución real "
                          f"(evidence_kind={recording.get('evidence_kind')})",
                "no_semantic_claim": True,
                "two_real_runs": False,
            }
            write_atomic(out_path, report)
            print(f"fail: {report['reason']}", file=sys.stderr)
            return 3

    reasons = compatibility(left, right)
    if reasons:
        report = {
            "generated_at": now_iso(),
            "comparable": False,
            "reason": "las dos ejecuciones no son comparables",
            "reasons": reasons,
            "no_semantic_claim": True,
            "two_real_runs": True,
        }
        write_atomic(out_path, report)
        print("fail: " + json.dumps(reasons, ensure_ascii=False), file=sys.stderr)
        return 5

    report = compare(left, right)
    write_atomic(out_path, report)
    print(
        f"ok: {report['segments_compared']} segmentos comparados, "
        f"idénticos={report['identical']} divergentes={report['diverged']} "
        f"variación={report['variation_rate']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())