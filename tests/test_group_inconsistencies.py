"""Pruebas de scripts/group_inconsistencies.py (fase 125).

Verifica que las divergencias se agrupan por ``sense_id`` y
``domain``, no sólo por palabra suelta, y que no se proponen
traducciones globales automáticamente.
"""

from __future__ import annotations

import tempfile
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "group_inconsistencies.py"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def _write_glossary(gp: Path, entries: list[dict]) -> None:
    payload = {"version": 1, "frozen": True, "allowed_languages": ["es"], "domains": ["ui", "api"], "entries": entries}
    gp.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_translation(td: Path, doc_id: str, entries: list[dict]) -> None:
    payload = {
        "document_id": doc_id,
        "path": f"{doc_id}.md",
        "source_hash": "a" * 64,
        "version": 1,
        "entries": entries,
    }
    td.mkdir(parents=True, exist_ok=True)
    (td / f"{doc_id}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _entry(seg_id: str, orig: str, tr: str) -> dict:
    return {
        "segment_id": seg_id,
        "original_text": orig,
        "translated_text": tr,
        "literals_preserved": True,
    }


def test_agrupa_por_sentido_no_palabra() -> None:
    """``state`` con mismo ``sense_id`` debe agruparse aunque esté en distintos docs."""
    glossary = TMP / "g1.json"
    _write_glossary(glossary, [{
        "id": "g-0001",
        "source_term": "state",
        "domain": "ui",
        "sense": "estado_visible",
        "sense_id": "app.runtime_state",
        "preferred": {"lang": "es", "term": "estado"},
        "allowed_variants": [],
        "forbidden_forms": ["estatus"],
        "preservation_policy": "translate",
        "context_examples": [],
        "justification": "test",
        "decided_by": "test",
        "decided_at": "2026-10-19T20:00:00Z",
    }])
    translations = TMP / "t1"
    _write_translation(translations, "doc-a", [
        _entry("seg-a1", "The state is open.", "El estado está abierto."),
        _entry("seg-a2", "the state remains empty.", "el estado sigue vacío."),
    ])
    _write_translation(translations, "doc-b", [
        _entry("seg-b1", "State changed.", "Estado cambiado."),
    ])
    out = TMP / "out1.md"
    proc = run([str(SCRIPT), "--translations", str(translations), "--glossary", str(glossary), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr or proc.stdout
    text = out.read_text(encoding="utf-8")
    assert "app.runtime_state" in text
    assert "doc-a" in text and "doc-b" in text


def test_inconsistencia_con_variantes_por_documento() -> None:
    """Cuando dos archivos traducen el mismo sentido con dos variantes, se reporta."""
    glossary = TMP / "g2.json"
    _write_glossary(glossary, [{
        "id": "g-0002",
        "source_term": "request",
        "domain": "api",
        "sense": "petición HTTP",
        "sense_id": "api.http_request",
        "preferred": {"lang": "es", "term": "solicitud"},
        "allowed_variants": [],
        "forbidden_forms": ["petición"],
        "preservation_policy": "translate",
        "context_examples": [],
        "justification": "test",
        "decided_by": "test",
        "decided_at": "2026-10-19T20:00:00Z",
    }])
    translations = TMP / "t2"
    _write_translation(translations, "doc-c", [_entry("seg-c1", "Send a request.", "Enviar una solicitud.")])
    _write_translation(translations, "doc-d", [_entry("seg-d1", "Request body.", "Cuerpo de la petición.")])
    out = TMP / "out2.md"
    proc = run([str(SCRIPT), "--translations", str(translations), "--glossary", str(glossary), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr
    text = out.read_text(encoding="utf-8")
    assert "api.http_request" in text
    assert "solicitud" in text and "petición" in text


def test_no_propone_traduccion_global() -> None:
    """El reporte expone la divergencia; nunca aplica una traducción retroactivamente."""
    glossary = TMP / "g3.json"
    _write_glossary(glossary, [{
        "id": "g-0003",
        "source_term": "render",
        "domain": "frontend",
        "sense": "renderizado",
        "sense_id": "ui.render",
        "preferred": {"lang": "es", "term": "renderizar"},
        "allowed_variants": [],
        "forbidden_forms": [],
        "preservation_policy": "translate",
        "context_examples": [],
        "justification": "test",
        "decided_by": "test",
        "decided_at": "2026-10-19T20:00:00Z",
    }])
    translations = TMP / "t3"
    _write_translation(translations, "doc-e", [_entry("seg-e1", "render", "renderizar")])
    _write_translation(translations, "doc-f", [_entry("seg-f1", "render", "render")])
    out = TMP / "out3.md"
    proc = run([str(SCRIPT), "--translations", str(translations), "--glossary", str(glossary), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr
    # Tras la ejecución los archivos originales no cambian.
    t3 = json.loads((translations / "doc-f.json").read_text(encoding="utf-8"))
    assert t3["entries"][0]["translated_text"] == "render"
