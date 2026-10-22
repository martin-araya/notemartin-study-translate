"""Pruebas de procedencia de términos (fase 096)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "glossaries"

sys.path.insert(0, str(SCRIPTS))

import term_provenance


def test_attach_provenance_anade_campo_por_entrada() -> None:
    data = json.loads((FIXTURES / "databases.json").read_text(encoding="utf-8"))
    out = term_provenance.attach_provenance(data, "rfc-example", "2026-10-20")
    assert all("provenance" in e for e in out["entries"])
    assert out["entries"][0]["provenance"]["source"] == "rfc-example"


def test_attach_provenance_es_idempotente() -> None:
    data = json.loads((FIXTURES / "databases.json").read_text(encoding="utf-8"))
    out1 = term_provenance.attach_provenance(data, "rfc-example", "2026-10-20")
    out2 = term_provenance.attach_provenance(out1, "rfc-example", "2026-10-20")
    assert out1 == out2


def test_attach_provenance_no_modifica_source_term_ni_preferred() -> None:
    data = json.loads((FIXTURES / "databases.json").read_text(encoding="utf-8"))
    snapshot_before = [(e["source_term"], e["preferred"]["term"], e["sense"]) for e in data["entries"]]
    out = term_provenance.attach_provenance(data, "internal-example", "2026-10-20", url="internal://v1")
    snapshot_after = [(e["source_term"], e["preferred"]["term"], e["sense"]) for e in out["entries"]]
    assert snapshot_before == snapshot_after


def test_attach_provenance_url_opcional() -> None:
    data = json.loads((FIXTURES / "databases.json").read_text(encoding="utf-8"))
    out = term_provenance.attach_provenance(data, "internal", "v1")
    for e in out["entries"]:
        assert "url" not in e["provenance"]


def test_attach_provenance_con_url() -> None:
    data = json.loads((FIXTURES / "databases.json").read_text(encoding="utf-8"))
    out = term_provenance.attach_provenance(data, "internal", "v1", url="https://example.com/v1")
    for e in out["entries"]:
        assert e["provenance"]["url"] == "https://example.com/v1"


def test_has_provenance_detecta_glosario_con_y_sin() -> None:
    data = json.loads((FIXTURES / "databases.json").read_text(encoding="utf-8"))
    assert term_provenance.has_provenance(data) is False
    out = term_provenance.attach_provenance(data, "x", "1")
    assert term_provenance.has_provenance(out) is True


def test_attach_provenance_rechaza_source_vacio() -> None:
    import pytest
    data = json.loads((FIXTURES / "databases.json").read_text(encoding="utf-8"))
    with pytest.raises(ValueError):
        term_provenance.attach_provenance(data, "", "1")
    with pytest.raises(ValueError):
        term_provenance.attach_provenance(data, "x", "")


def test_fixture_with_provenance_es_identico_a_databases() -> None:
    """El fixture decorado se genera a partir de databases y debe
    coincidir tras añadir provenance."""
    base = json.loads((FIXTURES / "databases.json").read_text(encoding="utf-8"))
    decorated = term_provenance.attach_provenance(base, "rfc-example", "2026-10-20", url="internal://v1")
    on_disk = json.loads((FIXTURES / "with_provenance.json").read_text(encoding="utf-8"))
    for live_entry, disk_entry in zip(decorated["entries"], on_disk["entries"]):
        assert live_entry["source_term"] == disk_entry["source_term"]
        assert "provenance" in disk_entry