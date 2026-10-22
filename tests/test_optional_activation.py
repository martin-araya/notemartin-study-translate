"""Casos negativos de activación: un módulo no se enciende sin corpus.

Criterio 1 de G-EXT. Para cada módulo que se activa por perfil, el esquema
tiene que **rechazar** la activación sin `corpus_ref` y `justification`.
Un esquema que acepta `enabled: true` a secas permite activar por descuido,
que es exactamente la activación inmotivada que este gate previene.

La prueba inversa —encender con corpus y con justificación— está en
`test_mdx_gate.py`, `test_html_gate.py` y `test_content_gates.py`.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT / "schemas" / "profile.schema.json"
TMP = Path(tempfile.gettempdir()) / "nst-tests"

BLOCKS_WITH_ENABLED = (
    "mdx",
    "html",
    "admonitions",
    "definition_lists",
    "directives",
    "wikilinks",
    "mixed_profile",
    "rtl",
    "delivery",
    "terminology",
)


def _base_profile() -> dict:
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
        "paths": {"source_root": "/tmp", "work_root": "/tmp", "output_root": "/tmp"},
        "exclusions": [],
        "context_budget": 1500,
        "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
    }


def _validator() -> jsonschema.Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return jsonschema.Draft202012Validator(schema)


def _errors(profile: dict) -> list[str]:
    return [e.message for e in _validator().iter_errors(profile)]


@pytest.mark.parametrize("block", BLOCKS_WITH_ENABLED)
def test_encender_sin_corpus_se_rechaza(block: str) -> None:
    profile = _base_profile()
    profile[block] = {"enabled": True}
    messages = _errors(profile)
    assert messages, f"{block}.enabled=true sin corpus_ref no debería validar"
    joined = " ".join(messages)
    assert "corpus_ref" in joined, joined
    assert "justification" in joined, joined


@pytest.mark.parametrize("block", BLOCKS_WITH_ENABLED)
def test_encender_con_corpus_y_justificacion_se_acepta(block: str) -> None:
    profile = _base_profile()
    profile[block] = {
        "enabled": True,
        "corpus_ref": "evals/cases/markdown-extensions.md",
        "justification": "El corpus declarado justifica encender este módulo concreto.",
    }
    extra = {}
    if block == "mermaid":
        profile[block]["labels"] = "deny"
    if block == "delivery":
        profile[block]["destination_id"] = "plain-markdown-local"
        profile[block]["profile_ref"] = "references/delivery-profiles/plain-markdown-local.json"
    if block == "terminology":
        profile[block]["profile_ref"] = "references/term-profiles.md"
        extra = {"enabled_domains": ["database"]}
    assert _errors(profile) == [], extra


def test_desactivar_no_exige_corpus() -> None:
    """Apagado sigue siendo gratis: el requisito es solo para encender."""
    profile = _base_profile()
    profile["mdx"] = {"enabled": False}
    assert _errors(profile) == []


def test_un_perfil_sin_bloques_opcionales_no_cambia() -> None:
    assert _errors(_base_profile()) == []


def test_declarar_una_variante_regional_exige_corpus() -> None:
    """Elegir variante regional también es una activación."""
    profile = _base_profile()
    profile["locale"] = {"variant": "es-MX"}
    messages = _errors(profile)
    assert any("corpus_ref" in m for m in messages), messages


def test_traducir_frontmatter_exige_corpus() -> None:
    profile = _base_profile()
    profile["frontmatter_policy"] = "translate-allowlist"
    profile["frontmatter_allowed_fields"] = ["title"]
    messages = _errors(profile)
    joined = " ".join(messages)
    assert "frontmatter_corpus_ref" in joined, joined
    assert "frontmatter_justification" in joined, joined


def test_traducir_frontmatter_con_corpus_se_acepta() -> None:
    profile = _base_profile()
    profile["frontmatter_policy"] = "translate-allowlist"
    profile["frontmatter_allowed_fields"] = ["title"]
    profile["frontmatter_corpus_ref"] = "evals/cases/markdown-extensions.md"
    profile["frontmatter_justification"] = "El corpus declarado justifica traducir el título del frontmatter."
    assert _errors(profile) == []


def test_mermaid_labels_allow_tambien_exige_corpus() -> None:
    """Traducir etiquetas Mermaid cambia el diagrama: exige justificación."""
    profile = _base_profile()
    profile["mermaid"] = {"enabled": True, "labels": "allow"}
    messages = _errors(profile)
    assert any("corpus_ref" in m for m in messages), messages

    profile["mermaid"]["corpus_ref"] = "evals/cases/markdown-extensions.md"
    profile["mermaid"]["justification"] = "El corpus declarado justifica traducir las etiquetas del diagrama."
    assert _errors(profile) == []


def test_migrate_profile_añade_el_corpus_del_caso() -> None:
    """La migración rellena desde `modules.json`, no desde la nada."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import migrate_profile

    profile = _base_profile()
    profile["mdx"] = {"enabled": True}
    facts = migrate_profile.load_module_facts(ROOT / "modules.json")
    migrated, pending = migrate_profile.migrate(profile, facts)
    assert pending == []
    assert migrated["mdx"]["corpus_ref"] == "evals/cases/mdx.md"
    assert len(migrated["mdx"]["justification"]) >= 20
    assert _errors(migrated) == []

    # Idempotente.
    again, pending2 = migrate_profile.migrate(migrated, facts)
    assert pending2 == []
    assert again == migrated


def test_migrate_profile_falla_si_el_caso_no_existe() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    import migrate_profile

    profile = _base_profile()
    profile["mdx"] = {"enabled": True}
    _, pending = migrate_profile.migrate(profile, {})
    assert pending == ["mdx"]


def test_migrate_profile_no_toca_los_perfiles_historicos() -> None:
    """Los perfiles de ejecuciones terminadas conservan su hash."""
    for name in ("reports/pilot/profile.json", "reports/beta/profile.json"):
        text = (ROOT / name).read_text(encoding="utf-8")
        assert "frontmatter_corpus_ref" not in text, name
    # Y sus hashes siguen coincidiendo con lo que el manifiesto registra.
    manifest = json.loads((ROOT / "reports/pilot/manifest.json").read_text(encoding="utf-8"))
    profile_hash = manifest["profile_snapshot"]["hash"]
    import hashlib

    actual = hashlib.sha256((ROOT / "reports/pilot/profile.json").read_bytes()).hexdigest()
    assert actual == profile_hash, (
        "el perfil del piloto cambió: su aprobación quedaría invalidada (INV-13)"
    )