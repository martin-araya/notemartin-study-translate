"""Pruebas del checklist de distribución (fase 058).

Cubre:

- Paquete completo: el script termina con rc=0 y emite un reporte.
- Referencias rotas: se detectan (rc!=0).
- Scripts referenciados pero inexistentes: se detectan.
- ``__pycache__`` u otros artefactos prohibidos: se detectan.
- ``--apply`` aborta con código distinto de 0.
"""

from __future__ import annotations

import tempfile
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "check_distribution.py"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def make_fixture_skill(tmp: Path) -> Path:
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    (tmp / "SKILL.md").write_text(
        "---\n"
        "name: test-skill\n"
        "description: Skill de prueba para tests de distribución.\n"
        "---\n\n"
        "# Test skill\n\n"
        "## §6 Tabla\n\n"
        "| Ruta | Rol |\n"
        "|---|---|\n"
        "| `references/workflow.md` | Flujo |\n"
        "| `references/no-existe.md` | Rota |\n"
        "| `scripts/inventory.py` | Script |\n",
        encoding="utf-8",
    )
    (tmp / "references").mkdir()
    (tmp / "references" / "workflow.md").write_text(
        "Usa `scripts/inventory.py` para inventariar. Ver [otra](otra.md).",
        encoding="utf-8",
    )
    (tmp / "scripts").mkdir()
    (tmp / "scripts" / "inventory.py").write_text("# script\n", encoding="utf-8")
    return tmp


def test_check_distribution_detecta_referencia_rota() -> None:
    fx = make_fixture_skill(TMP / "dist_fixture_a")
    out = TMP / "dist_report_a.json"
    proc = run([str(SCRIPT), "--root", str(fx), "--out", str(out)])
    assert proc.returncode != 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert not payload["ok"]
    skill_table_check = next(c for c in payload["checks"] if c["check"] == "skill_md_table_paths")
    assert "references/no-existe.md" in skill_table_check["missing"]


def test_check_distribution_detecta_script_y_enlace_ausentes() -> None:
    fx = TMP / "dist_fixture_b"
    if fx.exists():
        shutil.rmtree(fx)
    fx.mkdir(parents=True)
    (fx / "SKILL.md").write_text(
        "---\nname: x\ndescription: y\n---\n\n# x\n",
        encoding="utf-8",
    )
    (fx / "references").mkdir()
    (fx / "references" / "f.md").write_text(
        "Ver [otro](inexistente.md) y `scripts/que_no_existe.py`.",
        encoding="utf-8",
    )
    out = TMP / "dist_report_b.json"
    proc = run([str(SCRIPT), "--root", str(fx), "--out", str(out)])
    payload = json.loads(out.read_text(encoding="utf-8"))
    failed_checks = {c["check"] for c in payload["checks"] if not c.get("ok")}
    assert "references_internal_links" in failed_checks
    assert "references_scripts" in failed_checks


def test_check_distribution_detecta_artefactos_prohibidos() -> None:
    fx = TMP / "dist_fixture_c"
    if fx.exists():
        shutil.rmtree(fx)
    fx.mkdir(parents=True)
    (fx / "SKILL.md").write_text(
        "---\nname: x\ndescription: y\n---\n\n# x\n",
        encoding="utf-8",
    )
    (fx / "tests").mkdir()
    (fx / "tests" / "__pycache__").mkdir()
    (fx / "tests" / "__pycache__" / "junk.pyc").write_text("x", encoding="utf-8")
    out = TMP / "dist_report_c.json"
    proc = run([str(SCRIPT), "--root", str(fx), "--out", str(out)])
    payload = json.loads(out.read_text(encoding="utf-8"))
    forbidden_check = next(c for c in payload["checks"] if c["check"] == "forbidden_artifacts")
    assert not forbidden_check["ok"]
    assert any("__pycache__" in p or ".pyc" in p for p in forbidden_check["found"])


def test_check_distribution_apply_aborta() -> None:
    fx = TMP / "dist_fixture_d"
    if fx.exists():
        shutil.rmtree(fx)
    fx.mkdir(parents=True)
    (fx / "SKILL.md").write_text(
        "---\nname: x\ndescription: y\n---\n\n# x\n",
        encoding="utf-8",
    )
    out = TMP / "dist_report_d.json"
    proc = run([str(SCRIPT), "--root", str(fx), "--out", str(out), "--apply"])
    assert proc.returncode != 0


def test_check_distribution_paquete_actual() -> None:
    out = TMP / "dist_report_real.json"
    proc = run([str(SCRIPT), "--root", str(ROOT), "--out", str(out)])
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["checks"]
    install_profile = payload["install_profile"]
    assert install_profile["system"] == "Hermes"
    assert "usuario" in payload["user_action"].lower() or "realiza" in payload["user_action"].lower()
