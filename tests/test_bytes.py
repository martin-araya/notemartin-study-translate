"""Pruebas de lectura exacta de bytes.

Cubre:
- Hash SHA-256 sobre bytes UTF-8 con tildes.
- Hash sin normalización silenciosa sobre CRLF, LF y mezcla.
- Detección de codificación inválida sin reemplazo.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

INVENTORY = Path(__file__).resolve().parent.parent / "scripts" / "inventory.py"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(INVENTORY), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def inventory_of(root: Path) -> dict:
    out = root / "inv.json"
    proc = run(["--source", str(root), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr
    return json.loads(out.read_text(encoding="utf-8"))


def entry(payload: dict, name: str) -> dict:
    for e in payload["files"]:
        if e["path"] == name:
            return e
    raise AssertionError(f"no se encontró {name}")


def test_hash_con_tildes_coincide_con_hashlib(tmp_path: Path) -> None:
    text = "# Título con tildes: á é í ó ú ñ ü ¿¡\n"
    write_bytes(tmp_path / "tildes.md", text.encode("utf-8"))
    payload = inventory_of(tmp_path)
    e = entry(payload, "tildes.md")
    assert e["sha256"] == hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert e["encoding"] == "utf-8"


def test_crlf_preservado(tmp_path: Path) -> None:
    text = "línea uno\r\nlínea dos\r\n"
    write_bytes(tmp_path / "crlf.md", text.encode("utf-8"))
    payload = inventory_of(tmp_path)
    e = entry(payload, "crlf.md")
    assert e["line_ending"] == "crlf"
    assert e["bytes"] == len(text.encode("utf-8"))


def test_lf_preservado(tmp_path: Path) -> None:
    text = "línea uno\nlínea dos\n"
    write_bytes(tmp_path / "lf.md", text.encode("utf-8"))
    payload = inventory_of(tmp_path)
    e = entry(payload, "lf.md")
    assert e["line_ending"] == "lf"
    assert e["bytes"] == len(text.encode("utf-8"))


def test_mezcla_detectada(tmp_path: Path) -> None:
    text = "uno\r\ndos\ntres\r\n"
    write_bytes(tmp_path / "mix.md", text.encode("utf-8"))
    payload = inventory_of(tmp_path)
    e = entry(payload, "mix.md")
    assert e["line_ending"] == "mixed"


def test_secuencia_utf8_invalida_detectada(tmp_path: Path) -> None:
    data = b"# ok\n\xc3\x28mal\n"
    write_bytes(tmp_path / "bad.md", data)
    payload = inventory_of(tmp_path)
    e = entry(payload, "bad.md")
    assert e["encoding"] == "binary"
    assert "encoding_error" in e


def test_no_normaliza_nfc_nfd(tmp_path: Path) -> None:
    composed = "café\n"
    decomposed = "cafe\u0301\n"
    write_bytes(tmp_path / "nfc.md", composed.encode("utf-8"))
    write_bytes(tmp_path / "nfd.md", decomposed.encode("utf-8"))
    payload = inventory_of(tmp_path)
    nfc = entry(payload, "nfc.md")
    nfd = entry(payload, "nfd.md")
    assert nfc["sha256"] != nfd["sha256"]
    assert nfc["bytes"] == len(composed.encode("utf-8"))
    assert nfd["bytes"] == len(decomposed.encode("utf-8"))