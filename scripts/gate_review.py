"""Gate del flujo ampliado de revisión (fase 130).

Modos:

- ``basic`` (default): reproduce las verificaciones del núcleo; las
  fases 121-129 no se ejecutan ni se exigen. No ralentiza el flujo
  por defecto.
- ``expanded``: exige los artefactos adicionales y **además** ejecuta
  las comprobaciones del modo básico. Antes las sustituía, de modo que
  encender el módulo：【】perdía la comprobación de estados terminales.
  Emite códigos de salida distintos por requisito faltante:

    1 = falta informe bilingüe (121) o falta la vista priorizada (122).
    2 = falta decisión humana global (123), estados no terminales del
        núcleo, o falta el reporte de inconsistencias (125).
    3 = aprobación obsoleta por hash (124).
    4 = warning abierto de idioma residual (126).
    5 = métricas de retrotraducción fuera de tolerancia (127).
    6 = accesibilidad de los reportes (128).
    7 = el módulo se activa sin justificación de corpus.

``--justification`` es obligatoria en modo ``expanded``: sin ella el
módulo no se enciende. Es el mismo criterio que se aplica al resto de
módulos opcionales (criterio 1 de G-EXT).

El gate nunca modifica ``work_root/`` ni ``translations/``. Su
resultado se vuelca en ``reports/gate_review.json``.
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

# Estados en los que un documento está resuelto y puede revisarse como
# entrega. `advance_state.TERMINAL` no sirve aquí: no incluye `approved`,
# que es un estado de trabajo legítimo anterior a la exportación. Lo que
# este gate rechaza es un documento que nadie resolvió: bloqueado,
# fallido o a medio traducir.
DELIVERABLE_STATES = {"approved", "exported", "already_target", "excluded"}

# Todo estado de `advance_state.SEQUENCE` que no está en DELIVERABLE_STATES
# se rechaza. La prueba lo verifica contra la secuencia del núcleo, de
# modo que un estado nuevo no pueda colarse sin decidirlo.
def undecided_states() -> set[str]:
    from advance_state import SEQUENCE  # importación diferida: evita ciclo

    return set(SEQUENCE) - DELIVERABLE_STATES

EXIT_MISSING_BILINGUAL = 1
EXIT_MISSING_DECISION = 2
EXIT_APPROVAL_STALE = 3
EXIT_RESIDUAL_WARNING = 4
EXIT_BACK_TRANSLATION_TOLERANCE = 5
EXIT_ACCESSIBILITY_OR_LOGS = 6
EXIT_MISSING_JUSTIFICATION = 7


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="gate_review.py")
    p.add_argument("--mode", choices=["basic", "expanded"], default="basic")
    p.add_argument("--manifest", required=True)
    p.add_argument("--justification",
                   help="Ambigüedad justificada por un corpus concreto. "
                        "Obligatoria en modo expanded: sin ella el módulo "
                        "no se activa.")
    p.add_argument("--translations", help="Directorio translations/.")
    p.add_argument("--glossary", help="Glosario congelado.")
    p.add_argument("--bilingual-report", help="Ruta esperada del informe bilingüe (fase 121).")
    p.add_argument("--prioritized-report", help="Ruta de la vista priorizada (fase 122).")
    p.add_argument("--inconsistency-report", help="Ruta del reporte de inconsistencias (fase 125).")
    p.add_argument("--residuals", help="JSON del detector de idioma residual (fase 126).")
    p.add_argument("--back-translation", help="JSON de retrotraducción (fase 127).")
    p.add_argument("--tolerance", type=float, default=0.3, help="Tolerancia máxima de falsos positivos (fase 127).")
    p.add_argument("--out", required=True)
    return p.parse_args(argv)


def _read_json(path: str | None) -> dict | None:
    if not path:
        return None
    p = Path(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def basic_check(manifest: dict) -> dict:
    """Comprueba los controles del núcleo sin invocar las fases 121-129.

    `approved` cuenta como resuelto: es el estado anterior a la
    exportación. `blocked`, `failed` y los estados intermedios no cuentan,
    y su lista sale de `advance_state.SEQUENCE` para que no pueda divergir.
    """
    files = manifest.get("files") or []
    failures: list[str] = []
    if not files:
        failures.append("no hay archivos en el manifiesto")
    for f in files:
        if f.get("current_state") not in DELIVERABLE_STATES:
            failures.append(
                f"archivo en estado no terminal: {f.get('path')} = {f.get('current_state')}"
            )
    return {
        "mode": "basic",
        "files_inspected": len(files),
        "deliverable_states": sorted(DELIVERABLE_STATES),
        "undecided_states": sorted(undecided_states()),
        "failures": failures,
        "ok": not failures,
    }


def _check_bilingual(path: str | None) -> tuple[bool, str]:
    if not path or not Path(path).exists():
        return False, "informe bilingüe ausente"
    text = Path(path).read_text(encoding="utf-8")
    if not text.startswith("# Informe bilingüe"):
        return False, "formato del informe bilingüe incorrecto"
    return True, "ok"


def _check_decisions(manifest: dict) -> tuple[bool, str]:
    decisions = manifest.get("decisions") or []
    if not decisions:
        return False, "no hay decisiones humanas registradas"
    has_global = any(
        d.get("kind") == "approve" and d.get("scope") == "global" for d in decisions
    )
    if not has_global:
        return False, "no hay decisión global de tipo approve"
    has_hashes = all(
        isinstance(d.get("reviewed_hashes"), list) and len(d["reviewed_hashes"]) >= 1 for d in decisions
    )
    if not has_hashes:
        return False, "alguna decisión no tiene reviewed_hashes"
    return True, "ok"


def _check_approvals(manifest: dict) -> tuple[bool, str]:
    approvals = manifest.get("approvals") or []
    if not approvals:
        return False, "no hay aprobaciones"
    by_path = {f.get("path"): f.get("source_hash") for f in manifest.get("files") or [] if f.get("path")}
    stale = []
    for ap in approvals:
        target = ap.get("target_hash")
        artifact = ap.get("artifact")
        current = by_path.get(artifact)
        if target and current and target != current:
            stale.append(ap.get("approval_id") or "(sin id)")
        ghash = (manifest.get("glossary_snapshot") or {}).get("hash")
        if "target_glossary_hash" in ap and ghash and ap["target_glossary_hash"] != ghash:
            stale.append(ap.get("approval_id") or "(sin id)")
    if stale:
        return False, f"aprobaciones obsoletas: {sorted(stale)}"
    return True, "ok"


def _check_residuals(payload: dict | None) -> tuple[bool, str]:
    if not payload:
        return False, "reporte de residuo ausente"
    warnings = int(payload.get("warnings") or 0)
    if warnings > 0:
        return False, f"{warnings} warnings abiertos"
    return True, "ok"


def _check_back_translation(payload: dict | None, tolerance: float) -> tuple[bool, str]:
    if not payload:
        return False, "métricas de retrotraducción ausentes"
    fp = int(payload.get("false_positives") or 0)
    fn = int(payload.get("false_negatives") or 0)
    total = int(payload.get("total") or 0)
    if total == 0:
        return False, "no hay casos en la retrotraducción"
    rate = (fp + fn) / total
    if rate > tolerance:
        return False, f"tasa de error {rate:.2f} > {tolerance:.2f}"
    return True, "ok"


def _check_prioritized(path: str | None) -> tuple[bool, str]:
    """La vista priorizada (fase 122) es obligatoria en modo ampliado.

    `references/findings-priority.md` §4 la exige y antes solo se leía si
    existía: un gate que no falla por su ausencia no comprueba nada.
    """
    if not path:
        return False, "vista priorizada no declarada (--prioritized-report)"
    if not Path(path).exists():
        return False, f"vista priorizada ausente: {path}"
    return True, "ok"


def _check_inconsistencies(path: str | None) -> tuple[bool, str]:
    """El reporte de inconsistencias (fase 125) se exige y se lee."""
    if not path:
        return False, "reporte de inconsistencias no declarado (--inconsistency-report)"
    payload = _read_json(path)
    if payload is None:
        return False, f"reporte de inconsistencias ausente o ilegible: {path}"
    groups = payload.get("groups") or []
    if not groups:
        return False, "el reporte de inconsistencias no contiene grupos"
    return True, f"{len(groups)} grupos"


def _check_accessibility(paths: list[str]) -> tuple[bool, str]:
    """Verifica que los informes no cargan recursos externos.

    Solo las URLs de esquema activo o que apuntan fuera del árbol local
    rompen la regla: un informe puede citar la ruta de un documento del
    propio corpus.
    """
    if not paths:
        return True, "sin reportes para auditar"
    external = re.compile(r"(?:https?|ftp)://", re.IGNORECASE)
    for p in paths:
        if not Path(p).exists():
            return False, f"reporte ausente para auditar: {p}"
        text = Path(p).read_text(encoding="utf-8")
        match = external.search(text)
        if match:
            return False, f"recurso externo en {p}: {match.group(0)}"
    return True, "ok"


def expanded_check(args: argparse.Namespace) -> dict:
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    failures: list[str] = []
    exit_codes: list[int] = []
    checks: dict = {}

    # El modo ampliado **compone** el básico: no lo sustituye. Encender las
    # verificaciones 121-129 no puede relajar la comprobación de estados
    # terminales que el núcleo ya exige.
    basic = basic_check(manifest)
    checks["core_states"] = (basic["ok"], "estados terminales del núcleo")
    if not basic["ok"]:
        failures.extend(f"core_states: {m}" for m in basic["failures"])
        exit_codes.append(EXIT_MISSING_DECISION)

    ok, msg = _check_bilingual(args.bilingual_report)
    checks["bilingual_report"] = (ok, msg)
    if not ok:
        failures.append(f"bilingual: {msg}")
        exit_codes.append(EXIT_MISSING_BILINGUAL)

    ok, msg = _check_prioritized(args.prioritized_report)
    checks["prioritized_report"] = (ok, msg)
    if not ok:
        failures.append(f"prioritized: {msg}")
        exit_codes.append(EXIT_MISSING_BILINGUAL)

    ok, msg = _check_decisions(manifest)
    checks["human_decisions"] = (ok, msg)
    if not ok:
        failures.append(f"decisions: {msg}")
        exit_codes.append(EXIT_MISSING_DECISION)

    ok, msg = _check_approvals(manifest)
    checks["approvals"] = (ok, msg)
    if not ok:
        failures.append(f"approvals: {msg}")
        exit_codes.append(EXIT_APPROVAL_STALE)

    ok, msg = _check_inconsistencies(args.inconsistency_report)
    checks["inconsistency_report"] = (ok, msg)
    if not ok:
        failures.append(f"inconsistencies: {msg}")
        exit_codes.append(EXIT_MISSING_DECISION)

    residuals = _read_json(args.residuals)
    ok, msg = _check_residuals(residuals)
    checks["residuals"] = (ok, msg)
    if not ok:
        failures.append(f"residuals: {msg}")
        exit_codes.append(EXIT_RESIDUAL_WARNING)

    bt = _read_json(args.back_translation)
    ok, msg = _check_back_translation(bt, args.tolerance)
    checks["back_translation"] = (ok, msg)
    if not ok:
        failures.append(f"back_translation: {msg}")
        exit_codes.append(EXIT_BACK_TRANSLATION_TOLERANCE)

    reports_to_audit = [p for p in [args.bilingual_report, args.prioritized_report] if p]
    ok, msg = _check_accessibility(reports_to_audit)
    checks["accessibility"] = (ok, msg)
    if not ok:
        failures.append(f"accessibility: {msg}")
        exit_codes.append(EXIT_ACCESSIBILITY_OR_LOGS)

    return {
        "mode": "expanded",
        "checks": {k: {"ok": v[0], "message": v[1]} for k, v in checks.items()},
        "failures": failures,
        "ok": not failures,
        "exit_codes": sorted(set(exit_codes)),
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))

    if args.mode == "basic":
        result = basic_check(manifest)
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
        print("ok basic" if result["ok"] else "fail basic")
        return 0 if result["ok"] else 1

    # Encender el módulo ampliado sin decir por qué es una activación sin
    # justificación: es el defecto que el criterio 1 de G-EXT prohíbe.
    if not (args.justification or "").strip():
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(
            json.dumps(
                {
                    "mode": "expanded",
                    "checks": {"justification": {"ok": False, "message": "sin justificación"}},
                    "failures": ["justification: el modo expanded exige --justification con el corpus concreto"],
                    "ok": False,
                    "exit_codes": [EXIT_MISSING_JUSTIFICATION],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        print(
            "fail expanded: falta --justification con el corpus que justifica el módulo",
            file=sys.stderr,
        )
        return EXIT_MISSING_JUSTIFICATION

    result = expanded_check(args)
    result["justification"] = args.justification
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
    if result["ok"]:
        print("ok expanded")
        return 0
    print(
        "fail expanded: "
        + json.dumps(result["failures"], ensure_ascii=False)
    )
    if result["exit_codes"]:
        return result["exit_codes"][0]
    return 1


if __name__ == "__main__":
    sys.exit(main())
