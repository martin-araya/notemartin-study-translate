"""Pruebas de determinismo de IDs (fase 018).

Verifica que dos ejecuciones de ``scripts/prepare.py --segments`` sobre
la misma fuente producen ``segment_id``, ``document_id`` y ``byte_range``
idénticos. La marca de tiempo ``generated_at`` se ignora porque
contiene la hora actual.
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


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *args],
        capture_output=True,
        text=True,
        check=False,
    )


def normalize(payload: dict) -> dict:
    p = dict(payload)
    p.pop("generated_at", None)
    return p


def test_dos_ejecuciones_producen_mismos_ids() -> None:
    inv = TMP / "inv.json"
    seg_a = TMP / "seg_a.json"
    seg_b = TMP / "seg_b.json"
    assert run([str(INVENTORY), "--source", str(PILOT), "--out", str(inv)]).returncode == 0
    assert run([str(PREPARE), "--inventory", str(inv), "--segments", str(seg_a)]).returncode == 0
    assert run([str(PREPARE), "--inventory", str(inv), "--segments", str(seg_b)]).returncode == 0

    pa = normalize(json.loads(seg_a.read_text(encoding="utf-8")))
    pb = normalize(json.loads(seg_b.read_text(encoding="utf-8")))
    assert pa == pb


def test_document_id_formato() -> None:
    inv = TMP / "inv.json"
    seg = TMP / "seg.json"
    run([str(INVENTORY), "--source", str(PILOT), "--out", str(inv)])
    run([str(PREPARE), "--inventory", str(inv), "--segments", str(seg)])
    payload = json.loads(seg.read_text(encoding="utf-8"))
    import re
    for f in payload["files"]:
        assert re.match(r"^doc-[0-9a-f]{8}$", f["document_id"]), f["document_id"]
        for s in f["segments"]:
            assert re.match(r"^seg-[0-9a-f]{8}$", s["segment_id"]), s["segment_id"]


def test_segment_id_distinto_por_tipo() -> None:
    inv = TMP / "inv.json"
    seg = TMP / "seg.json"
    run([str(INVENTORY), "--source", str(PILOT), "--out", str(inv)])
    run([str(PREPARE), "--inventory", str(inv), "--segments", str(seg)])
    payload = json.loads(seg.read_text(encoding="utf-8"))
    seen: set[tuple[str, str]] = set()
    for f in payload["files"]:
        for s in f["segments"]:
            key = (f["document_id"], s["byte_range"]["start"], s["byte_range"]["end"])
            if key in seen:
                raise AssertionError(f"segmento duplicado en {key}")
            seen.add(key)
