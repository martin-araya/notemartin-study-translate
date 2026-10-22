"""Pruebas para scripts/build_packets.py (fase 025)."""

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
PILOT = ROOT / "tests" / "fixtures" / "pilot"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def write_profile(budget: int, path: Path) -> None:
    path.write_text(json.dumps({
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
        "context_budget": budget,
        "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
    }, indent=2), encoding="utf-8")


def prepare_inputs() -> None:
    inv = TMP / "inv.json"
    seg = TMP / "segments.json"
    classified = TMP / "classified.json"
    assert run([str(INVENTORY), "--source", str(PILOT), "--out", str(inv)]).returncode == 0
    assert run([str(PREPARE), "--inventory", str(inv), "--segments", str(seg)]).returncode == 0
    assert run([str(DETECT), "--segments", str(seg), "--out", str(classified)]).returncode == 0


def test_budget_pequeno_genera_mas_paquetes() -> None:
    prepare_inputs()
    classified = TMP / "classified.json"
    prof_small = TMP / "profile_small.json"
    prof_large = TMP / "profile_large.json"
    out_small = TMP / "packets_small.json"
    out_large = TMP / "packets_large.json"

    write_profile(500, prof_small)
    write_profile(100000, prof_large)

    assert run([str(BUILD), "--segments", str(classified), "--profile", str(prof_small), "--out", str(out_small)]).returncode == 0
    assert run([str(BUILD), "--segments", str(classified), "--profile", str(prof_large), "--out", str(out_large)]).returncode == 0

    small = json.loads(out_small.read_text(encoding="utf-8"))
    large = json.loads(out_large.read_text(encoding="utf-8"))
    assert small["total_packets"] >= large["total_packets"]


def test_paquete_no_excede_presupuesto() -> None:
    prepare_inputs()
    classified = TMP / "classified.json"
    prof = TMP / "profile_b.json"
    out = TMP / "packets_b.json"
    write_profile(700, prof)
    assert run([str(BUILD), "--segments", str(classified), "--profile", str(prof), "--out", str(out)]).returncode == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    for p in data["packets"]:
        if not p["overflow"]:
            assert p["total_chars"] <= 700, f"{p['packet_id']} excede 700 ({p['total_chars']})"


def test_owner_formato_correcto() -> None:
    prepare_inputs()
    classified = TMP / "classified.json"
    prof = TMP / "profile_c.json"
    out = TMP / "packets_c.json"
    write_profile(1000, prof)
    assert run([str(BUILD), "--segments", str(classified), "--profile", str(prof), "--out", str(out)]).returncode == 0
    data = json.loads(out.read_text(encoding="utf-8"))
    import re
    for p in data["packets"]:
        assert re.match(r"^pack-[0-9a-f]{8}$", p["owner"]), p["owner"]


def test_segmentos_already_target_excluidos() -> None:
    prepare_inputs()
    classified = TMP / "classified.json"
    prof = TMP / "profile_d.json"
    out = TMP / "packets_d.json"
    write_profile(1000, prof)
    assert run([str(BUILD), "--segments", str(classified), "--profile", str(prof), "--out", str(out)]).returncode == 0
    classified_data = json.loads(classified.read_text(encoding="utf-8"))
    already_target = {
        s["segment_id"]
        for f in classified_data["files"]
        for s in f["segments"]
        if s.get("disposition") == "already_target"
    }
    packets = json.loads(out.read_text(encoding="utf-8"))
    for p in packets["packets"]:
        for sid in p["segments"]:
            assert sid not in already_target, f"{sid} es already_target y no debe estar en paquetes"


def test_non_emitible_context_declarado() -> None:
    prepare_inputs()
    classified = TMP / "classified.json"
    prof = TMP / "profile_e.json"
    out = TMP / "packets_e.json"
    write_profile(1000, prof)
    assert run([str(BUILD), "--segments", str(classified), "--profile", str(prof), "--out", str(out)]).returncode == 0
    packets = json.loads(out.read_text(encoding="utf-8"))
    assert packets["packets"]
    has_context = any(len(p.get("non_emitible_context") or []) > 0 for p in packets["packets"])
    assert has_context
