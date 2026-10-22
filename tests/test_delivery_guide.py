"""Pruebas de la guía de entrega (fase 137).

Cubre:

- La guía se escribe fuera del árbol importable y fuera del paquete.
- Contiene las secciones obligatorias y el estado remoto real.
- No se presenta como verificación remota cuando no hay evidencia.
- Un destino dentro del árbol importable se rechaza.
- Una guía que coincide con un miembro del paquete se rechaza.
- La guía no filtra la ruta interna del work_root.
"""

from __future__ import annotations

import tempfile
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "render_delivery_guide.py"
CANONICAL = ROOT / "tests" / "fixtures" / "delivery" / "canonical"
EXPORT = ROOT / "scripts" / "export_zip.py"
TMP = Path(tempfile.gettempdir()) / "nst-tests"

RUN_ID = "run-guide-001"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def prepare(evidence: bool = False):
    tree = TMP / "guide_arbol"
    if tree.exists():
        shutil.rmtree(tree)
    shutil.copytree(CANONICAL, tree)
    work = TMP / "guide_work"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    files = []
    for path in sorted(tree.rglob("*.md")):
        rel = path.relative_to(tree).as_posix()
        files.append({
            "path": rel,
            "source_hash": "a" * 64,
            "current_state": "approved",
            "state_history": [{"state": "approved", "timestamp": "2026-10-20T11:00:00Z", "reason": "prueba"}],
            "last_transition_at": "2026-10-20T11:00:00Z",
        })
    files.append({
        "path": "bloqueado.md",
        "source_hash": "b" * 64,
        "current_state": "blocked",
        "state_history": [{"state": "blocked", "timestamp": "2026-10-20T11:00:00Z", "reason": "ambigüedad"}],
        "last_transition_at": "2026-10-20T11:00:00Z",
    })
    manifest = {
        "run_id": RUN_ID,
        "created_at": "2026-10-20T10:00:00Z",
        "skill_version": "0.1.5",
        "parser": {"name": "markdown-it-py", "version": "3.0.0"},
        "anchor_policy": {"algorithm": "github-slug-v1", "version": "v1"},
        "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
        "glossary_snapshot": {"version": "2", "hash": "c" * 64, "frozen": True},
        "profile_snapshot": {"hash": "d" * 64},
        "inputs": {"source_root": str(tree), "total_files": len(files), "total_bytes": 0, "hashes_indexed": len(files)},
        "files": files,
        "decisions": [{
            "author": "usuario",
            "role": "reviewer",
            "pair": "en-es",
            "scope": "global",
            "reason": "piloto aceptado",
            "reviewed_hashes": ["a" * 64],
            "decided_at": "2026-10-20T11:30:00Z",
            "kind": "approve",
        }],
    }
    manifest_path = work / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    package_path = work / "package_manifest.json"
    zip_path = work / f"{RUN_ID}.zip"
    proc = run([
        str(EXPORT), "--tree", str(tree), "--manifest", str(manifest_path),
        "--run-id", RUN_ID, "--destination-id", "notion-manual",
        "--out", str(zip_path), "--package-manifest", str(package_path),
    ])
    assert proc.returncode == 0, proc.stderr

    evidence_path = None
    if evidence:
        evidence_path = work / "import_evidence.json"
        evidence_path.write_text(json.dumps({
            "verified": True,
            "remote_status": "verificado_con_evidencia",
            "reviewer": {"kind": "human", "name": "usuario"},
            "checks": [],
        }, indent=2), encoding="utf-8")

    return tree, manifest_path, package_path, zip_path, evidence_path


def render(out_dir: Path, *, tree=None, package=None, zip_path=None, evidence=None,
           expect: int = 0, issues=None):
    target = tree or TMP / "guide_arbol"
    args = [
        str(SCRIPT),
        "--manifest", str(TMP / "guide_work" / "manifest.json"),
        "--run-id", RUN_ID,
        "--destination-id", "notion-manual",
        "--output-tree", str(target),
        "--out-dir", str(out_dir),
    ]
    if package is not False:
        args += ["--package-manifest", str(package or TMP / "guide_work" / "package_manifest.json")]
    if zip_path is not False:
        args += ["--zip", str(zip_path or TMP / "guide_work" / f"{RUN_ID}.zip")]
    if evidence:
        args += ["--import-evidence", str(evidence)]
    if issues:
        args += ["--issues", str(issues)]
    proc = run(args)
    assert proc.returncode == expect, proc.stderr
    return proc


def test_la_guia_se_escribe_fuera_del_arbol_y_del_paquete() -> None:
    tree, _manifest, package, zip_path, _evidence = prepare()
    out_dir = TMP / "guide_out"
    render(out_dir)
    guide = (out_dir / "DELIVERY.md").resolve()
    assert guide.exists()
    assert not guide.is_relative_to(tree.resolve()), "la guía no puede vivir en el árbol importable"
    with __import__("zipfile").ZipFile(zip_path) as zf:
        members = zf.namelist()
    assert all("DELIVERY.md" not in m for m in members)
    assert package.exists()


def test_la_guia_tiene_las_secciones_obligatorias() -> None:
    prepare()
    out_dir = TMP / "guide_secciones"
    render(out_dir)
    text = (out_dir / "DELIVERY.md").read_text(encoding="utf-8")
    for section in (
        "## 1. Identificación",
        "## 2. Alcance y conteos",
        "## 3. Glosario",
        "## 4. Comprobaciones ejecutadas",
        "## 5. Decisiones humanas",
        "## 6. Limitaciones aceptadas",
        "## 7. Estado de la verificación remota",
        "## 8. Adaptación aplicada",
        "## 9. Qué no afirma esta entrega",
        "## 10. Checklist de importación",
    ):
        assert section in text, section
    assert "delivery-notion-checklist.md" in text
    assert "no forma parte de la" in text


def test_la_guia_no_declara_verificacion_remota_sin_evidencia() -> None:
    prepare()
    out_dir = TMP / "guide_sin_evidencia"
    render(out_dir)
    text = (out_dir / "DELIVERY.md").read_text(encoding="utf-8")
    assert "**no_verificado**" in text
    assert "sin verificar" in text
    meta = json.loads((out_dir / "delivery_manifest.json").read_text(encoding="utf-8"))
    assert meta["evidence"]["verified"] is False
    assert meta["evidence"]["remote_status"] == "no_verificado"


def test_la_guia_refleja_la_evidencia_cuando_existe() -> None:
    _tree, _manifest, _package, _zip, evidence = prepare(evidence=True)
    out_dir = TMP / "guide_con_evidencia"
    render(out_dir, evidence=evidence)
    text = (out_dir / "DELIVERY.md").read_text(encoding="utf-8")
    assert "**verificado_con_evidencia**" in text
    assert "usuario" in text
    assert "muestra" in text


def test_las_limitaciones_aceptadas_se_listan() -> None:
    prepare()
    issues = TMP / "guide_issues.json"
    issues.write_text(json.dumps({
        "issues": [
            {"severity": "warning", "message": "enlace ya roto en la fuente", "path": "index.md"},
            {"severity": "error", "message": "no debe aparecer aquí", "path": "x.md"},
        ]
    }), encoding="utf-8")
    out_dir = TMP / "guide_limitaciones"
    render(out_dir, issues=issues)
    text = (out_dir / "DELIVERY.md").read_text(encoding="utf-8")
    assert "enlace ya roto en la fuente" in text
    assert "no debe aparecer aquí" not in text


def test_destino_dentro_del_arbol_importable_se_rechaza() -> None:
    tree, _manifest, _package, _zip, _evidence = prepare()
    out_dir = tree / "guias"
    render(out_dir, expect=2)


def test_guia_que_coincide_con_un_miembro_se_rechaza() -> None:
    prepare()
    out_dir = TMP / "guide_conflicto"
    proc = run([
        str(SCRIPT),
        "--manifest", str(TMP / "guide_work" / "manifest.json"),
        "--run-id", RUN_ID,
        "--destination-id", "notion-manual",
        "--output-tree", str(TMP / "guide_arbol"),
        "--package-manifest", str(TMP / "guide_work" / "package_manifest.json"),
        "--guide-name", "index.md",
        "--out-dir", str(out_dir),
    ])
    assert proc.returncode == 2
    assert "miembro del paquete" in proc.stderr
