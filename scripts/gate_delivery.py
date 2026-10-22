"""Gate de entrega (fase 140).

Siete comprobaciones con código de salida propio. El gate solo lee: no
escribe en ``output_root/``, en ``work_root/`` ni en el paquete.

    1 = el árbol canónico cambió o no coincide con la ejecución
    2 = el paquete no coincide con el manifiesto aprobado (fase 136)
    3 = la guía falta, se importa como documentación o está dentro del
        árbol entregable
    4 = el reporte de degradaciones declara pérdida de contenido
    5 = una regla activa sin justificación o con lossiness indebido
    6 = un destino sin activación explícita o sin limitaciones
    7 = desactivar el adaptador no reproduce el paquete canónico

El check 7 se considera cumplido por construcción cuando el paquete
declarado no lleva adaptación aplicada: en ese caso el paquete ES el
canónico. Si el paquete sí fue adaptado, hace falta comparar con el
paquete canónico y el gate falla sin ese archivo.

Uso::

    python scripts/gate_delivery.py \\
        --manifest work_root/run-001/manifest.json \\
        --canonical output_root/run-001 \\
        --package dist/run-001-notion-manual.zip \\
        --package-manifest reports/delivery/package_manifest.json \\
        --package-validation reports/delivery/package_validation.json \\
        --guide reports/delivery/run-001/DELIVERY.md \\
        --output-tree output_root/run-001 \\
        --adaptation-report reports/delivery/adaptation_report.json \\
        --degradation-report reports/delivery_degradations.json \\
        --delivery-matrix reports/delivery_matrix.json \\
        --canonical-package dist/run-001-canonical.zip \\
        --out reports/delivery/gate_delivery.json
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from delivery_common import (  # noqa: E402
    is_within,
    now_iso,
    sha256_file,
    tree_hashes,
    write_atomic,
)
from validate_zip_package import audit  # noqa: E402

EXIT_OK = 0
EXIT_INPUT_ERROR = 2
EXIT_CANONICAL_CHANGED = 1
EXIT_PACKAGE_MISMATCH = 2
EXIT_GUIDE_PLACEMENT = 3
EXIT_CONTENT_LOSS = 4
EXIT_RULE_UNDECLARED = 5
EXIT_DESTINATION_UNDECLARED = 6
EXIT_DISABLED_MISMATCH = 7


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="gate_delivery.py")
    p.add_argument("--manifest", required=True)
    p.add_argument("--canonical", required=True)
    p.add_argument("--package", required=True)
    p.add_argument("--package-manifest", required=True)
    p.add_argument("--package-validation")
    p.add_argument("--guide")
    p.add_argument("--output-tree")
    p.add_argument("--adaptation-report")
    p.add_argument("--degradation-report")
    p.add_argument("--delivery-matrix")
    p.add_argument("--canonical-package")
    p.add_argument("--out", required=True)
    return p.parse_args(argv)


def load_json(path: str | None):
    if not path:
        return None
    target = Path(path)
    if not target.exists():
        return None
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def zip_members(path: Path) -> list[str]:
    with zipfile.ZipFile(path, "r") as zf:
        return sorted(zf.namelist())


def check_canonical(manifest: dict, canonical: Path, adaptation: dict | None) -> dict:
    current = tree_hashes(canonical)
    failures: list[str] = []
    if adaptation:
        before = adaptation.get("canonical_hashes_before")
        after = adaptation.get("canonical_hashes_after")
        if before and after and before != after:
            failures.append("el informe de adaptación declara que el canónico cambió")
        if after and after != current:
            failures.append("los hashes actuales del canónico no coinciden con la ejecución")
        if not before and not after:
            failures.append("el informe de adaptación no registra los hashes del canónico")
    else:
        failures.append("falta el informe de adaptación para comprobar el canónico")
    return {"check": "canonical_untouched", "ok": not failures, "failures": failures,
            "files": len(current)}


def check_package(package: Path, package_validation: dict | None,
                  package_manifest: dict | None, manifest: dict) -> dict:
    failures: list[str] = []
    if not package_manifest:
        return {"check": "package_matches_manifest", "ok": False,
                "failures": ["falta el manifiesto del paquete"]}
    if package_manifest.get("guide_outside_package") is not True:
        failures.append("el manifiesto del paquete no declara guide_outside_package")

    live = audit(package, package_manifest, manifest)
    if not live["ok"]:
        failures.append(
            f"el paquete tiene {len(live['violations'])} violaciones al revalidarlo"
        )
    if package_validation is None:
        failures.append("falta el informe de validación del paquete (fase 136)")
    elif package_validation.get("ok") is not True:
        failures.append("el informe de validación declara el paquete inválido")
    elif package_validation.get("violations"):
        failures.append("el informe de validación conserva violaciones")

    return {
        "check": "package_matches_manifest",
        "ok": not failures,
        "failures": failures,
        "live_audit": {"violations": live["violations"], "members": live["observed_members"]},
    }


def check_guide(guide: str | None, output_tree: str | None, package: Path) -> dict:
    failures: list[str] = []
    if not guide:
        return {"check": "guide_outside_importable_tree", "ok": False,
                "failures": ["falta la guía de entrega (fase 137)"]}
    guide_path = Path(guide)
    if not guide_path.exists():
        failures.append(f"la guía no existe: {guide}")
    if output_tree:
        tree = Path(output_tree)
        if tree.exists() and is_within(guide_path, tree):
            failures.append("la guía está dentro del árbol importable")
    try:
        members = zip_members(package)
    except (OSError, zipfile.BadZipFile):
        members = []
    if guide_path.name in {Path(m).name for m in members}:
        failures.append("la guía está dentro del paquete")
    return {"check": "guide_outside_importable_tree", "ok": not failures, "failures": failures}


def check_degradations(report: dict | None) -> dict:
    failures: list[str] = []
    if not report:
        failures.append("falta el reporte de degradaciones (fase 138)")
    else:
        losses = report.get("counts", {}).get("content_loss", 0)
        if losses:
            failures.append(f"{losses} diferencias clasificadas como content_loss")
        if not report.get("ok"):
            failures.append("el reporte de degradaciones no está en verde")
    return {"check": "no_content_loss", "ok": not failures, "failures": failures}


def check_rules(adaptation: dict | None, package_manifest: dict | None) -> dict:
    failures: list[str] = []
    declared = (package_manifest or {}).get("adaptation") or {}
    applied = declared.get("applied_rules") or []
    if applied:
        if adaptation is None:
            failures.append("el paquete declara adaptación pero falta el informe de adaptación")
        else:
            for change in adaptation.get("changes") or []:
                if change.get("dry_run"):
                    continue
                if not change.get("rule_id"):
                    failures.append("cambio sin rule_id en el informe de adaptación")
                if not change.get("lossiness"):
                    failures.append("cambio sin lossiness declarado")
                if change.get("lossiness") == "content_loss":
                    failures.append(f"regla con pérdida de contenido: {change.get('rule_id')}")
    if adaptation and adaptation.get("rules_skipped"):
        failures.append("el informe de adaptación conserva reglas rechazadas: "
                        + ", ".join(adaptation["rules_skipped"]))
    return {"check": "rules_declared", "ok": not failures, "failures": failures}


def check_destinations(matrix: dict | None) -> dict:
    failures: list[str] = []
    if not matrix:
        failures.append("falta la matriz de destinos (fase 139)")
    else:
        destinations = matrix.get("destinations") or []
        if not destinations:
            failures.append("la matriz no declara destinos")
        for destination in destinations:
            did = destination.get("destination_id") or "(sin id)"
            if destination.get("activation") != "explicit":
                failures.append(f"destino sin activación explícita: {did}")
            if not destination.get("limitations"):
                failures.append(f"destino sin limitaciones declaradas: {did}")
            if destination.get("verified") is True and destination.get("real_app_evidence") is not True:
                failures.append(f"destino marcado verificado sin evidencia de aplicación real: {did}")
    return {"check": "destinations_declared", "ok": not failures, "failures": failures}


def check_disabled_reproduces(package: Path, package_manifest: dict | None,
                              canonical_package: str | None) -> dict:
    failures: list[str] = []
    if not (package_manifest or {}).get("adaptation"):
        return {
            "check": "disabled_adapter_reproduces_canonical",
            "ok": True,
            "failures": [],
            "detail": "el paquete no lleva adaptación aplicada: es el canónico por construcción",
        }
    if not canonical_package:
        failures.append("el paquete está adaptado y falta el paquete canónico para comparar")
    else:
        canonical_path = Path(canonical_package)
        if not canonical_path.exists():
            failures.append(f"el paquete canónico no existe: {canonical_path}")
        else:
            if zip_members(canonical_path) != zip_members(package):
                failures.append("los miembros del paquete adaptado difieren del canónico")
            elif sha256_file(canonical_path) != sha256_file(package):
                failures.append("los bytes del paquete adaptado difieren del canónico")
    return {"check": "disabled_adapter_reproduces_canonical", "ok": not failures, "failures": failures}


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest_path = Path(args.manifest)
    canonical = Path(args.canonical)
    package = Path(args.package)
    if not manifest_path.exists() or not canonical.is_dir() or not package.exists():
        print("error: manifiesto, árbol canónico o paquete inexistente", file=sys.stderr)
        return EXIT_INPUT_ERROR

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    package_manifest = load_json(args.package_manifest)
    package_validation = load_json(args.package_validation)
    adaptation = load_json(args.adaptation_report)
    degradations = load_json(args.degradation_report)
    matrix = load_json(args.delivery_matrix)

    checks = [
        check_canonical(manifest, canonical, adaptation),
        check_package(package, package_validation, package_manifest, manifest),
        check_guide(args.guide, args.output_tree, package),
        check_degradations(degradations),
        check_rules(adaptation, package_manifest),
        check_destinations(matrix),
        check_disabled_reproduces(package, package_manifest, args.canonical_package),
    ]

    codes = {
        "canonical_untouched": EXIT_CANONICAL_CHANGED,
        "package_matches_manifest": EXIT_PACKAGE_MISMATCH,
        "guide_outside_importable_tree": EXIT_GUIDE_PLACEMENT,
        "no_content_loss": EXIT_CONTENT_LOSS,
        "rules_declared": EXIT_RULE_UNDECLARED,
        "destinations_declared": EXIT_DESTINATION_UNDECLARED,
        "disabled_adapter_reproduces_canonical": EXIT_DISABLED_MISMATCH,
    }
    failures = [c for c in checks if not c["ok"]]
    result = {
        "generated_at": now_iso(),
        "run_id": manifest.get("run_id"),
        "destination_id": (package_manifest or {}).get("destination_id"),
        "checks": checks,
        "ok": not failures,
        "failed_checks": [c["check"] for c in failures],
        "exit_codes": [codes[c["check"]] for c in failures],
    }
    write_atomic(Path(args.out), result)

    if failures:
        print("fail: " + json.dumps(result["failed_checks"], ensure_ascii=False), file=sys.stderr)
        return result["exit_codes"][0]
    print(f"ok: gate de entrega aprobado ({len(checks)} comprobaciones)")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())