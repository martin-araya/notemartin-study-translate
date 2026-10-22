"""Gate del corpus permanente de regresión (fase 141).

Comprueba que cada fallo conocido declarado en
``schemas/regression_registry.schema.json`` tiene **un caso positivo y un
caso negativo reproducibles**:

- el fixture existe y contiene la variante declarada,
- la procedencia está completa y autorizada,
- el nodeid de pytest declarado existe de verdad,
- el catálogo de fallos conocidos no tiene huecos.

Con ``--reproduce`` ejecuta además los nodeids declarados en un
subproceso y exige que todos pasen. Sin ese flag el gate solo comprueba la
integridad del registro, para poder invocarse desde dentro de una suite.

Códigos de salida:

    1 = estructura o esquema del registro inválido (incluye ``case_id`` duplicado)
    2 = el fixture del caso positivo no existe
    3 = el fixture del caso negativo no existe
    4 = el nodeid del caso positivo no existe
    5 = el nodeid del caso negativo no existe
    6 = procedencia ausente o incompleta
    7 = un fallo conocido no tiene entrada en el registro
    8 = la variante declarada no existe dentro del fixture
    9 = ``--reproduce`` falló: el registro no es reproducible

Uso::

    python scripts/regression_gate.py \\
        --registry evals/regression/registry.json \\
        --root . \\
        --out reports/maintenance/regression.json

    python scripts/regression_gate.py --reproduce \\
        --registry evals/regression/registry.json \\
        --out reports/maintenance/regression.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from delivery_common import now_iso, write_atomic  # noqa: E402

SCHEMA_PATH = ROOT / "schemas" / "regression_registry.schema.json"
SIDES = ("positive", "negative")
PROVENANCE_FIELDS = ("kind", "source", "license_note", "anonymized", "justification")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="regression_gate.py")
    p.add_argument("--registry", default=str(ROOT / "evals" / "regression" / "registry.json"))
    p.add_argument("--root", default=str(ROOT))
    p.add_argument("--out", required=True)
    p.add_argument("--reproduce", action="store_true",
                   help="Ejecuta los nodeids declarados y exige que pasen.")
    p.add_argument("--skip-nodeids", action="store_true",
                   help="No comprueba la existencia de los nodeids (uso interno).")
    return p.parse_args(argv)


def load_registry(path: Path) -> dict | None:
    """Devuelve el registro o ``None`` si no se puede leer o parsear."""
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def schema_errors(registry: dict) -> list[str]:
    """Errores de esquema. Devuelve lista vacía si el registro es válido."""
    try:
        import jsonschema
    except ImportError:  # pragma: no cover - jsonschema está pineado
        return []
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    return [
        f"{'/'.join(str(p) for p in err.absolute_path) or '(raíz)'}: {err.message}"
        for err in sorted(validator.iter_errors(registry), key=lambda e: list(e.absolute_path))
    ]


def collect_nodeids(files: list[str], root: Path) -> set[str]:
    """Nodeids que pytest realmente puede colectar."""
    if not files:
        return set()
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", *sorted(set(files))],
        cwd=str(root), capture_output=True, text=True, check=False,
    )
    return {line.strip() for line in proc.stdout.splitlines() if line.strip().startswith("tests/")}


def _provenance_ok(entry: dict) -> list[str]:
    provenance = entry.get("provenance") or {}
    missing = [field for field in PROVENANCE_FIELDS if not provenance.get(field)
               and provenance.get(field) is not True]
    if provenance.get("kind") == "fixture_excerpt" and not provenance.get("justification"):
        missing.append("justification")
    if provenance.get("anonymized") is not True:
        missing.append("anonymized=true")
    return missing


def check_registry(
    registry_path: Path,
    root: Path = ROOT,
    nodeid_exists=None,
    skip_nodeids: bool = False,
) -> dict:
    """Audita el registro. ``nodeid_exists`` permite inyectar un comprobador."""
    registry_path = Path(registry_path)
    failures: dict[str, list[str]] = {
        str(code): [] for code in range(1, 10)
    }
    gaps: list[str] = []

    registry = load_registry(registry_path)
    if registry is None:
        failures["1"].append(f"el registro no se puede leer: {registry_path}")
        return _report(registry_path, failures, gaps, {})

    for message in schema_errors(registry):
        failures["1"].append(message)

    cases = registry.get("cases") or []
    seen_ids: set[str] = set()
    by_failure: dict[str, dict[str, int]] = {}
    provenance_counts: dict[str, int] = {"synthetic": 0, "fixture_excerpt": 0}

    for entry in cases:
        case_id = entry.get("case_id") or "(sin case_id)"
        if case_id in seen_ids:
            failures["1"].append(f"case_id duplicado: {case_id}")
        seen_ids.add(case_id)
        failure = entry.get("known_failure") or "(sin known_failure)"
        bucket = by_failure.setdefault(failure, {"positive": 0, "negative": 0})

        missing = _provenance_ok(entry)
        if missing:
            failures["6"].append(f"{case_id}: procedencia incompleta ({', '.join(missing)})")
        kind = (entry.get("provenance") or {}).get("kind")
        if kind in provenance_counts:
            provenance_counts[kind] += 1

        for side in SIDES:
            spec = entry.get(side) or {}
            fixture_rel = spec.get("fixture") or ""
            fixture_path = root / fixture_rel
            code = "2" if side == "positive" else "3"
            if not fixture_rel or not fixture_path.exists():
                failures[code].append(f"{case_id}: fixture {side} inexistente ({fixture_rel})")
                continue
            bucket[side] += 1
            try:
                fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                failures[code].append(f"{case_id}: fixture {side} ilegible ({exc})")
                continue
            variant_key = spec.get("variant_key")
            if variant_key not in fixture:
                failures["8"].append(
                    f"{case_id}: el fixture {fixture_rel} no contiene la variante {variant_key!r}"
                )

            nodeid = ((entry.get("tests") or {}).get(side)) or ""
            if not skip_nodeids:
                code_nodeid = "4" if side == "positive" else "5"
                if not nodeid:
                    failures[code_nodeid].append(f"{case_id}: nodeid {side} vacío")
                elif nodeid_exists is not None and not nodeid_exists(nodeid):
                    failures[code_nodeid].append(f"{case_id}: nodeid {side} inexistente ({nodeid})")

    for failure in registry.get("known_failures") or []:
        if failure not in by_failure:
            gaps.append(failure)

    counts = {
        "cases": len(cases),
        "known_failures": len(registry.get("known_failures") or []),
        "by_known_failure": by_failure,
        "provenance": provenance_counts,
    }
    return _report(registry_path, failures, gaps, counts)


def _report(registry_path: Path, failures: dict[str, list[str]], gaps: list[str],
            counts: dict) -> dict:
    populated = {code: messages for code, messages in failures.items() if messages}
    return {
        "generated_at": now_iso(),
        "registry": str(registry_path),
        "ok": not populated and not gaps,
        "failures": populated,
        "gaps": sorted(gaps),
        "counts": counts,
    }


def exit_code_for(report: dict) -> int:
    """Primer código de salida no nulo según el orden de severidad."""
    for code in sorted(report.get("failures") or {}):
        if str(code).isdigit():
            return int(code)
    return 7 if report.get("gaps") else 0


def declared_nodeids(registry: dict) -> list[str]:
    return sorted({
        (entry.get("tests") or {}).get(side)
        for entry in registry.get("cases") or []
        for side in SIDES
        if (entry.get("tests") or {}).get(side)
    })


def reproduce(registry: dict, root: Path) -> tuple[int, str]:
    nodeids = declared_nodeids(registry)
    if not nodeids:
        return 1, "el registro no declara nodeids"
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", *nodeids],
        cwd=str(root), capture_output=True, text=True, check=False,
    )
    return proc.returncode, (proc.stdout + proc.stderr)[-4000:]


def registry_test_files(registry: dict) -> list[str]:
    return sorted({
        nodeid.split("::")[0]
        for nodeid in declared_nodeids(registry)
        if "::" in nodeid
    })


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    registry_path = Path(args.registry)
    root = Path(args.root).resolve()

    if not args.skip_nodeids:
        registry = load_registry(registry_path) or {}
        collected = collect_nodeids(registry_test_files(registry), root)

        def nodeid_exists(nodeid: str) -> bool:
            return nodeid in collected
    else:
        def nodeid_exists(nodeid: str) -> bool:
            return True

    report = check_registry(
        registry_path, root=root, nodeid_exists=nodeid_exists,
        skip_nodeids=args.skip_nodeids,
    )

    if args.reproduce and not report["failures"] and not report["gaps"]:
        registry = load_registry(registry_path) or {}
        code, output = reproduce(registry, root)
        report["reproduce"] = {"exit_code": code, "nodeids": len(declared_nodeids(registry))}
        if code != 0:
            report["failures"].setdefault("9", []).append(
                f"pytest no reproduce el registro (código {code})"
            )
            report["reproduce"]["output_tail"] = output
            report["ok"] = False

    write_atomic(Path(args.out), report)
    code = exit_code_for(report)
    if code:
        print(
            f"fail: registro de regresión con hallazgos: {json.dumps(report['failures'], ensure_ascii=False)}"
            + (f" huecos={report['gaps']}" if report["gaps"] else ""),
            file=sys.stderr,
        )
        return code
    print(
        f"ok: {report['counts']['cases']} casos, "
        f"{report['counts']['known_failures']} fallos conocidos, sin huecos"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())