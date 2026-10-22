"""Validación de vigencia de las aprobaciones (fase 124).

Interfaz de línea de comandos de la fase 124. La regla vive en
``scripts/approval_freshness.py`` (núcleo) porque la usan también
``scripts/regression_detectors.py`` y la promoción de estados; un módulo
opcional no puede ser dependencia del flujo básico.

Lee el ``manifest.json``, busca el campo ``approvals[]`` y
compara cada ``target_hash`` (y, si están presentes, ``target_glossary_hash``,
``target_anchor_hash`` y ``target_profile_hash``) con los valores actuales.

El script nunca reescribe ``manifest.json``. Emite un reporte
``reports/approvals.json`` con el estado calculado. Devuelve código
distinto de cero si alguna aprobación queda ``stale``.

    0 = ninguna aprobación obsoleta
    1 = hay aprobaciones obsoletas
    2 = el manifiesto no se puede leer o no es JSON
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from approval_freshness import HASH_FIELDS, evaluate  # noqa: E402,F401

EXIT_OK = 0
EXIT_STALE = 1
EXIT_INPUT = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="check_approval_freshness.py")
    p.add_argument("--manifest", required=True)
    p.add_argument("--current-glossary-hash", help="SHA-256 hex del glossary actual (opcional).")
    p.add_argument("--current-anchor-hash", help="SHA-256 hex de anchors actual (opcional).")
    p.add_argument("--current-profile-hash", help="SHA-256 hex del profile actual (opcional).")
    p.add_argument("--out", required=True)
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest_path = Path(args.manifest)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        print(f"error: no se puede leer {args.manifest}: {err}", file=sys.stderr)
        return EXIT_INPUT

    overrides: dict[str, str | None] = {}
    if args.current_glossary_hash:
        overrides["target_glossary_hash"] = args.current_glossary_hash
    if args.current_anchor_hash:
        overrides["target_anchor_hash"] = args.current_anchor_hash
    if args.current_profile_hash:
        overrides["target_profile_hash"] = args.current_profile_hash

    report = evaluate(manifest, overrides)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        f"ok: stale={report['stale']} valid={report['valid']} superseded={report['superseded']} -> {args.out}"
    )
    return EXIT_STALE if report["stale"] else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())