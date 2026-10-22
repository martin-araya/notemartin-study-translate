"""Pruebas del caso piloto fr (fase 101)."""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PILOT = ROOT / "tests" / "fixtures" / "pilot-fr"
PILOT_MD = ROOT / "evals" / "cases" / "pilot-fr.md"

EXPECTED = {
    "01-prelude-et-licence.md": "06b2cead15159ee1",
    "02-fichiers-et-synchronisation.md": "f02b3b3f43bed1d3",
    "03-authentification.md": "5c64eaaf682e01d1",
    "04-configuration-2fa.md": "0fcaf443713b06be",
    "05-client-bureau.md": "dfd907470cc074a3",
    "06-preferences-utilisateur.md": "96c7001e89902612",
}


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def test_pilot_fr_md_existe_y_declara_licencia() -> None:
    assert PILOT_MD.exists(), f"falta {PILOT_MD}"
    text = PILOT_MD.read_text(encoding="utf-8")
    assert "CC0" in text or "CC-BY-SA" in text, "pilot-fr.md no declara licencia"
    assert "fr" in text.lower(), "pilot-fr.md debe nombrar el par fr"
    assert "experimental" in text.lower(), "pilot-fr.md debe declararse experimental"


def test_pilot_fr_md_admite_disclaimer_revisor() -> None:
    text = PILOT_MD.read_text(encoding="utf-8")
    assert "revisión asistida" in text or "revisión humana" in text, (
        "pilot-fr.md debe registrar el estado de revisión"
    )


def test_archivos_listados_existen_y_hash_coincide() -> None:
    assert PILOT.is_dir(), f"falta {PILOT}"
    assert sorted(PILOT.name for PILOT in PILOT.iterdir() if PILOT.is_file()) == sorted(
        EXPECTED.keys()
    ), "el conjunto de archivos no coincide con pilot-fr.md"
    for name, prefix in EXPECTED.items():
        p = PILOT / name
        h = sha256_hex(p.read_bytes())
        assert h.startswith(prefix), f"hash de {name} no coincide: {h[:16]} != {prefix}"


def test_codificacion_y_saltos_de_linea() -> None:
    for name in EXPECTED:
        data = (PILOT / name).read_bytes()
        data.decode("utf-8")
        assert b"\r\n" not in data, f"{name} usa CRLF; debe estar en LF"


def test_hay_al_menos_una_admonition_y_una_tabla_y_un_fenced() -> None:
    texts = [(PILOT / n).read_text(encoding="utf-8") for n in EXPECTED]
    corpus = "\n".join(texts)
    assert re.search(r"^>\s*\[!(NOTE|TIP|INFO|WARNING|CAUTION)\]", corpus, re.MULTILINE), (
        "se esperaba al menos una admonition tipo [!NOTE|TIP|...]"
    )
    assert re.search(r"^\|.+\|\s*$", corpus, re.MULTILINE), (
        "se esperaba al menos una fila de tabla GFM"
    )
    assert "```" in corpus, "se esperaba al menos un bloque de código fenced"


def test_dos_documentos_se_enlazan_entre_si() -> None:
    """`02-fichiers...md` debe tener al menos un enlace a otro doc del piloto."""
    text = (PILOT / "02-fichiers-et-synchronisation.md").read_text(encoding="utf-8")
    refs = re.findall(r"\]\((03-authentification\.md|04-configuration-2fa\.md|06-preferences-utilisateur\.md)\)", text)
    assert refs, "se esperaba al menos un enlace a otro doc del piloto"


def test_enlace_externo_presente() -> None:
    text = (PILOT / "05-client-bureau.md").read_text(encoding="utf-8")
    assert re.search(r"https?://", text), "se esperaba un enlace externo"


def test_cita_contractual_en_01_y_06() -> None:
    """`01-...` y `06-...` deben contener una cita de tipo contractual
    (note de licence)."""
    text_01 = (PILOT / "01-prelude-et-licence.md").read_text(encoding="utf-8")
    text_06 = (PILOT / "06-preferences-utilisateur.md").read_text(encoding="utf-8")
    assert "Note de licence" in text_01 or "Licence" in text_01
    assert "Note de licence" in text_06 or "Licence" in text_06


def test_frente_a_nucleo_intacto() -> None:
    """El piloto fr no debe invadir `tests/fixtures/pilot/`."""
    other = ROOT / "tests" / "fixtures" / "pilot"
    before = sorted(p.name for p in other.iterdir()) if other.exists() else []
    expected = {
        "APIs_OpenRouter_01_-_Introducción,_Autenticación_y_Formato_General.md",
        "APIs_OpenRouter_04_-_Capacidades_Avanzadas_Reasoning,_Tool_Calling.md",
        "developer-mozilla_Guides_Cascading_variables_Using_custom_properties.md",
        "developer-mozilla_How_to_Layout_cookbook_Card.md",
        "mermaid_build-and-edit_write-diagram-syntax.md",
        "mermaid_guides_presentation.md",
        "oracle_notas_Cap_14_Cap_14_Physical_Storage_Structures.md",
        "typescriptlang_handbook_2_basic-types.md",
        "typescriptlang_handbook_2_functions.md",
    }
    assert set(before) == expected, "el piloto en→es no debe cambiar"
