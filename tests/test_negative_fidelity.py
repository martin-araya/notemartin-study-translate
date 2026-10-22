"""Pruebas de errores de fidelidad conocidos (fase 052).

Inyecta cuatro clases de errores controlados sobre los fixtures
negativos y verifica que los detectores existentes los identifican:

- ``list_omitted``: traducción con un segmento ausente (entrada
  eliminada del JSON de salida). Detector: ``validate_translations.py``.
- ``command_altered``: traducción que pierde literales protegidos.
  Detector: ``validate.py`` (banderas ``flag_loss`` / ``missing_literals``).
- ``negation_inverted``: traducción sin la negación del original.
  Detector: ``validate_translations.py`` y ``raise_issues.py``.
- ``table_trimmed``: traducción sin el segmento de tabla. Detector:
  ``validate_translations.py`` (segmento ausente). Se complementa con
  un conteo explícito en el mensaje.
"""

from __future__ import annotations

import tempfile
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
INVENTORY = SCRIPTS / "inventory.py"
PREPARE = SCRIPTS / "prepare.py"
DETECT = SCRIPTS / "detect_language.py"
BUILD_PACKETS = SCRIPTS / "build_packets.py"
TRANSLATE = SCRIPTS / "translate_pilot.py"
VALIDATE_TRANSLATIONS = SCRIPTS / "validate_translations.py"
VALIDATE = SCRIPTS / "validate.py"
RAISE_ISSUES = SCRIPTS / "raise_issues.py"
NEG_FIX = ROOT / "tests" / "fixtures" / "negative"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def setup_pipeline() -> dict[str, Path]:
    """Construye inventory + segments + translations en modo identity."""
    inv = TMP / "inv_neg_pipeline.json"
    seg = TMP / "seg_neg_pipeline.json"
    snaps = TMP / "snaps_neg_pipeline.json"
    classified = TMP / "classified_neg_pipeline.json"
    packets = TMP / "packets_neg_pipeline.json"
    translations = TMP / "trans_neg_pipeline"
    profile = TMP / "profile_neg_pipeline.json"

    if translations.exists():
        shutil.rmtree(translations)
    translations.mkdir(parents=True)

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
        "paths": {"source_root": str(NEG_FIX), "work_root": "/tmp", "output_root": "/tmp"},
        "exclusions": [],
        "context_budget": 1500,
        "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
    }, indent=2), encoding="utf-8")

    assert run([str(INVENTORY), "--source", str(NEG_FIX), "--out", str(inv)]).returncode == 0
    assert run([str(PREPARE),
                "--inventory", str(inv),
                "--segments", str(seg),
                "--snapshots", str(snaps)]).returncode == 0
    assert run([str(DETECT), "--segments", str(seg), "--out", str(classified)]).returncode == 0
    assert run([str(BUILD_PACKETS),
                "--segments", str(classified),
                "--profile", str(profile),
                "--out", str(packets)]).returncode == 0
    assert run([str(TRANSLATE),
                "--packets", str(packets),
                "--segments", str(classified),
                "--out", str(translations),
                "--mode", "identity"]).returncode == 0

    return {
        "inv": inv, "seg": seg, "snaps": snaps,
        "classified": classified, "packets": packets,
        "translations": translations,
    }


def doc_id_for(classified: Path, path_suffix: str) -> str:
    data = json.loads(classified.read_text(encoding="utf-8"))
    for f in data["files"]:
        if f["path"].endswith(path_suffix):
            return f["document_id"]
    raise KeyError(path_suffix)


def test_list_omitted_es_detectado_como_segmento_ausente() -> None:
    paths = setup_pipeline()
    doc_id = doc_id_for(paths["classified"], "list_omitted.md")
    target = paths["translations"] / f"{doc_id}.json"
    data = json.loads(target.read_text(encoding="utf-8"))
    if len(data.get("entries", [])) < 2:
        import pytest
        pytest.skip("fixture no tiene segmentos suficientes para omitir uno")
    data["entries"].pop()
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    out = TMP / "vt_list_omitted.json"
    proc = run([
        str(VALIDATE_TRANSLATIONS),
        "--translations", str(paths["translations"]),
        "--segments", str(paths["classified"]),
        "--out", str(out),
    ])
    assert proc.returncode != 0, "validate_translations debería fallar"
    payload = json.loads(out.read_text(encoding="utf-8"))
    invalid = [r for r in payload["results"] if not r["valid"]]
    assert any("segmento ausente" in e for r in invalid for e in r["errors"])


def test_command_altered_es_detectado_por_flag_loss() -> None:
    paths = setup_pipeline()
    doc_id = doc_id_for(paths["classified"], "command_altered.md")
    target = paths["translations"] / f"{doc_id}.json"
    data = json.loads(target.read_text(encoding="utf-8"))
    if not data.get("entries"):
        import pytest
        pytest.skip("sin entradas")
    data["entries"][0]["flag_loss"] = True
    data["entries"][0]["missing_literals"] = ["git push origin main --force"]
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    solo_translations = TMP / "trans_cmd_altered"
    if solo_translations.exists():
        shutil.rmtree(solo_translations)
    solo_translations.mkdir()
    shutil.copy(target, solo_translations / target.name)

    solo_segments = TMP / "classified_cmd.json"
    classified_doc = json.loads(paths["classified"].read_text(encoding="utf-8"))
    solo_segments.write_text(json.dumps({
        "files": [f for f in classified_doc["files"] if f["path"].endswith("command_altered.md")]
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    issues = TMP / "issues_command.json"
    proc = run([
        str(RAISE_ISSUES),
        "--translations", str(solo_translations),
        "--segments", str(solo_segments),
        "--issues-out", str(issues),
    ])
    assert proc.returncode != 0
    payload = json.loads(issues.read_text(encoding="utf-8"))
    assert any(i.get("severity") == "critical" for i in payload["issues"])
    assert any("literales perdidos" in (i.get("message") or "") for i in payload["issues"])


def test_negation_inverted_es_detectada() -> None:
    paths = setup_pipeline()
    doc_id = doc_id_for(paths["classified"], "negation_inverted.md")
    target = paths["translations"] / f"{doc_id}.json"
    data = json.loads(target.read_text(encoding="utf-8"))
    if not data.get("entries"):
        import pytest
        pytest.skip("sin entradas")
    target_entry = next((e for e in data["entries"] if "MUST NOT" in (e.get("original_text") or "")), None)
    assert target_entry is not None
    target_entry["translated_text"] = "Debes eliminar el directorio de caché mientras la aplicación está en ejecución."
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    out = TMP / "vt_negation.json"
    proc = run([
        str(VALIDATE_TRANSLATIONS),
        "--translations", str(paths["translations"]),
        "--segments", str(paths["classified"]),
        "--out", str(out),
    ])
    assert proc.returncode != 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    invalid = [r for r in payload["results"] if not r["valid"]]
    assert any("negación perdida" in e for r in invalid for e in r["errors"])


def test_table_trimmed_es_detectada_como_segmento_ausente() -> None:
    paths = setup_pipeline()
    doc_id = doc_id_for(paths["classified"], "table_trimmed.md")
    target = paths["translations"] / f"{doc_id}.json"
    data = json.loads(target.read_text(encoding="utf-8"))
    table_entry = next(
        (e for e in data["entries"] if e.get("original_text") is not None),
        None,
    )
    assert table_entry is not None
    data["entries"] = [e for e in data["entries"] if e["segment_id"] != table_entry["segment_id"]]
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    out = TMP / "vt_table.json"
    proc = run([
        str(VALIDATE_TRANSLATIONS),
        "--translations", str(paths["translations"]),
        "--segments", str(paths["classified"]),
        "--out", str(out),
    ])
    assert proc.returncode != 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    invalid = [r for r in payload["results"] if not r["valid"]]
    assert any("segmento ausente" in e for r in invalid for e in r["errors"])
