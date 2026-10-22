"""Repara la divergencia entre `state` y `current_state` de un manifiesto.

Hay dos direcciones de divergencia y ninguna se repara sin evidencia.

**`state` adelantado.** ``approve_pilot.py`` escribía ``state: approved`` y
dejaba ``current_state: translated``. Esta herramienta **adopta** `state`
como `current_state` cuando el historial del archivo contiene esa
transición: la evidencia de que la aprobación ocurrió está en
`state_history`, no en el campo que el script dejó sin actualizar.

**`current_state` adelantado.** En la corrida beta quedaron 2608 de 2682
registros con ``state: translated`` y ``current_state: prepared``, sin
transición que lo sostenga. Todos los gates leen `current_state`, así que
la divergencia pasaba desapercibida mientras cualquier lector de `state`
leía 2608 documentos traducidos que no lo están (INV-12). Aquí `state` se
**degrada** a `current_state` cuando el historial sostiene `current_state`
y no `state`. El historial no se toca: degradar un campo no afirma ninguna
transición nueva.

Si el historial no sostiene ninguno de los dos, el registro se queda como
está y se reporta.

    python3 scripts/repair_state_field.py --in manifest.json --apply \\
        --out manifest.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

REPAIR_NOTE = (
    "current_state reparado desde state: approve_pilot.py escribía solo "
    "el campo state (defecto corregido en la 0.3.0)"
)

DEGRADE_NOTE = (
    "state degradado a current_state: declaraba un estado que "
    "state_history no sostiene (defecto corregido en la 0.3.0)"
)


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_atomic(target, payload: dict) -> None:
    target = str(target)
    tmp = target + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    os.replace(tmp, target)


def repair(manifest: dict, now: str | None = None) -> tuple[dict, dict]:
    stamp = now or now_iso()
    repaired = 0
    degraded = 0
    unchanged = 0
    without_evidence: list[dict] = []
    files = manifest.get("files") or []

    for record in files:
        state = record.get("state")
        current = record.get("current_state")
        if not state or state == current:
            unchanged += 1
            continue
        history = record.get("state_history") or []
        last = history[-1]["state"] if history else None
        if last == state:
            # El historial sostiene `state`: la transición ocurrió y el
            # campo que la escribió no la alcanzó.
            record["current_state"] = state
            notes = record.setdefault("notes", [])
            if REPAIR_NOTE not in notes:
                notes.append(REPAIR_NOTE)
            record["last_transition_at"] = history[-1].get("timestamp", stamp)
            repaired += 1
            continue
        if last == current:
            # El historial sostiene `current_state` y no `state`: el campo
            # adelantado afirma trabajo que nunca se registró.
            record["state"] = current
            notes = record.setdefault("notes", [])
            if DEGRADE_NOTE not in notes:
                notes.append(DEGRADE_NOTE)
            degraded += 1
            continue
        without_evidence.append({
            "path": record.get("path"),
            "current_state": current,
            "state": state,
            "last_history_state": last,
        })

    return manifest, {
        "files": len(files),
        "repaired": repaired,
        "degraded": degraded,
        "unchanged": unchanged,
        "without_evidence": without_evidence,
        "repaired_at": stamp,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="repair_state_field.py")
    p.add_argument("--in", dest="source", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--apply", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args(argv)

    try:
        manifest = json.loads(open(args.source, encoding="utf-8").read())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: no se puede leer el manifiesto: {exc}", file=sys.stderr)
        return 2
    if not isinstance(manifest, dict) or "files" not in manifest:
        print("error: el archivo no parece un manifiesto", file=sys.stderr)
        return 2

    repaired_manifest, report = repair(manifest)

    if report["without_evidence"]:
        print(
            f"advertencia: {len(report['without_evidence'])} archivos declaran un estado "
            "sin transición en su historial; se dejan como están",
            file=sys.stderr,
        )
        for entry in report["without_evidence"]:
            print(
                f"  {entry['path']}: current_state={entry['current_state']} "
                f"state={entry['state']} historial={entry['last_history_state']}",
                file=sys.stderr,
            )

    if args.apply and not args.dry_run:
        write_atomic(args.out, repaired_manifest)

    print(json.dumps({
        "ok": True,
        "written": bool(args.apply and not args.dry_run),
        "out": args.out,
        "repaired_from_state": report["repaired"],
        "degraded_to_current": report["degraded"],
        **report,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())