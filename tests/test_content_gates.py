"""Pruebas del schema y los gates de las extensiones 081–085."""

from __future__ import annotations

import tempfile
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
INVENTORY = SCRIPTS / "inventory.py"
PREPARE = SCRIPTS / "prepare.py"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def _build_profile(extra: dict) -> dict:
    base = {
        "target_language": "es",
        "source_language": "auto",
        "markdown_dialect": "commonmark+gfm",
        "slug_algorithm": {"name": "github", "version": "v1"},
        "code_preservation": "strict",
        "frontmatter_policy": "preserve",
        "bilingual_policy": "first-mention-per-document",
        "punctuation_preference": "es-comma-period",
        "review_mode": "assisted",
        "paths": {"source_root": "/tmp", "work_root": "/tmp", "output_root": "/tmp"},
        "exclusions": [],
        "context_budget": 1500,
        "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
    }
    base.update(extra)
    return base


CORPUS = {
    "corpus_ref": "evals/cases/markdown-extensions.md",
    "justification": "El corpus declarado justifica encender este módulo concreto.",
}


def test_profile_schema_acepta_admonitions() -> None:
    import jsonschema
    profile = _build_profile({"admonitions": {"enabled": True, "types": ["note", "warning"], **CORPUS}})
    schema = json.loads((ROOT / "schemas" / "profile.schema.json").read_text())
    jsonschema.validate(profile, schema)


def test_profile_schema_acepta_definition_lists() -> None:
    import jsonschema
    profile = _build_profile({"definition_lists": {"enabled": True, **CORPUS}})
    schema = json.loads((ROOT / "schemas" / "profile.schema.json").read_text())
    jsonschema.validate(profile, schema)


def test_profile_schema_acepta_directives() -> None:
    import jsonschema
    profile = _build_profile({"directives": {"enabled": True, "names": ["param", "type"], **CORPUS}})
    schema = json.loads((ROOT / "schemas" / "profile.schema.json").read_text())
    jsonschema.validate(profile, schema)


def test_profile_schema_acepta_mermaid() -> None:
    import jsonschema
    profile = _build_profile({"mermaid": {"enabled": True, "labels": "allow", **CORPUS}})
    schema = json.loads((ROOT / "schemas" / "profile.schema.json").read_text())
    jsonschema.validate(profile, schema)


def test_profile_schema_rechaza_admonitions_invalido() -> None:
    import jsonschema
    profile = _build_profile({"admonitions": {"enabled": "yes"}})
    schema = json.loads((ROOT / "schemas" / "profile.schema.json").read_text())
    raised = False
    try:
        jsonschema.validate(profile, schema)
    except jsonschema.ValidationError:
        raised = True
    assert raised


def test_prepare_bloquea_admonition_sin_gate() -> None:
    corpus = TMP / "gate_default_adm"
    if corpus.exists():
        shutil.rmtree(corpus)
    corpus.mkdir()
    (corpus / "doc.md").write_text("# t\n\n:::warning\nbody\n:::\n", encoding="utf-8")
    inv = TMP / "inv_adm.json"
    assert run([str(INVENTORY), "--source", str(corpus), "--out", str(inv)]).returncode == 0
    profile = TMP / "profile_adm.json"
    profile.write_text(json.dumps(_build_profile({}), indent=2), encoding="utf-8")
    out = TMP / "out_adm.json"
    proc = run([str(PREPARE), "--inventory", str(inv), "--out", str(out), "--profile", str(profile)])
    assert proc.returncode == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert any(f["verdict"] == "blocked" for f in payload["files"])


def test_prepare_pasa_admonition_con_gate() -> None:
    corpus = TMP / "gate_on_adm"
    if corpus.exists():
        shutil.rmtree(corpus)
    corpus.mkdir()
    (corpus / "doc.md").write_text("# t\n\n:::warning\nbody\n:::\n", encoding="utf-8")
    inv = TMP / "inv_adm_on.json"
    assert run([str(INVENTORY), "--source", str(corpus), "--out", str(inv)]).returncode == 0
    profile = TMP / "profile_adm_on.json"
    profile.write_text(json.dumps(_build_profile({"admonitions": {"enabled": True, "types": ["note", "warning"]}}), indent=2), encoding="utf-8")
    out = TMP / "out_adm_on.json"
    proc = run([str(PREPARE), "--inventory", str(inv), "--out", str(out), "--profile", str(profile)])
    assert proc.returncode == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert not any(f["verdict"] == "blocked" for f in payload["files"])


def _classify(body: str, extra_profile: dict, tag: str) -> list[dict]:
    """Inventaría un archivo y devuelve los registros clasificados."""
    corpus = TMP / f"gate_{tag}"
    if corpus.exists():
        shutil.rmtree(corpus)
    corpus.mkdir()
    (corpus / "doc.md").write_text(body, encoding="utf-8")
    inv = TMP / f"inv_{tag}.json"
    assert run([str(INVENTORY), "--source", str(corpus), "--out", str(inv)]).returncode == 0
    profile = TMP / f"profile_{tag}.json"
    profile.write_text(json.dumps(_build_profile(extra_profile), indent=2), encoding="utf-8")
    out = TMP / f"out_{tag}.json"
    proc = run([str(PREPARE), "--inventory", str(inv), "--out", str(out), "--profile", str(profile)])
    assert proc.returncode == 0, proc.stderr
    return json.loads(out.read_text(encoding="utf-8"))["files"]


def test_admonition_de_tipo_no_admitido_sigue_bloqueando() -> None:
    """La lista `types` restringe: un tipo fuera de ella no se perdona."""
    files = _classify(
        "# t\n\n:::danger\nbody\n:::\n",
        {"admonitions": {"enabled": True, "types": ["note", "warning"]}},
        "adm_types",
    )
    assert files[0]["verdict"] == "blocked"
    assert any(f["type"] == "unsupported_admonition" for f in files[0]["findings"])


def test_definition_lists_apaga_el_gate_sin_tocar_el_resto() -> None:
    """`definition_lists.enabled` llega al gate: antes era un parámetro muerto."""
    body = "# t\n\nAPI\n: endpoint que acepta peticiones\n\nTexto normal.\n"
    blocked = _classify(body, {}, "def_off")
    assert blocked[0]["verdict"] == "blocked"
    assert any(f["type"] == "definition_list" for f in blocked[0]["findings"])
    opened = _classify(body, {"definition_lists": {"enabled": True}}, "def_on")
    assert opened[0]["verdict"] == "ok"


def test_directiva_no_soportada_bloquea_cuando_el_modulo_esta_apagado() -> None:
    """Un nombre de directiva desconocido es un hallazgo, no un silencio."""
    files = _classify("# t\n\nDocumentación de la función.\n", {}, "dir_off")
    assert files[0]["verdict"] == "ok"

    corpus_docs = {"directives": {"enabled": True, "names": ["param", "type"]}}
    allowed = _classify(
        "# t\n\n:param x: valor de entrada\n",
        corpus_docs,
        "dir_on",
    )
    assert not any(f["type"] == "unsupported_directive" for f in allowed[0]["findings"])

    unknown = _classify(
        "# t\n\n:inventado: no está en la lista del perfil\n",
        corpus_docs,
        "dir_unknown",
    )
    assert any(f["type"] == "unsupported_directive" for f in unknown[0]["findings"])


def test_mermaid_malformado_solo_bloquea_al_traducir_etiquetas() -> None:
    """El núcleo preserva Mermaid literal; traducir etiquetas sí obliga a validar."""
    body = "# t\n\n```mermaid\nflowchart TD\nA]invalid\n```\n"
    core = _classify(body, {}, "mm_core")
    assert core[0]["verdict"] == "ok"
    assert any(f["type"] == "mermaid_unsupported" for f in core[0]["findings"])
    assert all(f["severity"] != "bloqueante" for f in core[0]["findings"])

    labels_on = _classify(body, {"mermaid": {"enabled": True, "labels": "allow"}}, "mm_on")
    assert labels_on[0]["verdict"] == "blocked"

    deny = _classify(body, {"mermaid": {"enabled": True, "labels": "deny"}}, "mm_deny")
    assert deny[0]["verdict"] == "ok"
