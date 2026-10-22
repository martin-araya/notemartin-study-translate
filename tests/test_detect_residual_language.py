"""Pruebas de scripts/detect_residual_language.py (fase 126).

Verifica:

- Los segmentos con código inline y fenced no se marcan.
- Los términos ``preserve: true`` del glosario no se marcan.
- Texto en español puro produce 0 avisos.
- Cadenas inglesas ≥ 4 palabras consecutivas se marcan como
  ``warning``.
- Cadenas de 1-3 palabras sólo ``info``.
"""

from __future__ import annotations

import tempfile
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "detect_residual_language.py"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def _write_glossary(gp: Path, *, preserve_terms: list[str], domain_terms: list[str] | None = None) -> None:
    payload = {
        "version": 1,
        "frozen": True,
        "allowed_languages": ["es"],
        "domains": ["ui"],
        "entries": [
            {
                "id": f"g-{i}",
                "source_term": t,
                "domain": "ui",
                "sense": t,
                "preferred": {"term": t, "lang": "es"},
                "preservation_policy": "preserve",
                "context_examples": [],
                "justification": "test",
                "decided_by": "test",
                "decided_at": "2026-10-19T00:00:00Z",
            }
            for i, t in enumerate(preserve_terms)
        ],
    }
    gp.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_translation(td: Path, doc_id: str, entries: list[dict]) -> None:
    payload = {
        "document_id": doc_id,
        "path": f"{doc_id}.md",
        "source_hash": "a" * 64,
        "version": 1,
        "entries": entries,
    }
    td.mkdir(parents=True, exist_ok=True)
    (td / f"{doc_id}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _entry(seg_id: str, tr: str, structural_type: str = "paragraph") -> dict:
    return {
        "segment_id": seg_id,
        "structural_type": structural_type,
        "byte_range": {"start": 0, "end": len(tr)},
        "heading_path": [],
        "original_text": "",
        "translated_text": tr,
        "source_hash": "0" * 64,
        "candidate_hash": "0" * 64,
    }


def test_espanol_puro_sin_avisos() -> None:
    glossary = TMP / "det_g1.json"
    _write_glossary(glossary, preserve_terms=["render"])
    translations = TMP / "det_t1"
    _write_translation(
        translations,
        "doc-es",
        [_entry("seg-aaaa1111", "El estado de la aplicación está abierto.")],
    )
    out = TMP / "det_r1.json"
    proc = run([str(SCRIPT), "--translations", str(translations), "--glossary", str(glossary), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["warnings"] == 0 and payload["info"] == 0


def test_codigo_inline_no_se_marca() -> None:
    glossary = TMP / "det_g2.json"
    _write_glossary(glossary, preserve_terms=["render"])
    translations = TMP / "det_t2"
    _write_translation(
        translations,
        "doc-code",
        [_entry("seg-bbbb2222", "Usa `npm install` desde la terminal.", structural_type="paragraph")],
    )
    out = TMP / "det_r2.json"
    proc = run([str(SCRIPT), "--translations", str(translations), "--glossary", str(glossary), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    # El detector salta el contenido entre backticks.
    assert payload["warnings"] == 0


def test_termino_preservado_no_se_marca() -> None:
    glossary = TMP / "det_g3.json"
    _write_glossary(glossary, preserve_terms=["render"])
    translations = TMP / "det_t3"
    _write_translation(
        translations,
        "doc-pr",
        [_entry("seg-cccc3333", "Función render del componente padre.")],
    )
    out = TMP / "det_r3.json"
    proc = run([str(SCRIPT), "--translations", str(translations), "--glossary", str(glossary), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["warnings"] == 0, payload


def test_ingles_residual_4_palabras_es_warning() -> None:
    glossary = TMP / "det_g4.json"
    _write_glossary(glossary, preserve_terms=[])
    translations = TMP / "det_t4"
    _write_translation(
        translations,
        "doc-warn",
        [_entry("seg-dddd4444", "Note: the state machine must reset on failure recovery scenarios.")],
    )
    out = TMP / "det_r4.json"
    proc = run([str(SCRIPT), "--translations", str(translations), "--glossary", str(glossary), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["warnings"] >= 1
    detail = payload["signals"][0]
    assert detail["severity"] == "warning"
    assert "state machine" in detail["snippet"].lower() or "reset on" in detail["snippet"].lower()


def test_ingles_residual_1_palabra_es_info() -> None:
    glossary = TMP / "det_g5.json"
    _write_glossary(glossary, preserve_terms=[])
    translations = TMP / "det_t5"
    _write_translation(
        translations,
        "doc-info",
        [_entry("seg-eeee5555", "Reset the default.")],
    )
    out = TMP / "det_r5.json"
    proc = run([str(SCRIPT), "--translations", str(translations), "--glossary", str(glossary), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["warnings"] == 0
    assert payload["info"] >= 1


def test_prosa_tecnica_en_espanol_no_produce_avisos() -> None:
    """El defecto que el piloto dejó declarado.

    Con la heurística anterior, estas señales eran 273 avisos falsos: la
    salida del detector se descartó como evidencia porque no servía
    para nada.
    """
    glossary = TMP / "det_g7.json"
    _write_glossary(glossary, preserve_terms=[])
    translations = TMP / "det_t7"
    _write_translation(
        translations,
        "doc-es-tecnico",
        [
            _entry("seg-1111aaaa", "Los nodos, conexiones y tipos de componente se declaran en el modulo."),
            _entry("seg-2222bbbb", "Cada vista mantiene su estado local y se actualiza al cambiar los datos."),
            _entry("seg-3333cccc", "Los estilos heredan del contenedor padre segun la especificacion."),
        ],
    )
    out = TMP / "det_r7.json"
    proc = run([str(SCRIPT), "--translations", str(translations), "--glossary", str(glossary), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["warnings"] == 0, payload
    assert payload["info"] == 0, payload


def test_ingles_sin_palabra_funcional_tambien_se_detecta() -> None:
    glossary = TMP / "det_g8.json"
    _write_glossary(glossary, preserve_terms=[])
    translations = TMP / "det_t8"
    _write_translation(
        translations,
        "doc-lista",
        [_entry("seg-4444dddd", "Revise settings, templates, plugins y workers antes de empezar.")],
    )
    out = TMP / "det_r8.json"
    proc = run([str(SCRIPT), "--translations", str(translations), "--glossary", str(glossary), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["warnings"] + payload["info"] >= 1, payload


def test_no_modifica_archivos_de_traduccion() -> None:
    glossary = TMP / "det_g6.json"
    _write_glossary(glossary, preserve_terms=[])
    translations = TMP / "det_t6"
    _write_translation(
        translations,
        "doc-stay",
        [_entry("seg-ffff6666", "Texto en español sin avisos.")],
    )
    out = TMP / "det_r6.json"
    proc = run([str(SCRIPT), "--translations", str(translations), "--glossary", str(glossary), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr
    payload = json.loads((translations / "doc-stay.json").read_text(encoding="utf-8"))
    assert payload["entries"][0]["translated_text"] == "Texto en español sin avisos."
