"""Pruebas del gate HTML por perfil (fase 070-H)."""

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


def make_html_corpus(name: str) -> Path:
    """Corpus con HTML dentro y fuera del contrato.

    `with_html.md` usa `<details>`, que `references/html-contract.md` §2
    admite. `unsupported.md` usa `<div>`, que no admite: encender el
    módulo no lo deja pasar, solo levanta el bloqueo de lo que sí está
    dentro del contrato.
    """
    out = TMP / name
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / "regular.md").write_text("# Heading\n\nText.\n", encoding="utf-8")
    (out / "with_html.md").write_text(
        "# Heading\n\n<details open>\n<summary>Resumen</summary>\n\nCuerpo visible.\n\n</details>\n",
        encoding="utf-8",
    )
    (out / "unsupported.md").write_text(
        "# Heading\n\n<div class=\"highlight\">Body</div>\n",
        encoding="utf-8",
    )
    return out


def build_inv(corpus: Path) -> Path:
    inv = TMP / f"inv_html_{corpus.name}.json"
    proc = run([str(INVENTORY), "--source", str(corpus), "--out", str(inv)])
    assert proc.returncode == 0, proc.stderr
    return inv


def profile(tmp: Path, html: dict | None) -> Path:
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
    if html is not None:
        data["html"] = html
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return p


def test_prepare_bloquea_html_con_enabled_false() -> None:
    corpus = make_html_corpus("html_gate_off")
    inv = build_inv(corpus)
    profile_path = profile(corpus, {"enabled": False})
    out = TMP / "html_gate_off.json"
    proc = run([
        str(PREPARE), "--inventory", str(inv),
        "--out", str(out),
        "--profile", str(profile_path),
    ])
    assert proc.returncode == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    blocked = [f for f in payload["files"] if f["verdict"] == "blocked"]
    # Con el módulo apagado, la etiqueta activa del HTML bloquea; la que sí
    # admite el contrato tampoco bloquea, pero su texto no se traduce: eso
    # lo decide el módulo apagado, y es la diferencia entre las dos filas.
    assert [f["path"] for f in blocked] == ["unsupported.md"]


def test_prepare_pasa_html_con_enabled_true() -> None:
    corpus = make_html_corpus("html_gate_on")
    inv = build_inv(corpus)
    profile_path = profile(corpus, {"enabled": True})
    out = TMP / "html_gate_on.json"
    proc = run([
        str(PREPARE), "--inventory", str(inv),
        "--out", str(out),
        "--profile", str(profile_path),
    ])
    assert proc.returncode == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    html_files = [f for f in payload["files"] if f["path"].endswith("with_html.md")]
    assert all(f["verdict"] != "blocked" for f in html_files)


def test_html_fuera_del_contrato_sigue_bloqueando_con_el_modulo_encendido() -> None:
    """Encender el módulo no es permitir cualquier HTML."""
    corpus = make_html_corpus("html_gate_contrato")
    inv = build_inv(corpus)
    profile_path = profile(corpus, {"enabled": True})
    out = TMP / "html_gate_contrato.json"
    proc = run([
        str(PREPARE), "--inventory", str(inv),
        "--out", str(out),
        "--profile", str(profile_path),
    ])
    assert proc.returncode == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    blocked = [f for f in payload["files"] if f["verdict"] == "blocked"]
    assert [f["path"] for f in blocked] == ["unsupported.md"]
    assert any(x["type"] == "unsupported_html" for x in blocked[0]["findings"])


def test_default_html_disabled() -> None:
    """Sin perfil no hay módulo: el HTML activo del núcleo sigue bloqueando."""
    corpus = make_html_corpus("html_gate_default")
    inv = build_inv(corpus)
    profile_path = profile(corpus, None)
    out = TMP / "html_gate_default.json"
    proc = run([
        str(PREPARE), "--inventory", str(inv),
        "--out", str(out),
        "--profile", str(profile_path),
    ])
    assert proc.returncode == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    blocked = [f for f in payload["files"] if f["verdict"] == "blocked"]
    assert [f["path"] for f in blocked] == ["unsupported.md"]
    assert any(f["type"] == "html_embebido" for f in blocked[0]["findings"])


def test_html_gate_no_altera_otros_documentos() -> None:
    corpus = make_html_corpus("html_gate_no_alter")
    inv = build_inv(corpus)
    profile_path = profile(corpus, {"enabled": True})
    out = TMP / "html_gate_no_alter.json"
    proc = run([
        str(PREPARE), "--inventory", str(inv),
        "--out", str(out),
        "--profile", str(profile_path),
    ])
    payload = json.loads(out.read_text(encoding="utf-8"))
    regular = [f for f in payload["files"] if f["path"].endswith("regular.md")]
    assert all(f["verdict"] == "ok" for f in regular)


def test_profile_schema_acepta_html_enabled() -> None:
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
        "html": {
            "enabled": True,
            "corpus_ref": "evals/cases/html.md",
            "justification": "El corpus declarado justifica encender este módulo concreto.",
            "contract_path": "references/html-contract.md",
            "attributes": ["title", "aria-label"],
        },
    }
    schema = json.loads((ROOT / "schemas" / "profile.schema.json").read_text())
    jsonschema.validate(profile_data, schema)


def test_profile_schema_rechaza_html_invalido() -> None:
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
        "html": {"enabled": "yes"},
    }
    schema = json.loads((ROOT / "schemas" / "profile.schema.json").read_text())
    raised = False
    try:
        jsonschema.validate(profile_data, schema)
    except jsonschema.ValidationError:
        raised = True
    assert raised
