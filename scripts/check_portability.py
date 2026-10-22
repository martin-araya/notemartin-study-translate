"""Construye la matriz de portabilidad (fase 147).

Regla dura: una fila de la matriz **nunca** llega a `verified` sin un
informe de ejecución real. `design_only` significa «esto debería funcionar
y aquí no se ha comprobado», que no es lo mismo que «no funciona».

Uso::

    python scripts/check_portability.py \\
        --probe reports/maintenance/platform_probe.json \\
        --external reports/maintenance/external/linux.json \\
        --out reports/maintenance/portability_matrix.json
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

# Sistemas que el paquete declara como objetivo. `verified` solo con
# evidencia; el resto queda en `design_only` hasta que exista una
# ejecución registrada.
TARGET_SYSTEMS = (
    {"system_id": "macos-darwin", "label": "macOS sobre Darwin",
     "requirement": "python >= 3.9, coreutils de POSIX, fcntl"},
    {"system_id": "linux-cpython", "label": "Linux con CPython",
     "requirement": "python >= 3.9, coreutils de POSIX, fcntl"},
    {"system_id": "windows-cpython", "label": "Windows con CPython",
     "requirement": "python >= 3.9; sin fcntl (usa el fallback threading.Lock)"},
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="check_portability.py")
    p.add_argument("--probe", required=True, help="Sonda del sistema actual")
    p.add_argument("--external", action="append", default=[],
                   help="Informes de ejecución en otros sistemas. Repetible.")
    p.add_argument("--out", required=True)
    return p.parse_args(argv)


def load_json(path: str | None) -> dict | None:
    if not path:
        return None
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _system_id(report: dict) -> str:
    if report.get("os_name") == "nt":
        return "windows-cpython"
    if report.get("os_name") == "posix" and str(report.get("platform", "")).startswith("darwin"):
        return "macos-darwin"
    if report.get("os_name") == "posix":
        return "linux-cpython"
    return str(report.get("platform") or "desconocido")


def build_matrix(local: dict | None, externals: list[dict]) -> dict:
    evidence: dict[str, dict] = {}
    if local:
        evidence[_system_id(local)] = {"report": local, "source": "local"}
    for report in externals:
        if report:
            evidence[_system_id(report)] = {"report": report, "source": "external"}

    rows = []
    for target in TARGET_SYSTEMS:
        system_id = target["system_id"]
        found = evidence.get(system_id)
        if found:
            rows.append({
                "system_id": system_id,
                "label": target["label"],
                "requirement": target["requirement"],
                "status": "verified",
                "evidence": found["report"],
                "executed_at": found["report"].get("generated_at"),
                "source": found["source"],
            })
        else:
            rows.append({
                "system_id": system_id,
                "label": target["label"],
                "requirement": target["requirement"],
                "status": "design_only",
                "evidence": None,
                "executed_at": None,
                "source": None,
                "reason": "no hay informe de ejecución en este sistema",
            })
    return {
        "generated_at": now_iso(),
        "verified_systems": [row["system_id"] for row in rows if row["status"] == "verified"],
        "design_only_systems": [row["system_id"] for row in rows if row["status"] == "design_only"],
        "rows": rows,
        "claim": (
            "verified significa que la suite se ejecutó en ese sistema. "
            "design_only significa que el paquete está diseñado para él y no se ha comprobado."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    local = load_json(args.probe)
    externals = [load_json(path) for path in args.external]
    if local is None and not any(externals):
        print("error: no hay ninguna sonda legible", file=sys.stderr)
        return 2

    matrix = build_matrix(local, externals)
    write_atomic(Path(args.out), matrix)
    print(
        f"ok: {len(matrix['verified_systems'])} sistemas verificados, "
        f"{len(matrix['design_only_systems'])} solo de diseño -> {args.out}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())