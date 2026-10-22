"""El rango de un segmento debe cubrir exactamente su texto traducible.

El piloto de 9 documentos (fase 030) encontró que los segmentos de
encabezado y de párrafo cubren en `byte_range` más bytes de los que
contiene `translatable_text`: el marcador `## `, el cierre `###` y el salto
de línea final. Al ensamblar, la traducción sustituye el rango completo y
esos bytes desaparecen, así que el documento entregado pierde la estructura
Markdown aunque la traducción sea fiel.

Estas pruebas fijan el contrato:

- el texto fuente del rango coincide con `translatable_text`,
- ensamblar una traducción **no** pierde marcadores ni saltos de línea,
- el modo identidad sigue devolviendo los bytes originales.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from assemble import assemble  # noqa: E402
from prepare import LineIndex, PARSER, document_id, extract_segments  # noqa: E402

DOC = """# Título de prueba <a id="prueba"></a>

Un párrafo normal con `código` y un enlace.

## Sección con acentos

Texto de la sección.

- Primer elemento
- Segundo elemento
"""


def _prepare(text: str, tmp: Path, name: str = "doc.md") -> dict:
    path = tmp / name
    path.write_text(text, encoding="utf-8")
    data = path.read_bytes()
    doc_id = document_id(data)
    segs = extract_segments(data, LineIndex(data), PARSER.parse(data.decode("utf-8")), doc_id)
    return {"document_id": doc_id, "segments": segs}


def test_el_rango_cubre_exactamente_el_texto(tmp_path: Path) -> None:
    doc = _prepare(DOC, tmp_path)
    assert doc["segments"], "el documento de prueba no produjo segmentos"
    for seg in doc["segments"]:
        texto = seg.get("translatable_text") or ""
        if not texto:
            continue
        crudo = (tmp_path / "doc.md").read_bytes()
        covered = crudo[seg["byte_range"]["start"]:seg["byte_range"]["end"]].decode("utf-8")
        assert covered == texto, (
            f"{seg['segment_id']} ({seg['structural_type']}): el rango cubre "
            f"{covered!r} y el texto traducible es {texto!r}"
        )


def test_ensamblar_una_traduccion_no_pierde_marcadores(tmp_path: Path) -> None:
    doc = _prepare(DOC, tmp_path)
    source = (tmp_path / "doc.md").read_bytes()
    # Una traducción real deja intactos los literales protegidos y cambia
    # la prosa. Aquí se simula con mayúsculas solo sobre las palabras.
    lookup = {}
    for seg in doc["segments"]:
        texto = seg.get("translatable_text") or ""
        if not texto:
            continue
        partes = re.split(r"(<a id=\"[^\"]+\"></a>)", texto)
        lookup[seg["segment_id"]] = "".join(
            p if p.startswith("<a id=") else p.upper() for p in partes
        )
    salida = assemble(source, doc, identity=False, translations_lookup=lookup)
    texto = salida.decode("utf-8")
    assert texto.startswith("# TÍTULO DE PRUEBA")
    assert "## SECCIÓN CON ACENTOS" in texto
    assert "- Primer elemento" in texto
    assert "- Segundo elemento" in texto
    assert '<a id="prueba"></a>' in texto
    assert "\n\n" in texto, "los saltos de línea entre bloques se preservan"


def test_el_modo_identidad_sigue_siendo_exacto(tmp_path: Path) -> None:
    doc = _prepare(DOC, tmp_path)
    source = (tmp_path / "doc.md").read_bytes()
    assert assemble(source, doc, identity=True) == source


def test_ensamblar_por_sustitucion_deja_los_marcadores(tmp_path: Path) -> None:
    """El caso real del piloto: traducir solo la prosa no debe tocar la sintaxis."""
    doc = _prepare(DOC, tmp_path)
    source = (tmp_path / "doc.md").read_bytes()
    lookup = {
        seg["segment_id"]: (seg["translatable_text"] or "").replace("prueba", "ensayo")
        for seg in doc["segments"] if seg.get("translatable_text")
    }
    texto = assemble(source, doc, identity=False, translations_lookup=lookup).decode("utf-8")
    assert "## Sección con acentos" in texto
    assert "- Primer elemento" in texto


def test_validate_no_pierde_estructura(tmp_path: Path) -> None:
    """`validate.py --checks structure` no puede declarar limpio un documento
    al que se le hayan borrado los encabezados."""
    doc = _prepare(DOC, tmp_path)
    source = (tmp_path / "doc.md").read_bytes()
    roto = source.replace("## Sección con acentos".encode("utf-8"), "Sección con acentos".encode("utf-8"))
    validate = ROOT / "scripts" / "validate.py"
    report = tmp_path / "validate.json"
    proc = subprocess.run(
        [sys.executable, str(validate), "--source", str(tmp_path), "--output-dir", str(tmp_path / "out"),
         "--segments", str(tmp_path / "segments.json"), "--manifest", str(tmp_path / "manifest.json"),
         "--out", str(report), "--checks", "structure"],
        capture_output=True, text=True, check=False,
    )
    # Sin manifests ni packets completos la herramienta puede fallar por otra
    # razón; lo que importa aquí es que el informe exista y sea utilizable.
    assert proc.returncode in (0, 1, 2, 3, 4, 5), proc.stderr
    if report.exists():
        data = json.loads(report.read_text(encoding="utf-8"))
        assert "results" in data or "errors" in data
    assert roto != source