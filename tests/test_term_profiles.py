"""Pruebas de perfiles terminológicos (fase 100)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
REF = ROOT / "references" / "term-profiles.md"

sys.path.insert(0, str(SCRIPTS))

import term_profiles


def test_referencia_existe_y_lista_perfiles_iniciales() -> None:
    text = REF.read_text(encoding="utf-8")
    for profile in ("database-only", "web-stack", "ml-pipeline", "mixed-default"):
        assert profile in text, f"falta perfil {profile!r} en term-profiles.md"


def test_perfiles_tienen_dominios_declarados() -> None:
    for profile in term_profiles.PROFILES_INICIALES:
        assert profile["enabled_domains"], f"perfil {profile['profile_id']} sin dominios"
        assert all(isinstance(d, str) for d in profile["enabled_domains"])


def test_perfiles_registran_approver_y_approved_at() -> None:
    for profile in term_profiles.PROFILES_INICIALES:
        assert profile["approver"]
        assert profile["approved_at"]


def _valid(**overrides) -> dict:
    profile = {
        "profile_id": "x",
        "version": "1.0.0",
        "enabled_domains": ["database"],
        "approver": "humana",
        "approved_at": "2026-10-20T00:00:00Z",
        "corpus_ref": "evals/cases/terminology.md",
        "justification": "El corpus declarado contiene el dominio que este perfil activa.",
        "corpus_real": False,
    }
    profile.update(overrides)
    return profile


def test_perfiles_excepciones_son_auditables() -> None:
    errors = term_profiles.validate_profile(_valid())
    assert errors == []


def test_un_perfil_sin_corpus_no_es_valido() -> None:
    """Criterio 1 de G-EXT: sin corpus declarado no hay activación."""
    errors = term_profiles.validate_profile(_valid(corpus_ref="", justification=""))
    assert any("corpus_ref" in e for e in errors)
    assert any("justification" in e for e in errors)


def test_un_corpus_ref_inexistente_se_rechaza() -> None:
    errors = term_profiles.validate_profile(_valid(corpus_ref="evals/cases/no-existe.md"))
    assert any("corpus_ref no existe" in e for e in errors)


def test_un_dominio_sin_glosario_se_rechaza() -> None:
    errors = term_profiles.validate_profile(_valid(enabled_domains=["database", "inventado"]))
    assert any("sin glosario declarado" in e for e in errors)


def test_un_perfil_real_no_puede_llevar_firma_de_laboratorio() -> None:
    errors = term_profiles.validate_profile(
        _valid(approver="example-agent", corpus_real=True)
    )
    assert any("laboratorio" in e for e in errors)


def test_los_perfiles_iniciales_validan_contra_el_esquema() -> None:
    for profile in term_profiles.PROFILES_INICIALES:
        assert term_profiles.validate_against_schema(profile) == []
        assert profile["corpus_real"] is False


def test_el_esquema_rechaza_un_perfil_sin_corpus() -> None:
    incomplete = {k: v for k, v in _valid().items() if k != "corpus_ref"}
    assert term_profiles.validate_against_schema(incomplete) != []


def test_perfiles_sin_approver_fallan() -> None:
    errors = term_profiles.validate_profile(_valid(approver=""))
    assert any("approver" in e for e in errors)


def test_perfiles_sin_dominios_fallan() -> None:
    errors = term_profiles.validate_profile(_valid(enabled_domains=[]))
    assert any("enabled_domains" in e for e in errors)


def test_perfiles_sin_approved_at_fallan() -> None:
    errors = term_profiles.validate_profile(_valid(approved_at=""))
    assert any("approved_at" in e for e in errors)


def test_perfiles_no_implican_uso_sin_aprobacion() -> None:
    """El validador rechaza cualquier perfil sin aprobación humana
    incluso si el id y los dominios están bien."""
    invalid = term_profiles.validate_profile({
        "profile_id": "x",
        "version": "1.0.0",
        "enabled_domains": ["database"],
    })
    assert len(invalid) >= 2


def test_validate_all_devuelve_por_perfil() -> None:
    out = term_profiles.validate_all(term_profiles.PROFILES_INICIALES)
    for profile in term_profiles.PROFILES_INICIALES:
        assert profile["profile_id"] in out
        assert out[profile["profile_id"]] == []