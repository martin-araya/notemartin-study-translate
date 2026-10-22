"""Pruebas del eval de par fr→es (fase 103)."""

from __future__ import annotations

import tempfile
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVAL = ROOT / "scripts" / "eval_pair.py"
PILOT = ROOT / "tests" / "fixtures" / "pilot-fr"
REPORTS = ROOT / "reports" / "fr-es-pilot"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def test_eval_pair_ejecuta_y_emite_artefactos() -> None:
    out = TMP / "fr-es-eval"
    rc = run([
        str(EVAL),
        "--source", str(PILOT),
        "--pair", "fr-es",
        "--out", str(out),
        "--recognized", "en,fr",
        "--reviewer-status", "assisted_only_pending_human",
    ]).returncode
    assert rc == 0
    assert (out / "eval.json").exists()
    assert (out / "summary.md").exists()
    assert (out / "citations.json").exists()
    assert (out / "packets.json").exists()
    assert (out / "inventory.json").exists()
    assert (out / "classified.json").exists()
    assert (out / "segments.json").exists()


def test_eval_json_tiene_schemas_esperados() -> None:
    eval_payload = json.loads((REPORTS / "eval.json").read_text(encoding="utf-8"))
    assert eval_payload["pair"] == "fr-es"
    assert eval_payload["source_language"] == "fr"
    assert eval_payload["target_language"] == "es"
    assert eval_payload["evaluation_kind"] == "assisted"
    assert eval_payload["reviewer_status"] in {
        "human_approved", "assisted_only_pending_human", "not_applicable",
    }
    assert "disclaimer" in eval_payload
    assert "asistida" in eval_payload["disclaimer"].lower() or "asistida" in eval_payload["disclaimer"]
    metrics = eval_payload["metrics"]
    assert metrics["total_segments"] > 0
    assert "by_language" in metrics
    assert "by_disposition" in metrics
    assert metrics["inventory"]["total_files"] >= 6
    rcs = eval_payload["returncodes"]
    assert rcs["inventory"] == 0
    assert rcs["prepare"] == 0
    assert rcs["detect_language"] == 0
    assert rcs["packetize"] == 0


def test_summary_md_declara_estado_experimental() -> None:
    text = (REPORTS / "summary.md").read_text(encoding="utf-8")
    assert "fr-es" in text
    assert "assisted_only_pending_human" in text or "asistida" in text.lower()
    assert "revisor" in text.lower()


def test_citations_json_clasifica_tres_tipos() -> None:
    payload = json.loads((REPORTS / "citations.json").read_text(encoding="utf-8"))
    counts = payload["counts"]
    assert counts.get("contractual", 0) >= 1, "se esperaba >=1 cita contractual"
    assert counts.get("technical_literal", 0) >= 1, "se esperaba >=1 literal técnico"
    assert counts.get("translatable_prose", 0) >= 1, "se esperaba >=1 prosa traducible"


def test_manifest_schema_acepta_language_pair() -> None:
    schema = json.loads((ROOT / "schemas" / "manifest.schema.json").read_text(encoding="utf-8"))
    assert "language_pair" in schema["properties"]
    lp = schema["properties"]["language_pair"]
    assert "reviewer_status" in lp["properties"]
    assert "evaluation_kind" in lp["properties"]
    assert "human_reviewer" in lp["properties"]


def test_no_dry_run_emite_summary_incluso_si_errores() -> None:
    out = TMP / "fr-es-eval-summary"
    rc = run([
        str(EVAL),
        "--source", str(PILOT),
        "--pair", "fr-es",
        "--out", str(out),
        "--recognized", "en,fr",
    ]).returncode
    assert rc == 0
    summary = out / "summary.md"
    assert summary.exists()
    text = summary.read_text(encoding="utf-8")
    assert "Decisiones pendientes" in text
