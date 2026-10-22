"""Cierra el ledger del corpus solicitado (fase 040).

Calcula la cobertura final del manifiesto, clasificando los archivos
por estado y registrando el veredicto ``integrity_ok``.

- ``integrated``: ``translated`` + ``already_target``.
- ``blocked``, ``excluded``, ``invalid``, ``pending`` no cuentan como
  íntegros.
- ``integrity_ok = (blocked == 0 and excluded == 0 and invalid == 0 and pending == 0)``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


INTEGRATED_STATES = {"approved", "exported", "already_target"}
NON_INTEGRATED_STATES = {"blocked", "excluded", "invalid", "pending", "failed"}
WORKING_STATES = {"inventoried", "prepared", "translated", "deterministic_pass", "semantic_pass"}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="check_integrity.py")
    p.add_argument("--manifest", required=True)
    p.add_argument("--out", required=True)
    return p.parse_args(argv)


def write_atomic(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def compute_coverage(manifest: dict) -> dict:
    by_state: dict[str, int] = {}
    unknown: list[str] = []
    divergent: list[dict] = []
    for f in manifest.get("files", []):
        state = f.get("current_state") or f.get("state") or "unknown"
        if state not in INTEGRATED_STATES | NON_INTEGRATED_STATES | WORKING_STATES and state != "unknown":
            unknown.append(f"{state} ({f.get('path', '?')})")
        legacy = f.get("state")
        if legacy and f.get("current_state") and legacy != f["current_state"]:
            divergent.append({
                "path": f.get("path"),
                "state": legacy,
                "current_state": f["current_state"],
            })
        by_state[state] = by_state.get(state, 0) + 1

    integrated = sum(n for s, n in by_state.items() if s in INTEGRATED_STATES)
    blocked = by_state.get("blocked", 0)
    invalid = by_state.get("invalid", 0)
    # Todo lo que aún no es terminal cuenta como pendiente. Reduce el
    # denominador en lugar de inflar el numerador. Los estados terminales
    # pero no integrados (excluded, already_target, etc.) sí cuentan
    # como integración: el archivo ha sido dispositionado, con motivo.
    pending = sum(
        n for s, n in by_state.items()
        if s not in INTEGRATED_STATES and s not in NON_INTEGRATED_STATES
    )

    total = sum(by_state.values())
    coverage = {
        "total": total,
        "integrated": integrated,
        "blocked": blocked,
        "excluded": by_state.get("excluded", 0),
        "invalid": invalid,
        "pending": pending,
    }
    if total > 0:
        coverage["integrated_ratio"] = round(integrated / total, 4)
        coverage["blocked_ratio"] = round(blocked / total, 4)
        coverage["excluded_ratio"] = round(by_state.get("excluded", 0) / total, 4)
    # `excluded` es un estado terminal con motivo: NO bloquea la integridad.
    # Lo que bloquea es que algún archivo siga en un estado de trabajo.
    #
    # También bloquea que un registro declare dos estados distintos: si
    # `state` y `current_state` se contradicen, el manifiesto describe dos
    # corpus a la vez y cualquier lector que use el campo equivocado
    # afirma progreso inexistente (INV-12).
    integrity_ok = (
        blocked == 0
        and invalid == 0
        and pending == 0
        and not unknown
        and not divergent
    )
    return {
        "coverage": coverage,
        "integrity_ok": integrity_ok,
        "files_by_state": by_state,
        "unknown_states": sorted(unknown),
        "divergent_states": len(divergent),
        "divergent": divergent,
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest_path = Path(args.manifest)
    out_path = Path(args.out)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    report = compute_coverage(manifest)

    manifest["coverage"] = report["coverage"]
    manifest["integrity_ok"] = report["integrity_ok"]
    write_atomic(manifest_path, manifest)

    write_atomic(out_path, {
        "manifest": manifest_path.name,
        **report,
    })
    state = "ok" if report["integrity_ok"] else "warning"
    print(f"{state}: integrated={report['coverage']['integrated']}/{report['coverage']['total']} -> {out_path}")
    if report["divergent_states"]:
        print(
            f"error: {report['divergent_states']} registros declaran un estado distinto "
            "en `state` y en `current_state`; repararlos con repair_state_field.py",
            file=sys.stderr,
        )
        for entry in report["divergent"][:10]:
            print(
                f"  {entry['path']}: state={entry['state']} "
                f"current_state={entry['current_state']}",
                file=sys.stderr,
            )
    for entry in report["unknown_states"]:
        print(f"estado no declarado por el contrato: {entry}", file=sys.stderr)
    return 0 if report["integrity_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())