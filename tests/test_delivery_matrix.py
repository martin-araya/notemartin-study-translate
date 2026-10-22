"""Pruebas de la matriz de destinos de entrega (fase 139)."""

from __future__ import annotations

import tempfile
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "delivery_matrix.py"
TMP = Path(tempfile.gettempdir()) / "nst-tests"
OUT = TMP / "delivery_matrix.json"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def matrix() -> dict:
    proc = run([str(SCRIPT), "--out", str(OUT)])
    assert proc.returncode == 0, proc.stderr
    return json.loads(OUT.read_text(encoding="utf-8"))


def test_la_matriz_declara_los_dos_destinos() -> None:
    payload = matrix()
    ids = [d["destination_id"] for d in payload["destinations"]]
    assert ids == ["notion-manual", "plain-markdown-local"]
    assert payload["any_verified"] is False


def test_ningun_destino_se_verifica_sin_evidencia() -> None:
    payload = matrix()
    for destination in payload["destinations"]:
        assert destination["verified"] is False
        assert destination["activation"] == "explicit"
        assert destination["limitations"], destination["destination_id"]
        assert destination["cases"], destination["destination_id"]


def test_el_adaptador_interno_declara_que_no_hay_app_real() -> None:
    payload = matrix()
    local = next(d for d in payload["destinations"] if d["destination_id"] == "plain-markdown-local")
    assert local["real_app_evidence"] is False
    assert local["evidence_kind"] == "local_fixture_only"
    assert local["kind"] == "local_adapter"
    assert local["rules"]
    assert local["profile_version"]


def test_el_destino_canonico_no_declara_evidencia_remota() -> None:
    payload = matrix()
    notion = next(d for d in payload["destinations"] if d["destination_id"] == "notion-manual")
    assert notion["kind"] == "canonical"
    assert notion["import_method"] == "manual"
    assert notion["evidence_kind"] == "user_reported"
    assert notion["real_app_evidence"] is False
    assert notion["delivery_profile"] is None


def test_la_matriz_admite_describir_que_no_verifica() -> None:
    payload = matrix()
    assert "no qué funciona" in payload["note"]
    assert "evidencia aportada por una persona" in payload["note"]
