"""Pruebas de la matriz de compatibilidad HTML (fase 079)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MATRIX = ROOT / "references" / "html-compatibility.md"


def test_matriz_existe() -> None:
    assert MATRIX.exists()


def test_matriz_cubre_etiquetas_soportadas() -> None:
    text = MATRIX.read_text(encoding="utf-8")
    for needle in ("`details`", "`summary`", "`a`", "`img`", "`table`", "`code`", "`kbd`", "`br`", "`span`"):
        assert needle in text, f"falta {needle!r} en la matriz de compatibilidad"


def test_matriz_declara_advertencia_sobre_notion() -> None:
    text = MATRIX.read_text(encoding="utf-8")
    lowered = text.lower()
    assert "notion" in lowered
    warning_phrases = ("puede", "típicamente", "no se garantiza", "no se carga", "no se repara")
    assert any(p in lowered for p in warning_phrases), "la matriz no incluye ninguna advertencia explícita"


def test_matriz_no_promete_paridad_universal() -> None:
    text = MATRIX.read_text(encoding="utf-8")
    lowered = text.lower()
    forbidden_phrases = [
        "garantizado",
        "garantía completa",
        "compatibilidad total",
    ]
    for phrase in forbidden_phrases:
        assert phrase not in lowered, f"la matriz contiene la promesa prohibida {phrase!r}"
    assert "no es una" in lowered and "promesa de paridad" in lowered
    assert "lo que no se garantiza" in lowered


def test_matriz_lista_etiquetas_prohibidas() -> None:
    text = MATRIX.read_text(encoding="utf-8")
    for needle in ("<script>", "<iframe>", "<object>", "<embed>", "onclick"):
        assert needle in text, f"falta {needle!r} en la sección de prohibidas"


def test_matriz_incluye_seccion_procedimiento() -> None:
    text = MATRIX.read_text(encoding="utf-8")
    assert "Procedimiento" in text or "procedimiento" in text
    assert "manifest.json" in text