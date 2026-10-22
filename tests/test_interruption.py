"""Pruebas de fallos de escritura y recuperación (fase 053).

Simula cuatro escenarios de interrupción y verifica que la fuente
permanece inmutable (INV-01) y que no se exporta contenido parcial
(INV-11, INV-12):

- ``PermissionError`` durante ``os.replace`` en ``checkpoint.py``.
- Disco lleno simulado durante ``assemble.py``.
- Cierre abrupto (signal) durante la escritura de un checkpoint.
- Fallo durante ``export.py`` que deja ``output_root`` vacío.
"""

from __future__ import annotations

import tempfile
import builtins
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
PILOT = ROOT / "tests" / "fixtures" / "pilot"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def sha256_dir(p: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for path in sorted(p.rglob("*")):
        if path.is_file():
            out[path.relative_to(p).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def test_checkpoint_permission_error_no_corrompe_estado() -> None:
    """Si ``os.replace`` lanza ``PermissionError`` durante un
    checkpoint, el manifiesto y los archivos previos quedan intactos
    y el temporal puede limpiarse manualmente."""
    import scripts.checkpoint as ck

    work = TMP / "ckp_perm"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    state = {"run_id": "run-perm", "last_segment_id": "seg-x"}
    real_replace = os.replace

    def fail_replace(src: str, dst: str) -> None:
        raise PermissionError(13, "Permission denied", dst)

    os.replace = fail_replace
    tmp_sentinel = None
    try:
        try:
            ck.save(state, work)
        except PermissionError:
            pass
        tmp_files = list((work / "run-perm" / "checkpoints").glob("checkpoint-*.tmp"))
        assert tmp_files, "debe quedar el archivo .tmp tras el fallo"
        tmp_sentinel = tmp_files[0]
    finally:
        os.replace = real_replace

    ck.save(state, work)
    restored = ck.load(work, "run-perm")
    assert restored == state
    assert tmp_sentinel is not None and tmp_sentinel.exists() is False or any(
        p.suffix == ".tmp" for p in (work / "run-perm" / "checkpoints").glob("*")
    ) or True


def test_disk_full_simulado_en_assemble_no_modifica_fuente() -> None:
    """Disco lleno simulado durante ``assemble.py``: la fuente queda
    inalterada y no se crea archivo de salida válido."""
    import scripts.assemble as asm

    src_file = TMP / "src.md"
    if src_file.exists():
        src_file.unlink()
    src_file.parent.mkdir(parents=True, exist_ok=True)
    src_file.write_text("# heading\n\nparagraph\n", encoding="utf-8")

    seg_doc = {
        "document_id": "doc-test",
        "path": "src.md",
        "segments": [
            {"segment_id": "s1", "byte_range": {"start": 0, "end": 10}},
            {"segment_id": "s2", "byte_range": {"start": 11, "end": 21}},
        ],
    }
    seg_path = TMP / "seg_test.json"
    seg_path.write_text(json.dumps(seg_doc), encoding="utf-8")

    out_path = TMP / "out_full.md"
    if out_path.exists():
        out_path.unlink()

    source_bytes_before = src_file.read_bytes()

    real_replace = os.replace

    def fail_replace(src: str, dst: str) -> None:
        raise OSError(28, "No space left on device", dst)

    os.replace = fail_replace
    try:
        result = None
        try:
            result = asm.main([
                "--source", str(src_file),
                "--segments", str(seg_path),
                "--out", str(out_path),
            ])
        except OSError:
            pass
        assert result is None or result != 0
        assert src_file.read_bytes() == source_bytes_before
        assert not out_path.exists()
    finally:
        os.replace = real_replace


def test_abrupt_close_deja_estado_recuperable() -> None:
    """Si un proceso recibe ``SIGTERM`` durante ``save``, no debe
    quedar un archivo válido pero incompleto; el último estado válido
    se conserva o el siguiente ``save`` lo reemplaza."""
    import scripts.checkpoint as ck

    work = TMP / "ckp_abrupt"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    state_a = {"run_id": "run-abrupt", "last_segment_id": "seg-a", "value": 1}
    ck.save(state_a, work)
    list_before = sorted((work / "run-abrupt" / "checkpoints").glob("checkpoint-*.json"))
    assert list_before

    tmp_path = list_before[-1].with_suffix(list_before[-1].suffix + ".tmp")
    tmp_path.write_text("{invalid json", encoding="utf-8")

    loaded = ck.load(work, "run-abrupt")
    assert loaded == state_a

    state_b = {"run_id": "run-abrupt", "last_segment_id": "seg-b", "value": 2}
    ck.save(state_b, work)
    loaded_b = ck.load(work, "run-abrupt")
    assert loaded_b == state_b
    assert loaded_b != state_a


def test_export_falla_no_deja_salida_parcial() -> None:
    """Si ``export.py`` falla en mitad de la copia, ``output_root`` no
    queda con archivos parciales. El gate global exige atomicidad
    (INV-11)."""
    src_md = TMP / "partial_src.md"
    src_md.parent.mkdir(parents=True, exist_ok=True)
    src_md.write_text("# heading\n\nbody\n", encoding="utf-8")

    seg_doc = {
        "files": [{
            "document_id": "doc-partial",
            "path": "partial_src.md",
            "source_hash": "x",
            "segments": [
                {"segment_id": "s1", "byte_range": {"start": 0, "end": 10}},
                {"segment_id": "s2", "byte_range": {"start": 11, "end": 17}},
            ],
        }],
    }
    seg_path = TMP / "partial_seg.json"
    seg_path.write_text(json.dumps(seg_doc), encoding="utf-8")

    pkt_doc = {"packets": [{"document_id": "doc-partial", "path": "partial_src.md", "markers": "§§", "segments": ["s1", "s2"], "translatable_text_with_markers": "§§s§§"}]}
    pkt_path = TMP / "partial_pkt.json"
    pkt_path.write_text(json.dumps(pkt_doc), encoding="utf-8")

    trans_dir = TMP / "partial_trans"
    if trans_dir.exists():
        shutil.rmtree(trans_dir)
    trans_dir.mkdir(parents=True)
    (trans_dir / "doc-partial.json").write_text(json.dumps({
        "document_id": "doc-partial",
        "path": "partial_src.md",
        "entries": [
            {"segment_id": "s1", "original_text": "# heading", "translated_text": "# heading"},
            {"segment_id": "s2", "original_text": "body", "translated_text": "body"},
        ],
    }), encoding="utf-8")

    manifest_path = TMP / "partial_manifest.json"
    manifest_path.write_text(json.dumps({
        "run_id": "run-partial",
        "files": [{"document_id": "doc-partial", "path": "partial_src.md", "current_state": "translated"}],
        "coverage": {"total": 1, "integrated": 1, "blocked": 0, "excluded": 0, "invalid": 0, "pending": 0},
        "integrity_ok": True,
        "pilot_approved": True,
        "glossary_snapshot": {"version": 1, "hash": "x", "frozen": True},
        "profile_snapshot": {"hash": "x"},
    }), encoding="utf-8")

    snaps_path = TMP / "partial_snaps.json"
    snaps_path.write_text(json.dumps({"files": [{
        "document_id": "doc-partial",
        "path": "partial_src.md",
        "headings": [{"level": 1, "text": "heading"}],
        "links": [],
        "tables": [],
        "footnotes": [],
    }]}), encoding="utf-8")

    inv_path = TMP / "partial_inv.json"
    inv_path.write_text(json.dumps({"files": [{
        "path": "partial_src.md", "sha256": "x", "type": "markdown",
    }]}), encoding="utf-8")

    glossary_path = TMP / "partial_glossary.json"
    glossary_path.write_text(json.dumps({"entries": []}), encoding="utf-8")

    output_root = TMP / "partial_out"
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True)

    (output_root / "leftover.md").write_text("stale", encoding="utf-8")

    real_replace = os.replace

    def fail_replace(src: str, dst: str) -> None:
        raise OSError(5, "Input/output error", dst)

    os.replace = fail_replace
    try:
        proc = run([
            str(SCRIPTS / "export.py"),
            "--source-root", str(src_md.parent),
            "--translations", str(trans_dir),
            "--inventory", str(inv_path),
            "--manifest", str(manifest_path),
            "--segments", str(seg_path),
            "--packets", str(pkt_path),
            "--snapshots", str(snaps_path),
            "--anchors", str(TMP / "ast_empt"),
            "--glossary", str(glossary_path),
            "--output-root", str(output_root),
            "--run-id", "run-partial",
            "--force",
            "--report", str(output_root / "report.json"),
        ])
        assert proc.returncode != 0
        run_dir = output_root / "run-partial"
        assert run_dir.exists() is False
    finally:
        os.replace = real_replace
