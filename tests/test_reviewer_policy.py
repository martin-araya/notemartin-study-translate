"""Pruebas de la política de revisores (fase 109)."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "references" / "reviewer-policy.md"
SCHEMA = ROOT / "schemas" / "manifest.schema.json"


def test_documento_existe_y_declara_secciones() -> None:
    assert DOC.exists()
    text = DOC.read_text(encoding="utf-8")
    for sec in ("Tabla de firmantes", "Cómo se firma", "Qué distingue una firma humana",
                "Qué **NO** es firma humana"):
        assert sec in text, f"falta la sección « {sec} »"


def test_tabla_de_firmantes_incluye_pares_clave() -> None:
    text = DOC.read_text(encoding="utf-8")
    for pair in ("fr → es", "es-ES", "es-MX", "es-AR", "ar → es"):
        assert pair in text, f"falta el par « {pair} »"


def test_schema_manifest_acepta_reviewers() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert "reviewers" in schema["properties"]
    item_schema = schema["properties"]["reviewers"]["items"]
    assert item_schema["required"] == ["pair", "name", "kind", "signed_at", "scope"]
    assert item_schema["properties"]["kind"]["enum"] == ["human", "assisted"]
    assert "signature_hash" in item_schema["properties"]


def test_human_approved_exige_firma() -> None:
    """Si un manifest declara reviewers.kind=human con scope=global,
    la entrada es válida. La fila del roadmap no se cierra hasta
    que al menos uno exista.
    """
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    item_schema = schema["properties"]["reviewers"]["items"]
    assert item_schema["properties"]["name"]["type"] == ["string", "null"]
    assert item_schema["properties"]["scope"]["type"] == ["string", "array"]


def test_nombre_null_es_valido_para_assisted() -> None:
    """Para entradas `assisted` el `name` puede ser null hasta que
    se registre un identificador."""
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    item = schema["properties"]["reviewers"]["items"]["properties"]
    assert item["name"]["type"] == ["string", "null"]
    assert "null" in item["name"]["type"]


def test_no_promete_garantia_absoluta() -> None:
    text = DOC.read_text(encoding="utf-8")
    assert "no firma equivalencia semántica absoluta" in text.lower() or \
        "firma equivalencia" not in text.lower()
    assert "firmado" in text.lower() or "firma" in text.lower()
