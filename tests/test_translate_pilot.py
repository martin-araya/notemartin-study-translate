"""Pruebas para scripts/translate_pilot.py (fase 028)."""

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
PILOT = ROOT / "tests" / "fixtures" / "pilot"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def full_pipeline() -> tuple[dict, Path]:
    inv = TMP / "inv.json"
    seg = TMP / "segments.json"
    classified = TMP / "classified.json"
    snaps = TMP / "snapshots.json"
    glossary = TMP / "glossary.json"
    packets = TMP / "packets_final.json"
    translations_dir = TMP / "translations"
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
        "paths": {
            "source_root": str(PILOT),
            "work_root": "/tmp/skill-work",
            "output_root": "/tmp/skill-output",
        },
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
    return json.loads(packets.read_text(encoding="utf-8")), translations_dir


def test_identity_mode_preserva_literales() -> None:
    packets, out_dir = full_pipeline()
    proc = run([str(TRANSLATE),
                "--packets", str(TMP / "packets_final.json"),
                "--segments", str(TMP / "classified.json"),
                "--out", str(out_dir),
                "--mode", "identity"])
    assert proc.returncode == 0, proc.stderr

    files = sorted(out_dir.glob("*.json"))
    assert files
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["flag_loss"] is False
        assert data["literals_preserved"] is True


def test_glossary_mode_sustituye_sin_romper_literales_basicos() -> None:
    packets, out_dir = full_pipeline()
    proc = run([str(TRANSLATE),
                "--packets", str(TMP / "packets_final.json"),
                "--segments", str(TMP / "classified.json"),
                "--glossary", str(TMP / "glossary.json"),
                "--out", str(out_dir),
                "--mode", "glossary"])
    assert proc.returncode == 0, proc.stderr


def test_una_entrada_por_segmento() -> None:
    packets, out_dir = full_pipeline()
    run([str(TRANSLATE),
         "--packets", str(TMP / "packets_final.json"),
         "--segments", str(TMP / "classified.json"),
         "--out", str(out_dir),
         "--mode", "identity"])
    classified = json.loads((TMP / "classified.json").read_text(encoding="utf-8"))
    skipped = {"code_skip", "no_text", "too_short", "mixed_or_code"}
    expected_ids = {
        s["segment_id"]
        for f in classified["files"]
        for s in f["segments"]
        if s.get("disposition") not in skipped
    }
    total_entries = 0
    seen: set[str] = set()
    for path in out_dir.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        for entry in data["entries"]:
            sid = entry["segment_id"]
            assert sid not in seen, f"ID duplicado {sid}"
            seen.add(sid)
            total_entries += 1
    assert seen == expected_ids


def test_version_y_generated_at_en_salida() -> None:
    _, out_dir = full_pipeline()
    run([str(TRANSLATE),
         "--packets", str(TMP / "packets_final.json"),
         "--segments", str(TMP / "classified.json"),
         "--out", str(out_dir),
         "--mode", "identity"])
    for path in out_dir.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["version"] == 1
        assert "generated_at" in data


def test_archivo_por_documento() -> None:
    _, out_dir = full_pipeline()
    run([str(TRANSLATE),
         "--packets", str(TMP / "packets_final.json"),
         "--segments", str(TMP / "classified.json"),
         "--out", str(out_dir),
         "--mode", "identity"])
    files = list(out_dir.glob("*.json"))
    assert len(files) >= 1
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        assert path.stem == data["document_id"]
