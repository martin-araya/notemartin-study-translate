"""Pruebas del gate MDX por perfil (fase 070)."""

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


def make_corpus(name: str) -> Path:
    out = TMP / name
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / "regular.md").write_text("# Heading\n\nText.\n", encoding="utf-8")
    (out / "component.mdx").write_text("# Heading\n\n<Info title=\"Welcome\">Body</Info>\n", encoding="utf-8")
    return out


def build_inv(corpus: Path) -> Path:
    inv = TMP / f"inv_{corpus.name}.json"
    proc = run([str(INVENTORY), "--source", str(corpus), "--out", str(inv)])
    assert proc.returncode == 0, proc.stderr
    return inv


def profile(tmp: Path, mdx: dict | None) -> Path:
    p = tmp / "profile.json"
    data = {
        "target_language": "es",
        "source_language": "auto",
        "markdown_dialect": "commonmark+gfm",
        "slug_algorithm": {"name": "github", "version": "v1"},
        "code_preservation": "strict",
        "frontmatter_policy": "preserve",
        "bilingual_policy": "first-mention-per-document",
        "punctuation_preference": "es-comma-period",
        "review_mode": "assisted",
        "paths": {"source_root": str(tmp), "work_root": str(tmp), "output_root": str(tmp)},
        "exclusions": [],
        "context_budget": 1500,
        "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
    }
    if mdx is not None:
        data["mdx"] = mdx
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return p


def test_prepare_bloquea_mdx_con_enabled_false() -> None:
    corpus = make_corpus("gate_off")
    inv = build_inv(corpus)
    profile_path = profile(corpus, {"enabled": False})
    out = TMP / "gate_off_out.json"
    proc = run([
        str(PREPARE), "--inventory", str(inv),
        "--out", str(out),
        "--profile", str(profile_path),
    ])
    assert proc.returncode == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    blocked = [f for f in payload["files"] if f["verdict"] == "blocked"]
    assert any(f["path"].endswith(".mdx") for f in blocked)


def test_prepare_pasa_mdx_con_enabled_true() -> None:
    corpus = make_corpus("gate_on")
    inv = build_inv(corpus)
    profile_path = profile(corpus, {"enabled": True})
    out = TMP / "gate_on_out.json"
    proc = run([
        str(PREPARE), "--inventory", str(inv),
        "--out", str(out),
        "--profile", str(profile_path),
    ])
    assert proc.returncode == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    mdx_files = [f for f in payload["files"] if f["path"].endswith(".mdx")]
    assert all(f["verdict"] != "blocked" for f in mdx_files)


def test_default_mdx_disabled() -> None:
    corpus = make_corpus("gate_default")
    inv = build_inv(corpus)
    profile_path = profile(corpus, None)
    out = TMP / "gate_default_out.json"
    proc = run([
        str(PREPARE), "--inventory", str(inv),
        "--out", str(out),
        "--profile", str(profile_path),
    ])
    assert proc.returncode == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    blocked = [f for f in payload["files"] if f["verdict"] == "blocked"]
    assert any(f["path"].endswith(".mdx") for f in blocked)


def test_prepare_sin_profile_bloquea_mdx() -> None:
    corpus = make_corpus("gate_no_profile")
    inv = build_inv(corpus)
    out = TMP / "gate_no_profile_out.json"
    proc = run([
        str(PREPARE), "--inventory", str(inv),
        "--out", str(out),
    ])
    assert proc.returncode == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    blocked = [f for f in payload["files"] if f["verdict"] == "blocked"]
    assert any(f["path"].endswith(".mdx") for f in blocked)


def test_gate_desactivado_no_altera_otros_documentos() -> None:
    corpus = make_corpus("gate_no_alter")
    inv = build_inv(corpus)
    profile_path = profile(corpus, {"enabled": False})
    out = TMP / "gate_no_alter_out.json"
    proc = run([
        str(PREPARE), "--inventory", str(inv),
        "--out", str(out),
        "--profile", str(profile_path),
    ])
    payload = json.loads(out.read_text(encoding="utf-8"))
    regular = [f for f in payload["files"] if f["path"].endswith(".md")]
    assert all(f["verdict"] == "ok" for f in regular)


def test_profile_schema_acepta_mdx_enabled() -> None:
    import jsonschema
    profile_data = {
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
        "mdx": {
            "enabled": True,
            "corpus_ref": "evals/cases/mdx.md",
            "justification": "El corpus piloto contiene componentes MDX que exigen este gate.",
            "contract_path": "references/mdx-contract.md",
            "attributes": ["title", "label"],
        },
    }
    schema = json.loads((ROOT / "schemas" / "profile.schema.json").read_text())
    jsonschema.validate(profile_data, schema)


def test_profile_schema_rechaza_mdx_invalido() -> None:
    import jsonschema
    profile_data = {
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
        "mdx": {"enabled": "yes"},
    }
    schema = json.loads((ROOT / "schemas" / "profile.schema.json").read_text())
    raised = False
    try:
        jsonschema.validate(profile_data, schema)
    except jsonschema.ValidationError:
        raised = True
    assert raised
