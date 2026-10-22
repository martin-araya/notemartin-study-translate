"""Pruebas de la matriz de dialectos versionada (fase 090)."""

from __future__ import annotations

import tempfile
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
MATRIX = ROOT / "references" / "dialect-profiles.md"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def test_matriz_existe_y_enumera_perfiles_iniciales() -> None:
    text = MATRIX.read_text(encoding="utf-8")
    for profile in ("core-v1", "mild-extensions-v1", "extended-mdx-v1", "extended-html-v1", "experimental-v1"):
        assert profile in text, f"falta {profile!r} en dialect-profiles.md"


def test_matriz_no_promete_soporte_implicito() -> None:
    text = MATRIX.read_text(encoding="utf-8")
    forbidden = [
        "activar mdx activa html",
        "activar html activa mdx",
        "activar mdx activa mermaid",
        "activar html activa mdx",
    ]
    for phrase in forbidden:
        assert phrase.lower() not in text.lower(), f"la matriz promete el soporte implícito {phrase!r}"


def test_matriz_versionada() -> None:
    text = MATRIX.read_text(encoding="utf-8")
    import re
    versions = re.findall(r"\b\d+\.\d+\.\d+\b", text)
    assert versions, "no se encontraron versiones semver en la matriz"


def test_dialect_matrix_script_emite_json() -> None:
    out = TMP / "dialect.json"
    proc = run([str(SCRIPTS / "dialect_matrix.py"), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert "profiles" in payload
    assert len(payload["profiles"]) >= 5
    for profile in payload["profiles"]:
        assert "profile_id" in profile
        assert "version" in profile
        assert "extensions_enabled" in profile


def test_dialect_matrix_perfiles_tienen_does_not_support() -> None:
    out = TMP / "dialect_dns.json"
    proc = run([str(SCRIPTS / "dialect_matrix.py"), "--out", str(out)])
    payload = json.loads(out.read_text(encoding="utf-8"))
    for profile in payload["profiles"]:
        assert "does_not_support" in profile, f"perfil {profile['profile_id']} sin does_not_support"
        assert isinstance(profile["does_not_support"], list)


def test_core_no_habilita_ninguna_extension() -> None:
    out = TMP / "dialect_core.json"
    proc = run([str(SCRIPTS / "dialect_matrix.py"), "--out", str(out)])
    payload = json.loads(out.read_text(encoding="utf-8"))
    core = next(p for p in payload["profiles"] if p["profile_id"] == "core-v1")
    assert core["extensions_enabled"] == []
