"""Pruebas del glosario de redes (fase 092)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "tests" / "fixtures" / "glossaries" / "networks.json"
SCHEMA = json.loads((ROOT / "schemas" / "glossary.schema.json").read_text(encoding="utf-8"))


def test_glosario_existe_y_valida() -> None:
    import jsonschema
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    jsonschema.validate(data, SCHEMA)


def test_glosario_tiene_terminos_clave() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    terms = {e["source_term"] for e in data["entries"]}
    assert "socket" in terms
    assert "endpoint" in terms
    assert "protocol" in terms
    assert "packet" in terms


def test_glosario_siglazy_protocolos_literales() -> None:
    """Siglas como TCP, HTTP, IP permanecen en inglés en los ejemplos."""
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    examples_text = " ".join(
        ex["before"] + " " + ex["after"]
        for e in data["entries"]
        for ex in e["context_examples"]
    )
    terms_text = " ".join(e["source_term"] for e in data["entries"])
    full_text = examples_text + " " + terms_text
    for sig in ("TCP", "HTTP", "IP"):
        assert sig in full_text, f"falta sigla {sig} en ejemplos o source_terms"


def test_socket_y_endpoint_se_desambiguen() -> None:
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    socket_entry = next(e for e in data["entries"] if e["source_term"] == "socket")
    endpoint_entry = next(e for e in data["entries"] if e["source_term"] == "endpoint")
    assert socket_entry["sense"] != endpoint_entry["sense"]
    assert socket_entry["preferred"]["term"] == "socket"
    assert endpoint_entry["preferred"]["term"] == "endpoint"
    assert socket_entry["preservation_policy"] == "keep-original"
    assert endpoint_entry["preservation_policy"] == "keep-original"