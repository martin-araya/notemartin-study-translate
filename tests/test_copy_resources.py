"""Pruebas para scripts/copy_resources.py (fase 046)."""

from __future__ import annotations

import tempfile
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INVENTORY = ROOT / "scripts" / "inventory.py"
COPY_RES = ROOT / "scripts" / "copy_resources.py"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def write_bytes(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        path.write_text(data, encoding="utf-8")
    else:
        path.write_bytes(data)


def make_source_with_png(src: Path) -> None:
    png = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
        "0000000d49444154789c63000100000005000100000008020000edce9d4f0000000049454e44ae426082"
    )
    write_bytes(src / "img" / "logo.png", png)
    write_bytes(src / "doc.md", "# Title\n\n![logo](img/logo.png)\n")


def make_inventory(src: Path, inv_path: Path) -> None:
    assert run([str(INVENTORY), "--source", str(src), "--out", str(inv_path)]).returncode == 0


def test_recurso_png_copiado_con_hash_identico() -> None:
    src = TMP / "cp_src1"
    out = TMP / "cp_out1"
    inv = TMP / "cp_inv1.json"
    if src.exists():
        shutil.rmtree(src)
    src.mkdir()
    if out.exists():
        shutil.rmtree(out)
    make_source_with_png(src)
    make_inventory(src, inv)
    report = TMP / "cp_report1.json"
    proc = run([str(COPY_RES), "--inventory", str(inv), "--source-root", str(src), "--output-root", str(out), "--report", str(report)])
    assert proc.returncode == 0, proc.stderr
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["summary"]["copied"] >= 1
    assert data["summary"]["mismatches"] == 0
    assert (out / "img" / "logo.png").exists()
    original = (src / "img" / "logo.png").read_bytes()
    copied = (out / "img" / "logo.png").read_bytes()
    assert hashlib.sha256(copied).hexdigest() == hashlib.sha256(original).hexdigest()


def test_hash_mismatch_se_detecta() -> None:
    src = TMP / "cp_src2"
    out = TMP / "cp_out2"
    inv = TMP / "cp_inv2.json"
    if src.exists():
        shutil.rmtree(src)
    src.mkdir()
    if out.exists():
        shutil.rmtree(out)
    make_source_with_png(src)
    make_inventory(src, inv)
    inv_data = json.loads(inv.read_text(encoding="utf-8"))
    for entry in inv_data["files"]:
        if entry["path"].endswith(".png"):
            entry["sha256"] = "0" * 64
    inv.write_text(json.dumps(inv_data, indent=2), encoding="utf-8")
    report = TMP / "cp_report2.json"
    proc = run([str(COPY_RES), "--inventory", str(inv), "--source-root", str(src), "--output-root", str(out), "--report", str(report)])
    assert proc.returncode != 0
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["summary"]["mismatches"] >= 1


def test_recurso_externo_se_registra_sin_copiarse() -> None:
    src = TMP / "cp_src3"
    out = TMP / "cp_out3"
    inv = TMP / "cp_inv3.json"
    if src.exists():
        shutil.rmtree(src)
    src.mkdir()
    if out.exists():
        shutil.rmtree(out)
    write_bytes(src / "doc.md", "# Title\n\n[remote](https://example.com/logo.png)\n")
    make_inventory(src, inv)
    inv_data = json.loads(inv.read_text(encoding="utf-8"))
    inv_data["files"].append({
        "path": "https://example.com/logo.png",
        "bytes": 100,
        "sha256": "x" * 64,
        "encoding": "binary",
        "line_ending": "lf",
        "type": "resource",
        "flag_mdx": False,
    })
    inv.write_text(json.dumps(inv_data, indent=2), encoding="utf-8")
    report = TMP / "cp_report3.json"
    proc = run([str(COPY_RES), "--inventory", str(inv), "--source-root", str(src), "--output-root", str(out), "--report", str(report)])
    assert proc.returncode == 0
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["summary"]["external"] >= 1
    assert data["summary"]["copied"] == 0


def test_recurso_ausente_se_reporta() -> None:
    src = TMP / "cp_src4"
    out = TMP / "cp_out4"
    inv = TMP / "cp_inv4.json"
    if src.exists():
        shutil.rmtree(src)
    src.mkdir()
    if out.exists():
        shutil.rmtree(out)
    write_bytes(src / "doc.md", "# Title\n")
    make_inventory(src, inv)
    inv_data = json.loads(inv.read_text(encoding="utf-8"))
    inv_data["files"].append({
        "path": "missing/file.png",
        "bytes": 0,
        "sha256": "x" * 64,
        "encoding": "binary",
        "line_ending": "lf",
        "type": "resource",
        "flag_mdx": False,
    })
    inv.write_text(json.dumps(inv_data, indent=2), encoding="utf-8")
    report = TMP / "cp_report4.json"
    proc = run([str(COPY_RES), "--inventory", str(inv), "--source-root", str(src), "--output-root", str(out), "--report", str(report)])
    assert proc.returncode != 0
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["summary"]["missing"] >= 1
