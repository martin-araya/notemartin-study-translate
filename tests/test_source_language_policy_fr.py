"""Pruebas de la política lingüística fr (fase 102)."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "references" / "source-language-policy-fr.md"


def test_documento_existe() -> None:
    assert DOC.exists(), f"falta {DOC}"


def test_contiene_secciones_obligatorias() -> None:
    text = DOC.read_text(encoding="utf-8")
    required = ["Modalidad", "Puntuación", "Falsos amigos", "Limitaciones"]
    for section in required:
        assert section in text, f"falta la sección « {section} »"


def test_tabla_de_falsos_amigos_minima() -> None:
    text = DOC.read_text(encoding="utf-8")
    matches = re.findall(r"^\| [A-Za-zàâçéèêëîïôûùüÿñœæÀ-ÖØ-öø-ÿ][^|]*\| [^|]+\|[^|]+\|[^|]+\|", text, re.MULTILINE)
    rows = [m for m in matches if m.startswith("| ") and "Calco" not in m and "---" not in m]
    entries = [r for r in rows if "Francés" not in r]
    assert len(entries) >= 6, (
        f"se esperaban >=6 entradas en falsos amigos; encontradas {len(entries)}"
    )


def test_no_modifica_ni_codigo_ni_unidades() -> None:
    text = DOC.read_text(encoding="utf-8")
    assert "NO" in text and "decimales" in text, "la política debe prohibir localizar separadores"
    assert "NO" in text and ("unidades" in text), "la política debe prohibir traducir unidades"


def test_vouvoiement_y_puntuacion_francesa() -> None:
    text = DOC.read_text(encoding="utf-8")
    assert "vous" in text, "la política debe nombrar el vouvoiement"
    assert "insécables" in text, "la política debe tratar los espacios insécables"


def test_revisa_no_promete_garantia_absoluta() -> None:
    text = DOC.read_text(encoding="utf-8")
    assert "experimental" in text.lower(), (
        "la política debe declarar el par experimental mientras no haya revisor humano"
    )
