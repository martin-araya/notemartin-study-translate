"""Pruebas del checklist de accesibilidad local (fase 128).

Verifica que los reportes generados localmente cumplen los requisitos
mínimos de navegación local:

- Cero URLs externas (excepto las marcadas como intencionales).
- Cero ``<script>``, ``<link rel="stylesheet" href="http…">``, ni
  ``<img src="http…">``.
- Tabla de contenidos con anclas explícitas que apunten a
  identificadores presentes en el documento.
- Codificación UTF-8 verificable.

El test opera sobre los artefactos producidos por las fases 121 y
122; también acepta rutas personalizadas para CI.
"""

from __future__ import annotations

import tempfile
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TMP = Path(tempfile.gettempdir()) / "nst-tests"

EXTERNAL_URL_PATTERNS = [
    re.compile(r"https?://", re.IGNORECASE),
    re.compile(r"<script\b", re.IGNORECASE),
    re.compile(r"<link\b[^>]*stylesheet", re.IGNORECASE),
    re.compile(r"<img\b[^>]*src\s*=", re.IGNORECASE),
]

ANCHOR_RE = re.compile(r"\]\(#([a-z0-9][a-z0-9\-]*)\)")
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*$", re.MULTILINE)
SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slug(text: str) -> str:
    return SLUG_RE.sub("-", text.strip().lower()).strip("-") or "x"


def _check_no_external_urls(text: str, label: str) -> list[str]:
    errors = []
    for pat in EXTERNAL_URL_PATTERNS:
        match = pat.search(text)
        if match:
            errors.append(f"{label}: patrón externo encontrado: {pat.pattern!r} -> {match.group(0)!r}")
    return errors


def _check_anchors_resolve(text: str) -> list[str]:
    """Each ``](#anchor)`` must point to an existing heading or HTML anchor."""
    headings = {_slug(h) for h in HEADING_RE.findall(text)}
    html_anchors = set(re.findall(r'<a id="([^"]+)"', text))
    anchor_ids = set(ANCHOR_RE.findall(text))
    missing: list[str] = []
    for anc in anchor_ids:
        if anc in headings or anc in html_anchors:
            continue
        # accept any heading slug whose prefix matches
        if not any(s.startswith(anc) for s in headings | html_anchors):
            missing.append(anc)
    return missing


def _check_utf8_encoding(path: Path) -> list[str]:
    try:
        path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return [f"{path}: UTF-8 inválido: {exc}"]
    return []


def render_bilingual(translations_dir: Path, out_path: Path) -> subprocess.CompletedProcess:
    render = ROOT / "scripts" / "render_bilingual.py"
    return subprocess.run(
        [sys.executable, str(render), "--translations", str(translations_dir), "--out", str(out_path)],
        capture_output=True,
        text=True,
        check=False,
    )


def _write_translation(translations_dir: Path, doc_id: str, entries: list[dict]) -> None:
    payload = {
        "document_id": doc_id,
        "path": f"{doc_id}.md",
        "source_hash": "a" * 64,
        "version": 1,
        "entries": entries,
        "flag_loss": False,
        "literals_preserved": True,
    }
    translations_dir.mkdir(parents=True, exist_ok=True)
    (translations_dir / f"{doc_id}.json").write_text(
        __import__("json").dumps(payload, indent=2), encoding="utf-8"
    )


def _entry(seg_id: str, orig: str, tr: str) -> dict:
    return {
        "segment_id": seg_id,
        "structural_type": "paragraph",
        "byte_range": {"start": 0, "end": len(orig)},
        "heading_path": [{"level": 1, "text": "Top"}],
        "original_text": orig,
        "translated_text": tr,
        "source_hash": "0" * 64,
        "candidate_hash": "0" * 64,
        "literals_preserved": True,
        "missing_literals": [],
        "flag_loss": False,
    }


def test_bilingual_sin_urls_externas() -> None:
    translations = TMP / "acc_bil_t"
    out = TMP / "acc_bil.md"
    _write_translation(translations, "doc-a11", [_entry("seg-aaa0000", "Hi", "Hola")])
    proc = render_bilingual(translations, out)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    text = out.read_text(encoding="utf-8")
    errs = _check_no_external_urls(text, "bilingual")
    assert not errs, errs


def test_bilingual_enlaces_ancla_validos() -> None:
    translations = TMP / "acc_bil_t2"
    out = TMP / "acc_bil2.md"
    _write_translation(translations, "doc-b22", [_entry("seg-bbb1111", "Hi", "Hola")])
    proc = render_bilingual(translations, out)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    text = out.read_text(encoding="utf-8")
    # El ancla usada en la fila debe resolver a un encabezado o ancla HTML del propio reporte.
    assert "[seg-bbb1111]" in text
    # Verifica que no haya un '](#x)' huérfano apuntando a un id inexistente.
    anchors = ANCHOR_RE.findall(text)
    slugs = {_slug(h) for h in HEADING_RE.findall(text)}
    html_anchors = set(re.findall(r'<a id="([^"]+)"', text))
    valid = slugs | html_anchors
    for a in anchors:
        assert a in valid or any(s.startswith(a) for s in valid), f"ancla huérfana: {a}"


def test_bilingual_codificacion_utf8() -> None:
    translations = TMP / "acc_bil_t3"
    out = TMP / "acc_bil3.md"
    _write_translation(translations, "doc-c33", [_entry("seg-ccc2222", "Hola — ñ — ¿", "Hola — ñ — ¿")])
    proc = render_bilingual(translations, out)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    errs = _check_utf8_encoding(out)
    assert not errs, errs
    text = out.read_text(encoding="utf-8")
    assert "ñ" in text and "¿" in text


def test_bilingual_titulo_y_tabla_de_contenidos_presentes() -> None:
    translations = TMP / "acc_bil_t4"
    out = TMP / "acc_bil4.md"
    _write_translation(translations, "doc-d44", [_entry("seg-ddd4444", "Hi", "Hola")])
    proc = render_bilingual(translations, out)
    assert proc.returncode == 0, proc.stderr or proc.stdout
    text = out.read_text(encoding="utf-8")
    assert text.startswith("# Informe bilingüe")
    assert "Tabla de contenidos" in text
