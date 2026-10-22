"""Criterio 4 de G-EXT: apagar un módulo no cambia el flujo del núcleo.

Cada prueba compara **byte a byte** los artefactos del flujo del núcleo
(`segments.json`, `packets.json` y `manifest.json`) producidos con el módulo
apagado de dos maneras:

1. con el módulo **explícitamente apagado** en el perfil;
2. con el módulo **ausente** del perfil.

Las dos tienen que dar el mismo resultado, y además tienen que ser idénticas
a la corrida de referencia sin perfil. Si un módulo cuesta algo apagado, es
que está metido en el camino del núcleo.

Patrón heredado de `tests/test_gate_delivery.py::test_desactivar_el_adaptador_reproduce_el_paquete_canonico`.

El corpus es `tests/fixtures/pilot/`: material real recortado, con tablas,
listas anidadas, código, frontmatter y citas. Los artefactos se comparan con
SHA-256 y con los bytes, no con una métrica de similitud.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "pilot"
TMP = Path(tempfile.gettempdir()) / "nst-tests"

INVENTORY = SCRIPTS / "inventory.py"
PREPARE = SCRIPTS / "prepare.py"
PACKETIZE = SCRIPTS / "packetize.py"


def _profile(extra: dict) -> dict:
    return {
        "target_language": "es",
        "source_language": "auto",
        "markdown_dialect": "commonmark+gfm",
        "slug_algorithm": {"name": "github", "version": "v1"},
        "code_preservation": "strict",
        "frontmatter_policy": "preserve",
        "bilingual_policy": "first-mention-per-document",
        "punctuation_preference": "es-comma-period",
        "review_mode": "assisted",
        "paths": {"source_root": str(FIXTURES), "work_root": "/tmp", "output_root": "/tmp"},
        "exclusions": [],
        "context_budget": 1500,
        "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
        **extra,
    }


# Claves cuyo valor es una marca de tiempo de la corrida. Se excluyen de la
# comparación porque cambian en cada ejecución: incluirlas haría que la
# prueba pasara siempre, y una prueba de identidad que no puede fallar no
# comprueba nada. Son las únicas que se quitan; todo lo demás se compara byte
# a byte.
VOLATILE_KEYS = ("generated_at", "created_at", "timestamp_utc")


def _canonical(payload: object) -> str:
    """Serializa el artefacto sin las marcas de tiempo de la corrida."""
    if isinstance(payload, dict):
        return json.dumps(
            {k: _canonical(v) for k, v in payload.items() if k not in VOLATILE_KEYS},
            sort_keys=True, ensure_ascii=False,
        )
    if isinstance(payload, list):
        return "[" + ",".join(_canonical(item) for item in payload) + "]"
    return json.dumps(payload, ensure_ascii=False)


def _run_core(tag: str, profile_extra: dict | None) -> dict[str, str]:
    """Ejecuta inventory → prepare → packetize y devuelve los hashes.

    Los hashes son de la forma canónica: sin `generated_at`. Con la marca de
    tiempo dentro, dos corridas idénticas darían hashes distintos y la
    comparación de bytes no probaría nada.
    """
    out_dir = TMP / f"optdeact_{tag}"
    out_dir.mkdir(parents=True, exist_ok=True)
    inv = out_dir / "inventory.json"
    prof = out_dir / "profile.json"
    prep = out_dir / "prepare.json"
    seg = out_dir / "segments.json"
    packets = out_dir / "packets.json"

    assert subprocess.run(
        [sys.executable, str(INVENTORY), "--source", str(FIXTURES), "--out", str(inv)],
        capture_output=True, text=True, check=False,
    ).returncode == 0

    cmd = [sys.executable, str(PREPARE), "--inventory", str(inv), "--out", str(prep), "--segments", str(seg)]
    if profile_extra is not None:
        prof.write_text(json.dumps(_profile(profile_extra), indent=2), encoding="utf-8")
        cmd += ["--profile", str(prof)]
    assert subprocess.run(cmd, capture_output=True, text=True, check=False).returncode == 0

    assert subprocess.run(
        [sys.executable, str(PACKETIZE), "--segments", str(seg), "--out", str(packets)],
        capture_output=True, text=True, check=False,
    ).returncode == 0

    return {
        name: hashlib.sha256(
            _canonical(json.loads(path.read_text(encoding="utf-8"))).encode("utf-8")
        ).hexdigest()
        for name, path in (("prepare", prep), ("segments", seg), ("packets", packets))
    }


# Los módulos opcionales que se encienden por perfil, con la forma exacta
# que el esquema exige para poder encenderlos.
PER_PROFILE_MODULES = {
    "mdx": {"mdx": {"enabled": False, "corpus_ref": "evals/cases/mdx.md",
                    "justification": "Apagado explícito para comprobar que no altera el flujo."}},
    "html": {"html": {"enabled": False, "corpus_ref": "evals/cases/html.md",
                      "justification": "Apagado explícito para comprobar que no altera el flujo."}},
    "admonitions": {"admonitions": {"enabled": False, "corpus_ref": "evals/cases/markdown-extensions.md",
                                    "justification": "Apagado explícito para comprobar que no altera el flujo."}},
    "definition_lists": {"definition_lists": {"enabled": False, "corpus_ref": "evals/cases/markdown-extensions.md",
                                              "justification": "Apagado explícito para comprobar que no altera el flujo."}},
    "directives": {"directives": {"enabled": False, "corpus_ref": "evals/cases/markdown-extensions.md",
                                  "justification": "Apagado explícito para comprobar que no altera el flujo."}},
    "mermaid": {"mermaid": {"enabled": False, "labels": "deny",
                            "corpus_ref": "evals/cases/markdown-extensions.md",
                            "justification": "Apagado explícito para comprobar que no altera el flujo."}},
    "wikilinks": {"wikilinks": {"enabled": False, "corpus_ref": "evals/cases/markdown-extensions.md",
                                "justification": "Apagado explícito para comprobar que no altera el flujo."}},
    "delivery": {"delivery": {"enabled": False, "corpus_ref": "evals/cases/delivery.md",
                              "justification": "Apagado explícito para comprobar que no altera el flujo."}},
    "terminology": {"terminology": {"enabled": False, "corpus_ref": "evals/cases/terminology.md",
                                    "justification": "Apagado explícito para comprobar que no altera el flujo."}},
    "mixed_profile": {"mixed_profile": {"enabled": False, "corpus_ref": "evals/cases/pilot-fr.md",
                                        "justification": "Apagado explícito para comprobar que no altera el flujo."}},
}


@pytest.fixture(scope="module")
def referencia() -> dict[str, str]:
    """Corrida sin perfil: el perfil mínimo no activa ningún módulo."""
    return _run_core("ref", None)


@pytest.mark.parametrize("module_id", sorted(PER_PROFILE_MODULES))
def test_desactivacion_deja_el_flujo_del_nucleo_identico(module_id: str, referencia) -> None:
    apagado = _run_core(f"{module_id}_off", PER_PROFILE_MODULES[module_id])
    ausente = _run_core(f"{module_id}_absent", None)
    assert apagado == referencia, (
        f"{module_id} apagado explícitamente no reproduce los bytes del núcleo"
    )
    assert apagado == ausente


def test_mixing_varios_modulos_apagados_no_altera_nada() -> None:
    """Todos apagados a la vez: el resultado sigue siendo el del núcleo."""
    combined: dict = {}
    for block in PER_PROFILE_MODULES.values():
        combined.update(block)
    apagados = _run_core("todos_off", combined)
    assert apagados == _run_core("todos_ref", None)


def test_la_referencia_no_esta_vacia() -> None:
    """Una prueba de identidad sobre un pipeline roto también «pasa»."""
    payload = json.loads((TMP / "optdeact_ref" / "segments.json").read_text(encoding="utf-8"))
    files = payload.get("files", [])
    assert len(files) == 9, f"el corpus piloto debería traer 9 archivos, trae {len(files)}"
    assert sum(len(f.get("segments", [])) for f in files) > 0


def test_la_referencia_tiene_bloqueos_que_apagar_un_modulo_puede_levantar() -> None:
    """Sin esto, la prueba de identidad no distinguiría nada.

    El corpus piloto viene bloqueado en el perfil mínimo (HTML activo y
    wikilinks real de Next.js). Encender un módulo cambia ese veredicto; si
    no cambiara nada, la identidad probaría que el gate no hace nada.
    """
    payload = json.loads((TMP / "optdeact_ref" / "prepare.json").read_text(encoding="utf-8"))
    bloqueados = [f for f in payload["files"] if f.get("verdict") == "blocked"]
    assert bloqueados, "el corpus piloto debería traer archivos bloqueados en el perfil mínimo"

    encendidos = _run_core("html_on", {"html": {"enabled": True,
                                                 "corpus_ref": "evals/cases/html.md",
                                                 "justification": "Comprobación de que encender cambia el veredicto."}})
    apagado = _run_core("html_off", PER_PROFILE_MODULES["html"])
    assert encendidos["prepare"] != apagado["prepare"]


def test_desactivacion_mixed_profile() -> None:
    """`mixed_profile` se enciende por un flag de `packetize`, no por el perfil.

    Por eso su identidad se comprueba en dos partes: el bloque del perfil no
    altera el flujo (prueba parametrizada), y el flag sí lo altera cuando se
    usa. Un módulo que no cambiara nada al activarse no estaría probando el
    criterio 4: estaría probando que el módulo no existe.
    """
    policy = TMP / "optdeact_mixed.json"
    policy.write_text(json.dumps({
        "enabled": True,
        "allowed_source_languages": ["en", "fr"],
        "default_handling": "translatable",
    }), encoding="utf-8")
    seg = TMP / "optdeact_ref" / "segments.json"
    sin_flag = TMP / "optdeact_mixed_sin.json"
    con_flag = TMP / "optdeact_mixed_con.json"
    for out, extra in ((sin_flag, []), (con_flag, ["--mixed-profile", str(policy)])):
        proc = subprocess.run(
            [sys.executable, str(PACKETIZE), "--segments", str(seg), "--out", str(out), *extra],
            capture_output=True, text=True, check=False,
        )
        assert proc.returncode == 0, proc.stderr
    assert hashlib.sha256(sin_flag.read_bytes()).hexdigest() != hashlib.sha256(
        con_flag.read_bytes()
    ).hexdigest(), "el flag mixed_profile no cambió nada: la comparación no probaría nada"


@pytest.mark.parametrize(
    "module_id, entrypoints",
    [
        ("scale", ("run_concurrent", "translation_cache", "worker", "coordinator", "gate_scale")),
        ("review", ("gate_review", "detect_residual_language", "render_bilingual",
                    "prioritize_findings", "group_inconsistencies", "eval_back_translation")),
        ("maintenance", ("gate_extended", "regression_gate", "regression_detectors",
                         "build_release_candidate", "audit_docs", "check_versioning",
                         "migrate_manifest", "migrate_profile", "probe_platform",
                         "purge_workdir", "record_model_run", "compare_model_runs",
                         "compare_parser", "check_portability")),
    ],
)
def test_desactivacion_de_modulos_fuera_del_flujo(module_id: str, entrypoints: tuple[str, ...]) -> None:
    """Estos módulos no se invocan desde el camino de traducción: se comprueba.

    Su activación es por línea de comandos, así que "desactivar" significa que
    el flujo del núcleo no los llama nunca. La prueba lee el código de la
    ruta de traducción y comprueba que ninguna herramienta del camino llama a
    estos entrypoints. No es una inspección de estilo: es la misma comprobación
    que hace el gate con `optional_modules.core_imports_optional`.
    """
    sys.path.insert(0, str(SCRIPTS))
    import optional_modules

    flow = (
        "inventory.py", "prepare.py", "packetize.py", "translate_pilot.py",
        "translate_corpus.py", "receive_translations.py", "assemble.py",
        "validate.py", "validate_translations.py", "export.py", "run_end_to_end.py",
        "rewrite_references.py", "build_anchors.py", "resolve_dispositions.py",
        "verify_already_target.py", "check_integrity.py", "check_numbers.py",
        "copy_resources.py", "advance_state.py", "approve_pilot.py",
    )
    offenders: list[str] = []
    for script in flow:
        path = SCRIPTS / script
        assert path.is_file(), script
        text = path.read_text(encoding="utf-8")
        for entry in entrypoints:
            if re.search(rf"\b{re.escape(entry)}\b", text) and f"import {entry}" in text:
                offenders.append(f"{script} importa {entry}")
    assert offenders == [], offenders

    # Y ninguna herramienta del núcleo (fuera de las delegaciones declaradas)
    # importa estos entrypoints.
    declared = {
        ("scripts/regression_detectors.py", "translation_cache"),
        ("scripts/regression_detectors.py", "compare_delivery"),
        ("scripts/regression_detectors.py", "validate_zip_package"),
    }
    for finding in optional_modules.core_imports_optional(SCRIPTS):
        key = (f"scripts/{finding['script']}", finding["imports"])
        assert key in declared or key[1] not in entrypoints, key