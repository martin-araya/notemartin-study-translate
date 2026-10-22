"""Gate de escala (fase 120 del roadmap).

Aplica cinco verificaciones sobre un par de manifiestos ``serial``
y ``concurrent``:

1. **Cobertura completa**: cada ruta del alcance está en el ledger
   aprobado de **los dos** modos, no solo en el serie.
2. **Mismo ledger**: los dos conjuntos de ``approved_segment_ids``
   coinciden exactamente. La auditoría completa con historial de cambios la
   hace ``scripts/diff_ledgers.py --strict``; este gate compara los dos
   conjuntos y no su historia.
3. **Cero regresiones de enlaces**: el conteo de errores
   ``link_anchor`` no aumenta respecto al serie.
4. **Sin nuevos bloqueos**: ningún archivo se mueve a
   ``blocked`` o ``failed`` por causa del paralelismo.
5. **Tolerancia de tiempo**: el concurrente no supera al serie
   + 10 % en duración total.

Los dos modos cuentan como aprobado **solo lo que tiene traducción real**:
`approved_segment_ids` sale de los candidatos con contenido, no de la
partición asignada. Por eso este gate puede comparar los dos modos: antes,
uno de los dos reportaba cobertura inexistente.

Si las cinco pasan, el gate vuelca ``gates/scale.json`` con
``passed: true``. Si alguna falla, vuelca ``passed: false`` con el
motivo y devuelve código 1.

Uso::

    python3 scripts/gate_scale.py \\
        --serial reports/serial/manifest.json \\
        --concurrent reports/concurrent/manifest.json \\
        --scope scope.json \\
        --tolerance 0.1 \\
        --out reports/gates/scale.json
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="gate_scale.py")
    p.add_argument("--serial", required=True)
    p.add_argument("--concurrent", required=True)
    p.add_argument("--scope", default=None,
                   help="Archivo JSON con la lista de rutas del alcance.")
    p.add_argument("--tolerance", type=float, default=0.1,
                   help="Tolerancia de tiempo concurrente vs serie. Default 0.1 (10 por ciento).")
    p.add_argument("--out", default=None)
    return p.parse_args(argv)


def write_atomic(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def check_coverage(serial_payload: dict, concurrent_payload: dict, scope: set[str] | None) -> tuple[bool, str]:
    if scope is None:
        return True, "sin scope declarado"
    if not scope:
        return True, "scope vacío"
    serial_files = set(serial_payload.get("approved_segment_ids", []))
    concurrent_files = set(concurrent_payload.get("approved_segment_ids", []))
    missing_serial = scope - serial_files
    missing_concurrent = scope - concurrent_files
    if missing_serial or missing_concurrent:
        return False, (
            f"cobertura incompleta: fuera del ledger serie={len(missing_serial)}, "
            f"concurrente={len(missing_concurrent)}"
        )
    return True, "cobertura completa en ambos modos"


def check_ledger(serial_payload: dict, concurrent_payload: dict) -> tuple[bool, str]:
    s = set(serial_payload.get("approved_segment_ids", []))
    c = set(concurrent_payload.get("approved_segment_ids", []))
    only_s = s - c
    only_c = c - s
    if only_s or only_c:
        return False, (
            f"ledgers divergentes: only_in_serial={len(only_s)}, only_in_concurrent={len(only_c)}"
        )
    return True, "ledgers coinciden"


def check_link_regressions(serial_payload: dict, concurrent_payload: dict) -> tuple[bool, str]:
    s_anchors = serial_payload.get("link_anchor_errors", 0)
    c_anchors = concurrent_payload.get("link_anchor_errors", 0)
    if c_anchors > s_anchors:
        return False, f"regresión de enlaces: serial={s_anchors}, concurrent={c_anchors}"
    return True, f"sin regresión de enlaces: serial={s_anchors}, concurrent={c_anchors}"


def check_new_blockers(serial_payload: dict, concurrent_payload: dict) -> tuple[bool, str]:
    s_blocked = serial_payload.get("blocked_count", 0)
    c_blocked = concurrent_payload.get("blocked_count", 0)
    s_failed = serial_payload.get("failed_count", 0)
    c_failed = concurrent_payload.get("failed_count", 0)
    if c_blocked > s_blocked or c_failed > s_failed:
        return False, (
            f"nuevos bloqueos: bloqueados {s_blocked}->{c_blocked}, "
            f"fallos {s_failed}->{c_failed}"
        )
    return True, "sin nuevos bloqueos"


def check_time_tolerance(serial_payload: dict, concurrent_payload: dict, tolerance: float) -> tuple[bool, str]:
    s_dur = serial_payload.get("duration_sec")
    c_dur = concurrent_payload.get("duration_sec")
    if s_dur is None or c_dur is None:
        return True, "duración no medida; gate de tiempo omitido"
    ceiling = s_dur * (1.0 + tolerance)
    if c_dur > ceiling:
        return False, (
            f"tiempo concurrente {c_dur:.2f}s > {ceiling:.2f}s (serie {s_dur:.2f}s + "
            f"{int(tolerance * 100)}%)"
        )
    return True, f"tiempo concurrente {c_dur:.2f}s <= {ceiling:.2f}s"


def load_scope(path: str | None) -> set[str] | None:
    if not path:
        return None
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        return set(payload.get("scope", []))
    if isinstance(payload, list):
        return set(payload)
    return None


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    serial = json.loads(Path(args.serial).read_text(encoding="utf-8"))
    concurrent = json.loads(Path(args.concurrent).read_text(encoding="utf-8"))
    scope = load_scope(args.scope)

    checks = [
        ("coverage", check_coverage(serial, concurrent, scope)),
        ("ledger", check_ledger(serial, concurrent)),
        ("link_regressions", check_link_regressions(serial, concurrent)),
        ("new_blockers", check_new_blockers(serial, concurrent)),
        ("time_tolerance", check_time_tolerance(serial, concurrent, args.tolerance)),
    ]

    failures = [(name, msg) for name, (ok, msg) in checks if not ok]
    payload = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tolerance": args.tolerance,
        "scope_size": len(scope) if scope else None,
        "checks": {name: {"passed": ok, "message": msg} for name, (ok, msg) in checks},
        "passed": not failures,
        "failures": [{"check": name, "message": msg} for name, msg in failures],
    }
    if args.out:
        write_atomic(Path(args.out), payload)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
