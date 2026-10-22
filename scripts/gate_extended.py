"""Gate del release ampliado (fase 149).

Cada número de salida corresponde a una comprobación interna de una fase.
Los **huecos externos** no son fallos: se declaran, se listan y no bloquean
el release local. Lo que bloquea es mentir:

- declarar un módulo activo sin gate,
- declarar `verified` en un sistema sin evidencia,
- afirmar una verificación remota que no existe,
- reintroducir aprobaciones vigentes al migrar manifiestos.

    1 = regresión permanente con hueco o no reproducible (141)
    2 = versionado incoherente (142)
    3 = migración pendiente: manifiesto sin `manifest_version` (143)
    4 = candidato con parser promovido sin migrar dependientes (144)
    5 = el candidato afirma verificación remota sin evidencia (145)
    6 = auditoría documental con hallazgos (146)
    7 = matriz de portabilidad con `verified` sin evidencia (147)
    8 = política de retención ausente o purga sin trazabilidad (148)
    9 = regresión del núcleo: `pytest` en rojo

    0 = todo lo interno en verde

Uso::

    python scripts/gate_extended.py \\
        --candidate reports/maintenance/release_candidate.json \\
        --out reports/maintenance/gate_extended.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from delivery_common import now_iso, write_atomic  # noqa: E402

CHECKS = {
    1: "regresion_permanente",
    2: "versionado",
    3: "migracion_manifiesto",
    4: "parser_promovido",
    5: "afirmacion_remota_sin_evidencia",
    6: "auditoria_documental",
    7: "portabilidad_sin_evidencia",
    8: "retencion_y_trazabilidad",
    9: "regresion_del_nucleo",
}

REMOTE_CLAIMS = ("verificado en notion", "importado en notion", "soportado in notion",
                 "soportado en notion")
HUMAN_SIGNS = ("firma nativa", "firmado por", "revisado por")
NEGATIONS = ("no ", "nunca", "sin ", "not ", "jamas", "pendiente", "sin evidencia",
             "no se ha", "ningun", "ningún")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="gate_extended.py")
    p.add_argument("--candidate", required=True)
    p.add_argument("--root", default=str(ROOT))
    p.add_argument("--out", required=True)
    p.add_argument("--core-exit-code", type=int, default=None,
                   help="Código de salida de la suite del núcleo. Si no se pasa, se lee del candidato.")
    return p.parse_args(argv)


def _load(path: Path) -> dict | None:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def check_regression(root: Path, findings: dict[str, list[str]]) -> None:
    report = _load(root / "reports" / "maintenance" / "regression.json")
    if report is None:
        findings["1"].append("no hay informe del registro de regresión")
        return
    if not report.get("ok"):
        for code, messages in (report.get("failures") or {}).items():
            findings["1"].append(f"registro de regresión, código {code}: {messages}")
    if report.get("gaps"):
        findings["1"].append(f"huecos en el registro: {report['gaps']}")
    if not report.get("reproduce"):
        findings["1"].append(
            "el registro no se reprodujo con pytest (falta --reproduce en el informe)"
        )


def check_versioning(root: Path, findings: dict[str, list[str]]) -> None:
    report = _load(root / "reports" / "maintenance" / "versioning.json")
    if report is None:
        findings["2"].append("no hay informe de versionado")
        return
    if not report.get("ok"):
        for code, messages in (report.get("failures") or {}).items():
            findings["2"].append(f"versionado, código {code}: {messages}")


def check_migration(root: Path, findings: dict[str, list[str]]) -> None:
    manifests = sorted((root / "reports").rglob("*.json"))
    for path in manifests:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict) or "files" not in data or "run_id" not in data:
            continue
        if not data.get("manifest_version"):
            findings["3"].append(f"{path.relative_to(root)}: manifiesto sin manifest_version")
        for approval in data.get("approvals") or []:
            if approval.get("status") == "valid" and not approval.get("stale"):
                findings["3"].append(
                    f"{path.relative_to(root)}: aprobación {approval.get('approval_id')} vigente "
                    f"en un manifiesto migrado"
                )


def check_parser(root: Path, candidate: dict, findings: dict[str, list[str]]) -> None:
    report = _load(root / "reports" / "maintenance" / "parser_comparison.json")
    if report is None:
        findings["4"].append("no hay informe de comparación de parser")
        return
    if report.get("promotion") == "blocked" and not report.get("dependents_to_migrate"):
        findings["4"].append("promoción bloqueada sin dependientes declarados")
    for module in candidate.get("modules") or []:
        if module.get("module_id") == "core" and module.get("ok") and not report.get("promotion"):
            findings["4"].append("el candidato declara el núcleo en verde sin informe de parser")


def check_remote_claims(candidate: dict, findings: dict[str, list[str]]) -> None:
    """Hueco externo declarado ≠ afirmación hecha.

    Se recorre el candidato entero porque una afirmación también puede
    colarse en una limitación o en el detalle de un gate. Una frase solo
    cuenta como afirmación si el contexto que la rodea no la niega ni la
    declara pendiente.
    """
    text = json.dumps(candidate, ensure_ascii=False).lower()
    declared = json.dumps(candidate.get("open_external_items") or [], ensure_ascii=False).lower()
    for phrase in REMOTE_CLAIMS + HUMAN_SIGNS:
        for match in re.finditer(re.escape(phrase), text):
            window = text[max(0, match.start() - 320):match.start()]
            if any(negation in window for negation in NEGATIONS):
                continue
            if phrase in declared:
                continue
            findings["5"].append(f"el candidato afirma {phrase!r} fuera de una lista de huecos")


def check_docs(root: Path, findings: dict[str, list[str]]) -> None:
    report = _load(root / "reports" / "maintenance" / "docs_audit.json")
    if report is None:
        findings["6"].append("no hay informe de auditoría documental")
        return
    if not report.get("ok"):
        for code, messages in (report.get("failures") or {}).items():
            findings["6"].append(f"auditoría documental, código {code}: {messages}")


def check_portability(root: Path, findings: dict[str, list[str]]) -> None:
    matrix = _load(root / "reports" / "maintenance" / "portability_matrix.json")
    if matrix is None:
        findings["7"].append("no hay matriz de portabilidad")
        return
    for row in matrix.get("rows") or []:
        if row.get("status") == "verified" and not row.get("evidence"):
            findings["7"].append(f"{row.get('system_id')} figura como verificado sin evidencia")
        if row.get("status") == "verified" and not row.get("executed_at"):
            findings["7"].append(f"{row.get('system_id')} figura como verificado sin fecha de ejecución")


def check_retention(root: Path, findings: dict[str, list[str]]) -> None:
    policy = root / "references" / "workdir-retention.md"
    if not policy.exists():
        findings["8"].append("no existe references/workdir-retention.md")
    log = _load(root / "reports" / "maintenance" / "purge_log.json")
    if log is not None:
        if not log.get("dry_run") and not log.get("authorized_by"):
            findings["8"].append("hay una purga aplicada sin authorized_by en el log")
        if not log.get("generated_at"):
            findings["8"].append("el log de purga no tiene marca de tiempo")


def check_core(candidate: dict, core_exit_code: int | None, findings: dict[str, list[str]]) -> None:
    code = core_exit_code
    if code is None:
        for module in candidate.get("modules") or []:
            if module.get("module_id") == "core":
                code = module.get("exit_code", 1)
    if code is None:
        findings["9"].append("el candidato no declara el resultado del núcleo")
    elif code != 0:
        findings["9"].append(f"la suite del núcleo termina con código {code}")


def gate(candidate: dict, root: Path, core_exit_code: int | None = None) -> dict:
    findings: dict[str, list[str]] = {str(code): [] for code in CHECKS}
    check_regression(root, findings)
    check_versioning(root, findings)
    check_migration(root, findings)
    check_parser(root, candidate, findings)
    check_remote_claims(candidate, findings)
    check_docs(root, findings)
    check_portability(root, findings)
    check_retention(root, findings)
    check_core(candidate, core_exit_code, findings)

    populated = {code: messages for code, messages in findings.items() if messages}
    return {
        "generated_at": now_iso(),
        "candidate_version": candidate.get("candidate_version"),
        "ok": not populated,
        "failures": populated,
        "checks": CHECKS,
        "open_external_items": candidate.get("open_external_items") or [],
        "external_items_do_not_block_local_release": True,
    }


def exit_code_for(report: dict) -> int:
    codes = sorted(int(code) for code in (report.get("failures") or {}))
    return codes[0] if codes else 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    candidate = _load(Path(args.candidate))
    if candidate is None:
        print(f"error: no se puede leer el candidato {args.candidate}", file=sys.stderr)
        return 2

    report = gate(candidate, root, args.core_exit_code)
    write_atomic(Path(args.out), report)
    code = exit_code_for(report)
    if code:
        print(f"fail: {json.dumps(report['failures'], ensure_ascii=False)}", file=sys.stderr)
        return code
    print(
        f"ok: release ampliado {report['candidate_version']} con las nueve comprobaciones "
        f"internas en verde y {len(report['open_external_items'])} huecos externos declarados"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())