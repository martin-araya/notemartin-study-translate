"""Pruebas del rol de revisor (fase 115)."""

from __future__ import annotations

import tempfile
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REVIEWER = ROOT / "scripts" / "reviewer_role.py"
CLEAN = ROOT / "tests" / "fixtures" / "review" / "candidate-clean.json"
POLLUTED = ROOT / "tests" / "fixtures" / "review" / "candidate-polluted.json"
TOKENS = ROOT / "tests" / "fixtures" / "review" / "candidate-tokens.json"
RUBRIC = ROOT / "evals" / "rubric-distributed.md"
SOURCE = ROOT / "tests" / "fixtures" / "scale" / "packets_workers.json"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def _review(input_path: Path, out: Path) -> int:
    return subprocess.run(
        [sys.executable, str(REVIEWER),
         "--reviewer-id", "R1",
         "--input", str(input_path),
         "--rubric", str(RUBRIC),
         "--source-path", str(SOURCE),
         "--out", str(out)],
        capture_output=True, text=True, check=False,
    ).returncode


def test_input_limpio_emite_jsonl() -> None:
    out = TMP / "reviews-clean.jsonl"
    if out.exists():
        out.unlink()
    rc = _review(CLEAN, out)
    assert rc == 0
    lines = out.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["reviewer_id"] == "R1"
    assert entry["verdict"] is None
    assert entry["packet_id"] == "pack-33d416f2"


def test_input_con_author_notes_es_rechazado() -> None:
    out = TMP / "reviews-polluted.jsonl"
    if out.exists():
        out.unlink()
    rc = _review(POLLUTED, out)
    assert rc == 3


def test_input_con_tokens_es_rechazado() -> None:
    out = TMP / "reviews-tokens.jsonl"
    if out.exists():
        out.unlink()
    rc = _review(TOKENS, out)
    assert rc == 3


def test_input_inexistente_falla_con_2() -> None:
    out = TMP / "reviews-noinput.jsonl"
    if out.exists():
        out.unlink()
    rc = subprocess.run(
        [sys.executable, str(REVIEWER),
         "--reviewer-id", "R1",
         "--input", "/tmp/inexistente-12345.json",
         "--rubric", str(RUBRIC),
         "--source-path", str(SOURCE),
         "--out", str(out)],
        capture_output=True, text=True, check=False,
    ).returncode
    assert rc == 2


def test_bitacora_es_jsonl_valido() -> None:
    """Una línea por segmento, cada línea es JSON válido."""
    out = TMP / "reviews-format.jsonl"
    if out.exists():
        out.unlink()
    rc = _review(CLEAN, out)
    assert rc == 0
    for line in out.read_text(encoding="utf-8").splitlines():
        json.loads(line)


def test_protocolo_doc_existe_y_declara_inputs() -> None:
    doc = ROOT / "references" / "reviewer-protocol.md"
    assert doc.exists()
    text = doc.read_text(encoding="utf-8")
    for sec in ("Lo que el revisor recibe", "Lo que el revisor emite",
                "Anti-contaminación"):
        assert sec in text


def test_rubric_distributed_existe() -> None:
    assert RUBRIC.exists()
    text = RUBRIC.read_text(encoding="utf-8")
    for sec in ("Criterios distribuidos", "Severidades", "Plantilla de veredicto"):
        assert sec in text
