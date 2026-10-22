"""Pruebas para scripts/apply_corrections.py (fase 043)."""

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
APPLY = ROOT / "scripts" / "apply_corrections.py"
PILOT = ROOT / "tests" / "fixtures" / "pilot"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def setup_translations() -> tuple[Path, Path, Path]:
    inv = TMP / "inv.json"
    seg = TMP / "segments.json"
    classified = TMP / "classified.json"
    snaps = TMP / "snapshots.json"
    packets = TMP / "packets.json"
    translations = TMP / "translations"
    profile = TMP / "profile.json"
    assert run([str(INVENTORY), "--source", str(PILOT), "--out", str(inv)]).returncode == 0
    assert run([str(PREPARE), "--inventory", str(inv), "--segments", str(seg), "--snapshots", str(snaps)]).returncode == 0
    assert run([str(DETECT), "--segments", str(seg), "--out", str(classified)]).returncode == 0
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
    return classified, packets, translations


def test_correccion_aplicada() -> None:
    classified, packets, translations = setup_translations()
    out = TMP / "out_corrections"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir()
    target = next(translations.glob("*.json"))
    data = json.loads(target.read_text(encoding="utf-8"))
    target_seg = data["entries"][0]
    corrections_path = TMP / "corrections.json"
    corrections = [{
        "segment_id": target_seg["segment_id"],
        "corrected_text": target_seg["translated_text"] + " [CORREGIDO]",
        "reason": "test de corrección",
    }]
    corrections_path.write_text(json.dumps(corrections, indent=2), encoding="utf-8")
    report = TMP / "apply_report.json"
    assert run([str(APPLY),
                "--translations", str(translations),
                "--corrections", str(corrections_path),
                "--out-translations", str(out),
                "--report", str(report)]).returncode == 0
    rep = json.loads(report.read_text(encoding="utf-8"))
    assert rep["applied_count"] == 1
    assert rep["not_found_count"] == 0
    out_data = json.loads((out / target.name).read_text(encoding="utf-8"))
    entry = next(e for e in out_data["entries"] if e["segment_id"] == target_seg["segment_id"])
    assert entry["translated_text"].endswith("[CORREGIDO]")


def test_correccion_segmento_inexistente() -> None:
    classified, packets, translations = setup_translations()
    out = TMP / "out_inexistente"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir()
    corrections_path = TMP / "corrections_inexistente.json"
    corrections_path.write_text(json.dumps([{
        "segment_id": "seg-no-existe",
        "corrected_text": "no se aplicará",
        "reason": "test",
    }], indent=2), encoding="utf-8")
    report = TMP / "apply_report_inexistente.json"
    assert run([str(APPLY),
                "--translations", str(translations),
                "--corrections", str(corrections_path),
                "--out-translations", str(out),
                "--report", str(report)]).returncode == 0
    rep = json.loads(report.read_text(encoding="utf-8"))
    assert rep["applied_count"] == 0
    assert rep["not_found_count"] == 1


def test_json_invalido_rechaza() -> None:
    classified, packets, translations = setup_translations()
    out = TMP / "out_invalido"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir()
    bad = TMP / "bad.json"
    bad.write_text("{ not valid", encoding="utf-8")
    report = TMP / "apply_report_bad.json"
    proc = run([str(APPLY),
                "--translations", str(translations),
                "--corrections", str(bad),
                "--out-translations", str(out),
                "--report", str(report)])
    assert proc.returncode != 0
