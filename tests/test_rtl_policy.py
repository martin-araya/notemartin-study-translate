"""Pruebas de la política RTL (fase 108)."""

from __future__ import annotations

import tempfile
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "references" / "rtl-policy.md"
SCHEMA_SEG = ROOT / "schemas" / "segment.schema.json"
DETECT_RTL = ROOT / "scripts" / "detect_text_direction.py"
EVAL_RTL = ROOT / "scripts" / "eval_rtl.py"
FIXTURE = ROOT / "tests" / "fixtures" / "rtl"
MIX = ROOT / "tests" / "fixtures" / "mix-ltr-rtl"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def test_politica_existe_y_cubre_secciones() -> None:
    assert DOC.exists()
    text = DOC.read_text(encoding="utf-8")
    for sec in ("Detección por carácter", "Reglas de preservación", "Numerales", "Lo que NO se modifica"):
        assert sec in text, f"falta « {sec} »"


def test_detector_ltr() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    import detect_text_direction as dtd  # noqa: E402

    seg = {"translatable_text": "Hola mundo en español."}
    assert dtd.detect_text_direction(seg["translatable_text"]) == "ltr"


def test_detector_rtl_puro() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    import detect_text_direction as dtd  # noqa: E402

    arabic = "الويب المفتوح يمنحك فرصا واسعة كمطوّر"
    assert dtd.detect_text_direction(arabic) == "rtl"


def test_detector_mixed() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    import detect_text_direction as dtd  # noqa: E402

    mixed = "مرحبا أهلاً بالعالم. This sentence is in English."
    assert dtd.detect_text_direction(mixed) == "mixed"


def test_detector_hebreo_es_rtl() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    import detect_text_direction as dtd  # noqa: E402

    hebrew = "שלום עולם"
    assert dtd.detect_text_direction(hebrew) == "rtl"


def test_digits_ascii_y_arabicos() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    import detect_text_direction as dtd  # noqa: E402

    assert dtd.detect_digits("año 2024") == "ascii"
    assert dtd.detect_digits("السنة ٢٠٢٤") == "arabic_indic"
    assert dtd.detect_digits("سال ۲۰۲۴") == "arabic_eastern"
    assert dtd.detect_digits("sin cifras") == "other"


def test_segment_schema_contiene_text_direction() -> None:
    schema = json.loads(SCHEMA_SEG.read_text(encoding="utf-8"))
    seg_props = schema["$defs"]["segment"]["properties"]
    assert "text_direction" in seg_props
    assert seg_props["text_direction"]["enum"] == ["ltr", "rtl", "mixed"]
    assert "digits" in seg_props


def test_fixtures_rtl_existen() -> None:
    assert FIXTURE.is_dir()
    files = sorted(p for p in FIXTURE.iterdir() if p.suffix == ".md")
    assert len(files) >= 3, "se esperaban >=3 archivos ar"
    combined = "\n".join(p.read_text(encoding="utf-8") for p in files)
    # Comprueba que existe texto árabe real.
    assert any(0x0600 <= ord(c) <= 0x06FF for c in combined), (
        "el fixture debe contener caracteres árabes reales"
    )
    assert "CC0" in combined, "los fixtures ar son derivados CC0"


def test_fixture_mixto_ltr_rtl() -> None:
    assert MIX.is_dir()
    files = sorted(p for p in MIX.iterdir() if p.suffix == ".md")
    assert len(files) >= 1
    text = files[0].read_text(encoding="utf-8")
    assert any(0x0600 <= ord(c) <= 0x06FF for c in text)
    assert "español" in text.lower()


def test_eval_rtl_emite_artefactos() -> None:
    out = TMP / "rtl"
    if out.exists():
        import shutil
        shutil.rmtree(out)
    rc = subprocess.run(
        [sys.executable, str(EVAL_RTL), "--source", str(FIXTURE),
         "--pair", "ar-es", "--out", str(out), "--recognized", "en,ar"],
        capture_output=True, text=True, check=False,
    ).returncode
    assert rc == 0
    eval_payload = json.loads((out / "eval.json").read_text(encoding="utf-8"))
    assert eval_payload["pair"] == "ar-es"
    assert eval_payload["source_language"] == "ar"
    metrics = eval_payload["metrics"]
    assert metrics["by_text_direction"]["rtl"] >= 1
    assert (out / "rtl.json").exists()
    assert (out / "summary.md").exists()


def test_preservacion_de_bytes_unicode() -> None:
    """El inventario conserva el SHA-256 original; el eval lo registra."""
    inv_path = TMP / "rtl-inv.json"
    if inv_path.exists():
        inv_path.unlink()
    rc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "inventory.py"),
         "--source", str(FIXTURE), "--out", str(inv_path)],
        capture_output=True, text=True, check=False,
    ).returncode
    assert rc == 0
    import hashlib
    payload = json.loads(inv_path.read_text(encoding="utf-8"))
    for entry in payload.get("files", []):
        path = ROOT / "tests" / "fixtures" / "rtl" / entry["path"]
        if path.exists():
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            assert entry["sha256"] == actual, (
                f"hash de {entry['path']} no coincide: {entry['sha256']} != {actual}"
            )
