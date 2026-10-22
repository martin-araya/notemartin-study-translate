"""Inventario de módulos opcionales y dirección de dependencias (G-EXT).

Este archivo es la única fuente de verdad sobre **qué es el núcleo y qué es
opcional**. La clasificación es explícita y auditable: cada script de
``scripts/`` pertenece al núcleo o a un módulo opcional, y no hay un valor
por defecto. Si mañana aparece un script nuevo, este inventario falla hasta
que alguien lo declare.

La dirección permitida es una sola:

- un módulo opcional **puede** importar del núcleo (comparte utilidades);
- el núcleo **no puede** importar de un módulo opcional. Si lo hace, apagar
  el módulo rompe el flujo básico, que es justo lo que el criterio 4 del
  gate G-EXT prohíbe.

Ninguna función de este archivo traduce, ensambla ni modifica documentos.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

# Scripts del núcleo: fases 001-060 del roadmap y 141-150 (mantenimiento).
# El mantenimiento cuenta como núcleo porque sus herramientas son las que
# comprueban el release, no una capacidad opcional del pipeline.
CORE_SCRIPTS = frozenset({
    # Fases 001-060: flujo de traducción
    "advance_state.py",
    "apply_corrections.py",
    "approve_pilot.py",
    "assemble.py",
    "audit_terminology.py",
    "build_anchors.py",
    "build_glossary.py",
    "build_manifest.py",
    "build_packets.py",
    "check_distribution.py",
    "check_integrity.py",
    "check_numbers.py",
    "checkpoint.py",
    "copy_resources.py",
    "dump_anchor_collisions.py",
    "export.py",
    "extract_terms.py",
    "inject_translation_ids.py",
    "inventory.py",
    "invalidate_run.py",
    "packetize.py",
    "prepare.py",
    "promote_glossary_decisions.py",
    "raise_issues.py",
    "rebuild_overflow_packets.py",
    "receive_translations.py",
    "repair_state_field.py",
    "resolve_dispositions.py",
    "rewrite_references.py",
    "run_end_to_end.py",
    "select_lote.py",
    "test_release.py",
    "translate_corpus.py",
    "translate_pilot.py",
    "translation_key.py",
    "validate.py",
    "validate_translations.py",
    "verify_already_target.py",
    # Utilidades de núcleo que nacieron al corregir contratos (G-EXT)
    "approval_freshness.py",
    "text_signals.py",
    "redaction.py",
    # `delivery_common.py` nació con el lote de entrega (134-140), pero lo
    # importan doce herramientas de núcleo y de mantenimiento. Un módulo que
    # el núcleo importa no puede ser opcional: apagarlo rompería el flujo
    # básico. Pasa a ser núcleo y el contrato de entrega lo cita como
    # utilidad compartida.
    "delivery_common.py",
    # Fases 141-150: mantenimiento
    "audit_docs.py",
    "build_release_candidate.py",
    "check_portability.py",
    "check_versioning.py",
    "compare_model_runs.py",
    "compare_parser.py",
    "gate_extended.py",
    "gate_optional.py",
    "migrate_manifest.py",
    "migrate_profile.py",
    "optional_modules.py",
    "probe_platform.py",
    "purge_workdir.py",
    "record_model_run.py",
    "regression_detectors.py",
    "regression_gate.py",
})

# Scripts de cada módulo opcional, con la fase que los origina. La fase no
# es decorativa: es lo que permite auditar contra el roadmap.
OPTIONAL_SCRIPTS = {
    "mdx": {
        "phases": "061-070",
        "files": ("mdx_assemble.py", "mdx_parser.py", "mdx_protect.py", "mdx_selector.py"),
    },
    "html": {
        "phases": "071-080",
        "files": ("html_assemble.py", "html_inventory.py", "html_parser.py", "html_selector.py"),
    },
    "markdown-extensions": {
        "phases": "081-090",
        "files": (
            "admonitions.py",
            "definition_lists.py",
            "dialect_matrix.py",
            "directives.py",
            "footnotes.py",
            "frontmatter_translate.py",
            "math_ext.py",
            "mermaid_adapter.py",
            "wikilinks.py",
        ),
    },
    "terminology": {
        "phases": "091-100",
        "files": (
            "term_drift.py",
            "term_precedence.py",
            "term_profiles.py",
            "term_provenance.py",
            "term_report.py",
        ),
    },
    "language": {
        "phases": "101-110",
        "files": (
            "check_cache_isolation.py",
            "citations.py",
            "detect_language.py",
            "detect_text_direction.py",
            "eval_pair.py",
            "eval_regional.py",
            "eval_rtl.py",
            "language_matrix.py",
        ),
    },
    "scale": {
        "phases": "111-120",
        "files": (
            "coordinator.py",
            "diff_ledgers.py",
            "gate_scale.py",
            "invalidate_cache.py",
            "measure_execution.py",
            "reviewer_role.py",
            "run_concurrent.py",
            "run_serial.py",
            "schedule_packets.py",
            "translation_cache.py",
            "worker.py",
        ),
    },
    "review": {
        "phases": "121-130",
        "files": (
            "check_approval_freshness.py",
            "detect_residual_language.py",
            "eval_back_translation.py",
            "gate_review.py",
            "group_inconsistencies.py",
            "prioritize_findings.py",
            "redact.py",
            "render_bilingual.py",
        ),
    },
    "delivery": {
        "phases": "131-140",
        "files": (
            "adapt_delivery.py",
            "compare_delivery.py",
            "delivery_matrix.py",
            "export_zip.py",
            "gate_delivery.py",
            "record_import_evidence.py",
            "render_delivery_guide.py",
            "validate_zip_package.py",
        ),
    },
}

MODULE_IDS = tuple(sorted(OPTIONAL_SCRIPTS))

# Un módulo puede(versionar) scripts que sirven a varios lotes: se declara
# una sola vez y ambos contratos lo mencionan.
SHARED_NOTE = (
    "dialect_matrix.py (090) lo declara también el lote de idioma (101-110): "
    "el perfil de dialecto es la capacidad y el par de idioma su uso."
)

IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+([A-Za-z_][A-Za-z0-9_]*)", re.M)


def all_script_files(scripts_dir: Path) -> list[str]:
    return sorted(p.name for p in scripts_dir.glob("*.py") if not p.name.startswith("_"))


def script_owner(name: str) -> str:
    """Módulo opcional al que pertenece un script, o ``core``.

    Lanza ``ValueError`` si el script no está clasificado. Un inventario
    incompleto es un defecto, no un valor por defecto.
    """
    if name in CORE_SCRIPTS:
        return "core"
    for module_id, entry in OPTIONAL_SCRIPTS.items():
        if name in entry["files"]:
            return module_id
    raise ValueError(f"script sin clasificar: {name}")


def unclassified_scripts(scripts_dir: Path) -> list[str]:
    return [name for name in all_script_files(scripts_dir) if not is_classified(name)]


def is_classified(name: str) -> bool:
    try:
        script_owner(name)
    except ValueError:
        return False
    return True


def module_of_script(name: str) -> str | None:
    owner = script_owner(name)
    return None if owner == "core" else owner


def imports_of(path: Path) -> list[str]:
    """Módulos de primer nivel importados por un script.

    Se usa el AST y no una expresión regular: un nombre de módulo puede
    aparecer dentro de un literal, un comentario o una cadena de
    documentación sin ser un import.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError) as err:
        raise ValueError(f"no se puede analizar {path}: {err}") from err
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            names.append(node.module.split(".")[0])
    return sorted(set(names))


def core_imports_optional(scripts_dir: Path) -> list[dict]:
    """Scripts del núcleo que importan un módulo opcional.

    Devuelve una entrada por coincidencia con el archivo y la línea, para
    que el hallazgo sea accionable y no una afirmación.
    """
    findings: list[dict] = []
    optional_modules = {
        Path(file_name).stem: module_id
        for module_id, entry in OPTIONAL_SCRIPTS.items()
        for file_name in entry["files"]
    }
    for path in sorted(scripts_dir.glob("*.py")):
        if not is_classified(path.name) or script_owner(path.name) != "core":
            continue
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        for node in ast.walk(ast.parse(text)):
            imported: list[str] = []
            if isinstance(node, ast.Import):
                imported = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                imported = [node.module.split(".")[0]]
            for name in imported:
                if name in optional_modules:
                    findings.append({
                        "script": path.name,
                        "line": node.lineno,
                        "imports": name,
                        "module_id": optional_modules[name],
                    })
    return findings


def test_files(tests_dir: Path) -> list[str]:
    return sorted(p.name for p in tests_dir.glob("test_*.py"))


def module_test_files(tests_dir: Path, prefixes: list[str]) -> list[str]:
    """Ficheros de prueba cuyo nombre empieza por alguno de los prefijos."""
    return [name for name in test_files(tests_dir) if any(name.startswith(p) for p in prefixes)]


def shared_prefixes(tests_dir: Path, declarations: dict[str, dict]) -> dict[str, list[str]]:
    """Ficheros de prueba que dos módulos reclamarían a la vez."""
    by_file: dict[str, list[str]] = {}
    for module_id, decl in declarations.items():
        for prefix in decl.get("test_prefixes", []):
            for name in module_test_files(tests_dir, [prefix]):
                by_file.setdefault(name, []).append(module_id)
    return {name: sorted(set(owners)) for name, owners in by_file.items() if len(owners) > 1}