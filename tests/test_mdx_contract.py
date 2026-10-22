"""Pruebas del contrato MDX (fase 061)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTRACT = ROOT / "references" / "mdx-contract.md"
FIXTURES = ROOT / "tests" / "fixtures" / "mdx"


def test_mdx_contract_existe() -> None:
    assert CONTRACT.exists()


def test_mdx_contract_declara_estado_opt_in() -> None:
    text = CONTRACT.read_text(encoding="utf-8")
    assert "opt-in" in text
    assert "desactivado" in text.lower() or "desactivada" in text.lower()


def test_mdx_contract_lista_componentes_del_corpus() -> None:
    text = CONTRACT.read_text(encoding="utf-8")
    expected = ["Info", "Note", "Warning", "TabItem", "Card", "CardGroup", "Callout"]
    for component in expected:
        assert component in text, f"falta componente {component!r} en mdx-contract.md"


def test_mdx_contract_enumera_prohibidos() -> None:
    text = CONTRACT.read_text(encoding="utf-8")
    assert "no está soportado" in text.lower() or "no soportado" in text.lower()


def test_fixtures_existen_y_contienen_componentes() -> None:
    assert FIXTURES.is_dir()
    files = list(FIXTURES.glob("*.mdx"))
    assert len(files) >= 3
    combined = "\n".join(f.read_text(encoding="utf-8") for f in files)
    for needle in ("<Callout", "<Note", "<Warning", "<TabItem", "<CardGroup", "<Card "):
        assert needle in combined, f"ningún fixture contiene {needle!r}"