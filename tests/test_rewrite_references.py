"""Pruebas para scripts/rewrite_references.py (fase 039)."""

from __future__ import annotations

import tempfile
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REWRITE = ROOT / "scripts" / "rewrite_references.py"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def fresh(name: str) -> Path:
    out = TMP / name
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    return out


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_anchor_local_se_reescribe() -> None:
    source = fresh("rw_source")
    output = TMP / "rw_output"
    if output.exists():
        shutil.rmtree(output)
    anchors = TMP / "rw_anchors"
    if anchors.exists():
        shutil.rmtree(anchors)
    anchors.mkdir()
    write_text(source / "doc.md", "[Old Section](#old-section) and [Tabla](#tabla)")
    write_json(anchors / "doc-id.json", {
        "document_id": "doc-id",
        "path": "doc.md",
        "algorithm": "github-slug-v1",
        "anchors": [
            {"old_text": "Old Section", "old_slug": "old-section", "new_text": "New Section", "new_slug": "new-section", "source": "implicit"},
            {"old_text": "Tabla", "old_slug": "tabla", "new_text": "Tabla", "new_slug": "tabla", "source": "implicit"},
        ],
    })
    report = TMP / "rw_report.json"
    assert run([str(REWRITE),
                "--source", str(source),
                "--output-dir", str(output),
                "--anchors", str(anchors),
                "--report", str(report)]).returncode == 0

    out_text = (output / "doc.md").read_text(encoding="utf-8")
    assert "[Old Section](#new-section)" in out_text
    assert "[Tabla](#tabla)" in out_text


def test_url_externa_no_se_toca() -> None:
    source = fresh("rw_ext_source")
    output = TMP / "rw_ext_output"
    if output.exists():
        shutil.rmtree(output)
    anchors = TMP / "rw_ext_anchors"
    if anchors.exists():
        shutil.rmtree(anchors)
    anchors.mkdir()
    write_text(source / "doc.md", "[external](https://example.com)")
    write_json(anchors / "doc-id.json", {
        "document_id": "doc-id",
        "path": "doc.md",
        "algorithm": "github-slug-v1",
        "anchors": [],
    })
    report = TMP / "rw_ext_report.json"
    assert run([str(REWRITE),
                "--source", str(source),
                "--output-dir", str(output),
                "--anchors", str(anchors),
                "--report", str(report)]).returncode == 0
    out_text = (output / "doc.md").read_text(encoding="utf-8")
    assert "[external](https://example.com)" in out_text


def test_referencia_sin_ancla_se_reporta() -> None:
    source = fresh("rw_orphan_source")
    output = TMP / "rw_orphan_output"
    if output.exists():
        shutil.rmtree(output)
    anchors = TMP / "rw_orphan_anchors"
    if anchors.exists():
        shutil.rmtree(anchors)
    anchors.mkdir()
    write_text(source / "doc.md", "[link](#no-existe)")
    write_json(anchors / "doc-id.json", {
        "document_id": "doc-id",
        "path": "doc.md",
        "algorithm": "github-slug-v1",
        "anchors": [],
    })
    report = TMP / "rw_orphan_report.json"
    assert run([str(REWRITE),
                "--source", str(source),
                "--output-dir", str(output),
                "--anchors", str(anchors),
                "--report", str(report)]).returncode == 0
    rep = json.loads(report.read_text(encoding="utf-8"))
    assert rep["unresolved_total"] == 1


def test_anchor_igual_no_modifica() -> None:
    source = fresh("rw_unchanged_source")
    output = TMP / "rw_unchanged_output"
    if output.exists():
        shutil.rmtree(output)
    anchors = TMP / "rw_unchanged_anchors"
    if anchors.exists():
        shutil.rmtree(anchors)
    anchors.mkdir()
    write_text(source / "doc.md", "[link](#mismo)")
    write_json(anchors / "doc-id.json", {
        "document_id": "doc-id",
        "path": "doc.md",
        "algorithm": "github-slug-v1",
        "anchors": [
            {"old_text": "mismo", "old_slug": "mismo", "new_text": "mismo", "new_slug": "mismo", "source": "implicit"},
        ],
    })
    report = TMP / "rw_unchanged_report.json"
    assert run([str(REWRITE),
                "--source", str(source),
                "--output-dir", str(output),
                "--anchors", str(anchors),
                "--report", str(report)]).returncode == 0
    out_text = (output / "doc.md").read_text(encoding="utf-8")
    assert "[link](#mismo)" in out_text
