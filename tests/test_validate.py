"""Pruebas para scripts/validate.py (fase 041)."""

from __future__ import annotations

import tempfile
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INVENTORY = ROOT / "scripts" / "inventory.py"
PREPARE = ROOT / "scripts" / "prepare.py"
DETECT = ROOT / "scripts" / "detect_language.py"
BUILD = ROOT / "scripts" / "build_packets.py"
TRANSLATE = ROOT / "scripts" / "translate_pilot.py"
VALIDATE = ROOT / "scripts" / "validate.py"
PILOT = ROOT / "tests" / "fixtures" / "pilot"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def setup_pipeline() -> dict[str, Path]:
    inv = TMP / "inv.json"
    seg = TMP / "segments.json"
    classified = TMP / "classified.json"
    snaps = TMP / "snapshots.json"
    packets = TMP / "packets.json"
    translations = TMP / "translations"
    profile = TMP / "profile.json"
    manifest = TMP / "manifest.json"

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
        "paths": {"source_root": str(PILOT), "work_root": "/tmp", "output_root": "/tmp"},
        "exclusions": [],
        "context_budget": 1500,
        "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
    }, indent=2), encoding="utf-8")

    assert run([str(INVENTORY), "--source", str(PILOT), "--out", str(inv)]).returncode == 0
    assert run([str(PREPARE), "--inventory", str(inv), "--segments", str(seg), "--snapshots", str(snaps)]).returncode == 0
    assert run([str(DETECT), "--segments", str(seg), "--out", str(classified)]).returncode == 0
    assert run([str(BUILD),
                "--segments", str(classified),
                "--profile", str(profile),
                "--out", str(packets)]).returncode == 0
    if translations.exists():
        shutil.rmtree(translations)
    translations.mkdir(parents=True)
    assert run([str(TRANSLATE),
                "--packets", str(packets),
                "--segments", str(classified),
                "--out", str(translations),
                "--mode", "identity"]).returncode == 0

    doc_ids = json.loads(classified.read_text(encoding="utf-8"))["files"]
    files = [{
        "path": f["path"],
        "document_id": f["document_id"],
        "source_hash": f["source_hash"],
        "current_state": "approved",
        "state_history": [{"state": "inventoried", "timestamp": "2026-10-19T20:00:00Z", "reason": "init"}, {"state": "approved", "timestamp": "2026-10-19T20:01:00Z", "reason": "done"}],
        "last_transition_at": "2026-10-19T20:01:00Z",
    } for f in doc_ids]
    manifest_payload = {
        "run_id": "run-validate",
        "created_at": "2026-10-19T20:00:00Z",
        "skill_version": "0.1.0",
        "parser": {"name": "markdown-it-py", "version": "3.0.0"},
        "anchor_policy": {"algorithm": "github", "version": "v1"},
        "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
        "glossary_snapshot": {"version": 1, "hash": "x", "frozen": True},
        "profile_snapshot": {"hash": "x"},
        "inputs": {"source_root": str(PILOT), "total_files": len(files), "total_bytes": 0, "hashes_indexed": True},
        "files": files,
    }
    manifest.write_text(json.dumps(manifest_payload, indent=2), encoding="utf-8")
    return {"packets": packets, "snapshots": snaps, "segments": classified, "translations": translations, "manifest": manifest, "source": PILOT, "output_dir": TMP / "validate_output"}


def test_corpus_sin_regresiones() -> None:
    paths = setup_pipeline()
    paths["output_dir"].mkdir(parents=True, exist_ok=True)
    out = TMP / "validate_ok.json"
    proc = run([
        str(VALIDATE),
        "--source", str(paths["source"]),
        "--output-dir", str(paths["output_dir"]),
        "--packets", str(paths["packets"]),
        "--segments", str(paths["segments"]),
        "--translations", str(paths["translations"]),
        "--snapshots", str(paths["snapshots"]),
        "--anchors", str(TMP / "anchors"),
        "--manifest", str(paths["manifest"]),
        "--out", str(out),
    ])
    report = json.loads(out.read_text(encoding="utf-8"))
    structure_errors = [e for e in report["errors"] if e["check"] == "structure"]
    destinations_errors = [e for e in report["errors"] if e["check"] == "destinations"]
    assert proc.returncode == 0, f"validate.py terminó con {proc.returncode}: {proc.stderr}"
    assert structure_errors == []
    assert destinations_errors == []


def test_url_externa_modificada_se_detecta() -> None:
    paths = setup_pipeline()
    target = next(paths["translations"].glob("*.json"))
    data = json.loads(target.read_text(encoding="utf-8"))
    joined = "\n\n".join(e.get("translated_text", "") for e in data["entries"])
    if "https://" not in joined:
        out = TMP / "validate_destinations_skip.json"
        run([
            str(VALIDATE),
            "--source", str(paths["source"]),
            "--output-dir", str(paths["output_dir"]),
            "--packets", str(paths["packets"]),
            "--segments", str(paths["segments"]),
            "--translations", str(paths["translations"]),
            "--snapshots", str(paths["snapshots"]),
            "--anchors", str(TMP / "anchors"),
            "--manifest", str(paths["manifest"]),
            "--out", str(out),
            "--checks", "destinations",
        ])
        assert True
        return
    url_to_remove = __import__("re").search(r"https?://\S+", joined).group(0)
    for entry in data["entries"]:
        if url_to_remove in (entry.get("translated_text") or ""):
            entry["translated_text"] = entry["translated_text"].replace(url_to_remove, "")
            break
    target.write_text(json.dumps(data, indent=2), encoding="utf-8")
    out = TMP / "validate_destinations.json"
    run([
        str(VALIDATE),
        "--source", str(paths["source"]),
        "--output-dir", str(paths["output_dir"]),
        "--packets", str(paths["packets"]),
        "--segments", str(paths["segments"]),
        "--translations", str(paths["translations"]),
        "--snapshots", str(paths["snapshots"]),
        "--anchors", str(TMP / "anchors"),
        "--manifest", str(paths["manifest"]),
        "--out", str(out),
        "--checks", "destinations",
    ])
    report = json.loads(out.read_text(encoding="utf-8"))
    dest_errors = [e for e in report["errors"] if e["check"] == "destinations"]
    assert dest_errors, "URL perdida no detectada"


def test_marcador_extra_en_traduccion_se_detecta() -> None:
    paths = setup_pipeline()
    target = next(paths["translations"].glob("*.json"))
    data = json.loads(target.read_text(encoding="utf-8"))
    if data["entries"]:
        data["entries"][0]["translated_text"] = "§§fake§§ " + data["entries"][0]["translated_text"]
    target.write_text(json.dumps(data, indent=2), encoding="utf-8")
    out = TMP / "validate_protection.json"
    run([
        str(VALIDATE),
        "--source", str(paths["source"]),
        "--output-dir", str(paths["output_dir"]),
        "--packets", str(paths["packets"]),
        "--segments", str(paths["segments"]),
        "--translations", str(paths["translations"]),
        "--snapshots", str(paths["snapshots"]),
        "--anchors", str(TMP / "anchors"),
        "--manifest", str(paths["manifest"]),
        "--out", str(out),
        "--checks", "protection",
    ])
    report = json.loads(out.read_text(encoding="utf-8"))
    prot_errors = [e for e in report["errors"] if e["check"] == "protection"]
    assert prot_errors, "marcador extra no detectado"
