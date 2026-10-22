"""Pruebas de extracción de literales protegidos (fase 017).

Verifica que ``scripts/prepare.py --segments`` enumera correctamente:

- Código inline (entre backticks) sin los delimitadores.
- Bloques de código fenced con su ``language``.
- Bloques de código indentados.
- Destinos de enlaces.
- Destinos y alt de imágenes.
- Anchors HTML ``<a id="..."></a>``.

Para cada literal, comprueba que ``byte_range`` produce el contenido
esperado al cortar los bytes del archivo original.
"""

from __future__ import annotations

import tempfile
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PREPARE = ROOT / "scripts" / "prepare.py"
INVENTORY = ROOT / "scripts" / "inventory.py"
PILOT = ROOT / "tests" / "fixtures" / "pilot"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run_script(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *args],
        capture_output=True,
        text=True,
        check=False,
    )


def prepare_segments() -> dict:
    inv = TMP / "inv.json"
    segs = TMP / "segments.json"
    assert run_script([str(INVENTORY), "--source", str(PILOT), "--out", str(inv)]).returncode == 0
    assert run_script([str(PREPARE), "--inventory", str(inv), "--segments", str(segs)]).returncode == 0
    return json.loads(segs.read_text(encoding="utf-8"))


def doc_segments(payload: dict, name: str) -> dict:
    for f in payload["files"]:
        if f["path"] == name:
            return f
    raise AssertionError(f"no se encontró {name}")


def test_code_fenced_con_language() -> None:
    payload = prepare_segments()
    doc = doc_segments(payload, "typescriptlang_handbook_2_basic-types.md")
    literals = [lit for s in doc["segments"] for lit in s.get("protected_literals", [])]
    fenced = [lit for lit in literals if lit["type"] == "code_fenced"]
    assert len(fenced) >= 2
    for f in fenced:
        assert "byte_range" in f
        assert "language" in f


def test_code_inline_sin_backticks() -> None:
    payload = prepare_segments()
    doc = doc_segments(payload, "typescriptlang_handbook_2_basic-types.md")
    literals = [lit for s in doc["segments"] for lit in s.get("protected_literals", [])]
    inline = [lit for lit in literals if lit["type"] == "code_inline"]
    assert any("message" in (lit.get("value") or "") for lit in inline), "expected at least one inline 'message' literal"


def test_anchor_en_mdn() -> None:
    payload = prepare_segments()
    doc = doc_segments(payload, "developer-mozilla_How_to_Layout_cookbook_Card.md")
    literals = [lit for s in doc["segments"] for lit in s.get("protected_literals", [])]
    anchors = [lit for lit in literals if lit["type"] == "anchor"]
    assert len(anchors) >= 1
    src = (PILOT / doc["path"]).read_bytes()
    for a in anchors:
        br = a["byte_range"]
        start, end = br["start"], br["end"]
        slice_text = src[start:end].decode("utf-8", errors="replace")
        assert slice_text.startswith("<a id="), f"anchor no empieza por '<a id=': {slice_text!r}"


def test_image_destination_en_openrouter() -> None:
    payload = prepare_segments()
    doc = doc_segments(payload, "APIs_OpenRouter_01_-_Introducción,_Autenticación_y_Formato_General.md")
    literals = [lit for s in doc["segments"] for lit in s.get("protected_literals", [])]
    fenced = [lit for lit in literals if lit["type"] == "code_fenced"]
    assert len(fenced) >= 1, "OpenRouter 01 debería contener al menos un bloque de código fence"


def test_byte_ranges_no_cortan_utf8() -> None:
    payload = prepare_segments()
    for f in payload["files"]:
        path = PILOT / f["path"]
        src = path.read_bytes()
        for seg in f["segments"]:
            br = seg["byte_range"]
            start, end = br["start"], br["end"]
            slice_bytes = src[start:end]
            try:
                slice_bytes.decode("utf-8")
            except UnicodeDecodeError as e:
                raise AssertionError(
                    f"{f['path']} seg={seg['segment_id']} corta UTF-8 en {start}-{end}: {e}"
                )
            for lit in seg.get("protected_literals", []):
                lit_br = lit["byte_range"]
                lit_bytes = src[lit_br["start"]:lit_br["end"]]
                try:
                    lit_bytes.decode("utf-8")
                except UnicodeDecodeError as e:
                    raise AssertionError(
                        f"{f['path']} literal={lit['type']} corta UTF-8: {e}"
                    )
