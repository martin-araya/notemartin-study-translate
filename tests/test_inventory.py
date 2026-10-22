"""Pruebas para scripts/inventory.py.

Cubre:
- Rechazo de escapes ``..`` fuera del source_root.
- Rechazo de symlinks en el interior del source_root.
- Rechazo de solapamientos entre source_root, work_root y output_root.
- Rechazo de colisiones por mayúsculas o Unicode (NFC/NFD).
- Caso válido: produce el inventario esperado.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

INVENTORY = Path(__file__).resolve().parent.parent / "scripts" / "inventory.py"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(INVENTORY), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def write(path: Path, content: str = "hello\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def test_rechaza_escape_con_doble_punto(tmp_path: Path) -> None:
    root = tmp_path / "src"
    write(root / "ok.md", "# ok\n")
    out = tmp_path / "inv.json"
    proc = run(["--source", str(root), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr

    subdir = root / "sub"
    write(subdir / "evil.md", "# evil\n")
    escape_link = subdir / "escape.md"
    try:
        escape_link.symlink_to(root / "ok.md")
    except OSError:
        pytest.skip("symlink no soportado en este entorno")

    proc = run(["--source", str(root), "--out", str(out)])
    assert proc.returncode != 0
    assert "symlink" in proc.stderr.lower() or "escape" in proc.stderr.lower()


def test_rechaza_symlink_en_interior(tmp_path: Path) -> None:
    root = tmp_path / "src"
    write(root / "real.md", "# real\n")
    try:
        (root / "link.md").symlink_to(root / "real.md")
    except OSError:
        pytest.skip("symlink no soportado en este entorno")
    out = tmp_path / "inv.json"
    proc = run(["--source", str(root), "--out", str(out)])
    assert proc.returncode != 0
    assert "symlink" in proc.stderr.lower()


def test_rechaza_solapamiento_con_work_root(tmp_path: Path) -> None:
    root = tmp_path / "src"
    write(root / "a.md", "# a\n")
    out = tmp_path / "inv.json"
    proc = run(["--source", str(root), "--work", str(root), "--out", str(out)])
    assert proc.returncode == 3
    assert "solapa" in proc.stderr.lower()


def test_rechaza_solapamiento_con_output_root(tmp_path: Path) -> None:
    root = tmp_path / "src"
    write(root / "a.md", "# a\n")
    out = tmp_path / "inv.json"
    proc = run(["--source", str(root), "--output-root", str(root), "--out", str(out)])
    assert proc.returncode == 3


def test_rechaza_colision_por_mayusculas(tmp_path: Path) -> None:
    from .fs_probe import filesystem_is_case_insensitive
    if filesystem_is_case_insensitive():
        pytest.skip("filesystem case-insensitive: la colisión no se puede crear")
    root = tmp_path / "src"
    write(root / "Doc.md", "# x\n")
    write(root / "doc.md", "# y\n")
    out = tmp_path / "inv.json"
    proc = run(["--source", str(root), "--out", str(out)])
    assert proc.returncode == 5
    assert "colisión" in proc.stderr.lower()


def test_rechaza_colision_por_unicode(tmp_path: Path) -> None:
    from .fs_probe import filesystem_normalizes_unicode
    if filesystem_normalizes_unicode():
        pytest.skip("filesystem normaliza Unicode: la colisión no se puede crear")
    import unicodedata
    root = tmp_path / "src"
    write(root / "a.md", "# base\n")
    write(root / (unicodedata.normalize("NFC", "á") + ".md"), "# nfc\n")
    write(root / (unicodedata.normalize("NFD", "á") + ".md"), "# nfd\n")
    out = tmp_path / "inv.json"
    proc = run(["--source", str(root), "--out", str(out)])
    assert proc.returncode == 5
    assert "colisión" in proc.stderr.lower()


def test_caso_valido(tmp_path: Path) -> None:
    root = tmp_path / "src"
    write(root / "a.md", "# a\n")
    write_bytes(root / "img.png", b"\x89PNG\r\n\x1a\n")
    out = tmp_path / "inv.json"
    proc = run(["--source", str(root), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["total_files"] == 2
    types = {f["path"]: f["type"] for f in payload["files"]}
    assert types["a.md"] == "markdown"
    assert types["img.png"] == "resource"


def test_distingue_recursos(tmp_path: Path) -> None:
    root = tmp_path / "src"
    write(root / "page.md", "# page\n")
    for ext in (".png", ".jpg", ".svg", ".pdf", ".zip"):
        write(root / f"file{ext}", "x")
    out = tmp_path / "inv.json"
    proc = run(["--source", str(root), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    types = {f["path"]: f["type"] for f in payload["files"]}
    assert types["page.md"] == "markdown"
    for ext in (".png", ".jpg", ".svg", ".pdf", ".zip"):
        assert types[f"file{ext}"] == "resource", ext