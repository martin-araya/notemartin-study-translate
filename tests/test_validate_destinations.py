"""Pruebas de `check_destinations` sobre fragmentos y enlaces locales (fase 041).

La comprobación anterior solo verificaba que sobrevivieran las URL
`http(s)`. Un enlace roto por traducir un título es casi siempre un
fragmento `#ancla` o una ruta local, y ninguno de los dos se miraba.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INVENTORY = ROOT / "scripts" / "inventory.py"
PREPARE = ROOT / "scripts" / "prepare.py"
DETECT = ROOT / "scripts" / "detect_language.py"
BUILD = ROOT / "scripts" / "build_packets.py"
TRANSLATE = ROOT / "scripts" / "translate_pilot.py"
VALIDATE = ROOT / "scripts" / "validate.py"
TMP = Path(tempfile.gettempdir()) / "nst-tests"

DOC = """# Getting started guide

See the [section below](#internal-section) and the [other guide](../other/guide.md).

The diagram below shows the flow: ![Diagram](assets/diagram.png).

External source: [documentation](https://example.com/docs).

## Internal section

Content of the internal section.
"""


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def build_corpus(name: str) -> dict[str, Path]:
    source = TMP / name / "source"
    if source.exists():
        shutil.rmtree(source)
    (source / "guide").mkdir(parents=True)
    (source / "guide" / "start.md").write_text(DOC, encoding="utf-8")
    (source / "other").mkdir(parents=True)
    (source / "other" / "guide.md").write_text("# Other guide\n\nSome text here.\n", encoding="utf-8")

    work = TMP / name / "work"
    work.mkdir(parents=True, exist_ok=True)
    profile = work / "profile.json"
    profile.write_text(json.dumps({
        "target_language": "es",
        "source_language": "auto",
        "markdown_dialect": "commonmark+gfm",
        "slug_algorithm": {"name": "github", "version": "v1"},
        "code_preservation": "strict",
        "frontmatter_policy": "preserve",
        "bilingual_policy": "first-mention-per-document",
        "punctuation_preference": "es-comma-period",
        "review_mode": "assisted",
        "paths": {"source_root": str(source), "work_root": str(work), "output_root": str(TMP / name / "output")},
        "exclusions": [],
        "context_budget": 1500,
        "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
    }, indent=2), encoding="utf-8")

    inv = work / "inventory.json"
    seg = work / "segments.json"
    snaps = work / "snapshots.json"
    classified = work / "classified.json"
    packets = work / "packets.json"
    translations = work / "translations"
    manifest = work / "manifest.json"

    assert run([str(INVENTORY), "--source", str(source), "--out", str(inv)]).returncode == 0
    assert run([str(PREPARE), "--inventory", str(inv), "--segments", str(seg), "--snapshots", str(snaps)]).returncode == 0
    assert run([str(DETECT), "--segments", str(seg), "--out", str(classified)]).returncode == 0
    assert run([str(BUILD), "--segments", str(classified), "--profile", str(profile), "--out", str(packets)]).returncode == 0
    if translations.exists():
        shutil.rmtree(translations)
    translations.mkdir(parents=True)
    assert run([str(TRANSLATE), "--packets", str(packets), "--segments", str(classified),
                "--out", str(translations), "--mode", "identity"]).returncode == 0

    docs = json.loads(classified.read_text(encoding="utf-8"))["files"]
    files = [{
        "path": f["path"],
        "document_id": f["document_id"],
        "source_hash": f["source_hash"],
        "current_state": "translated",
        "state_history": [
            {"state": "inventoried", "timestamp": "2026-10-20T00:00:00Z", "reason": "init"},
            {"state": "translated", "timestamp": "2026-10-20T00:01:00Z", "reason": "done"},
        ],
        "last_transition_at": "2026-10-20T00:01:00Z",
    } for f in docs]
    manifest.write_text(json.dumps({
        "run_id": "run-destinations",
        "created_at": "2026-10-20T00:00:00Z",
        "manifest_version": "translate/v1",
        "skill_version": "0.2.0",
        "parser": {"name": "markdown-it-py", "version": "3.0.0"},
        "anchor_policy": {"algorithm": "github-slug-v1", "version": "v1"},
        "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
        "glossary_snapshot": {"version": 1, "hash": "0" * 64, "frozen": True},
        "profile_snapshot": {"hash": "0" * 64},
        "inputs": {"source_root": str(source), "total_files": len(files), "total_bytes": 0, "hashes_indexed": True},
        "files": files,
    }, indent=2), encoding="utf-8")

    return {
        "source": source,
        "output": TMP / name / "output",
        "packets": packets,
        "segments": classified,
        "snapshots": snaps,
        "translations": translations,
        "manifest": manifest,
        "target": translations / f"{docs[0]['document_id']}.json",
    }


def validate(paths: dict[str, Path], out_name: str) -> list[dict]:
    out = TMP / out_name
    proc = run([
        str(VALIDATE),
        "--source", str(paths["source"]),
        "--output-dir", str(paths["output"]),
        "--packets", str(paths["packets"]),
        "--segments", str(paths["segments"]),
        "--translations", str(paths["translations"]),
        "--snapshots", str(paths["snapshots"]),
        "--anchors", str(TMP / "anchors"),
        "--manifest", str(paths["manifest"]),
        "--out", str(out),
        "--checks", "destinations",
    ])
    assert proc.returncode in (0, 1), f"validate.py terminó con {proc.returncode}: {proc.stderr}"
    report = json.loads(out.read_text(encoding="utf-8"))
    return [e for e in report["errors"] if e["check"] == "destinations"]


def drop_from_translation(paths: dict[str, Path], needle: str) -> bool:
    """Quita una construcción de enlace de la traducción y la conserva en la fuente."""
    data = json.loads(paths["target"].read_text(encoding="utf-8"))
    hit = False
    for entry in data["entries"]:
        text = entry.get("translated_text") or ""
        if needle in text:
            entry["translated_text"] = text.replace(needle, "")
            hit = True
    paths["target"].write_text(json.dumps(data, indent=2), encoding="utf-8")
    return hit


def test_traduccion_identica_no_reporta_errores() -> None:
    paths = build_corpus("dest-ok")
    assert validate(paths, "validate_dest_ok.json") == []


def test_fragmento_perdido_se_detecta() -> None:
    paths = build_corpus("dest-frag")
    assert drop_from_translation(paths, "(#internal-section)")
    errors = validate(paths, "validate_dest_frag.json")
    assert errors, "fragmento perdido no detectado"
    assert any("fragmento" in e["message"] for e in errors)


def test_enlace_local_perdido_se_detecta() -> None:
    paths = build_corpus("dest-local")
    assert drop_from_translation(paths, "(../other/guide.md)")
    errors = validate(paths, "validate_dest_local.json")
    assert errors, "enlace local perdido no detectado"


def test_imagen_local_perdida_se_detecta() -> None:
    paths = build_corpus("dest-image")
    assert drop_from_translation(paths, "(assets/diagram.png)")
    errors = validate(paths, "validate_dest_image.json")
    assert errors, "imagen local perdida no detectada"


def test_url_externa_perdida_se_detecta() -> None:
    paths = build_corpus("dest-ext")
    assert drop_from_translation(paths, "(https://example.com/docs)")
    errors = validate(paths, "validate_dest_ext.json")
    assert errors, "URL externa perdida no detectada"


def test_fragmento_reescrito_legitimamente_no_es_error() -> None:
    """Cambiar el valor de un fragmento es la excepción autorizada de INV-09.

    Lo que no puede cambiar es cuántos fragmentos hay.
    """
    paths = build_corpus("dest-rewrite")
    data = json.loads(paths["target"].read_text(encoding="utf-8"))
    hit = False
    for entry in data["entries"]:
        text = entry.get("translated_text") or ""
        if "(#internal-section)" in text:
            entry["translated_text"] = text.replace("(#internal-section)", "(#internal-section-es)")
            hit = True
    assert hit
    paths["target"].write_text(json.dumps(data, indent=2), encoding="utf-8")
    assert validate(paths, "validate_dest_rewritten.json") == []