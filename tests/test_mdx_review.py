"""Pruebas de la revisión semántica MDX (fase 069)."""

from __future__ import annotations

import tempfile
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
REF = ROOT / "references" / "mdx-review.md"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def test_referencia_existe() -> None:
    assert REF.exists()


def test_referencia_incluye_componentes_clave() -> None:
    text = REF.read_text(encoding="utf-8")
    for needle in ("<Info>", "<Warning>", "<Note>", "<TabItem>"):
        assert needle in text, f"falta {needle!r} en mdx-review.md"


def test_referencia_lista_severidades() -> None:
    text = REF.read_text(encoding="utf-8")
    for needle in ("critical", "major", "info"):
        assert needle in text


def test_raise_issues_detecta_negacion_invertida_en_warning() -> None:
    """Una traducción que invierte MUST NOT en un Warning debe
    producir un issue de clarificación con severidad major."""
    classified = TMP / "seg_review.json"
    classified.write_text(json.dumps({
        "files": [{
            "document_id": "doc-warn",
            "path": "warning.mdx",
            "segments": [{
                "segment_id": "seg-w1",
                "disposition": "translatable",
                "translatable_text": "You MUST NOT delete the cache.",
            }],
        }],
    }), encoding="utf-8")

    translations = TMP / "trans_review"
    if translations.exists():
        shutil.rmtree(translations)
    translations.mkdir()
    (translations / "doc-warn.json").write_text(json.dumps({
        "document_id": "doc-warn",
        "path": "warning.mdx",
        "entries": [{
            "segment_id": "seg-w1",
            "original_text": "You MUST NOT delete the cache.",
            "translated_text": "Debes eliminar el directorio de caché.",
            "parent": "Warning",
        }],
    }), encoding="utf-8")

    issues_out = TMP / "issues_warn.json"
    run([
        str(SCRIPTS / "raise_issues.py"),
        "--translations", str(translations),
        "--segments", str(classified),
        "--issues-out", str(issues_out),
    ])
    payload = json.loads(issues_out.read_text(encoding="utf-8"))
    clarifications = [i for i in payload["issues"] if i["category"] == "clarification_needed"]
    assert any("negación" in (i["message"] or "").lower() for i in clarifications)
    major_findings = [i for i in clarifications if i.get("severity") == "major"]
    assert major_findings


def test_raise_issues_detecta_traduccion_identidad() -> None:
    classified = TMP / "seg_id.json"
    classified.write_text(json.dumps({
        "files": [{
            "document_id": "doc-id",
            "path": "info.mdx",
            "segments": [{
                "segment_id": "seg-id",
                "disposition": "translatable",
                "translatable_text": "Original text.",
            }],
        }],
    }), encoding="utf-8")

    translations = TMP / "trans_id"
    if translations.exists():
        shutil.rmtree(translations)
    translations.mkdir()
    (translations / "doc-id.json").write_text(json.dumps({
        "document_id": "doc-id",
        "path": "info.mdx",
        "entries": [{
            "segment_id": "seg-id",
            "original_text": "Original text.",
            "translated_text": "Original text.",
            "parent": "Info",
        }],
    }), encoding="utf-8")

    issues_out = TMP / "issues_id.json"
    proc = run([
        str(SCRIPTS / "raise_issues.py"),
        "--translations", str(translations),
        "--segments", str(classified),
        "--issues-out", str(issues_out),
    ])
    assert proc.returncode == 0
    payload = json.loads(issues_out.read_text(encoding="utf-8"))
    ambiguous = [i for i in payload["issues"] if i["category"] == "ambiguous"]
    assert any("idéntica" in (i["message"] or "").lower() for i in ambiguous)


def test_raise_issues_no_modifica_segmentos_de_proteccion() -> None:
    """Los segmentos con kind expression o jsx_element no deben ser
    auditados; solo el texto y los atributos traducibles."""
    classified = TMP / "seg_protect.json"
    classified.write_text(json.dumps({
        "files": [{
            "document_id": "doc-p",
            "path": "p.mdx",
            "segments": [
                {
                    "segment_id": "seg-expr",
                    "disposition": "translatable",
                    "translatable_text": "{severity}",
                },
            ],
        }],
    }), encoding="utf-8")

    translations = TMP / "trans_protect"
    if translations.exists():
        shutil.rmtree(translations)
    translations.mkdir()
    (translations / "doc-p.json").write_text(json.dumps({
        "document_id": "doc-p",
        "path": "p.mdx",
        "entries": [{
            "segment_id": "seg-expr",
            "original_text": "{severity}",
            "translated_text": "low",
            "kind": "expression",
        }],
    }), encoding="utf-8")

    issues_out = TMP / "issues_p.json"
    proc = run([
        str(SCRIPTS / "raise_issues.py"),
        "--translations", str(translations),
        "--segments", str(classified),
        "--issues-out", str(issues_out),
    ])
    payload = json.loads(issues_out.read_text(encoding="utf-8"))
    clarifications = [i for i in payload["issues"] if i["category"] == "clarification_needed"]
    assert not clarifications
