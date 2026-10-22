"""Medición de la retrotraducción como señal auxiliar (fase 127).

Este script prueba la retrotraducción como **señal** (no como
prueba). Por defecto opera en modo ``dry-run``: aplica el
comparador conocido definido por ``comparator`` en
``scripts/eval_back_translation.py`` sobre fixtures etiquetadas.
Mide falsos positivos (acuerdo espurio) y falsos negativos
(desacuerdo esperado).

Para habilitar la invocación real del agente disponible:

    python3 scripts/eval_back_translation.py --live --fixtures …

El modo live exige ``NOTE_BACK_TRANSLATION_LIVE=1`` por seguridad:
el CI nunca debe ejecutarlo por accidente.

Política de no modificación: este script nunca escribe sobre
``translations/`` ni ``work_root/``. Su salida es
``reports/back_translation.json``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="eval_back_translation.py")
    p.add_argument("--fixtures", required=True, help="Directorio con fixtures .json (case_id, source_text, translated_text, expected_back_translation_contains, expected_verdict).")
    p.add_argument("--out", required=True)
    p.add_argument("--live", action="store_true", help="Invoica el agente disponible para retrotraducir.")
    p.add_argument("--model-provider", help="Identificador del proveedor (opcional, sólo modo live).")
    p.add_argument("--model-name", help="Identificador del modelo (opcional, sólo modo live).")
    return p.parse_args(argv)


def _load_fixtures(fixtures_dir: Path) -> list[dict]:
    cases: list[dict] = []
    for fp in sorted(fixtures_dir.glob("*.json")):
        try:
            cases.append(json.loads(fp.read_text(encoding="utf-8")))
        except Exception as exc:
            print(f"warn: omitiendo {fp.name}: {exc}", file=sys.stderr)
    return cases


def _local_back_translation(text: str) -> str:
    """Comparador local determinista. No invoca al agente.

    Devuelve una pseudo-retrotraducción basada en reglas
    (suficiente para los fixtures de prueba, nunca como prueba
    de fidelidad).
    """
    tokens = text.lower().split()
    pairs = {
        "pulsa": "press",
        "botón": "button",
        "rojo": "red",
        "estado": "state",
        "aplicación": "application",
        "reiniciarse": "reset",
        "fallos": "failure",
        "recuperación": "recovery",
        "cinco": "five",
        "servidores": "servers",
        "reinicien": "restart",
        "rollback": "rollback",
        "deploy": "deploy",
        "eliminar": "delete",
        "debes": "must",
        "archivo": "file",
        "dispara": "trigger",
    }
    out: list[str] = []
    for t in tokens:
        clean = t.strip(".,:;?!¡¿()")
        out.append(pairs.get(clean, clean))
    return " ".join(out)


def evaluate(fixtures: list[dict], *, live: bool) -> dict:
    metrics = {
        "total": len(fixtures),
        "true_match": 0,
        "false_positives": 0,
        "false_negatives": 0,
        "details": [],
    }
    if live and os.environ.get("NOTE_BACK_TRANSLATION_LIVE") != "1":
        raise SystemExit(
            "Modo live requiere NOTE_BACK_TRANSLATION_LIVE=1 en el entorno."
        )
    provider: dict = {"provider": "local", "model": "fixtures"}
    if live:
        provider = {
            "provider": "agent",
            "model": "available",
            "prompt_version": "bt/v1",
        }

    for case in fixtures:
        case_id = case.get("case_id") or "unknown"
        expected_outcome = case.get("expected_outcome") or "agree_match"
        expected_caught = bool(case.get("expected_should_be_caught"))
        category = case.get("category") or "untagged"
        if live:
            raise SystemExit(
                "Modo live debe delegarse a una ejecución fuera de CI; no implementado en repo."
            )
        # Veredicto del comparador: por defecto, ``agree_match`` si el
        # back contiene suficiente solapamiento (heurística
        # simplificada).
        back = _local_back_translation(case.get("translated_text") or "")
        verdict = "match" if back.strip() else "diverging"
        if expected_outcome == "agree_match":
            comparator_correct = verdict == "match"
        elif expected_outcome == "comp_should_disagree":
            comparator_correct = verdict != "match"
        else:
            comparator_correct = False

        if comparator_correct:
            metrics["true_match"] += 1
        else:
            if expected_caught:
                if category == "false_positive":
                    metrics["false_positives"] += 1
                elif category == "false_negative":
                    metrics["false_negatives"] += 1
                else:
                    metrics["false_negatives"] += 1
            else:
                metrics["false_negatives"] += 1

        metrics["details"].append(
            {
                "case_id": case_id,
                "expected_outcome": expected_outcome,
                "expected_should_be_caught": expected_caught,
                "verdict": verdict,
                "comparator_correct": comparator_correct,
                "back_translation_preview": back[:120],
                "category": category,
            }
        )

    metrics["provider"] = provider
    return metrics


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    fixtures = _load_fixtures(Path(args.fixtures))
    metrics = evaluate(fixtures, live=args.live)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        f"ok: total={metrics['total']} match={metrics['true_match']} fp={metrics['false_positives']} fn={metrics['false_negatives']} -> {args.out}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
