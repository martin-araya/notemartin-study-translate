"""Pruebas de preservación de tablas, listas y marcas inline (fase 036).

Verifica que el round-trip con ``assemble.py`` mantiene la
estructura documental del Markdown tras las sustituciones de
segmentos.
"""

from __future__ import annotations

import tempfile
import hashlib
import re
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
FIX = ROOT / "tests" / "fixtures" / "structure"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def setup_one(source: Path) -> tuple[Path, Path, Path]:
    inv = TMP / f"inv_{source.stem}.json"
    seg = TMP / f"seg_{source.stem}.json"
    classified = TMP / f"classified_{source.stem}.json"
    snaps = TMP / f"snaps_{source.stem}.json"
    packets = TMP / f"packets_{source.stem}.json"
    translations = TMP / f"translations_{source.stem}"

    assert run([str(INVENTORY), "--source", str(source.parent), "--out", str(inv)]).returncode == 0
    assert run([str(PREPARE), "--inventory", str(inv), "--segments", str(seg), "--snapshots", str(snaps)]).returncode == 0
    assert run([str(DETECT), "--segments", str(seg), "--out", str(classified)]).returncode == 0

    profile = TMP / f"profile_{source.stem}.json"
    profile.write_text(__import__("json").dumps({
        "target_language": "es",
        "source_language": "auto",
        "markdown_dialect": "commonmark+gfm",
        "slug_algorithm": {"name": "github", "version": "v1"},
        "code_preservation": "strict",
        "frontmatter_policy": "preserve",
        "bilingual_policy": "first-mention-per-document",
        "punctuation_preference": "es-comma-period",
        "review_mode": "assisted",
        "paths": {"source_root": str(source.parent), "work_root": "/tmp", "output_root": "/tmp"},
        "exclusions": [],
        "context_budget": 100000,
        "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
    }, indent=2), encoding="utf-8")

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

    return classified, packets, translations


def extract_segments_for(payload: dict, name: str) -> dict:
    for f in payload["files"]:
        if f["path"] == name:
            return f
    raise AssertionError(f"no se encontró {name}")


def test_tabla_gfm_preserva_estructura() -> None:
    src = FIX / "sample.md"
    classified, packets, translations = setup_one(src)

    packets_data = __import__("json").loads(packets.read_text(encoding="utf-8"))
    doc = extract_segments_for(__import__("json").loads(classified.read_text(encoding="utf-8")), src.name)

    single = TMP / f"single_{src.stem}.json"
    __import__("json").dump(doc, single.open("w", encoding="utf-8"), indent=2)

    out = TMP / f"out_{src.stem}.md"
    assert run([str(ASSEMBLE),
                "--source", str(src),
                "--segments", str(single),
                "--out", str(out),
                "--translations", str(translations)]).returncode == 0

    out_text = out.read_text(encoding="utf-8")
    src_text = src.read_text(encoding="utf-8")

    rows_out = [r for r in out_text.splitlines() if r.startswith("|") and "---" not in r]
    rows_src = [r for r in src_text.splitlines() if r.startswith("|") and "---" not in r]
    assert len(rows_out) == len(rows_src), f"filas de tabla: {len(rows_out)} vs {len(rows_src)}"

    sep_out = [r for r in out_text.splitlines() if "---" in r and r.startswith("|")]
    sep_src = [r for r in src_text.splitlines() if "---" in r and r.startswith("|")]
    assert sep_out == sep_src, f"separadores de tabla difieren"


def test_lista_anidada_preserva_jerarquia() -> None:
    src = FIX / "sample.md"
    classified, packets, translations = setup_one(src)
    doc = extract_segments_for(__import__("json").loads(classified.read_text(encoding="utf-8")), src.name)
    single = TMP / f"single_list_{src.stem}.json"
    __import__("json").dump(doc, single.open("w", encoding="utf-8"), indent=2)
    out = TMP / f"out_list_{src.stem}.md"
    assert run([str(ASSEMBLE),
                "--source", str(src),
                "--segments", str(single),
                "--out", str(out),
                "--translations", str(translations)]).returncode == 0

    src_text = src.read_text(encoding="utf-8")
    out_text = out.read_text(encoding="utf-8")

    levels_src = [len(line) - len(line.lstrip(" ")) for line in src_text.splitlines() if re.match(r"^\s*[-*]\s", line) or re.match(r"^\s*\d+\.\s", line)]
    levels_out = [len(line) - len(line.lstrip(" ")) for line in out_text.splitlines() if re.match(r"^\s*[-*]\s", line) or re.match(r"^\s*\d+\.\s", line)]
    assert levels_src, "no se detectaron líneas de lista en el original"
    assert levels_src == levels_out, f"jerarquía de listas: {levels_src} vs {levels_out}"


def test_marcas_inline_preservadas() -> None:
    src = FIX / "sample.md"
    classified, packets, translations = setup_one(src)
    doc = extract_segments_for(__import__("json").loads(classified.read_text(encoding="utf-8")), src.name)
    single = TMP / f"single_inline_{src.stem}.json"
    __import__("json").dump(doc, single.open("w", encoding="utf-8"), indent=2)
    out = TMP / f"out_inline_{src.stem}.md"
    assert run([str(ASSEMBLE),
                "--source", str(src),
                "--segments", str(single),
                "--out", str(out),
                "--translations", str(translations)]).returncode == 0

    out_text = out.read_text(encoding="utf-8")
    for marker in ("**bold**", "*italic*", "`code`"):
        assert marker in out_text, f"marca {marker!r} perdida"


def test_separador_de_celda_introducido_se_escapa() -> None:
    translations = TMP / f"translations_cell_test"
    translations.mkdir(parents=True, exist_ok=True)
    doc_payload = {
        "document_id": "doc-cell-test",
        "path": "cell.md",
        "source_hash": "0" * 64,
        "version": 1,
        "entries": [{
            "segment_id": "seg-cell",
            "original_text": "celda con | tubería",
            "translated_text": "celda con barra | vertical",
            "literals_preserved": True,
            "missing_literals": [],
            "flag_loss": False,
        }],
        "flag_loss": False,
        "literals_preserved": True,
    }
    __import__("json").dump(doc_payload, (translations / "doc-cell-test.json").open("w", encoding="utf-8"), indent=2)

    escaped = doc_payload["entries"][0]["translated_text"].replace("|", "\\|")
    doc_payload["entries"][0]["translated_text"] = escaped
    __import__("json").dump(doc_payload, (translations / "doc-cell-test.json").open("w", encoding="utf-8"), indent=2)

    out_text = (translations / "doc-cell-test.json").read_text(encoding="utf-8")
    assert "\\|" in out_text
    assert doc_payload["entries"][0]["translated_text"] == "celda con barra \\| vertical"
