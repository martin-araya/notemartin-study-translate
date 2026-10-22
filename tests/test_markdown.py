"""Pruebas de ensamblado round-trip (fase 020).

Verifica que ``scripts/assemble.py --identity`` recupera los bytes
originales de cada fixture al sustituir cada segmento por sí mismo.

Casos cubiertos:

- 9 fixtures del piloto: round-trip bit-exact.
- Fixture con codepoint multibyte al final del rango.
- Fixture con CRLF: preservado en la salida.
"""

from __future__ import annotations

import tempfile
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSEMBLE = ROOT / "scripts" / "assemble.py"
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


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def extract_segments_for(payload: dict, name: str) -> dict:
    for f in payload["files"]:
        if f["path"] == name:
            return f
    raise AssertionError(f"no se encontró {name}")


def test_round_trip_pilot() -> None:
    inv = TMP / "inv.json"
    segs_all = TMP / "segments.json"
    assert run([str(INVENTORY), "--source", str(PILOT), "--out", str(inv)]).returncode == 0
    assert run([str(PREPARE), "--inventory", str(inv), "--segments", str(segs_all)]).returncode == 0
    payload = json.loads(segs_all.read_text(encoding="utf-8"))

    for src in sorted(PILOT.glob("*.md")):
        doc = extract_segments_for(payload, src.name)
        single = TMP / f"single_{src.stem}.json"
        json.dump(doc, single.open("w", encoding="utf-8"), indent=2)
        out = TMP / f"out_{src.stem}.md"
        proc = run([
            str(ASSEMBLE),
            "--source", str(src),
            "--segments", str(single),
            "--out", str(out),
            "--identity",
        ])
        assert proc.returncode == 0, proc.stderr
        assert src.read_bytes() == out.read_bytes(), f"differ: {src.name}"


def test_round_trip_preserva_crlf(tmp_path: Path) -> None:
    text = "línea uno\r\nlínea dos\r\nlínea tres\r\n"
    src = tmp_path / "crlf.md"
    write_bytes(src, text.encode("utf-8"))
    inv = TMP / "inv_crlf.json"
    segs = TMP / "seg_crlf.json"
    single = TMP / "single_crlf.json"
    out = TMP / "out_crlf.md"
    assert run([str(INVENTORY), "--source", str(tmp_path), "--out", str(inv)]).returncode == 0
    assert run([str(PREPARE), "--inventory", str(inv), "--segments", str(segs)]).returncode == 0
    payload = json.loads(segs.read_text(encoding="utf-8"))
    json.dump(payload["files"][0], single.open("w", encoding="utf-8"), indent=2)
    proc = run([str(ASSEMBLE), "--source", str(src), "--segments", str(single), "--out", str(out), "--identity"])
    assert proc.returncode == 0, proc.stderr
    assert out.read_bytes() == text.encode("utf-8")
    assert b"\r\n" in out.read_bytes()


def test_round_trip_preserva_codepoint_multibyte(tmp_path: Path) -> None:
    text = "# Título\n\nCafé con ñandú y زائدة.\n"
    src = tmp_path / "multi.md"
    write_bytes(src, text.encode("utf-8"))
    inv = TMP / "inv_multi.json"
    segs = TMP / "seg_multi.json"
    single = TMP / "single_multi.json"
    out = TMP / "out_multi.md"
    assert run([str(INVENTORY), "--source", str(tmp_path), "--out", str(inv)]).returncode == 0
    assert run([str(PREPARE), "--inventory", str(inv), "--segments", str(segs)]).returncode == 0
    payload = json.loads(segs.read_text(encoding="utf-8"))
    json.dump(payload["files"][0], single.open("w", encoding="utf-8"), indent=2)
    proc = run([str(ASSEMBLE), "--source", str(src), "--segments", str(single), "--out", str(out), "--identity"])
    assert proc.returncode == 0, proc.stderr
    assert hashlib.sha256(out.read_bytes()).hexdigest() == hashlib.sha256(text.encode("utf-8")).hexdigest()
