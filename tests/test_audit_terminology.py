"""Pruebas para scripts/audit_terminology.py (fase 045)."""

from __future__ import annotations

import tempfile
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / "scripts" / "audit_terminology.py"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def write_glossary(path: Path, entries: list[dict]) -> None:
    payload = {"version": 1, "frozen": True, "allowed_languages": ["es"], "entries": entries}
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_translation(path: Path, entries: list[dict]) -> None:
    payload = {
        "document_id": "doc-test",
        "path": "test.md",
        "source_hash": "x" * 64,
        "version": 1,
        "entries": entries,
        "flag_loss": False,
        "literals_preserved": True,
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_traducciones_consistentes() -> None:
    glossary = TMP / "glossary_ok.json"
    translations = TMP / "translations_ok"
    translations.mkdir(parents=True, exist_ok=True)
    write_glossary(glossary, [{
        "id": "g-0001",
        "source_term": "state",
        "domain": "ui",
        "sense": "estado visible",
        "preferred": {"lang": "es", "term": "estado"},
        "allowed_variants": [],
        "forbidden_forms": ["estatus"],
        "preservation_policy": "translate",
        "context_examples": [],
        "justification": "test",
        "decided_by": "test",
        "decided_at": "2026-10-19T20:00:00Z",
    }])
    write_translation(translations / "doc-test.json", [{
        "segment_id": "seg-1",
        "original_text": "The state is empty.",
        "translated_text": "El estado está vacío.",
        "literals_preserved": True,
        "missing_literals": [],
        "flag_loss": False,
    }])
    out = TMP / "audit_ok.json"
    assert run([str(AUDIT), "--translations", str(translations), "--glossary", str(glossary), "--out", str(out)]).returncode == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["summary"]["inconsistencies"] == 0


def test_allowed_variant_no_es_inconsistente() -> None:
    glossary = TMP / "glossary_var.json"
    translations = TMP / "translations_var"
    translations.mkdir(parents=True, exist_ok=True)
    write_glossary(glossary, [{
        "id": "g-0001",
        "source_term": "stream",
        "domain": "api",
        "sense": "envío incremental",
        "preferred": {"lang": "es", "term": "streaming"},
        "allowed_variants": ["flujo"],
        "forbidden_forms": [],
        "preservation_policy": "keep-original",
        "context_examples": [],
        "justification": "test",
        "decided_by": "test",
        "decided_at": "2026-10-19T20:00:00Z",
    }])
    write_translation(translations / "doc-test.json", [{
        "segment_id": "seg-1",
        "original_text": "Enable stream responses.",
        "translated_text": "Habilitar flujo de respuestas.",
        "literals_preserved": True,
        "missing_literals": [],
        "flag_loss": False,
    }])
    out = TMP / "audit_var.json"
    assert run([str(AUDIT), "--translations", str(translations), "--glossary", str(glossary), "--out", str(out)]).returncode == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["summary"]["inconsistencies"] == 0
    assert report["summary"]["allowed_uses"] >= 1


def test_inconsistencia_con_preferido() -> None:
    glossary = TMP / "glossary_bad.json"
    translations = TMP / "translations_bad"
    translations.mkdir(parents=True, exist_ok=True)
    write_glossary(glossary, [{
        "id": "g-0001",
        "source_term": "request",
        "domain": "api",
        "sense": "petición HTTP",
        "preferred": {"lang": "es", "term": "solicitud"},
        "allowed_variants": [],
        "forbidden_forms": ["petición"],
        "preservation_policy": "translate",
        "context_examples": [],
        "justification": "test",
        "decided_by": "test",
        "decided_at": "2026-10-19T20:00:00Z",
    }])
    write_translation(translations / "doc-test.json", [{
        "segment_id": "seg-1",
        "original_text": "Send request body.",
        "translated_text": "Enviar cuerpo de petición.",
        "literals_preserved": True,
        "missing_literals": [],
        "flag_loss": False,
    }])
    out = TMP / "audit_bad.json"
    proc = run([str(AUDIT), "--translations", str(translations), "--glossary", str(glossary), "--out", str(out)])
    assert proc.returncode != 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["summary"]["forbidden_uses"] >= 1
