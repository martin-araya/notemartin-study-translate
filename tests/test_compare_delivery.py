"""Pruebas del reporte de degradaciones (fase 138).

Cubre:

- Sin adaptación no hay diferencias.
- Una adaptación que solo cambia rutas y nombres no produce
  ``content_loss``.
- Perder un ejemplo, una advertencia o una fila de tabla sí lo produce y
  bloquea con código 3.
- Una tabla recortada, un bloque de código alterado o una prosa
  ampliada se detectan.
"""

from __future__ import annotations

import tempfile
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "compare_delivery.py"
ADAPT = ROOT / "scripts" / "adapt_delivery.py"
PROFILE = ROOT / "references" / "delivery-profiles" / "plain-markdown-local.json"
CANONICAL = ROOT / "tests" / "fixtures" / "delivery" / "canonical"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def make_canonical(name: str, *, awkward: bool = False) -> Path:
    target = TMP / name
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(CANONICAL, target)
    if awkward:
        (target / "imagenes" / "Diagrama de Flujo.png").write_bytes(
            (CANONICAL / "imagenes" / "diagrama.png").read_bytes()
        )
        doc = target / "index.md"
        doc.write_text(
            doc.read_text(encoding="utf-8")
            + "\n![Diagrama avanzado](imagenes/Diagrama%20de%20Flujo.png)\n",
            encoding="utf-8",
        )
    return target


def adapt(canonical: Path, name: str, *rules: str) -> Path:
    destination = TMP / name
    report = TMP / f"{name}_adapt.json"
    args = [
        str(ADAPT), "--canonical", str(canonical), "--profile", str(PROFILE),
        "--destination-out", str(destination), "--out", str(report),
    ]
    for rule in rules:
        args += ["--enable", rule]
    proc = run(args)
    assert proc.returncode == 0, proc.stderr
    return destination


def compare(canonical: Path, adapted: Path, name: str, expect: int = 0) -> dict:
    out = TMP / f"{name}_degradations.json"
    proc = run([
        str(SCRIPT), "--canonical", str(canonical), "--adapted", str(adapted), "--out", str(out)
    ])
    assert proc.returncode == expect, proc.stderr
    return json.loads(out.read_text(encoding="utf-8"))


def test_sin_adaptacion_no_hay_diferencias() -> None:
    canonical = make_canonical("cmp_base")
    copied = adapt(canonical, "cmp_base_copy")
    report = compare(canonical, copied, "cmp_base")
    assert report["differences"] == []
    assert report["counts"]["content_loss"] == 0
    assert report["ok"] is True
    assert report["documents_compared"] == 2


def test_adaptacion_de_rutas_no_pierde_contenido() -> None:
    canonical = make_canonical("cmp_rutas", awkward=True)
    adapted = adapt(canonical, "cmp_rutas_out", "relative-resource-paths", "ascii-resource-names")
    report = compare(canonical, adapted, "cmp_rutas")
    assert report["counts"]["content_loss"] == 0, report["differences"]
    assert report["ok"] is True
    renamed = [d for d in report["differences"] if d["aspect"] == "resource_renamed"]
    assert renamed and renamed[0]["classification"] == "format_only"
    assert renamed[0]["sha256"]


def test_perder_un_bloque_de_codigo_bloquea() -> None:
    canonical = make_canonical("cmp_codigo")
    adapted = adapt(canonical, "cmp_codigo_out")
    doc = adapted / "index.md"
    lines = doc.read_text(encoding="utf-8").splitlines(keepends=True)
    start = next(i for i, line in enumerate(lines) if line.startswith("```bash"))
    end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("```"))
    doc.write_text("".join(lines[:start] + lines[end + 1:]), encoding="utf-8")
    report = compare(canonical, adapted, "cmp_codigo", expect=3)
    assert report["counts"]["content_loss"] > 0
    aspects = {d["aspect"] for d in report["differences"] if d["classification"] == "content_loss"}
    assert "code_blocks" in aspects


def test_perder_una_advertencia_bloquea() -> None:
    canonical = make_canonical("cmp_advertencia")
    adapted = adapt(canonical, "cmp_advertencia_out")
    doc = adapted / "index.md"
    text = doc.read_text(encoding="utf-8")
    doc.write_text(text.replace("> **Advertencia.**", "> Nota."), encoding="utf-8")
    report = compare(canonical, adapted, "cmp_advertencia", expect=3)
    assert report["counts"]["content_loss"] > 0


def test_tabla_recortada_bloquea() -> None:
    canonical = make_canonical("cmp_tabla")
    adapted = adapt(canonical, "cmp_tabla_out")
    doc = adapted / "index.md"
    lines = doc.read_text(encoding="utf-8").splitlines(keepends=True)
    doc.write_text("".join(l for l in lines if not l.startswith("| Node.js")), encoding="utf-8")
    report = compare(canonical, adapted, "cmp_tabla", expect=3)
    aspects = {d["aspect"] for d in report["differences"] if d["classification"] == "content_loss"}
    assert "tables" in aspects


def test_ampliar_prosa_bloquea() -> None:
    canonical = make_canonical("cmp_prosa")
    adapted = adapt(canonical, "cmp_prosa_out")
    doc = adapted / "guias" / "instalacion.md"
    doc.write_text(
        doc.read_text(encoding="utf-8") + "\n## Sección añadida por el adaptador\n",
        encoding="utf-8",
    )
    report = compare(canonical, adapted, "cmp_prosa", expect=3)
    aspects = {d["aspect"] for d in report["differences"] if d["classification"] == "content_loss"}
    assert "headings" in aspects


def test_documento_ausente_bloquea() -> None:
    canonical = make_canonical("cmp_ausente")
    adapted = adapt(canonical, "cmp_ausente_out")
    (adapted / "guias" / "instalacion.md").unlink()
    report = compare(canonical, adapted, "cmp_ausente", expect=3)
    assert any(
        d["aspect"] == "document_missing" and d["classification"] == "content_loss"
        for d in report["differences"]
    )


def test_recurso_perdido_bloquea() -> None:
    canonical = make_canonical("cmp_recurso")
    adapted = adapt(canonical, "cmp_recurso_out")
    (adapted / "imagenes" / "diagrama.png").unlink()
    report = compare(canonical, adapted, "cmp_recurso", expect=3)
    assert any(
        d["aspect"] == "resource_missing" and d["classification"] == "content_loss"
        for d in report["differences"]
    )
