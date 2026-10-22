"""Pruebas para scripts/check_numbers.py (fase 037)."""

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
CHECK_NUMBERS = ROOT / "scripts" / "check_numbers.py"
PILOT = ROOT / "tests" / "fixtures" / "pilot"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def setup_pipeline() -> tuple[Path, Path]:
    inv = TMP / "inv.json"
    seg = TMP / "segments.json"
    classified = TMP / "classified.json"
    snaps = TMP / "snapshots.json"
    glossary = TMP / "glossary.json"
    packets = TMP / "packets_final.json"
    translations = TMP / "translations"
    profile = TMP / "profile.json"

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
    assert run([str(EXTRACT := ROOT / "scripts" / "extract_terms.py"),
                "--inventory", str(inv),
                "--snapshots", str(snaps),
                "--segments", str(classified),
                "--out", str(glossary)]).returncode == 0
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
    return classified, translations


def test_cambio_de_unidad_detectado() -> None:
    classified, translations = setup_pipeline()
    target = next(translations.glob("*.json"))
    data = json.loads(target.read_text(encoding="utf-8"))
    found = False
    for entry in data["entries"]:
        if "100ms" in (entry.get("original_text") or "") or "500ms" in (entry.get("original_text") or ""):
            entry["translated_text"] = entry["translated_text"].replace("100ms", "200ms")
            entry["translated_text"] = entry["translated_text"].replace("500ms", "600ms")
            found = True
            break
    if not found:
        target2 = next(translations.glob("*.json"))
        data = json.loads(target2.read_text(encoding="utf-8"))
        for entry in data["entries"]:
            entry["translated_text"] = entry["translated_text"] + " 200ms extra"
            found = True
            break
        target2.write_text(json.dumps(data, indent=2), encoding="utf-8")

    target.write_text(json.dumps(data, indent=2), encoding="utf-8")
    out = TMP / "check_numbers_unit.json"
    assert run([str(CHECK_NUMBERS), "--translations", str(translations), "--segments", str(classified), "--out", str(out)]).returncode == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["total_numeric_changes"] >= 1


def test_reordenamiento_seguro_no_es_numerico() -> None:
    classified, translations = setup_pipeline()
    target = next(translations.glob("*.json"))
    data = json.loads(target.read_text(encoding="utf-8"))
    for entry in data["entries"]:
        original = entry.get("original_text") or ""
        if len(original) > 30:
            tokens = original.split()
            if len(tokens) >= 2:
                entry["translated_text"] = " ".join(reversed(tokens))
                break
    target.write_text(json.dumps(data, indent=2), encoding="utf-8")
    out = TMP / "check_numbers_reorder.json"
    assert run([str(CHECK_NUMBERS), "--translations", str(translations), "--segments", str(classified), "--out", str(out)]).returncode == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["total_numeric_changes"] == 0
    assert report["total_safe_reorders"] >= 1


def test_traduccion_identica_sin_hallazgos() -> None:
    classified, translations = setup_pipeline()
    out = TMP / "check_numbers_clean.json"
    assert run([str(CHECK_NUMBERS), "--translations", str(translations), "--segments", str(classified), "--out", str(out)]).returncode == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["total_numeric_changes"] == 0
