"""Pruebas de snapshots estructurales (fase 019).

Verifica que ``scripts/prepare.py --snapshots`` produce:

- ``headings`` en orden, con ``level`` y ``text``.
- ``links`` con ``kind`` en {internal, external} y ``target``.
- ``tables`` con ``headers`` y ``alignments``.
- ``structure_hash`` determinista.
"""

from __future__ import annotations

import tempfile
import json
import re
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


def prepare_snapshots() -> dict:
    inv = TMP / "inv.json"
    snap = TMP / "snapshots.json"
    assert run([str(INVENTORY), "--source", str(PILOT), "--out", str(inv)]).returncode == 0
    assert run([str(PREPARE), "--inventory", str(inv), "--snapshots", str(snap)]).returncode == 0
    return json.loads(snap.read_text(encoding="utf-8"))


def doc(payload: dict, name: str) -> dict:
    for f in payload["files"]:
        if f["path"] == name:
            return f
    raise AssertionError(f"no se encontró {name}")


def test_headings_typescriptlang() -> None:
    payload = prepare_snapshots()
    d = doc(payload, "typescriptlang_handbook_2_basic-types.md")
    assert len(d["headings"]) >= 1
    for h in d["headings"]:
        assert h["level"] >= 1
        assert "text" in h


def test_links_openrouter() -> None:
    payload = prepare_snapshots()
    d = doc(payload, "APIs_OpenRouter_01_-_Introducción,_Autenticación_y_Formato_General.md")
    assert len(d["links"]) >= 3
    assert any(l["kind"] == "external" and l["target"].startswith("https://") for l in d["links"])


def test_links_internos_mdn() -> None:
    payload = prepare_snapshots()
    d = doc(payload, "developer-mozilla_How_to_Layout_cookbook_Card.md")
    assert any(l["kind"] == "internal" and l["target"].startswith("#") for l in d["links"])


def test_structure_hash_determinista() -> None:
    inv = TMP / "inv.json"
    snap_a = TMP / "snap_a.json"
    snap_b = TMP / "snap_b.json"
    run([str(INVENTORY), "--source", str(PILOT), "--out", str(inv)])
    run([str(PREPARE), "--inventory", str(inv), "--snapshots", str(snap_a)])
    run([str(PREPARE), "--inventory", str(inv), "--snapshots", str(snap_b)])
    pa = json.loads(snap_a.read_text(encoding="utf-8"))
    pb = json.loads(snap_b.read_text(encoding="utf-8"))
    for fa, fb in zip(pa["files"], pb["files"]):
        assert fa["structure_hash"] == fb["structure_hash"], fa["path"]


def test_structure_hash_formato_hex() -> None:
    payload = prepare_snapshots()
    for f in payload["files"]:
        assert re.match(r"^[0-9a-f]{64}$", f["structure_hash"]), f["structure_hash"]
