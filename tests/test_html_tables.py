"""Pruebas de tablas HTML complejas (fase 076).

Cubre:

- Round-trip byte-exacto con ``colspan`` y ``rowspan``.
- El inventario cuenta ``colspan`` y ``rowspan``.
- El ensamblador no normaliza atributos de celda.
- El selector detecta texto en cada ``<td>`` y ``<th>``.
"""

from __future__ import annotations

import tempfile
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "html"
TMP = Path(tempfile.gettempdir()) / "nst-tests"

sys.path.insert(0, str(SCRIPTS))

import html_assemble
import html_parser
import html_selector


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def test_round_trip_tabla_con_colspan_y_rowspan() -> None:
    text = (FIXTURES / "tables_complex.md").read_text(encoding="utf-8")
    assert html_parser.round_trip(text) == text


def test_inventory_cuenta_colspan_y_rowspan() -> None:
    out = TMP / "tables_inv.json"
    proc = run([str(SCRIPTS / "html_inventory.py"), "--root", str(FIXTURES), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    counts = payload["attribute_counts"]
    assert counts.get("colspan", 0) >= 1
    assert counts.get("rowspan", 0) >= 1


def test_assemble_no_normaliza_atributos_de_celda() -> None:
    text = """<table>
<tr>
<th colspan="2">Combined header</th>
</tr>
<tr>
<td>A1</td>
<td>A2</td>
</tr>
</table>"""
    source_bytes = text.encode("utf-8")
    segments = html_selector.select_translatable(text)
    out_bytes = html_assemble.assemble(source_bytes, segments, identity=True)
    assert b'colspan="2"' in out_bytes


def test_selector_detecta_texto_en_cada_celda() -> None:
    text = """<table>
<tr>
<th>A</th>
<th>B</th>
</tr>
<tr>
<td>C</td>
<td>D</td>
</tr>
</table>"""
    segments = html_selector.select_translatable(text)
    cell_texts = [s.text for s in segments if s.kind == "text" and s.tag in ("td", "th")]
    assert set(cell_texts) == {"A", "B", "C", "D"}


def test_assemble_conserva_rowspan_y_colspan() -> None:
    text = (FIXTURES / "tables_complex.md").read_text(encoding="utf-8")
    source_bytes = text.encode("utf-8")
    segments = html_assemble.segments_from_text(text)
    out_bytes = html_assemble.assemble(source_bytes, segments, identity=True)
    assert out_bytes == source_bytes
    assert b'colspan="2"' in out_bytes
    assert b'rowspan="2"' in out_bytes


def test_selector_no_modifica_atributos_de_celda() -> None:
    text = '<table><tr><th colspan="2" title="merged">head</th></tr></table>'
    segments = html_selector.select_translatable(text)
    title_seg = next(s for s in segments if s.kind == "attribute" and s.attribute == "title")
    segments_dicts = [s.to_dict() for s in segments]
    for d in segments_dicts:
        if d.get("attribute") == "title":
            d["translated_text"] = "encabezado combinado"
    out_bytes = html_assemble.assemble(text.encode("utf-8"), segments_dicts)
    assert b'colspan="2"' in out_bytes
    assert b'title="encabezado combinado"' in out_bytes
