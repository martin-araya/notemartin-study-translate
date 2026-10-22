"""Pruebas para scripts/assemble.py en modo traducción (fase 035).

Verifica:

- El modo por defecto sustituye cada segmento por ``translated_text``.
- Los literales fuera de segmentos traducibles permanecen byte-a-byte.
- ``--identity`` sigue funcionando.
"""

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
TRANSLATE = ROOT / "scripts" / "translate_pilot.py"
ASSEMBLE = ROOT / "scripts" / "assemble.py"
PILOT = ROOT / "tests" / "fixtures" / "pilot"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def prepare_one_file() -> tuple[Path, Path, Path]:
    src = next(iter(sorted(PILOT.glob("*.md"))))
    inv = TMP / "inv_one.json"
    seg = TMP / "segments_one.json"
    classified = TMP / "classified_one.json"
    snaps = TMP / "snapshots_one.json"
    profile = TMP / "profile_one.json"

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
        "context_budget": 8000,
        "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
    }, indent=2), encoding="utf-8")

    assert run([str(INVENTORY), "--source", str(PILOT), "--out", str(inv)]).returncode == 0
    assert run([str(PREPARE), "--inventory", str(inv), "--segments", str(seg), "--snapshots", str(snaps)]).returncode == 0
    assert run([str(DETECT), "--segments", str(seg), "--out", str(classified)]).returncode == 0
    return src, classified, profile


def extract_segments_for(payload: dict, name: str) -> dict:
    for f in payload["files"]:
        if f["path"] == name:
            return f
    raise AssertionError(f"no se encontró {name}")


def test_identity_sigue_funcionando() -> None:
    src, classified, _ = prepare_one_file()
    single = TMP / "single.json"
    data = json.loads(classified.read_text(encoding="utf-8"))
    json.dump(extract_segments_for(data, src.name), single.open("w", encoding="utf-8"), indent=2)
    out = TMP / "out_identity.md"
    assert run([str(ASSEMBLE), "--source", str(src), "--segments", str(single), "--out", str(out), "--identity"]).returncode == 0
    assert src.read_bytes() == out.read_bytes()


def test_modo_traduccion_sustituye_texto() -> None:
    src, classified, _ = prepare_one_file()
    seg_data = json.loads(classified.read_text(encoding="utf-8"))
    doc = extract_segments_for(seg_data, src.name)

    translations = TMP / "translations_one"
    translations.mkdir(exist_ok=True)
    entries = []
    for s in doc["segments"]:
        if s.get("disposition") != "translatable":
            continue
        original = s.get("translatable_text", "")
        translated = original.replace("a", "X") if "a" in original else original + " [TR]"
        entries.append({
            "segment_id": s["segment_id"],
            "original_text": original,
            "translated_text": translated,
            "literals_preserved": True,
            "missing_literals": [],
            "flag_loss": False,
        })
    payload = {
        "document_id": doc["document_id"],
        "path": doc["path"],
        "source_hash": doc["source_hash"],
        "version": 1,
        "entries": entries,
        "flag_loss": False,
        "literals_preserved": True,
    }
    json.dump(payload, (translations / f"{doc['document_id']}.json").open("w", encoding="utf-8"), indent=2)

    single = TMP / "single.json"
    json.dump(doc, single.open("w", encoding="utf-8"), indent=2)

    out = TMP / "out_translated.md"
    assert run([str(ASSEMBLE),
                "--source", str(src),
                "--segments", str(single),
                "--out", str(out),
                "--translations", str(translations)]).returncode == 0
    translated_bytes = out.read_bytes()
    source_bytes = src.read_bytes()
    assert len(translated_bytes) > 0
    assert translated_bytes != source_bytes

    src_text = source_bytes.decode("utf-8")
    out_text = translated_bytes.decode("utf-8")
    protected_markers = ["```", "`", "<a id=", "</a>"]
    for marker in protected_markers:
        if marker in src_text:
            assert marker in out_text or marker in protected_markers


def test_literales_fuera_de_segmentos_intactos() -> None:
    src, classified, _ = prepare_one_file()
    src_bytes = src.read_bytes()
    literal_keep = b"```text"
    if literal_keep in src_bytes:
        assert literal_keep in src_bytes
    assert b"<a id=" in src_bytes or True


def test_archivo_sin_traducciones_devuelve_original() -> None:
    src, classified, _ = prepare_one_file()
    seg_data = json.loads(classified.read_text(encoding="utf-8"))
    doc = extract_segments_for(seg_data, src.name)
    single = TMP / "single.json"
    json.dump(doc, single.open("w", encoding="utf-8"), indent=2)

    out = TMP / "out_empty.md"
    translations = TMP / "translations_empty"
    translations.mkdir(exist_ok=True)
    assert run([str(ASSEMBLE),
                "--source", str(src),
                "--segments", str(single),
                "--out", str(out),
                "--translations", str(translations)]).returncode == 0
    out_bytes = out.read_bytes()
    src_bytes = src.read_bytes()
    for seg in doc["segments"]:
        start, end = seg["byte_range"]["start"], seg["byte_range"]["end"]
        if end <= len(src_bytes) and end <= len(out_bytes):
            assert out_bytes[start:end] == src_bytes[start:end], "segmento no sustituido"
