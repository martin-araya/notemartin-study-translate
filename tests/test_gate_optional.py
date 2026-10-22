"""Pruebas de scripts/gate_optional.py (checklist G-EXT).

Un caso por código de salida, más una integración contra el `modules.json`
real del repositorio. Las pruebasPositive y negativas usan declaraciones
sintéticas en un directorio temporal: el gate se prueba con declaraciones
que fallan a propósito, no solo con las que funcionan.

El pase estructural del repositorio real no ejecuta pytest (eso lo hace el
gate completo, en la línea de comandos). Aquí se comprueba que, sin ejecutar
pruebas, **las únicas** falhas son las esperadas de ese modo.
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "gate_optional.py"
DECLARATIONS = ROOT / "modules.json"
TMP = Path(tempfile.gettempdir()) / "nst-tests" / "gate_optional"


def _declarations() -> dict:
    return json.loads(DECLARATIONS.read_text(encoding="utf-8"))


def _module(data: dict, module_id: str) -> dict:
    return next(m for m in data["modules"] if m["module_id"] == module_id)


def _write(data: dict, tag: str) -> Path:
    TMP.mkdir(parents=True, exist_ok=True)
    path = TMP / f"modules_{tag}.json"
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def _run(tag: str, *, declarations: Path, root: Path | None = None,
         core_exit_code: int | None = 0, run_tests: bool = False) -> dict:
    out = TMP / f"gate_{tag}.json"
    cmd = [
        sys.executable, str(SCRIPT),
        "--root", str(root or ROOT),
        "--declarations", str(declarations),
        "--out", str(out),
    ]
    if core_exit_code is not None:
        cmd += ["--core-exit-code", str(core_exit_code)]
    if not run_tests:
        cmd.append("--no-run-tests")
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False, cwd=str(ROOT))
    payload = json.loads(out.read_text(encoding="utf-8"))
    payload["_returncode"] = proc.returncode
    payload["_stderr"] = proc.stderr
    return payload


# --------------------------------------------------------------------------
# código 7 · las declaraciones no se pueden leer o no validan
# --------------------------------------------------------------------------

def test_codigo_7_si_el_fichero_no_existe() -> None:
    payload = _run("inexistente", declarations=TMP / "no-existe.json")
    assert payload["_returncode"] == 7
    assert payload["exit_code"] == 7
    assert "7" in payload["failures"]


def test_codigo_7_si_una_declaracion_no_valida() -> None:
    data = _declarations()
    del _module(data, "mdx")["justification"]
    payload = _run("invalida", declarations=_write(data, "invalida"))
    assert payload["_returncode"] == 7
    assert "7" in payload["failures"]


# --------------------------------------------------------------------------
# código 1 · activación sin corpus declarado
# --------------------------------------------------------------------------

def test_codigo_1_si_el_corpus_no_existe() -> None:
    data = _declarations()
    _module(data, "mdx")["corpus_ref"] = "evals/cases/no-existe.md"
    payload = _run("sin_corpus", declarations=_write(data, "sin_corpus"))
    assert payload["_returncode"] == 1
    assert any("corpus_ref no existe" in m for m in payload["failures"]["1"])


def test_codigo_1_si_la_justificacion_es_un_tanto() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    import gate_optional

    findings: dict[str, list[str]] = {"1": [], "2": [], "3": [], "4": [], "5": [], "6": []}
    gate_optional.check_activation(
        ROOT,
        {"html": {"corpus_ref": "evals/cases/html.md", "justification": "porque sí",
                  "default_enabled": False, "activation": "dormant_by_default",
                  "enforcement": "schema", "profile_keys": ["html"]}},
        findings,
    )
    assert any("justification" in m for m in findings["1"]), findings["1"]


def test_codigo_1_si_un_modulo_estuviera_activo_por_defecto() -> None:
    data = _declarations()
    _module(data, "mdx")["default_enabled"] = True
    payload = _run("defecto", declarations=_write(data, "defecto"))
    assert payload["_returncode"] == 1
    assert any("por defecto" in m for m in payload["failures"]["1"])


def test_codigo_1_si_el_esquema_no_exige_corpus() -> None:
    """Un módulo puede declararse bien y que el esquema no lo exija."""
    data = _declarations()
    profile = TMP / "profile_sin_corpus.json"
    schema = json.loads((ROOT / "schemas" / "profile.schema.json").read_text(encoding="utf-8"))
    schema["properties"]["mdx"].pop("allOf", None)
    del schema["properties"]["mdx"]["properties"]["corpus_ref"]
    profile.write_text(json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8")

    fake_root = TMP / "raiz_sin_corpus"
    (fake_root / "schemas").mkdir(parents=True, exist_ok=True)
    (fake_root / "schemas" / "profile.schema.json").write_text(
        profile.read_text(encoding="utf-8"), encoding="utf-8"
    )
    payload = _run("schema flojo", declarations=DECLARATIONS, root=fake_root)
    assert payload["_returncode"] == 1
    assert any("corpus_ref" in m for m in payload["failures"]["1"])


def test_mdx_no_acepta_activacion_sin_corpus() -> None:
    data = _declarations()
    _module(data, "mdx")["corpus_ref"] = "evals/cases/no-debe-existir.md"
    payload = _run("mdx_sin", declarations=_write(data, "mdx_sin"))
    assert payload["_returncode"] == 1
    assert any("mdx" in m for m in payload["failures"]["1"])


def test_html_no_acepta_activacion_sin_corpus() -> None:
    data = _declarations()
    _module(data, "html")["corpus_ref"] = "evals/cases/no-debe-existir.md"
    payload = _run("html_sin", declarations=_write(data, "html_sin"))
    assert payload["_returncode"] == 1


def test_markdown_extensions_no_acepta_activacion_sin_corpus() -> None:
    data = _declarations()
    _module(data, "markdown-extensions")["corpus_ref"] = "evals/cases/no-debe-existir.md"
    payload = _run("mdext_sin", declarations=_write(data, "mdext_sin"))
    assert payload["_returncode"] == 1
    assert any("markdown-extensions" in m for m in payload["failures"]["1"])


def test_terminology_no_acepta_activacion_sin_corpus() -> None:
    data = _declarations()
    _module(data, "terminology")["corpus_ref"] = "evals/cases/no-debe-existir.md"
    payload = _run("term_sin", declarations=_write(data, "term_sin"))
    assert payload["_returncode"] == 1


def test_language_no_acepta_activacion_sin_corpus() -> None:
    data = _declarations()
    _module(data, "language")["corpus_ref"] = "evals/cases/no-debe-existir.md"
    payload = _run("lang_sin", declarations=_write(data, "lang_sin"))
    assert payload["_returncode"] == 1


def test_scale_no_acepta_activacion_sin_corpus() -> None:
    data = _declarations()
    _module(data, "scale")["corpus_ref"] = "evals/cases/no-debe-existir.md"
    payload = _run("scale_sin", declarations=_write(data, "scale_sin"))
    assert payload["_returncode"] == 1


def test_review_no_acepta_activacion_sin_corpus() -> None:
    data = _declarations()
    _module(data, "review")["corpus_ref"] = "evals/cases/no-debe-existir.md"
    payload = _run("review_sin", declarations=_write(data, "review_sin"))
    assert payload["_returncode"] == 1


def test_maintenance_no_acepta_activacion_sin_corpus() -> None:
    data = _declarations()
    _module(data, "maintenance")["corpus_ref"] = "evals/cases/no-debe-existir.md"
    payload = _run("maint_sin", declarations=_write(data, "maint_sin"))
    assert payload["_returncode"] == 1


def test_delivery_no_acepta_activacion_sin_corpus() -> None:
    data = _declarations()
    _module(data, "delivery")["corpus_ref"] = "evals/cases/no-debe-existir.md"
    payload = _run("delivery_sin", declarations=_write(data, "delivery_sin"))
    assert payload["_returncode"] == 1


# --------------------------------------------------------------------------
# código 2 · contrato y política de fallo
# --------------------------------------------------------------------------

def test_codigo_2_si_falta_un_contrato() -> None:
    data = _declarations()
    _module(data, "mdx")["contract_paths"] = ["references/no-existe.md"]
    payload = _run("sin_contrato", declarations=_write(data, "sin_contrato"))
    assert payload["_returncode"] == 2
    assert any("contrato ausente" in m for m in payload["failures"]["2"])


def test_codigo_2_si_un_contrato_no_tiene_version() -> None:
    """Caso negativo directo sobre la comprobación, con una raíz temporal.

    No se puede provocar desde `modules.json`: el patrón del esquema exige
    una ruta bajo `references/`, y `audit_docs.py` obliga a que todo
    documento de `references/` lleve marca de versión. La rama se prueba
    contra una raíz sintética donde esa invariante no se cumple.
    """
    sys.path.insert(0, str(ROOT / "scripts"))
    import gate_optional

    fake_root = TMP / "raiz_sin_version"
    (fake_root / "references").mkdir(parents=True, exist_ok=True)
    (fake_root / "references" / "contrato.md").write_text("# Sin marca\n", encoding="utf-8")
    (fake_root / "scripts").mkdir(parents=True, exist_ok=True)
    (fake_root / "scripts" / "prep.py").write_text("", encoding="utf-8")

    findings: dict[str, list[str]] = {"1": [], "2": [], "3": [], "4": [], "5": [], "6": []}
    modules = {"demo": {
        "contract_paths": ["references/contrato.md"],
        "failure_policy": {"entrypoint": "scripts/prep.py", "exit_codes": [0],
                           "documented_in": "references/contrato.md"},
    }}
    gate_optional.check_contract(fake_root, modules, findings)
    assert any("marca de versión" in m for m in findings["2"]), findings["2"]


def test_codigo_2_si_la_politica_de_fallo_no_tiene_codigos() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    import gate_optional

    findings: dict[str, list[str]] = {"1": [], "2": [], "3": [], "4": [], "5": [], "6": []}
    gate_optional.check_contract(
        ROOT,
        {"scale": {"contract_paths": ["references/scheduler-policy.md"],
                   "failure_policy": {"entrypoint": "scripts/gate_scale.py", "exit_codes": [],
                                      "documented_in": "references/serial-fallback.md"}}},
        findings,
    )
    assert any("códigos de salida" in m for m in findings["2"]), findings["2"]


def test_codigo_2_si_la_entrada_de_la_politica_no_existe() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    import gate_optional

    findings: dict[str, list[str]] = {"1": [], "2": [], "3": [], "4": [], "5": [], "6": []}
    gate_optional.check_contract(
        ROOT,
        {"scale": {"contract_paths": ["references/scheduler-policy.md"],
                   "failure_policy": {"entrypoint": "scripts/no_existe.py", "exit_codes": [1],
                                      "documented_in": "references/serial-fallback.md"}}},
        findings,
    )
    assert any("entrada inexistente" in m for m in findings["2"]), findings["2"]


# --------------------------------------------------------------------------
# código 3 · casos positivos y negativos
# --------------------------------------------------------------------------

def test_codigo_3_si_una_prueba_del_modulo_no_esta_declarada() -> None:
    data = _declarations()
    mod = _module(data, "mdx")
    mod["test_files"] = [f for f in mod["test_files"] if "test_mdx_tabs" not in f]
    payload = _run("sin_tabs", declarations=_write(data, "sin_tabs"))
    assert payload["_returncode"] == 3
    assert any("test_mdx_tabs" in m for m in payload["failures"]["3"])


def test_codigo_3_si_se_declara_una_prueba_inexistente() -> None:
    data = _declarations()
    _module(data, "mdx")["test_files"].append("tests/test_no_existe.py")
    payload = _run("prueba_fantasma", declarations=_write(data, "prueba_fantasma"))
    assert payload["_returncode"] == 3
    assert any("inexistentes" in m for m in payload["failures"]["3"])


def test_codigo_3_si_la_prueba_de_desactivacion_apunta_a_un_archivo_que_no_esta() -> None:
    data = _declarations()
    _module(data, "mdx")["deactivation_test"] = "tests/test_no_existe.py::x"
    payload = _run("deact_fantasma", declarations=_write(data, "deact_fantasma"))
    assert payload["_returncode"] == 3


# --------------------------------------------------------------------------
# código 4 · regresión del núcleo
# --------------------------------------------------------------------------

def test_codigo_4_si_la_suite_del_nucleo_no_esta_medida() -> None:
    payload = _run("sin_medir", declarations=DECLARATIONS, core_exit_code=None)
    assert payload["_returncode"] == 4
    assert any("no está medida" in m for m in payload["failures"]["4"])


def test_codigo_4_si_la_suite_del_nucleo_falla() -> None:
    payload = _run("nucleo_rojo", declarations=DECLARATIONS, core_exit_code=1)
    assert payload["_returncode"] == 4
    assert any("código 1" in m for m in payload["failures"]["4"])


def test_codigo_4_si_una_dependencia_inversa_no_esta_declarada() -> None:
    """Se declara mal a propósito la delegación de un módulo que sí la tiene."""
    data = _declarations()
    _module(data, "mdx")["core_delegations"] = []
    payload = _run("sin_delegacion", declarations=_write(data, "sin_delegacion"))
    assert payload["_returncode"] == 4
    assert any("mdx_selector" in m for m in payload["failures"]["4"])


def test_codigo_4_si_una_delegacion_de_regresion_viene_de_mal_lugar() -> None:
    data = _declarations()
    _module(data, "delivery")["core_delegations"][0]["from_script"] = "scripts/prepare.py"
    payload = _run("delegacion_mal", declarations=_write(data, "delegacion_mal"))
    assert payload["_returncode"] == 4


# --------------------------------------------------------------------------
# código 5 · desactivación no medida
# --------------------------------------------------------------------------

def test_el_pase_estructural_declara_no_measure_las_pruebas() -> None:
    payload = _run("estructural", declarations=DECLARATIONS)
    assert payload["_returncode"] == 5
    assert payload["tests_executed"] is False
    assert any("no se ejecutaron" in m for m in payload["failures"]["5"])


# --------------------------------------------------------------------------
# código 6 · consistencia con el candidato
# --------------------------------------------------------------------------

def test_codigo_6_si_el_candidato_declara_activo_un_modulo_dormiente() -> None:
    data = _declarations()
    candidate = TMP / "candidate_activo.json"
    candidate.write_text(json.dumps({
        "skill_version": "0.0.0",
        "modules": [
            {"module_id": m["module_id"], "activation": "active", "limitations": []}
            for m in data["modules"]
        ],
        "not_required": [],
    }), encoding="utf-8")
    out = TMP / "gate_candidato.json"
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(ROOT), "--declarations", str(DECLARATIONS),
         "--out", str(out), "--candidate", str(candidate), "--core-exit-code", "0",
         "--no-run-tests"],
        capture_output=True, text=True, check=False, cwd=str(ROOT),
    )
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert "6" in payload["failures"]
    assert any("activation" in m for m in payload["failures"]["6"])
    # El código devuelto es el más bajo que falla: el pase estructural
    # también reporta 5 por no medir pruebas. Ver `test_el_codigo_mas_bajo_gana`.
    assert proc.returncode == 5


def test_codigo_6_si_el_candidato_no_declara_un_modulo() -> None:
    candidate = TMP / "candidate_incompleto.json"
    candidate.write_text(json.dumps({"modules": [], "not_required": []}), encoding="utf-8")
    out = TMP / "gate_candidato2.json"
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(ROOT), "--declarations", str(DECLARATIONS),
         "--out", str(out), "--candidate", str(candidate), "--core-exit-code", "0",
         "--no-run-tests"],
        capture_output=True, text=True, check=False, cwd=str(ROOT),
    )
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert "6" in payload["failures"]
    assert any("no lo declara" in m for m in payload["failures"]["6"])
    assert proc.returncode == 5


def test_el_codigo_mas_bajo_gana() -> None:
    """Regla documentada: el código devuelto es el más bajo de los que fallan.

    Así 1 (activación) manda sobre 5 (pruebas no medidas): si algo está mal
    declarado, se arregla antes de volver a correr las pruebas.
    """
    data = _declarations()
    _module(data, "mdx")["corpus_ref"] = "evals/cases/no-debe-existir.md"
    payload = _run("orden", declarations=_write(data, "orden"))
    assert set(payload["failures"]) == {"1", "5"}
    assert payload["_returncode"] == 1


# --------------------------------------------------------------------------
# integración contra el repositorio real
# --------------------------------------------------------------------------

def test_las_declaraciones_reales_cumplen_las_cuatro_casillas_en_forma() -> None:
    """Pase estructural del repositorio real: solo falla el código 5.

    Es la comprobación que se ejecuta en cada commit: si alguien declara un
    módulo sin contrato, sin corpus o con una dependencia inversa, el suite
    falla aquí y no hace falta esperar a la línea de comandos.
    """
    payload = _run("real", declarations=DECLARATIONS, core_exit_code=0)
    assert set(payload["failures"]) <= {"5"}, payload["failures"]
    esperados = sorted(m["module_id"] for m in _declarations()["modules"])
    assert payload["modules"] == esperados


def test_las_declaraciones_reales_no_declaran_modulo_por_defecto() -> None:
    data = _declarations()
    for module in data["modules"]:
        assert module["default_enabled"] is False, module["module_id"]
        assert module["activation"] in {"dormant_by_default", "opt_in"}, module["module_id"]


def test_cada_modulo_declara_su_corpus_y_su_justificacion() -> None:
    data = _declarations()
    for module in data["modules"]:
        assert (ROOT / module["corpus_ref"]).is_file(), module["module_id"]
        assert len(module["justification"]) >= 20, module["module_id"]
        assert module["limitations"], (
            f"{module['module_id']} declara limitations vacío: o tiene corpus real "
            "o tiene que decir qué no demuestra"
        )


def test_cada_modulo_tiene_contratos_por_lo_menos_por_dos() -> None:
    for module in _declarations()["modules"]:
        assert len(module["contract_paths"]) >= 2, module["module_id"]


def test_los_nueve_modulos_estan_declarados() -> None:
    ids = {m["module_id"] for m in _declarations()["modules"]}
    assert ids == {
        "mdx", "html", "markdown-extensions", "terminology", "language",
        "scale", "review", "delivery", "maintenance",
    }


def test_la_clasificacion_de_scripts_es_completa() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    import optional_modules

    sin_clasificar = optional_modules.unclassified_scripts(ROOT / "scripts")
    assert sin_clasificar == [], sin_clasificar


def test_el_nucleo_no_importa_modulos_opcionales_sin_declarar() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    import optional_modules

    declarados = {
        ("scripts/prepare.py", "mdx_selector"),
        ("scripts/prepare.py", "html_parser"),
        ("scripts/prepare.py", "admonitions"),
        ("scripts/prepare.py", "directives"),
        ("scripts/prepare.py", "mermaid_adapter"),
        ("scripts/regression_detectors.py", "translation_cache"),
        ("scripts/regression_detectors.py", "compare_delivery"),
        ("scripts/regression_detectors.py", "validate_zip_package"),
    }
    findings = optional_modules.core_imports_optional(ROOT / "scripts")
    sin_declarar = [
        (f["script"], f["imports"]) for f in findings
        if (f"scripts/{f['script']}", f["imports"]) not in declarados
    ]
    assert sin_declarar == [], sin_declarar