"""Pruebas de la política regional del español (fase 106)."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "references" / "locale-policy.md"
SCHEMA = ROOT / "schemas" / "profile.schema.json"
DIALECT_PROFILES = ROOT / "references" / "dialect-profiles.md"
ES_ES = ROOT / "tests" / "fixtures" / "es-es"
ES_MX = ROOT / "tests" / "fixtures" / "es-mx"
ES_AR = ROOT / "tests" / "fixtures" / "es-ar"


def test_locale_policy_existe() -> None:
    assert DOC.exists(), f"falta {DOC}"


def test_secciones_obligatorias() -> None:
    text = DOC.read_text(encoding="utf-8")
    for sec in ("Variantes soportadas", "Marcadores obligatorios", "Coloquialismos", "Lo que NO se localiza"):
        assert sec in text, f"falta la sección « {sec} »"


def test_tres_variantes_enumeradas() -> None:
    text = DOC.read_text(encoding="utf-8")
    for v in ("es-ES", "es-MX", "es-AR"):
        assert v in text, f"falta la variante {v}"


def test_coloquialismos_cerrados_minimo() -> None:
    text = DOC.read_text(encoding="utf-8")
    items = {"vosotros", "coche", "ordenador", "vale", "chido", "carnal",
             "che", "boludo", "pibe", "guay", "chaval"}
    found = {w for w in items if w in text}
    assert len(found) >= 8, f"se esperaban >=8 coloquialismos, hallados {found}"


def test_no_localiza_api_numeros_ni_unidades() -> None:
    text = DOC.read_text(encoding="utf-8")
    assert "no se localiza" in text.lower() or "preservar" in text.lower()
    for kw in ("API", "números", "unidades", "URLs"):
        assert kw in text or kw.lower() in text.lower(), f"falta la mención a {kw}"


def test_schema_profile_tiene_locale() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert "locale" in schema["properties"]
    loc = schema["properties"]["locale"]
    assert loc["properties"]["variant"]["enum"] == ["es", "es-ES", "es-MX", "es-AR"]
    assert "voseo" in loc["properties"]
    assert "vosotros" in loc["properties"]
    assert "neutralize_colloquialisms" in loc["properties"]


def test_schema_profile_tiene_rtl() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    assert "rtl" in schema["properties"]
    rtl = schema["properties"]["rtl"]
    assert rtl["properties"]["enabled"]["type"] == "boolean"


def test_dialect_profiles_enumera_las_tres_variantes() -> None:
    text = DIALECT_PROFILES.read_text(encoding="utf-8")
    for v in ("en-es-ar-v1", "en-es-mx-v1", "en-es-es-v1", "fr-es-experimental-v1"):
        assert v in text, f"dialect-profiles.md no declara {v}"


def test_fixtures_es_es_es_real_mdn() -> None:
    assert ES_ES.is_dir()
    files = sorted(p for p in ES_ES.iterdir() if p.suffix == ".md")
    assert len(files) >= 4
    combined = "\n".join(p.read_text(encoding="utf-8") for p in files)
    assert "MDN" in combined or "desarrolladores" in combined
    assert "CC0" not in combined, "el fixture es-ES debe ser real MDN, no derivado CC0"


def _prosa_sin_intro(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    parts = re.split(r"^---\s*$", text, maxsplit=2, flags=re.MULTILINE)
    if len(parts) >= 3:
        return parts[2]
    return text


def test_fixtures_es_mx_es_derivado_cc0_con_usted() -> None:
    assert ES_MX.is_dir()
    files = sorted(p for p in ES_MX.iterdir() if p.suffix == ".md")
    assert len(files) >= 4
    prosa = "\n".join(_prosa_sin_intro(p) for p in files)
    full = "\n".join(p.read_text(encoding="utf-8") for p in files)
    assert "CC0" in full, "los fixtures es-MX son derivados CC0"
    assert "usted" in prosa.lower()
    assert re.search(r"\bvosotros\b", prosa, re.IGNORECASE) is None, (
        "es-MX no debe usar vosotros en la prosa"
    )


def test_fixtures_es_ar_es_derivado_cc0_con_voseo() -> None:
    assert ES_AR.is_dir()
    files = sorted(p for p in ES_AR.iterdir() if p.suffix == ".md")
    assert len(files) >= 4
    prosa = "\n".join(_prosa_sin_intro(p) for p in files)
    full = "\n".join(p.read_text(encoding="utf-8") for p in files)
    assert "CC0" in full
    assert re.search(r"\b(tenés|podés|sabés|querés|detectaste)\b", prosa), (
        "se esperaba al menos una forma de voseo en la prosa"
    )
    assert re.search(r"\bvosotros\b", prosa, re.IGNORECASE) is None, (
        "es-AR no debe usar vosotros en la prosa"
    )
