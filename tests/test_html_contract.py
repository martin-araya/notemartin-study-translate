"""Pruebas del contrato HTML (fase 071)."""

from __future__ import annotations

import tempfile
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
CONTRACT = ROOT / "references" / "html-contract.md"
FIXTURES = ROOT / "tests" / "fixtures" / "html"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def test_html_contract_existe() -> None:
    assert CONTRACT.exists()


def test_html_contract_lista_etiquetas() -> None:
    text = CONTRACT.read_text(encoding="utf-8")
    for needle in ("`details`", "`summary`", "`a`", "`img`", "`table`", "`code`", "`kbd`", "`span`"):
        assert needle in text, f"falta {needle!r} en html-contract.md"


def test_html_contract_declara_no_ejecucion() -> None:
    text = CONTRACT.read_text(encoding="utf-8")
    assert "no se ejecuta" in text.lower() or "no ejecuta" in text.lower()
    for needle in ("<script>", "<iframe>", "<object>", "<embed>"):
        assert needle in text


def test_fixtures_existen_y_contienen_etiquetas() -> None:
    assert FIXTURES.is_dir()
    files = list(FIXTURES.glob("*.md"))
    assert len(files) >= 3
    combined = "\n".join(f.read_text(encoding="utf-8") for f in files)
    for needle in ("<details>", "<summary>", "<table>", "<th>", "<td>", "<kbd>", "<code>", "<img"):
        assert needle in combined, f"ningún fixture contiene {needle!r}"


def test_inventory_cuenta_etiquetas_sin_ejecutar() -> None:
    out = TMP / "html_inv.json"
    proc = run([str(SCRIPTS / "html_inventory.py"), "--root", str(FIXTURES), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["summary"]["files"] >= 3
    assert "details" in payload["tag_counts"]
    assert "summary" in payload["tag_counts"]
    assert payload["summary"]["unsafe_total"] == 0


def test_inventory_detecta_script_y_iframe() -> None:
    fixture = TMP / "html_unsafe.md"
    fixture.parent.mkdir(parents=True, exist_ok=True)
    fixture.write_text("# t\n\n<script>alert(1)</script>\n\n<iframe src=\"evil\"></iframe>\n", encoding="utf-8")
    out = TMP / "html_unsafe_inv.json"
    proc = run([str(SCRIPTS / "html_inventory.py"), "--root", str(fixture.parent), "--out", str(out)])
    assert proc.returncode == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    kinds = {f["kind"] for f in payload["unsafe_findings"]}
    assert "unsafe_script" in kinds
    assert "unsafe_iframe" in kinds


def test_inventory_detecta_event_handlers() -> None:
    fixture = TMP / "html_event.md"
    fixture.parent.mkdir(parents=True, exist_ok=True)
    fixture.write_text("<a href=\"x\" onclick=\"alert(1)\">link</a>\n", encoding="utf-8")
    out = TMP / "html_event_inv.json"
    proc = run([str(SCRIPTS / "html_inventory.py"), "--root", str(fixture.parent), "--out", str(out)])
    assert proc.returncode == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    kinds = {f["kind"] for f in payload["unsafe_findings"]}
    assert "unsafe_event_handler" in kinds
