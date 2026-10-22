"""Pruebas para scripts/raise_issues.py (fase 044)."""

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
RAISE = ROOT / "scripts" / "raise_issues.py"
PILOT = ROOT / "tests" / "fixtures" / "pilot"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def setup_pipeline() -> tuple[Path, Path]:
    inv = TMP / "inv.json"
    seg = TMP / "segments.json"
    classified = TMP / "classified.json"
    snaps = TMP / "snapshots.json"
    packets = TMP / "packets.json"
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


def test_sin_flag_loss_aprueba() -> None:
    classified, translations = setup_pipeline()
    issues_out = TMP / "issues_clean.json"
    proc = run([str(RAISE),
                "--translations", str(translations),
                "--segments", str(classified),
                "--issues-out", str(issues_out)])
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(issues_out.read_text(encoding="utf-8"))
    assert payload["by_severity"]["critical"] == 0


def test_flag_loss_genera_issue_critical() -> None:
    classified, translations = setup_pipeline()
    target = next(translations.glob("*.json"))
    data = json.loads(target.read_text(encoding="utf-8"))
    if data["entries"]:
        data["entries"][0]["flag_loss"] = True
        data["entries"][0]["missing_literals"] = ["foo"]
    target.write_text(json.dumps(data, indent=2), encoding="utf-8")
    issues_out = TMP / "issues_flag_loss.json"
    proc = run([str(RAISE),
                "--translations", str(translations),
                "--segments", str(classified),
                "--issues-out", str(issues_out)])
    assert proc.returncode != 0
    payload = json.loads(issues_out.read_text(encoding="utf-8"))
    assert payload["by_severity"]["critical"] >= 1
    assert any(i["category"] == "technical" for i in payload["issues"])


def test_identidad_sospechosa_es_info() -> None:
    classified, translations = setup_pipeline()
    target = next(translations.glob("*.json"))
    data = json.loads(target.read_text(encoding="utf-8"))
    by_id = {e["segment_id"]: e for e in data["entries"]}
    for sid, seg in __import__("json").loads(classified.read_text(encoding="utf-8"))["files"][0]["items" if "items" in __import__("json").loads(classified.read_text(encoding="utf-8"))["files"][0] else "segments"][0].items() if False else []:
        pass
    classified_data = __import__("json").loads(classified.read_text(encoding="utf-8"))
    translatable_ids = {s["segment_id"] for f in classified_data["files"] for s in f["segments"] if s.get("disposition") == "translatable"}
    for entry in data["entries"]:
        if entry["segment_id"] in translatable_ids:
            entry["translated_text"] = entry["original_text"]
            break
    target.write_text(json.dumps(data, indent=2), encoding="utf-8")
    issues_out = TMP / "issues_identity.json"
    proc = run([str(RAISE),
                "--translations", str(translations),
                "--segments", str(classified),
                "--issues-out", str(issues_out)])
    payload = json.loads(issues_out.read_text(encoding="utf-8"))
    assert any(i["category"] == "ambiguous" for i in payload["issues"])
