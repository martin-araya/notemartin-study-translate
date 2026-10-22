"""Pruebas de precedencia entre glosarios (fase 097)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "glossaries"

sys.path.insert(0, str(SCRIPTS))

import term_precedence


def _load(*names: str) -> list[dict]:
    return [json.loads((FIXTURES / n).read_text(encoding="utf-8")) for n in names]


def test_dominio_especifico_gana_a_global() -> None:
    front = _load("frontend.json")
    db = _load("databases.json")
    front_entry = front[0]["entries"][0]
    assert front_entry["source_term"] == "render"
    out = term_precedence.resolve_conflict("render", "frontend", front + db)
    assert out is not None
    assert out["domain"] == "frontend"


def test_dominio_global_no_reemplaza_especifico() -> None:
    db = _load("databases.json")
    out = term_precedence.resolve_conflict("schema", "database", db)
    assert out is not None
    assert out["domain"] == "database"


def test_dos_entradas_mismo_dominio_no_se_reemplazan() -> None:
    conflict = _load("with_conflict.json")
    out = term_precedence.resolve_conflict("state", "frontend", conflict)
    assert out is not None
    out_db = term_precedence.resolve_conflict("state", "database", conflict)
    assert out_db is not None
    assert out["domain"] == "frontend"
    assert out_db["domain"] == "database"


def test_resolve_conflict_devuelve_none_si_no_hay_match() -> None:
    db = _load("databases.json")
    out = term_precedence.resolve_conflict("unknown_term", "database", db)
    assert out is None


def test_misma_palabra_dominios_distintos_no_es_conflict() -> None:
    """Misma palabra en dos dominios con equivalente distinto NO es
    conflicto: cada dominio gana en su contexto."""
    conflict = _load("with_conflict.json")
    out = term_precedence.list_conflicts(conflict)
    assert out == []


def test_list_conflicts_detecta_equivalentes_distintos_en_mismo_dominio() -> None:
    db = _load("databases.json")
    fake = {
        "source": "fake-source",
        "version": 1,
        "frozen": False,
        "allowed_languages": ["es"],
        "entries": [{
            "id": "g-zzzz",
            "source_term": "schema",
            "domain": "database",
            "sense": "Sentido distinto",
            "preferred": {"lang": "es", "term": "esquema_distinto"},
            "preservation_policy": "translate",
            "context_examples": [{
                "document_id": "x", "segment_id": "x",
                "before": "", "after": "", "note": ""
            }],
            "justification": "test",
            "decided_by": "example-agent",
            "decided_at": "2026-10-20T00:00:00Z",
        }],
    }
    out = term_precedence.list_conflicts(db + [fake])
    assert any(c["source_term"] == "schema" and c["domain"] == "database" for c in out)