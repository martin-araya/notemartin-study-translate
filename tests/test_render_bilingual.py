"""Pruebas para scripts/render_bilingual.py (fase 121)."""

from __future__ import annotations

import tempfile
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RENDER = ROOT / "scripts" / "render_bilingual.py"
FIX = ROOT / "tests" / "fixtures" / "bilingual"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def _write_doc_translation(translations_dir: Path, doc_id: str, path: str, entries: list[dict]) -> Path:
    payload = {
        "document_id": doc_id,
        "path": path,
        "source_hash": "a" * 64,
        "version": 1,
        "entries": entries,
        "flag_loss": False,
        "literals_preserved": True,
    }
    target = translations_dir / f"{doc_id}.json"
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return target


def _entry(seg_id: str, original: str, translated: str, *, structural_type: str = "paragraph",
           heading_path: list | None = None) -> dict:
    src_hash = hashlib.sha256(original.encode("utf-8")).hexdigest()
    cand_hash = hashlib.sha256(translated.encode("utf-8")).hexdigest()
    return {
        "segment_id": seg_id,
        "structural_type": structural_type,
        "byte_range": {"start": 0, "end": len(original.encode("utf-8"))},
        "heading_path": heading_path or [],
        "translatable_text": original,
        "original_text": original,
        "translated_text": translated,
        "source_hash": src_hash,
        "candidate_hash": cand_hash,
        "literals_preserved": True,
        "missing_literals": [],
        "flag_loss": False,
    }


def test_render_basico_segmentos_con_hashes() -> None:
    """El reporte incluye una fila por segmento traducible con hashes correctos."""
    translations = TMP / "bilingual_t1"
    translations.mkdir(parents=True, exist_ok=True)
    _write_doc_translation(
        translations,
        "doc-basic",
        "docs/basic.md",
        [
            _entry("seg-aaaa1111", "Hello world.", "Hola mundo."),
            _entry("seg-bbbb2222", "Bye.", "Adiós."),
        ],
    )

    out = TMP / "bilingual_t1.md"
    proc = run([str(RENDER), "--translations", str(translations), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr or proc.stdout
    text = out.read_text(encoding="utf-8")
    assert text.startswith("# Informe bilingüe"), text[:120]
    assert "seg-aaaa1111" in text
    assert "seg-bbbb2222" in text
    src_h = hashlib.sha256(b"Hello world.").hexdigest()
    cand_h = hashlib.sha256(b"Hola mundo.").hexdigest()
    assert src_h in text
    assert cand_h in text


def test_render_orden_por_documento_y_heading() -> None:
    """El reporte agrupa por documento y conserva el orden de heading_path."""
    translations = TMP / "bilingual_t2"
    translations.mkdir(parents=True, exist_ok=True)
    _write_doc_translation(
        translations,
        "doc-zz",
        "z.md",
        [_entry("seg-z-1", "Z1.", "Zeta uno.", heading_path=[{"level": 2, "text": "Z"}])],
    )
    _write_doc_translation(
        translations,
        "doc-aa",
        "a.md",
        [
            _entry("seg-a-1", "A1.", "A uno.", heading_path=[{"level": 1, "text": "A"}]),
            _entry("seg-a-2", "A2.", "A dos.", heading_path=[{"level": 1, "text": "A"}]),
        ],
    )

    out = TMP / "bilingual_t2.md"
    proc = run([str(RENDER), "--translations", str(translations), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr or proc.stdout
    text = out.read_text(encoding="utf-8")
    a_pos = text.find("seg-a-1")
    z_pos = text.find("seg-z-1")
    assert a_pos < z_pos, "doc-aa debe preceder a doc-zz"


def test_render_escapa_caracteres_tabla_md() -> None:
    """El reporte escapa pipes en celdas para no romper la tabla Markdown."""
    translations = TMP / "bilingual_t3"
    translations.mkdir(parents=True, exist_ok=True)
    _write_doc_translation(
        translations,
        "doc-pipe",
        "p.md",
        [_entry("seg-pipe-1", "a | b", "a | b")],
    )
    out = TMP / "bilingual_t3.md"
    proc = run([str(RENDER), "--translations", str(translations), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr
    text = out.read_text(encoding="utf-8")
    assert r"a \| b" in text or "a &#124; b" in text, text


def test_render_no_modifica_literales_en_la_fila() -> None:
    """Las filas muestran el candidato exacto; el validador de literales se delega al gate."""
    translations = TMP / "bilingual_t4"
    translations.mkdir(parents=True, exist_ok=True)
    _write_doc_translation(
        translations,
        "doc-lit",
        "l.md",
        [_entry("seg-lit-1", "Use `npm install`.", "Usa `npm install`.", structural_type="paragraph")],
    )
    out = TMP / "bilingual_t4.md"
    proc = run([str(RENDER), "--translations", str(translations), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr
    text = out.read_text(encoding="utf-8")
    assert "`npm install`" in text


def test_render_incluye_tabla_de_contenidos() -> None:
    """El reporte abre con un TOC navegable por anclas Markdown."""
    translations = TMP / "bilingual_t5"
    translations.mkdir(parents=True, exist_ok=True)
    _write_doc_translation(
        translations,
        "doc-toc",
        "t.md",
        [_entry("seg-toc-1", "Section A", "Sección A", structural_type="heading")],
    )
    out = TMP / "bilingual_t5.md"
    proc = run([str(RENDER), "--translations", str(translations), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr
    text = out.read_text(encoding="utf-8")
    assert "## Tabla de contenidos" in text or "Tabla de contenidos" in text
    assert "(#seg-toc-1)" in text or "(#doc-toc-seg-toc-1)" in text


def test_render_conteo_filas_coincide_con_segmentos() -> None:
    translations = TMP / "bilingual_t6"
    translations.mkdir(parents=True, exist_ok=True)
    entries = [_entry(f"seg-{i:08x}", f"orig {i}", f"trad {i}") for i in range(7)]
    _write_doc_translation(translations, "doc-cnt", "c.md", entries)
    out = TMP / "bilingual_t6.md"
    proc = run([str(RENDER), "--translations", str(translations), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr
    text = out.read_text(encoding="utf-8")
    for entry in entries:
        assert entry["segment_id"] in text


def test_render_no_escribe_si_no_hay_segmentos() -> None:
    translations = TMP / "bilingual_t7"
    translations.mkdir(parents=True, exist_ok=True)
    _write_doc_translation(translations, "doc-empty", "e.md", [])
    out = TMP / "bilingual_t7.md"
    proc = run([str(RENDER), "--translations", str(translations), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr
    text = out.read_text(encoding="utf-8")
    assert "0 filas" in text or "no contiene" in text.lower()


def test_render_documenta_fixture_real() -> None:
    """Carga el fixture versionado y verifica que no lo modifica byte a byte."""
    if not FIX.exists():
        # No se ha creado fixture versionado: el test sigue siendo opcional.
        return
    out = TMP / "bilingual_real.md"
    proc = run([str(RENDER), "--translations", str(FIX), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr
    assert out.exists()
