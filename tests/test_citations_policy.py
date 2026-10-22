"""Pruebas de la política de citas (fase 105)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import citations  # noqa: E402

DOC_POLICY = ROOT / "references" / "citations-policy.md"
FIXTURE = ROOT / "tests" / "fixtures" / "citations" / "exemple.md"


def test_politica_existe_y_declara_tres_categorias() -> None:
    assert DOC_POLICY.exists()
    text = DOC_POLICY.read_text(encoding="utf-8")
    for cat in ("cita_contractual", "literal_tecnico", "prosa_traducible"):
        assert cat in text, f"falta la categoría {cat}"


def test_clasificador_codigo_es_tecnico() -> None:
    seg = {
        "structural_type": "code_fenced",
        "translatable_text": "occ twofactor:disable --user foo",
    }
    assert citations.classify(seg) == "technical_literal"


def test_clasificador_spdx_es_contractual() -> None:
    seg = {
        "structural_type": "blockquote",
        "translatable_text": "SPDX-License-Identifier: CC0-1.0",
    }
    assert citations.classify(seg) == "contractual"


def test_clasificador_admonition_legal_es_contractual() -> None:
    seg = {
        "structural_type": "blockquote",
        "translatable_text": "> **Note de licence.** Cette œuvre est dédiée au domaine public.",
    }
    assert citations.classify(seg) == "contractual"


def test_clasificador_phrase_legale_es_contractual() -> None:
    seg = {
        "structural_type": "paragraph",
        "translatable_text": "Les conditions d'utilisation s'appliquent à tous les utilisateurs.",
    }
    assert citations.classify(seg) == "contractual"


def test_clasificador_cita_literaria_es_prosa_traducible() -> None:
    seg = {
        "structural_type": "blockquote",
        "translatable_text": "« La documentation technique n'est pas un récit ; elle est un instrument. »",
    }
    assert citations.classify(seg) == "translatable_prose"


def test_cuenta_de_clasificacion_consistente() -> None:
    segments = [
        {"structural_type": "code_fenced", "translatable_text": "echo hi"},
        {"structural_type": "blockquote", "translatable_text": "SPDX-License-Identifier: MIT"},
        {"structural_type": "blockquote", "translatable_text": "Note de licence : tout est libre."},
        {"structural_type": "blockquote", "translatable_text": "« Pensée du jour. »"},
        {"structural_type": "paragraph", "translatable_text": "Prosa normal, sin marcas legales."},
    ]
    counts = citations.classify_all(segments)
    assert counts["technical_literal"] >= 1
    assert counts["contractual"] >= 2
    assert counts["translatable_prose"] >= 1


def test_fixture_tiene_las_tres_categorias() -> None:
    text = FIXTURE.read_text(encoding="utf-8")
    assert "SPDX-License-Identifier" in text
    assert "Conditions d'utilisation" in text or "conditions d'utilisation" in text
    assert "Note de licence" in text
    assert "```" in text
    assert "« " in text or "«»" in text
