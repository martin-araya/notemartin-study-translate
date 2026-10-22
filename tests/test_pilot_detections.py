"""Regresiones permanentes encontradas por el piloto real (fase 030).

Estas tres detecciones fallaron contra el corpus piloto autorizado y ya no
deben volver a hacerlo. Sus fixtures se quedan en
``tests/fixtures/regression/`` como caso de referencia, pero **no** viven en
``evals/regression/registry.json``: ese catálogo lista fallos que todavía se
producen, y estas tres reglas ya están corregidas. Lo que las protege es
este archivo.

Cada defecto tiene su par positivo y negativo: lo que no debe marcarse y lo
que sí.

    1. El código inline es un literal protegido: `Array<T>` no es JSX.
    2. El frontmatter se preserva literal: sus aliases no son wikilinks.
    3. Con el módulo MDX activo, el bloqueo se levanta aunque el archivo
       no tenga extensión `.mdx`.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from prepare import classify_file, detect_findings  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "regression"


def _variant(name: str, key: str) -> dict:
    payload = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
    return payload[key]


def _types(document: str) -> set[str]:
    return {finding["type"] for finding in detect_findings(document)}


# --------------------------------------------------------------------------
# 1 · el código inline no es un componente JSX
# --------------------------------------------------------------------------

def test_el_codigo_inline_no_se_declara_jsx() -> None:
    document = _variant("jsx_in_inline_code", "positive")["document"]
    assert "mdx_component" not in _types(document)


def test_un_componente_jsx_en_prosa_sigue_declarado() -> None:
    document = _variant("jsx_in_inline_code", "negative")["document"]
    assert "mdx_component" in _types(document)


def test_una_etiqueta_html_en_codigo_inline_no_bloquea() -> None:
    assert "html_embebido" not in _types('Ejemplo de contenedor `<div class="x">`.\n')


def test_una_etiqueta_html_en_prosa_sigue_bloqueando() -> None:
    assert "html_embebido" in _types('<div class="x">\ncontenido\n</div>\n')


# --------------------------------------------------------------------------
# 2 · el frontmatter no es cuerpo del documento
# --------------------------------------------------------------------------

def test_un_wikilink_en_frontmatter_no_bloquea() -> None:
    document = _variant("wikilink_in_frontmatter", "positive")["document"]
    assert "wikilink" not in _types(document)


def test_un_wikilink_en_el_cuerpo_sigue_bloqueando() -> None:
    document = _variant("wikilink_in_frontmatter", "negative")["document"]
    assert "wikilink" in _types(document)


def test_el_frontmatter_se_preserva_litro() -> None:
    document = _variant("wikilink_in_frontmatter", "positive")["document"]
    frontmatter = document.split("---\n")[1]
    assert frontmatter.startswith("aliases:")


# --------------------------------------------------------------------------
# 3 · el gate MDX se levanta por el hallazgo, no por la extensión
# --------------------------------------------------------------------------

def _verdict(profile: dict, flag_mdx: bool) -> str:
    case = json.loads((FIXTURES / "mdx_gate_ignored_finding.json").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="nst-pilot-") as raw:
        root = Path(raw)
        (root / "doc.md").write_text(case["case"]["document"], encoding="utf-8")
        entry = {"path": "doc.md", "type": "markdown", "flag_mdx": flag_mdx}
        return classify_file(
            entry, root, mdx_enabled=bool(profile.get("mdx", {}).get("enabled"))
        )["verdict"]


def test_sin_el_modulo_el_componente_mdx_bloquea() -> None:
    assert _verdict({}, False) == "blocked"


def test_con_el_modulo_el_componente_mdx_deja_de_bloquear() -> None:
    assert _verdict({"mdx": {"enabled": True}}, False) == "ok"


def test_el_gate_no_depende_de_la_extension() -> None:
    """Un archivo `.md` con MDX y otro `.mdx` se tratan igual con el módulo."""
    assert _verdict({"mdx": {"enabled": True}}, True) == _verdict({"mdx": {"enabled": True}}, False)


def test_el_html_embebido_tiene_su_propio_gate() -> None:
    document = '<div class="cards">\n<img src="a.png" alt="x">\n</div>\n'
    assert "html_embebido" in _types(document)