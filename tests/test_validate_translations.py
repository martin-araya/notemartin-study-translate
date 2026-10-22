"""Pruebas para scripts/validate_translations.py (fase 034)."""

from __future__ import annotations

import tempfile
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INVENTORY = ROOT / "scripts" / "inventory.py"
PREPARE = ROOT / "scripts" / "prepare.py"
DETECT = ROOT / "scripts" / "detect_language.py"
BUILD = ROOT / "scripts" / "build_packets.py"
EXTRACT = ROOT / "scripts" / "extract_terms.py"
TRANSLATE = ROOT / "scripts" / "translate_pilot.py"
VALIDATE = ROOT / "scripts" / "validate_translations.py"
PILOT = ROOT / "tests" / "fixtures" / "pilot"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def setup_clean_translations() -> tuple[Path, Path]:
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
    assert run([str(EXTRACT),
                "--inventory", str(inv),
                "--snapshots", str(snaps),
                "--segments", str(classified),
                "--out", str(glossary)]).returncode == 0
    assert run([str(BUILD),
                "--segments", str(classified),
                "--profile", str(profile),
                "--out", str(packets)]).returncode == 0
    if translations.exists():
        import shutil
        shutil.rmtree(translations)
    translations.mkdir(parents=True)
    assert run([str(TRANSLATE),
                "--packets", str(packets),
                "--segments", str(classified),
                "--out", str(translations),
                "--mode", "identity"]).returncode == 0
    return translations, classified


def test_candidatos_correctos_pasan() -> None:
    translations, classified = setup_clean_translations()
    for path in translations.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        for entry in data["entries"]:
            original = entry.get("original_text") or ""
            entry["translated_text"] = original.replace(" not ", " no ")
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    out = TMP / "validation_ok.json"
    proc = run([str(VALIDATE), "--translations", str(translations), "--segments", str(classified), "--out", str(out)])
    assert proc.returncode == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["total_invalid"] == 0
    assert report["total_valid"] >= 1


def test_negacion_perdida_detectada() -> None:
    translations, classified = setup_clean_translations()
    target = next(translations.glob("*.json"))
    data = json.loads(target.read_text(encoding="utf-8"))
    for entry in data["entries"]:
        original_lower = (entry.get("original_text") or "").lower()
        if " not " in original_lower:
            entry["translated_text"] = entry["translated_text"].replace(" no ", " ", 1)
            break
    target.write_text(json.dumps(data, indent=2), encoding="utf-8")
    out = TMP / "validation_neg.json"
    proc = run([str(VALIDATE), "--translations", str(translations), "--segments", str(classified), "--out", str(out)])
    assert proc.returncode != 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert any("negación" in e for r in report["results"] for e in r["errors"])


def test_marcador_extra_detectado() -> None:
    translations, classified = setup_clean_translations()
    target = next(translations.glob("*.json"))
    data = json.loads(target.read_text(encoding="utf-8"))
    for entry in data["entries"]:
        entry["translated_text"] = "§§fake marker§§ " + entry["translated_text"]
        break
    target.write_text(json.dumps(data, indent=2), encoding="utf-8")
    out = TMP / "validation_marker.json"
    proc = run([str(VALIDATE), "--translations", str(translations), "--segments", str(classified), "--out", str(out)])
    assert proc.returncode != 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert any("marcador extra" in e for r in report["results"] for e in r["errors"])


def test_segmento_ausente_detectado() -> None:
    translations, classified = setup_clean_translations()
    target = next(translations.glob("*.json"))
    data = json.loads(target.read_text(encoding="utf-8"))
    if data["entries"]:
        data["entries"] = data["entries"][:-1]
    target.write_text(json.dumps(data, indent=2), encoding="utf-8")
    out = TMP / "validation_missing.json"
    proc = run([str(VALIDATE), "--translations", str(translations), "--segments", str(classified), "--out", str(out)])
    assert proc.returncode != 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert any("ausente" in e for r in report["results"] for e in r["errors"])
