"""Gate de los módulos opcionales (checklist G-EXT del roadmap).

Cada módulo opcional debe cumplir cuatro casillas antes de poder declararse
sustentado:

1. **Activación explícita justificada por un corpus concreto.** El módulo es
   dormiente por defecto y encenderlo exige `corpus_ref` y `justification`,
   declarados en `modules.json` y, cuando el módulo se activa por perfil,
   exigidos por `schemas/profile.schema.json`.
2. **Contrato, casos positivos y negativos y política de fallo.** Los
   documentos del contrato existen y llevan marca de versión; las pruebas
   del módulo están todas declaradas y pasan; la política de fallo existe
   en código, con su entrada y sus códigos de salida.
3. **Regresión del núcleo intacta.** La suite completa está en verde y
   ninguna herramienta del núcleo importa un módulo opcional sin
   declaración expresa.
4. **Desactivación sin efectos sobre el flujo básico.** La prueba de
   desactivación de cada módulo se ejecuta y pasa: con el módulo apagado, el
   flujo del núcleo se reproduce byte a byte.

Un código de salida por casilla, más los de entrada. Lo no medido no es lo
mismo que lo verde: sin `--run-tests`, las casillas 3 y 4 se declaran
`not_run` y el gate sale distinto de cero.

    1 = activación sin corpus declarado
    2 = contrato ausente o sin marca de versión
    3 = casos incompletos o pruebas del módulo fuera de la declaración
    4 = regresión del núcleo no medida, en rojo o con una dependencia inversa
    5 = desactivación no verificada
    6 = inconsistencia entre la declaración y el candidato de release
    7 = las declaraciones no se pueden leer o no validan contra el esquema

Uso::

    python scripts/gate_optional.py \\
        --declarations modules.json \\
        --core-report reports/core/pytest.json \\
        --out reports/maintenance/gate_optional.json

    python scripts/gate_optional.py --no-run-tests   # pase estructural rápido
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

import optional_modules  # noqa: E402
from delivery_common import now_iso, write_atomic  # noqa: E402

SCHEMA_PATH = ROOT / "schemas" / "module_declaration.schema.json"
PROFILE_SCHEMA_PATH = ROOT / "schemas" / "profile.schema.json"

EXIT_ACTIVATION = 1
EXIT_CONTRACT = 2
EXIT_CASES = 3
EXIT_CORE = 4
EXIT_DEACTIVATION = 5
EXIT_CANDIDATE = 6
EXIT_INPUT = 7

CHECKS = {
    EXIT_ACTIVATION: "activacion_con_corpus",
    EXIT_CONTRACT: "contrato_y_politica_de_fallo",
    EXIT_CASES: "casos_positivos_y_negativos",
    EXIT_CORE: "regresion_del_nucleo",
    EXIT_DEACTIVATION: "desactivacion_sin_efectos",
    EXIT_CANDIDATE: "consistencia_con_el_candidato",
}

VERSION_MARK = "<!-- version:"


class DeclarationsError(Exception):
    """Las declaraciones no se pueden leer o no validan contra el esquema."""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="gate_optional.py")
    p.add_argument("--root", default=str(ROOT))
    p.add_argument("--declarations", default="modules.json")
    p.add_argument("--out", required=True)
    p.add_argument("--candidate", help="Candidato de release a contrastar.")
    p.add_argument("--core-exit-code", type=int, default=None,
                   help="Código de salida de la suite del núcleo.")
    p.add_argument("--core-report", help="JSON con {exit_code} de la suite del núcleo.")
    p.add_argument("--no-run-tests", action="store_true",
                   help="Pase estructural: no ejecuta pytest. El gate sale con 5 y "
                        "marca las comprobaciones de ejecución como not_run.")
    p.add_argument("--evidence-dir",
                   help="Directorio donde escribir un informe por módulo "
                        "(reports/optional/). Lo escribe el mismo gate que "
                        "verifica: un informe escrito a mano no es evidencia.")
    return p.parse_args(argv)


def load_declarations(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        raise DeclarationsError(f"no se puede leer {path}: {err}") from err
    try:
        import jsonschema
    except ImportError:  # pragma: no cover
        return data
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = [
        f"{'/'.join(str(p) for p in e.absolute_path) or '(raíz)'}: {e.message}"
        for e in sorted(
            jsonschema.Draft202012Validator(schema).iter_errors(data),
            key=lambda e: list(e.absolute_path),
        )
    ]
    if errors:
        raise DeclarationsError("las declaraciones no validan:\n  " + "\n  ".join(errors))
    return data


def index_modules(declarations: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for module in declarations.get("modules", []):
        out[module["module_id"]] = module
    return out


# --------------------------------------------------------------------------
# casilla 1 · activación con corpus declarado
# --------------------------------------------------------------------------

def profile_requires_corpus(profile_schema: dict, key: str) -> bool:
    """¿El esquema de perfil exige `corpus_ref` al activar `key`?

    Se buscan dos formas, porque hay dos formas de activar:

    - un bloque con `enabled` (o con `labels`) y una regla `if/then` dentro
      del propio bloque;
    - una regla en el `allOf` de la raíz, para las claves que se activan
      ellas mismas (`frontmatter_policy: translate-allowlist`,
      `locale.variant`).

    También se acepta que el bloque exija `corpus_ref` siempre: declararse
    ya es activarse. Sin esto, `enabled: true` seguiría siendo una
    activación sin corpus y la casilla 1 sería decorativa.
    """
    root_required = (profile_schema.get("properties") or {}).get(key, {}).get("required") or []
    if any("corpus_ref" in r for r in root_required):
        return True

    def matches_rule(node: object, in_root_rules: bool) -> bool:
        if isinstance(node, list):
            return any(matches_rule(item, in_root_rules) for item in node)
        if not isinstance(node, dict):
            return False
        if "then" in node and "if" in node:
            required = (node.get("then") or {}).get("required") or []
            mentions_key = key in json.dumps(node.get("if"), ensure_ascii=False)
            if any("corpus_ref" in r for r in required) and (mentions_key or in_root_rules):
                return True
        return any(matches_rule(value, in_root_rules) for value in node.values())

    block = (profile_schema.get("properties") or {}).get(key)
    if isinstance(block, dict) and matches_rule(block, in_root_rules=False):
        return True
    return matches_rule(profile_schema.get("allOf"), in_root_rules=True)


def check_activation(root: Path, modules: dict[str, dict], findings: dict[str, list[str]]) -> dict:
    profile_schema = json.loads(PROFILE_SCHEMA_PATH.read_text(encoding="utf-8"))
    detail: dict[str, dict] = {}
    for module_id, module in modules.items():
        entry: dict[str, object] = {}
        corpus_ref = module.get("corpus_ref") or ""
        if not (root / corpus_ref).is_file():
            findings["1"].append(f"{module_id}: corpus_ref no existe: {corpus_ref!r}")
        entry["corpus_ref"] = corpus_ref
        if len(module.get("justification") or "") < 20:
            findings["1"].append(f"{module_id}: justification demasiado corta para ser un motivo")
        if module.get("default_enabled") is not False:
            findings["1"].append(f"{module_id}: un módulo opcional no puede estar activo por defecto")
        if module.get("activation") not in {"dormant_by_default", "opt_in"}:
            findings["1"].append(f"{module_id}: activation inválido: {module.get('activation')!r}")
        if module.get("enforcement") == "schema":
            missing = [
                key for key in module.get("profile_keys", [])
                if not profile_requires_corpus(profile_schema, key)
            ]
            if missing:
                findings["1"].append(
                    f"{module_id}: el esquema de perfil no exige corpus_ref al activar {missing}"
                )
            entry["schema_enforced"] = not missing
        detail[module_id] = entry
    return detail


# --------------------------------------------------------------------------
# casilla 2 · contrato y política de fallo
# --------------------------------------------------------------------------

def check_contract(root: Path, modules: dict[str, dict], findings: dict[str, list[str]]) -> dict:
    detail: dict[str, dict] = {}
    for module_id, module in modules.items():
        entry: dict[str, object] = {}
        for rel in module.get("contract_paths", []):
            path = root / rel
            if not path.is_file():
                findings["2"].append(f"{module_id}: contrato ausente: {rel}")
                continue
            if VERSION_MARK not in path.read_text(encoding="utf-8")[:400]:
                findings["2"].append(f"{module_id}: contrato sin marca de versión: {rel}")
        policy = module.get("failure_policy") or {}
        entrypoint = policy.get("entrypoint", "")
        if not (root / entrypoint).is_file():
            findings["2"].append(f"{module_id}: la política de fallo declara una entrada inexistente: {entrypoint}")
        elif not policy.get("exit_codes"):
            findings["2"].append(f"{module_id}: la política de fallo no declara códigos de salida")
        if not (root / (policy.get("documented_in") or "")).is_file():
            findings["2"].append(f"{module_id}: la política de fallo no está documentada donde dice estar")
        entry["contract_paths"] = len(module.get("contract_paths", []))
        entry["entrypoint"] = entrypoint
        entry["exit_codes"] = policy.get("exit_codes")
        detail[module_id] = entry
    return detail


# --------------------------------------------------------------------------
# casilla 3 · casos positivos y negativos
# --------------------------------------------------------------------------

def collect_test_names(root: Path, files: list[str]) -> dict[str, set[str]]:
    """Nombres de prueba realmente existentes en cada fichero.

    Comprobar solo que el fichero exista no basta: un `nodeid` con el nombre
    mal escrito es un puntero a nada, y el gate lo daba por bueno. Aquí se
    recoge lo que pytest realmente collectiona.
    """
    present: dict[str, set[str]] = {}
    existing = [f for f in files if (root / f).is_file()]
    if not existing:
        return present
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *existing, "--collect-only", "-q", "--no-header"],
        capture_output=True, text=True, check=False, cwd=root,
    )
    for line in (proc.stdout or "").splitlines():
        line = line.strip()
        if "::" not in line or line.startswith(("=", "-", " ")):
            continue
        path = line.split("::", 1)[0]
        name = line.split("::", 1)[1]
        present.setdefault(path, set()).add(name)
    return present


def _nodeid_matches(root: Path, nodeid: str, collected: dict[str, set[str]]) -> tuple[bool, str]:
    """¿Resuelve este `nodeid` a una prueba real?

    Acepta el nombre exacto y los identificadores parametrizados: pytest
    permite `test_x[param]`, y el `nodeid` declarado suele llevar el
    parámetro.
    """
    file_part, _, test_part = nodeid.partition("::")
    names = collected.get(file_part)
    if names is None:
        return False, f"no se pudo coleccionar {file_part}"
    if test_part in names:
        return True, test_part
    base = test_part.split("[", 1)[0]
    if any(name == base or name.startswith(base + "[") for name in names):
        return True, test_part
    return False, f"{test_part} no existe en {file_part}"


def check_cases(root: Path, modules: dict[str, dict], findings: dict[str, list[str]]) -> dict:
    tests_dir = root / "tests"
    declarations = {mid: m for mid, m in modules.items()}
    shared = optional_modules.shared_prefixes(tests_dir, declarations)
    all_files = sorted({
        f for module in modules.values()
        for f in list(module.get("test_files", []))
        + [str(module.get(role, "")).partition("::")[0]
           for role in ("activation_negative_test", "deactivation_test")]
    })
    collected = collect_test_names(root, all_files)
    detail: dict[str, dict] = {}
    for module_id, module in modules.items():
        listed = {Path(f).name for f in module.get("test_files", [])}
        prefixes = module.get("test_prefixes", [])
        expected = set(optional_modules.module_test_files(tests_dir, prefixes))
        missing_files = sorted(f for f in listed if not (tests_dir / f).is_file())
        if missing_files:
            findings["3"].append(f"{module_id}: declara pruebas inexistentes: {missing_files}")
        undeclared = sorted(expected - listed)
        if undeclared:
            findings["3"].append(f"{module_id}: pruebas del módulo sin declarar: {undeclared}")
        evidence = {}
        for role in ("activation_negative_test", "deactivation_test"):
            nodeid = module.get(role) or ""
            file_part, _, _name = nodeid.partition("::")
            if not (root / file_part).is_file():
                findings["3"].append(f"{module_id}: {role} apunta a un fichero inexistente: {file_part}")
                continue
            ok, reason = _nodeid_matches(root, nodeid, collected)
            evidence[role] = {"nodeid": nodeid, "exists": ok, "detail": reason}
            if not ok:
                findings["3"].append(f"{module_id}: {role} no resuelve a una prueba real: {reason}")
        detail[module_id] = {
            "declared": len(listed),
            "matched_by_prefix": len(expected),
            "undeclared": undeclared,
            "missing": missing_files,
            "evidence_tests": evidence,
        }
    for name, owners in sorted(shared.items()):
        findings["3"].append(f"prueba reclamada por varios módulos: {name} ({owners})")
    detail["__collected__"] = collected
    return detail


# --------------------------------------------------------------------------
# casilla 4 · regresión del núcleo intacta
# --------------------------------------------------------------------------

def core_suite_exit_code(args: argparse.Namespace) -> tuple[int | None, str]:
    if args.core_exit_code is not None:
        return args.core_exit_code, "--core-exit-code"
    if args.core_report:
        try:
            data = json.loads(Path(args.core_report).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as err:
            return None, f"no se puede leer {args.core_report}: {err}"
        code = data.get("exit_code")
        if isinstance(code, int):
            return code, args.core_report
        return None, f"{args.core_report} no declara exit_code"
    return None, "sin medir"


def check_core(root: Path, modules: dict[str, dict], args: argparse.Namespace,
               findings: dict[str, list[str]]) -> dict:
    declared: dict[tuple[str, str], dict] = {}
    for module in modules.values():
        for delegation in module.get("core_delegations", []):
            declared[(delegation["from_script"], delegation["imports"])] = delegation

    undeclared = []
    for finding in optional_modules.core_imports_optional(root / "scripts"):
        key = (f"scripts/{finding['script']}", finding["imports"])
        delegation = declared.get(key)
        if delegation is None:
            undeclared.append(
                f"{key[0]}:{finding['line']} importa {key[1]} "
                f"(módulo {finding['module_id']}) sin delegación declarada"
            )
            continue
        if delegation["kind"] == "regression" and key[0] != "scripts/regression_detectors.py":
            undeclared.append(
                f"{key[0]}:{finding['line']}: una delegación de regresión solo puede venir "
                "de regression_detectors.py"
            )
    for message in undeclared:
        findings["4"].append(message)

    unclassified = optional_modules.unclassified_scripts(root / "scripts")
    for name in unclassified:
        findings["4"].append(f"script sin clasificar en optional_modules.py: {name}")

    code, source = core_suite_exit_code(args)
    if code is None:
        findings["4"].append(f"la regresión del núcleo no está medida ({source}); lo no medido no es verde")
    elif code != 0:
        findings["4"].append(f"la suite del núcleo termina con código {code} ({source})")

    return {
        "core_suite_exit_code": code,
        "core_suite_source": source,
        "undeclared_dependencies": undeclared,
        "declared_delegations": sorted(
            f"{s} -> {i} ({d['kind']})" for (s, i), d in declared.items()
        ),
        "unclassified_scripts": unclassified,
    }


# --------------------------------------------------------------------------
# casilla 5 · desactivación sin efectos
# --------------------------------------------------------------------------

def run_nodeid(nodeid: str, cwd: Path) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", nodeid, "-q", "--no-header"],
        capture_output=True,
        text=True,
        check=False,
        cwd=cwd,
    )
    return proc.returncode, (proc.stdout or proc.stderr)[-400:]


def check_deactivation(root: Path, modules: dict[str, dict], run_tests: bool,
                       findings: dict[str, list[str]]) -> dict:
    detail: dict[str, dict] = {}
    for module_id, module in modules.items():
        nodeid = module.get("deactivation_test") or ""
        if not run_tests:
            detail[module_id] = {"nodeid": nodeid, "status": "not_run"}
            continue
        code, output = run_nodeid(nodeid, root)
        detail[module_id] = {"nodeid": nodeid, "status": "pass" if code == 0 else "fail", "exit_code": code}
        if code != 0:
            findings["5"].append(f"{module_id}: la prueba de desactivación falla ({nodeid}): {output.strip()[-200:]}")
    return detail


# --------------------------------------------------------------------------
# casilla 6 · consistencia con el candidato de release
# --------------------------------------------------------------------------

def check_candidate(root: Path, modules: dict[str, dict], candidate_path: str | None,
                    findings: dict[str, list[str]]) -> dict:
    if not candidate_path:
        return {"status": "not_run", "reason": "sin --candidate"}
    try:
        candidate = json.loads(Path(candidate_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        findings["6"].append(f"no se puede leer el candidato {candidate_path}: {err}")
        return {"status": "unreadable"}

    by_id = {m.get("module_id"): m for m in candidate.get("modules", [])}
    not_required = {entry.get("option") for entry in candidate.get("not_required", [])}
    for module_id, module in modules.items():
        entry = by_id.get(module_id)
        if entry is None:
            findings["6"].append(f"{module_id}: el candidato no lo declara")
            continue
        if entry.get("activation") != module["activation"]:
            findings["6"].append(
                f"{module_id}: el candidato dice activation={entry.get('activation')!r} "
                f"y la declaración dice {module['activation']!r}"
            )
        if module["activation"] == "dormant_by_default":
            option = (module.get("activation_option") or "").split(",")[0].strip()
            if option and option not in not_required:
                findings["6"].append(f"{module_id}: {option} no está en not_required")
        if not entry.get("limitations") and not module.get("corpus_real"):
            findings["6"].append(f"{module_id}: el candidato declara limitations vacías sin corpus real")
        # El gate del candidato tiene que ejecutar todo lo que el módulo
        # declara. Si el gate se queda corto, el candidato afirma una
        # cobertura de pruebas que no existe.
        declared_files = {Path(f).name for f in module.get("test_files", [])}
        gate_obj = entry.get("gate") or {}
        candidate_files = {Path(f).name for f in gate_obj.get("test_files", [])}
        excluded = {Path(e["path"]).name: e for e in gate_obj.get("excluded_tests", [])}
        sin_cubrir = sorted(declared_files - candidate_files - set(excluded))
        if sin_cubrir:
            findings["6"].append(
                f"{module_id}: el gate del candidato no cubre {sin_cubrir} "
                "y no están declarados como excluidos con motivo"
            )
        for name, exclusion in excluded.items():
            if name not in declared_files:
                findings["6"].append(
                    f"{module_id}: declara excluida una prueba que no es de este módulo: {name}"
                )
    return {
        "status": "checked",
        "candidate": candidate_path,
        "modules_in_candidate": sorted(by_id),
        "not_required": sorted(n for n in not_required if n),
    }


# --------------------------------------------------------------------------
# ejecución
# --------------------------------------------------------------------------

def run_module_tests(root: Path, module: dict) -> tuple[int, str]:
    files = [f for f in module.get("test_files", []) if (root / f).is_file()]
    if not files:
        return 1, "sin pruebas declaradas"
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *files, "-q", "--no-header"],
        capture_output=True,
        text=True,
        check=False,
        cwd=root,
    )
    return proc.returncode, (proc.stdout or proc.stderr)[-400:]


def gate(args: argparse.Namespace) -> dict:
    root = Path(args.root).resolve()
    try:
        declarations = load_declarations(Path(args.declarations))
    except DeclarationsError as err:
        return {
            "generated_at": now_iso(),
            "ok": False,
            "exit_code": EXIT_INPUT,
            "failures": {"7": [str(err)]},
            "checks": CHECKS,
        }

    modules = index_modules(declarations)
    findings: dict[str, list[str]] = {str(code): [] for code in CHECKS}

    activation = check_activation(root, modules, findings)
    contract = check_contract(root, modules, findings)
    cases = check_cases(root, modules, findings)
    collected = cases.pop("__collected__")
    core = check_core(root, modules, args, findings)
    deactivation = check_deactivation(
        root, modules, not args.no_run_tests, findings
    )
    candidate = check_candidate(root, modules, args.candidate, findings)

    test_runs: dict[str, dict] = {}
    if args.no_run_tests:
        findings["5"].append(
            "pase estructural: las pruebas del módulo y la de desactivación no se ejecutaron"
        )
    else:
        for module_id, module in modules.items():
            code, output = run_module_tests(root, module)
            test_runs[module_id] = {"exit_code": code, "files": len(module.get("test_files", []))}
            if code != 0:
                findings["3"].append(
                    f"{module_id}: sus pruebas no pasan (código {code}): {output.strip()[-200:]}"
                )
        for module_id, module in modules.items():
            nodeid = module.get("activation_negative_test") or ""
            code, _ = run_nodeid(nodeid, root)
            if code != 0:
                findings["3"].append(f"{module_id}: el caso negativo de activación no pasa ({nodeid})")

    populated = {code: messages for code, messages in findings.items() if messages}
    codes = sorted(int(code) for code in populated)
    return {
        "generated_at": now_iso(),
        "declaration_version": declarations.get("declaration_version"),
        "ok": not populated,
        "exit_code": codes[0] if codes else 0,
        "failures": populated,
        "checks": CHECKS,
        "modules": sorted(modules),
        "tests_executed": not args.no_run_tests,
        "detail": {
            "activation": activation,
            "contract": contract,
            "cases": cases,
            "core": core,
            "deactivation": deactivation,
            "candidate": candidate,
            "module_test_runs": test_runs,
        },
        "external_items_do_not_block_local_release": True,
    }


def write_evidence(directory: Path, modules: dict[str, dict], report: dict) -> list[str]:
    """Un informe por módulo con lo que este gate acaba de comprobar.

    Los cuatro criteria se derivan de la ejecución, no de una plantilla:
    si una casilla falla, el informe de ese módulo lo dice.
    """
    directory.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    failures = report["failures"]
    detail = report["detail"]
    for module_id, module in sorted(modules.items()):
        failing = {
            code: [m for m in messages if module_id in m]
            for code, messages in failures.items()
        }
        failing = {code: msgs for code, msgs in failing.items() if msgs}
        payload = {
            "module_id": module_id,
            "generated_at": report["generated_at"],
            "gate": "scripts/gate_optional.py",
            "gate_exit_code": report["exit_code"],
            "phases": module["phases"],
            "activation": module["activation"],
            "default_enabled": module["default_enabled"],
            "activation_option": module["activation_option"],
            "corpus_ref": module["corpus_ref"],
            "corpus_real": module["corpus_real"],
            "justification": module["justification"],
            "criteria": {
                "1_activacion_con_corpus": {
                    "passed": "1" not in failing,
                    "detail": detail["activation"].get(module_id),
                },
                "2_contrato_y_politica_de_fallo": {
                    "passed": "2" not in failing,
                    "detail": detail["contract"].get(module_id),
                },
                "3_casos_positivos_y_negativos": {
                    "passed": "3" not in failing,
                    "detail": detail["cases"].get(module_id),
                    "test_runs": detail["module_test_runs"].get(module_id),
                },
                "4_regresion_del_nucleo": {
                    "passed": "4" not in failing,
                    "core_suite_exit_code": detail["core"]["core_suite_exit_code"],
                    "core_suite_source": detail["core"]["core_suite_source"],
                    "undeclared_dependencies": detail["core"]["undeclared_dependencies"],
                },
                "desactivacion_sin_efectos": {
                    "passed": "5" not in failing,
                    "detail": detail["deactivation"].get(module_id),
                },
                "consistencia_con_el_candidato": {
                    "passed": "6" not in failing,
                    "detail": detail["candidate"],
                },
            },
            "contract_paths": module["contract_paths"],
            "test_files": module["test_files"],
            "limitations": module["limitations"],
            "known_external_gaps": module["known_external_gaps"],
            "core_delegations": module["core_delegations"],
            "failing_checks": failing,
            "note": (
                "Este archivo lo escribe el gate que comprueba los cuatro "
                "criterios. No demuestra equivalencia semántica ni ejecución "
                "sobre el corpus real; dice lo que el gate midió."
            ),
        }
        path = directory / f"{module_id}.json"
        write_atomic(path, payload)
        written.append(str(path.relative_to(directory.parent)))
    return written


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = gate(args)
    if args.evidence_dir:
        try:
            modules = index_modules(load_declarations(Path(args.declarations)))
            report["evidence_written"] = write_evidence(Path(args.evidence_dir), modules, report)
        except DeclarationsError as err:
            report["evidence_error"] = str(err)
            report["exit_code"] = report["exit_code"] or EXIT_INPUT
            report["ok"] = False
    write_atomic(Path(args.out), report)
    if report["ok"]:
        measured = len(report["detail"]["module_test_runs"])
        print(
            f"ok: gate de módulos opcionales aprobado (9 declaraciones, "
            f"{measured} módulos con pruebas ejecutadas, "
            f"{report['detail']['core']['core_suite_exit_code']} en la suite del núcleo)"
        )
        return 0
    print(f"fail: {json.dumps(report['failures'], ensure_ascii=False)}", file=sys.stderr)
    return int(report["exit_code"])


if __name__ == "__main__":
    sys.exit(main())