"""Pruebas de la matriz lingüística (fase 110)."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LM = ROOT / "scripts" / "language_matrix.py"
JSON = ROOT / "reports" / "language_matrix.json"
DOC = ROOT / "references" / "dialect-profiles.md"


def test_script_genera_json() -> None:
    rc = subprocess.run(
        [sys.executable, str(LM), "--out", str(JSON)],
        capture_output=True, text=True, check=False,
    ).returncode
    assert rc == 0
    assert JSON.exists()


def test_json_contiene_estructura_esperada() -> None:
    payload = json.loads(JSON.read_text(encoding="utf-8"))
    for key in ("generated_at", "skill", "schema_version", "threshold_human_approved",
                "stable", "human_approved_count", "pairs", "planned_pairs"):
        assert key in payload, f"falta la clave « {key} »"
    assert isinstance(payload["pairs"], list)
    assert isinstance(payload["planned_pairs"], list)
    assert payload["threshold_human_approved"] >= 1


def test_cada_par_declara_tipo_y_politica() -> None:
    payload = json.loads(JSON.read_text(encoding="utf-8"))
    for pair in payload["pairs"]:
        for key in ("pair", "locale", "evaluation_kind", "reviewer_status",
                    "human_reviewer", "corpus", "limits", "rtl"):
            assert key in pair, f"par « {pair.get('pair', '?') } » sin clave « {key} »"
        assert pair["evaluation_kind"] in {
            "human_approved", "assisted", "experimental", "not_started",
        }
        assert pair["reviewer_status"] in {
            "human_approved", "assisted_only_pending_human", "not_applicable",
        }


def test_rubrica_evaluation_kind_y_reviewer_status_consistente() -> None:
    payload = json.loads(JSON.read_text(encoding="utf-8"))
    for pair in payload["pairs"]:
        kind = pair["evaluation_kind"]
        status = pair["reviewer_status"]
        if kind == "human_approved":
            assert status == "human_approved", pair
            assert pair["human_reviewer"], pair
        if kind in ("assisted", "experimental"):
            assert status in {"assisted_only_pending_human", "not_applicable"}, pair


def test_dialect_profiles_referencia_la_matriz() -> None:
    text = DOC.read_text(encoding="utf-8")
    assert "reports/language_matrix.json" in text
    assert "umbral" in text.lower() or "tres pares" in text.lower()


def test_pares_con_evaluation_kind_human_approved() -> None:
    payload = json.loads(JSON.read_text(encoding="utf-8"))
    human = [p for p in payload["pairs"] if p["evaluation_kind"] == "human_approved"]
    assert len(human) >= 1, "se esperaba al menos un par con firma humana (en-es)"
    assert "en-es" in [p["pair"] for p in human]


def test_stable_false_hasta_alcanzar_umbral() -> None:
    payload = json.loads(JSON.read_text(encoding="utf-8"))
    if payload["human_approved_count"] < payload["threshold_human_approved"]:
        assert payload["stable"] is False


def test_incluye_par_fr_es() -> None:
    payload = json.loads(JSON.read_text(encoding="utf-8"))
    pairs = {p["pair"] for p in payload["pairs"]}
    assert "fr-es" in pairs


def test_incluye_par_ar_es_con_rtl_true() -> None:
    payload = json.loads(JSON.read_text(encoding="utf-8"))
    ar = next((p for p in payload["pairs"] if p["pair"] == "ar-es"), None)
    assert ar is not None
    assert ar["rtl"] is True
    assert ar["evaluation_kind"] in {"assisted", "experimental", "human_approved"}
