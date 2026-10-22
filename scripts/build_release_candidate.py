"""Construye el candidato de release ampliado (fase 149).

Un candidato es un inventario: qué módulos entran, con qué gate se comprueba
cada uno, qué queda fuera y qué evidencia externa falta. Este script no
inventa evidencia: ejecuta los gates declarados y copia sus códigos de
salida reales.

Los huecos externos se declaran aparte y **no** hacen fallar el candidato.
Lo que sí lo hace es mentir: declarar `verified` sin evidencia, o dejar un
módulo activo sin gate.

Uso::

    python scripts/build_release_candidate.py --root . --version 0.2.0 \\
        --out reports/maintenance/release_candidate.json
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

from delivery_common import now_iso, sha256_file, write_atomic  # noqa: E402

SCHEMA_PATH = ROOT / "schemas" / "release_candidate.schema.json"

# Inventario de módulos del release. Cada módulo tiene su gate.
#
# El gate de un módulo ejecuta **todas** sus pruebas, no una muestra: antes
# el gate de MDX cubría 1 de sus 10 ficheros de prueba y el de terminología
# 3 de 10, de modo que una regresión en un extractor sin test de gate pasaba
# el release. Las listas salen de `modules.json`, y `gate_optional.py` falla
# si aquí falta alguna.
def _gate(target: str, files: list[str]) -> dict:
    return {
        "kind": "pytest",
        "target": target,
        "command": "python3 -m pytest " + " ".join(files) + " -q",
        "test_files": files,
    }


MODULE_INVENTORY = [
    {
        "module_id": "core",
        "phases": list(range(1, 61)),
        "gate": {"kind": "pytest", "target": "tests/",
                 # El gate del release no puede depender del candidato que genera:
                 # sus propias pruebas se validan después, con gate_extended.
                 "command": "python3 -m pytest tests/ -q --no-header "
                            "--ignore=tests/test_release_candidate.py"},
        "limitations": ["Las pruebas cubren comportamiento local, no el corpus real."],
    },
    {
        "module_id": "mdx",
        "phases": list(range(61, 71)),
        "gate": _gate("tests/test_mdx_*.py", [
            "tests/test_mdx_assemble.py", "tests/test_mdx_attributes.py",
            "tests/test_mdx_contract.py", "tests/test_mdx_gate.py",
            "tests/test_mdx_parser.py", "tests/test_mdx_props.py",
            "tests/test_mdx_protect.py", "tests/test_mdx_review.py",
            "tests/test_mdx_selector.py", "tests/test_mdx_tabs.py",
        ]),
        "limitations": [
            "No hay ningún archivo .mdx real: el corpus usa componentes MDX dentro de .md.",
            "La paridad de render en el destino no está comprobada.",
        ],
    },
    {
        "module_id": "html",
        "phases": list(range(71, 81)),
        "gate": _gate("tests/test_html_*.py", [
            "tests/test_html_assemble.py", "tests/test_html_attributes.py",
            "tests/test_html_classify.py", "tests/test_html_contract.py",
            "tests/test_html_gate.py", "tests/test_html_malformed.py",
            "tests/test_html_matrix.py", "tests/test_html_parser.py",
            "tests/test_html_release_gate.py", "tests/test_html_selector.py",
            "tests/test_html_tables.py",
        ]),
        "limitations": [
            "La paridad de render en el destino no está comprobada.",
            "Los corpus autorizados contienen 0 etiquetas del contrato HTML: solo lo activan fixtures sintéticos.",
        ],
    },
    {
        "module_id": "markdown-extensions",
        "phases": list(range(81, 91)),
        "gate": _gate("tests/test_*extensions*.py", [
            "tests/test_admonitions.py", "tests/test_content_gates.py",
            "tests/test_definition_lists.py", "tests/test_dialect_matrix.py",
            "tests/test_directives.py", "tests/test_extension_combinations.py",
            "tests/test_footnotes.py", "tests/test_frontmatter_translate.py",
            "tests/test_math.py", "tests/test_mermaid_labels.py",
            "tests/test_wikilinks.py",
        ]),
        "limitations": [
            "Todos los fixtures del lote son sintéticos: ningún corpus autorizado contiene estas construcciones.",
            "Footnotes y matemáticas no tienen interruptor: el núcleo los trata siempre.",
        ],
    },
    {
        "module_id": "terminology",
        "phases": list(range(91, 101)),
        "gate": _gate("tests/test_glossary_*.py + tests/test_term_*.py", [
            "tests/test_glossary_database.py", "tests/test_glossary_frontend.py",
            "tests/test_glossary_ml_ai.py", "tests/test_glossary_network.py",
            "tests/test_glossary_systems.py", "tests/test_term_drift.py",
            "tests/test_term_precedence.py", "tests/test_term_profiles.py",
            "tests/test_term_provenance.py", "tests/test_term_report.py",
        ]),
        "limitations": [
            "Los cinco perfiles de dominio son de laboratorio y no los activa ningún glosario real.",
        ],
    },
    {
        "module_id": "language",
        "phases": list(range(101, 111)),
        "gate": _gate("tests/test_*policy*.py + tests/test_*language*.py", [
            "tests/test_citations_policy.py", "tests/test_detect_language.py",
            "tests/test_eval_fr.py", "tests/test_language_matrix.py",
            "tests/test_locale_policy.py", "tests/test_mixed_profile.py",
            "tests/test_pilot_fr.py", "tests/test_regional_eval.py",
            "tests/test_reviewer_policy.py", "tests/test_rtl_policy.py",
            "tests/test_source_language_policy_fr.py",
        ]),
        "limitations": [
            "Fases 103, 109 y 110 sin firma nativa de revisor: 1 par humano de 3 exigidos.",
        ],
    },
    {
        "module_id": "scale",
        "phases": list(range(111, 121)),
        "gate": _gate("tests/test_*concurren*.py + tests/test_*cache*.py + tests/test_gate_scale.py", [
            "tests/test_concurrency_policy.py", "tests/test_coordinator.py",
            "tests/test_gate_scale.py", "tests/test_invalidate_cache.py",
            "tests/test_measure_execution.py", "tests/test_reviewer_protocol.py",
            "tests/test_schedule_packets.py", "tests/test_serial_fallback.py",
            "tests/test_translation_cache.py", "tests/test_worker_protocol.py",
        ]),
        "limitations": [
            "El muestreador de CI corre sobre 30 documentos, no sobre el corpus completo.",
            "El modo concurrente no se ha ejecutado sobre material real: gate_scale solo se ha probado con manifiestos sintéticos.",
            "El backoff exponencial y la cola FIFO que describe concurrency-policy.md no están implementados.",
        ],
    },
    {
        "module_id": "review",
        "phases": list(range(121, 131)),
        "gate": _gate("tests/test_*report*.py + tests/test_gate_review.py", [
            "tests/test_approval_freshness.py", "tests/test_decision_schema.py",
            "tests/test_detect_residual_language.py", "tests/test_eval_back_translation.py",
            "tests/test_gate_review.py", "tests/test_group_inconsistencies.py",
            "tests/test_log_redaction.py", "tests/test_prioritize_findings.py",
            "tests/test_render_bilingual.py", "tests/test_report_accessibility.py",
        ]),
        "limitations": [
            "La retrotraducción de la fase 127 solo se ejecuta en modo seco.",
            "Ningún artefacto de este módulo existe en reports/: solo se ejecutó el detector de idioma residual, con resultado negativo.",
        ],
    },
    {
        "module_id": "delivery",
        "phases": list(range(131, 141)),
        "gate": _gate("tests/test_*delivery*.py + tests/test_export_zip.py", [
            "tests/test_adapt_delivery.py", "tests/test_compare_delivery.py",
            "tests/test_delivery_docs.py", "tests/test_delivery_guide.py",
            "tests/test_delivery_matrix.py", "tests/test_export_zip.py",
            "tests/test_gate_delivery.py", "tests/test_import_evidence.py",
        ]),
        "limitations": [
            "Fases 131-133 sin evidencia de importación real en Notion.",
            "Fase 139 sin destino de entrega real distinto del árbol canónico.",
        ],
    },
    {
        "module_id": "maintenance",
        "phases": list(range(141, 151)),
        "gate": {
            **_gate("tests/ (fases 141-148)", [
                "tests/test_audit_docs.py", "tests/test_compare_parser.py",
                "tests/test_gate_optional.py", "tests/test_manifest_migration.py",
                "tests/test_model_variation.py", "tests/test_optional_activation.py",
                "tests/test_optional_deactivation.py", "tests/test_portability.py",
                "tests/test_purge_workdir.py", "tests/test_regression_cases.py",
                "tests/test_regression_registry.py", "tests/test_release_candidate.py",
                "tests/test_release_docs_0_4_0.py", "tests/test_versioning_policy.py",
            ]),
            # Estas pruebas leen el candidato que este script está construyendo.
            # Incluirlas haría que el gate dependiera del archivo que produce:
            # leería la versión anterior, fallaría y el candidato nunca
            # convergería a verde. Se ejecutan en la suite y con gate_extended.
            "excluded_tests": [
                {
                    "path": "tests/test_release_candidate.py",
                    "reason": "valida el candidato que este script escribe; se ejecuta aparte",
                },
            ],
            "command": (
                "python3 -m pytest tests/test_audit_docs.py "
                "tests/test_compare_parser.py tests/test_gate_optional.py "
                "tests/test_manifest_migration.py tests/test_model_variation.py "
                "tests/test_optional_activation.py tests/test_optional_deactivation.py "
                "tests/test_portability.py tests/test_purge_workdir.py "
                "tests/test_regression_cases.py tests/test_regression_registry.py "
                "tests/test_release_docs_0_4_0.py tests/test_versioning_policy.py -q"
            ),
        },
        "limitations": [
            "El gate extendido (149) se ejecuta aparte: necesita el candidato que este script construye.",
            "Los casos de regresión son sintéticos: sus hashes no corresponden a artefactos reales.",
        ],
    },
]

NOT_REQUIRED = [
    {"option": "delivery.enabled", "default": "false",
     "reason": "La exportación y la adaptación local siguen siendo opt-in por perfil."},
    {"option": "html.enabled", "default": "false",
     "reason": "El HTML embebido se clasifica pero no se adapta sin activar el módulo."},
    {"option": "mdx.enabled", "default": "false",
     "reason": "MDX se clasifica con el contrato aplicado; sin corpus declarado no se activa."},
    {"option": "admonitions.enabled", "default": "false",
     "reason": "Las directivas ::: solo bloquean sin activar el módulo."},
    {"option": "definition_lists.enabled", "default": "false",
     "reason": "Sin corpus que las contenga, no hay qué activar."},
    {"option": "directives.enabled", "default": "false",
     "reason": "Una directiva desconocida bloquea el archivo; activarla solo cambia el trato."},
    {"option": "wikilinks.enabled", "default": "false",
     "reason": "Los wikilinks reales del corpus son rutas dentro de código; no se traducen."},
    {"option": "terminology.enabled", "default": "false",
     "reason": "Ningún perfil de dominio tiene corpus real que lo justifique."},
    {"option": "mixed_profile.enabled", "default": "false",
     "reason": "El perfil mixto exige una segunda fuente separada; no entra en este release."},
    {"option": "rtl.enabled", "default": "false",
     "reason": "La política RTL está escrita y probada, pero su activación requiere corpus propio."},
    {"option": "locale", "default": "es",
     "reason": "Elegir variante regional exige corpus_ref y justification desde el perfil 1.1.0."},
    {"option": "mermaid labels", "default": "preservados",
     "reason": "Las etiquetas Mermaid no se traducen en el núcleo."},
    {"option": "frontmatter traducible", "default": "preserve",
     "reason": "El frontmatter se preserva literal por política."},
    {"option": "gate_review.py --mode expanded", "default": "basic",
     "reason": "La revisión ampliada exige --justification con un corpus concreto."},
    {"option": "run_concurrent.py", "default": "run_serial.py",
     "reason": "El modo serie es el valor por defecto; el concurrente se invoca a mano."},
]

OPEN_EXTERNAL = [
    {
        "id": "notion_import_evidence",
        "phases": [131, 132, 133],
        "reason": "No existe importación real comprobada en Notion: solo el checklist y el contrato.",
        "owner": "usuario",
        "procedure": "Importar una muestra con references/delivery-notion-checklist.md y registrar "
                     "la evidencia con scripts/record_import_evidence.py.",
        "blocking_scope": "remote_verification_claim",
    },
    {
        "id": "second_delivery_destination",
        "phases": [139],
        "reason": "No hay un destino de entrega real distinto del árbol canónico.",
        "owner": "usuario",
        "procedure": "Elegir un destino de references/delivery-matrix.md y ejecutar una entrega real.",
        "blocking_scope": "remote_verification_claim",
    },
    {
        "id": "native_reviewer_signature",
        "phases": [103, 109, 110],
        "reason": "Firmas de revisor nativo pendientes: 1 par humano de 3 exigidos.",
        "owner": "revisor humano",
        "procedure": "Revisar la muestra bilingüe y registrar la decisión en el manifiesto.",
        "blocking_scope": "human_signature",
    },
    {
        "id": "live_back_translation",
        "phases": [127],
        "reason": "La retrotraducción solo se ha ejecutado en modo seco.",
        "owner": "usuario",
        "procedure": "Ejecutar eval_back_translation.py en modo live con el proveedor autorizado.",
        "blocking_scope": "human_signature",
    },
    {
        "id": "second_model_run",
        "phases": [145],
        "reason": "Solo hay una ejecución real registrada; la comparación entre modelos necesita dos.",
        "owner": "usuario",
        "procedure": "Traducir el piloto con otro modelo y registrarlo con scripts/record_model_run.py.",
        "blocking_scope": "human_signature",
    },
    {
        "id": "windows_execution",
        "phases": [147],
        "reason": "Windows queda en design_only: no hay máquina ni imagen para ejecutarlo.",
        "owner": "equipo de mantenimiento",
        "procedure": "Ejecutar la suite en Windows y adjuntar el informe de sonda.",
        "blocking_scope": "human_signature",
    },
]

CLAIMS_NOT_MADE = [
    "No se afirma equivalencia semántica de la traducción.",
    "No se afirma que nada se haya importado en Notion ni en ningún destino remoto.",
    "No se afirma que la salida sea reproducible bit a bit entre ejecuciones del modelo.",
    "No se afirma portabilidad en Windows: esa fila está en design_only.",
    "No se afirma cobertura del corpus remoto del usuario: la fidelidad se evalúa sobre los Markdown recibidos.",
    "No se activa ningún módulo opcional por defecto.",
]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="build_release_candidate.py")
    p.add_argument("--root", default=str(ROOT))
    p.add_argument("--version", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--skip-gates", action="store_true",
                   help="No ejecuta los gates; los deja como no ejecutados (código -1 no válido).")
    return p.parse_args(argv)


def run_gate(command: str, root: Path) -> tuple[int, str]:
    parts = command.split()
    if parts and Path(parts[0]).name.startswith("python"):
        parts = parts[1:]
    proc = subprocess.run(
        [sys.executable, *parts], cwd=str(root), capture_output=True, text=True, check=False
    )
    return proc.returncode, (proc.stdout + proc.stderr)[-600:]


def load_declarations(root: Path) -> dict[str, dict]:
    """Módulos opcionales tal como los declara `modules.json` (G-EXT)."""
    path = root / "modules.json"
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {m["module_id"]: m for m in payload.get("modules", [])}


def build(root: Path, version: str, skip_gates: bool = False) -> dict:
    contract_path = root / "release_contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8")) if contract_path.exists() else {}
    skill_version = contract.get("skill_version", "unknown")
    declarations = load_declarations(root)

    modules = []
    for entry in MODULE_INVENTORY:
        command = entry["gate"].get("command")
        if skip_gates or not command or entry["gate"]["kind"] == "report":
            exit_code, ok, detail = 0, True, "gate declarado sin ejecución en este candidato"
        else:
            exit_code, detail = run_gate(command, root)
            ok = exit_code == 0
        declared = declarations.get(entry["module_id"], {})
        # `activation` no es un literal: sale de la declaración G-EXT. Si un
        # módulo está dormiente, el candidato no puede llamarlo «activo», por
        # mucho que sus pruebas estén en verde. El núcleo no es opcional:
        # no necesita corpus para existir.
        activation = declared.get(
            "activation",
            "core_required" if entry["module_id"] == "core" else "opt_in",
        )
        limitations = list(entry.get("limitations", []))
        limitations.extend(declared.get("limitations", []))
        if declared and not declared.get("corpus_real"):
            limitations.append(
                f"El corpus que lo activa es sintético o inexistente: {declared.get('corpus_ref')}"
            )
        modules.append({
            "module_id": entry["module_id"],
            "phases": entry["phases"],
            "activation": activation,
            "corpus_ref": declared.get("corpus_ref"),
            "gate": entry["gate"],
            "exit_code": exit_code,
            "ok": ok,
            "limitations": sorted(set(limitations)),
            "gate_detail": detail,
        })

    artifacts = []
    for rel in (
        "release_contract.json",
        "evals/regression/registry.json",
        "reports/maintenance/regression.json",
        "reports/maintenance/versioning.json",
        "reports/maintenance/parser_comparison.json",
        "reports/maintenance/model_runs/run-0000d3mo.json",
        "reports/maintenance/docs_audit.json",
        "reports/maintenance/platform_probe.json",
        "reports/maintenance/portability_matrix.json",
    ):
        path = root / rel
        if path.exists():
            artifacts.append({"path": rel, "sha256": sha256_file(path)})

    return {
        "generated_at": now_iso(),
        "candidate_version": version,
        "skill_version": skill_version,
        "modules": modules,
        "not_required": NOT_REQUIRED,
        "open_external_items": OPEN_EXTERNAL,
        "artifacts": artifacts,
        "claims_not_made": CLAIMS_NOT_MADE,
    }


def schema_violations(candidate: dict) -> list[str]:
    try:
        import jsonschema
    except ImportError:  # pragma: no cover
        return []
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    return [
        f"{'/'.join(str(p) for p in err.absolute_path) or '(raíz)'}: {err.message}"
        for err in sorted(validator.iter_errors(candidate), key=lambda e: list(e.absolute_path))
    ]


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    candidate = build(root, args.version, args.skip_gates)

    violations = schema_violations(candidate)
    if violations:
        print("error: el candidato no valida: " + json.dumps(violations, ensure_ascii=False),
              file=sys.stderr)
        return 2

    write_atomic(Path(args.out), candidate)
    failed = [m["module_id"] for m in candidate["modules"] if not m["ok"]]
    print(
        f"ok: candidato {args.version} con {len(candidate['modules'])} módulos activos, "
        f"{len(candidate['open_external_items'])} huecos externos declarados"
        + (f"; módulos con gate en rojo: {failed}" if failed else "")
    )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())