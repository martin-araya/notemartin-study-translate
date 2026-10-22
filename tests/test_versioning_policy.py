"""Pruebas de la política de versionado (fase 142).

Comprueban dos cosas distintas:

1. que el árbol real sea coherente con `release_contract.json`,
2. que `scripts/check_versioning.py` detecte cada violación construyendo
   un árbol mínimo en `tmp_path` y rompiendo una regla cada vez.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from check_versioning import check_versioning, exit_code_for  # noqa: E402


def _minimal_tree(root: Path, *, skill_version: str = "0.2.0",
                  changelog_version: str = "0.2.0") -> Path:
    (root / "schemas").mkdir(parents=True, exist_ok=True)
    (root / "references").mkdir(parents=True, exist_ok=True)
    (root / "scripts").mkdir(parents=True, exist_ok=True)
    (root / "schemas" / "demo.schema.json").write_text(json.dumps({
        "$id": "https://notemartin-study-translate.local/schemas/demo.schema.json",
        "x-schema-version": "1.0.0",
        "title": "Demo",
        "type": "object",
    }, indent=2), encoding="utf-8")
    (root / "references" / "demo.md").write_text(
        "<!-- version: 1.0.0 -->\n\n# Demo\n", encoding="utf-8")
    (root / "references" / "markdown-contract.md").write_text(
        "<!-- version: 1.0.0 -->\n\n# Contrato\n\n- **Versión fijada**: `3.0.0`\n",
        encoding="utf-8")
    (root / "references" / "parser-upgrade.md").write_text(
        "<!-- version: 1.0.0 -->\n\n# Parser\n", encoding="utf-8")
    (root / "scripts" / "migrate_manifest.py").write_text("# migración\n", encoding="utf-8")
    (root / "CHANGELOG.md").write_text(
        f"# Changelog\n\n### {changelog_version} — prueba\n\n- 141: algo\n", encoding="utf-8")
    (root / "requirements.txt").write_text("jsonschema==4.25.1\n", encoding="utf-8")
    contract = {
        "skill_version": skill_version,
        "contracts": [
            {"id": "C-RUN", "version": "translate/v1", "doc": "references/demo.md"},
        ],
        "schemas": [{"path": "schemas/demo.schema.json", "version": "1.0.0"}],
        "docs": [
            {"path": "references/demo.md", "version": "1.0.0"},
            {"path": "references/markdown-contract.md", "version": "1.0.0"},
            {"path": "references/parser-upgrade.md", "version": "1.0.0"},
        ],
        "breaking_changes": [{
            "id": "demo-breaking",
            "phase": 143,
            "description": "Cambio incompatible de demostración con migración.",
            "migration": "scripts/migrate_manifest.py",
        }],
        "migrations": [{"from": "translate/v0", "to": "translate/v1",
                        "tool": "scripts/migrate_manifest.py"}],
        "parser": {"name": "markdown-it-py", "pinned": "3.0.0",
                   "policy": "references/parser-upgrade.md"},
        "prompt_version": "1.0.0",
    }
    (root / "release_contract.json").write_text(json.dumps(contract, indent=2), encoding="utf-8")
    return root


def _contract(root: Path) -> dict:
    return json.loads((root / "release_contract.json").read_text(encoding="utf-8"))


def _save(root: Path, contract: dict) -> None:
    (root / "release_contract.json").write_text(json.dumps(contract, indent=2), encoding="utf-8")


# --------------------------------------------------------------------------
# árbol real
# --------------------------------------------------------------------------

def test_el_arbol_real_es_coherente() -> None:
    report = check_versioning(ROOT)
    assert report["failures"] == {}, report["failures"]
    assert exit_code_for(report) == 0


def test_el_contrato_real_declara_la_ultima_version_del_changelog() -> None:
    """Que el contrato coincida con el changelog, no con un literal.

    Fijar aquí un número de versión hacía fallar esta prueba en cada
    cambio real, que es justo cuando debe pasar.
    """
    report = check_versioning(ROOT)
    declared = report["counts"]["skill_version"]
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    match = re.search(r"^### (\d+\.\d+\.\d+) ", text, re.MULTILINE)
    assert match, "el changelog no tiene entrada de versión"
    assert declared == match.group(1)


def test_toda_referencia_real_lleva_marca_de_version() -> None:
    for path in sorted((ROOT / "references").rglob("*.md")):
        assert "<!-- version:" in path.read_text(encoding="utf-8"), path.name


def test_todo_esquema_real_declara_x_schema_version() -> None:
    for path in sorted((ROOT / "schemas").glob("*.schema.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data.get("x-schema-version"), path.name


# --------------------------------------------------------------------------
# detección de violaciones
# --------------------------------------------------------------------------

def test_árbol_mínimo_válido_pasa(tmp_path: Path) -> None:
    report = check_versioning(_minimal_tree(tmp_path))
    assert report["ok"], report["failures"]
    assert exit_code_for(report) == 0


def test_sin_entrada_de_changelog_falla(tmp_path: Path) -> None:
    root = _minimal_tree(tmp_path, changelog_version="0.1.5")
    report = check_versioning(root)
    assert report["failures"]["1"], report["failures"]
    assert exit_code_for(report) == 1


def test_esquema_sin_x_schema_version_falla(tmp_path: Path) -> None:
    root = _minimal_tree(tmp_path)
    path = root / "schemas" / "demo.schema.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data.pop("x-schema-version")
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    report = check_versioning(root)
    assert report["failures"]["2"], report["failures"]
    assert exit_code_for(report) == 2


def test_esquema_listado_inexistente_falla(tmp_path: Path) -> None:
    root = _minimal_tree(tmp_path)
    contract = _contract(root)
    contract["schemas"].append({"path": "schemas/no_existe.schema.json", "version": "1.0.0"})
    _save(root, contract)
    report = check_versioning(root)
    assert report["failures"]["2"], report["failures"]


def test_referencia_sin_marca_de_version_falla(tmp_path: Path) -> None:
    root = _minimal_tree(tmp_path)
    (root / "references" / "sin_marca.md").write_text("# Sin marca\n", encoding="utf-8")
    report = check_versioning(root)
    assert report["failures"]["3"], report["failures"]
    assert exit_code_for(report) == 3


def test_dependencias_sin_pinear_fallan(tmp_path: Path) -> None:
    root = _minimal_tree(tmp_path)
    (root / "requirements.txt").write_text("jsonschema\n", encoding="utf-8")
    report = check_versioning(root)
    assert report["failures"]["6"], report["failures"]
    assert exit_code_for(report) == 6


def test_cambio_incompatible_sin_migracion_falla(tmp_path: Path) -> None:
    root = _minimal_tree(tmp_path)
    contract = _contract(root)
    contract["migrations"] = []
    _save(root, contract)
    report = check_versioning(root)
    assert report["failures"]["4"], report["failures"]
    assert exit_code_for(report) == 4


def test_parser_fijado_distinto_del_contrato_falla(tmp_path: Path) -> None:
    root = _minimal_tree(tmp_path)
    contract = _contract(root)
    contract["parser"]["pinned"] = "4.0.0"
    _save(root, contract)
    report = check_versioning(root)
    assert report["failures"]["5"], report["failures"]
    assert exit_code_for(report) == 5


def test_contrato_ilegible_falla(tmp_path: Path) -> None:
    root = _minimal_tree(tmp_path)
    (root / "release_contract.json").write_text("{no es json", encoding="utf-8")
    report = check_versioning(root)
    assert report["failures"]["5"], report["failures"]
    assert exit_code_for(report) == 5