"""Pruebas de los documentos de release (fase 060).

Cubre:

- ``RELEASE.md`` existe, declara el dialecto probado y enumera
  limitaciones no garantizadas.
- ``CHANGELOG.md`` existe y está enlazado desde ``RELEASE.md``.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RELEASE = ROOT / "RELEASE.md"
CHANGELOG = ROOT / "CHANGELOG.md"


def test_release_md_existe() -> None:
    assert RELEASE.exists()


def test_release_md_declara_dialecto() -> None:
    text = RELEASE.read_text(encoding="utf-8")
    lowered = text.lower()
    assert "commonmark" in lowered or "github flavored markdown" in lowered


def test_release_md_enumera_limitaciones_no_garantizadas() -> None:
    text = RELEASE.read_text(encoding="utf-8")
    assert "## 2. Lo que NO se garantiza" in text or "no se garantiza" in text.lower()
    needles = [
        "fidelidad semántica",
        "Notion",
        "inferencia local",
        "MDX",
    ]
    for n in needles:
        assert n.lower() in text.lower(), f"falta la limitación {n!r}"


def test_release_md_no_se_presenta_como_production_ready() -> None:
    text = RELEASE.read_text(encoding="utf-8")
    lowered = text.lower()
    assert "release candidata" in lowered
    assert "no production-ready" in lowered or "no es production-ready" in lowered or "no es un lanzamiento 1.0.0" in lowered
    positive_claims = [
        " es production-ready",
        "está production-ready",
        "es lista para producción",
    ]
    for claim in positive_claims:
        assert claim not in lowered, f"RELEASE.md no debe contener la afirmación {claim!r}"


def test_changelog_presente_y_referenciable() -> None:
    assert CHANGELOG.exists()
    text = CHANGELOG.read_text(encoding="utf-8")
    assert "Changelog" in text or "changelog" in text.lower()
    release_text = RELEASE.read_text(encoding="utf-8")
    assert "CHANGELOG.md" in release_text