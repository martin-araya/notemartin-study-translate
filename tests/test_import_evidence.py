"""Pruebas del registro de evidencia de importación (fases 131-133).

Cubre:

- La plantilla nace sin verificación y con todo ``remote_result`` en
  ``unknown`` (131).
- La resolución local de enlaces se calcula de forma determinista y la
  navegación remota sigue sin comprobarse (132).
- La matriz de importación nace ``unverified`` y un Markdown válido no
  la promueve (133).
- La promoción a ``verified`` exige revisor humano declarado, al menos
  un documento importado y evidencia por cada comprobación superada.
"""

from __future__ import annotations

import tempfile
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "record_import_evidence.py"
SCHEMA = ROOT / "schemas" / "import_evidence.schema.json"
CANONICAL = ROOT / "tests" / "fixtures" / "delivery" / "canonical"
RECORDS = ROOT / "tests" / "fixtures" / "import_evidence"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def build_manifest(tree: Path) -> Path:
    """Manifiesto con todos los documentos del fixture en estado aprobado."""
    files = []
    for path in sorted(tree.rglob("*.md")):
        rel = path.relative_to(tree).as_posix()
        files.append({
            "path": rel,
            "source_hash": hashlib.sha256(path.read_bytes()).hexdigest(),
            "current_state": "approved",
            "state_history": [
                {"state": "inventoried", "timestamp": "2026-10-20T10:00:00Z", "reason": "inventario"},
                {"state": "approved", "timestamp": "2026-10-20T11:00:00Z", "reason": "aprobado"},
            ],
            "last_transition_at": "2026-10-20T11:00:00Z",
        })
    payload = {
        "run_id": "run-fixture-001",
        "created_at": "2026-10-20T10:00:00Z",
        "skill_version": "0.1.5",
        "parser": {"name": "markdown-it-py", "version": "3.0.0"},
        "anchor_policy": {"algorithm": "github-slug-v1", "version": "v1"},
        "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
        "glossary_snapshot": {"version": "1", "hash": "0" * 64, "frozen": True},
        "profile_snapshot": {"hash": "1" * 64},
        "inputs": {"source_root": str(tree), "total_files": len(files), "total_bytes": 0, "hashes_indexed": len(files)},
        "files": files,
    }
    target = TMP / "evidence_manifest.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return target


def copy_tree(name: str) -> Path:
    target = TMP / name
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(CANONICAL, target)
    return target


def _evidence(name: str) -> dict:
    return json.loads((TMP / name).read_text(encoding="utf-8"))


def test_template_nace_sin_verificar() -> None:
    manifest = build_manifest(CANONICAL)
    out = TMP / "evidence_template.json"
    proc = run([str(SCRIPT), "--manifest", str(manifest), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr
    payload = _evidence("evidence_template.json")
    assert payload["verified"] is False
    assert payload["remote_status"] == "no_verificado"
    assert payload["reviewer"] == {"kind": None, "name": None, "declared_at": None}
    assert all(c["remote_result"] == "unknown" for c in payload["checks"])
    assert all(cell["status"] == "unverified" for cell in payload["matrix"])
    assert payload["sample_documents"], "la plantilla debe listar documentos de muestra"


def test_plantilla_cumple_el_esquema() -> None:
    import jsonschema

    manifest = build_manifest(CANONICAL)
    out = TMP / "evidence_schema.json"
    proc = run([str(SCRIPT), "--manifest", str(manifest), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.validate(_evidence("evidence_schema.json"), schema)


def test_resolucion_local_detecta_enlace_roto() -> None:
    tree = copy_tree("evidence_tree_roto")
    broken = tree / "guias" / "instalacion.md"
    broken.write_text(
        broken.read_text(encoding="utf-8") + "\n[vuelve](index.md#destino-inexistente)\n",
        encoding="utf-8",
    )
    manifest = build_manifest(CANONICAL)
    out = TMP / "evidence_roto.json"
    proc = run([
        str(SCRIPT), "--manifest", str(manifest), "--output-tree", str(tree),
        "--check-links", "--out", str(out),
    ])
    assert proc.returncode == 0, proc.stderr
    payload = _evidence("evidence_roto.json")
    local = next(c for c in payload["checks"] if c["check_id"] == "internal_link_local")
    assert local["local_resolution"] == "fail"
    assert local["detail"]["broken"]
    assert local["detail"]["ok"] is False


def test_resolucion_local_no_afirma_navegacion_remota() -> None:
    tree = copy_tree("evidence_tree_ok")
    manifest = build_manifest(CANONICAL)
    out = TMP / "evidence_ok.json"
    proc = run([
        str(SCRIPT), "--manifest", str(manifest), "--output-tree", str(tree),
        "--check-links", "--out", str(out),
    ])
    assert proc.returncode == 0, proc.stderr
    payload = _evidence("evidence_ok.json")
    local = next(c for c in payload["checks"] if c["check_id"] == "internal_link_local")
    remote = next(c for c in payload["checks"] if c["check_id"] == "internal_link_remote")
    assert local["local_resolution"] == "pass"
    assert local["detail"]["checked"] > 0
    assert remote["local_resolution"] == "not_tested"
    assert remote["remote_result"] == "unknown"
    assert payload["verified"] is False


def test_matriz_se_emite_sin_promover_celulas() -> None:
    manifest = build_manifest(CANONICAL)
    out = TMP / "evidence_matriz.json"
    matrix_out = TMP / "import_matrix.json"
    proc = run([
        str(SCRIPT), "--manifest", str(manifest),
        "--output-tree", str(copy_tree("evidence_tree_matriz")),
        "--check-links", "--matrix-out", str(matrix_out), "--out", str(out),
    ])
    assert proc.returncode == 0, proc.stderr
    matrix = json.loads(matrix_out.read_text(encoding="utf-8"))
    assert matrix["cells"]
    assert matrix["unverified_cells"] == len(matrix["cells"])
    assert all(c["status"] == "unverified" for c in matrix["cells"])
    assert "Markdown válido" in matrix["note"]


def test_evidencia_sin_revisor_humano_se_rechaza() -> None:
    manifest = build_manifest(CANONICAL)
    out = TMP / "evidence_sin_revisor.json"
    proc = run([
        str(SCRIPT), "--manifest", str(manifest), "--record",
        str(RECORDS / "record_sin_revisor.json"), "--out", str(out),
    ])
    assert proc.returncode == 3, proc.stderr
    payload = _evidence("evidence_sin_revisor.json")
    assert payload["verified"] is False
    assert payload["remote_status"] == "no_verificado"
    assert any("revisor humano" in n for n in payload["notes"])


def test_evidencia_con_revisor_humano_se_acepta() -> None:
    manifest = build_manifest(CANONICAL)
    out = TMP / "evidence_humano.json"
    proc = run([
        str(SCRIPT), "--manifest", str(manifest), "--record",
        str(RECORDS / "record_humano_valido.json"), "--out", str(out),
    ])
    assert proc.returncode == 0, proc.stderr
    payload = _evidence("evidence_humano.json")
    assert payload["verified"] is True
    assert payload["remote_status"] == "verificado_con_evidencia"
    assert payload["reviewer"]["kind"] == "human"
    remote = next(c for c in payload["checks"] if c["check_id"] == "internal_link_remote")
    assert remote["remote_result"] == "pass"
    assert remote["evidence"]
    cell = next(c for c in payload["matrix"] if c["construction"] == "internal_link_remote")
    assert cell["status"] == "pass"


def test_pass_sin_evidencia_se_rechaza() -> None:
    manifest = build_manifest(CANONICAL)
    out = TMP / "evidence_sin_evidencia.json"
    proc = run([
        str(SCRIPT), "--manifest", str(manifest), "--record",
        str(RECORDS / "record_pass_sin_evidencia.json"), "--out", str(out),
    ])
    assert proc.returncode == 3, proc.stderr
    payload = _evidence("evidence_sin_evidencia.json")
    assert payload["verified"] is False
    assert any("sin evidencia" in n for n in payload["notes"])


def test_resuelve_anclas_html_explicitas() -> None:
    """Los fixtures del corpus real declaran `<a id="…"></a>` explícitos."""
    tree = copy_tree("evidence_anclas")
    doc = tree / "guias" / "instalacion.md"
    doc.write_text(
        "# Configuración avanzada\n\n"
        "## [Requisitos](#requisitos) <a id=\"requisitos\"></a>\n\n"
        "Texto.\n",
        encoding="utf-8",
    )
    index = tree / "index.md"
    index.write_text(
        index.read_text(encoding="utf-8")
        + "\n[Requisitos](guias/instalacion.md#requisitos)\n",
        encoding="utf-8",
    )
    manifest = build_manifest(CANONICAL)
    out = TMP / "evidence_anclas.json"
    proc = run([
        str(SCRIPT), "--manifest", str(manifest), "--output-tree", str(tree),
        "--check-links", "--out", str(out),
    ])
    assert proc.returncode == 0, proc.stderr
    local = next(
        c for c in _evidence("evidence_anclas.json")["checks"]
        if c["check_id"] == "internal_link_local"
    )
    assert local["local_resolution"] == "pass"
    assert local["detail"]["broken"] == []


def test_las_rutas_del_sitio_son_deuda_de_entrada() -> None:
    tree = copy_tree("evidence_sitio")
    doc = tree / "guias" / "instalacion.md"
    doc.write_text(
        doc.read_text(encoding="utf-8")
        + "\n[Referencia del sitio](/es/docs/Web/CSS/Values/var)\n",
        encoding="utf-8",
    )
    manifest = build_manifest(CANONICAL)
    out = TMP / "evidence_sitio.json"
    proc = run([
        str(SCRIPT), "--manifest", str(manifest), "--output-tree", str(tree),
        "--check-links", "--out", str(out),
    ])
    assert proc.returncode == 0, proc.stderr
    local = next(
        c for c in _evidence("evidence_sitio.json")["checks"]
        if c["check_id"] == "internal_link_local"
    )
    assert local["local_resolution"] == "pass", "una ruta del sitio no es una regresión local"
    assert local["detail"]["site_relative"]
    assert "deuda de entrada" in local["detail"]["note"]


def test_esquema_rechaza_verified_sin_revisor() -> None:
    import jsonschema
    import pytest

    manifest = build_manifest(CANONICAL)
    out = TMP / "evidence_esquema_negativo.json"
    assert run([str(SCRIPT), "--manifest", str(manifest), "--out", str(out)]).returncode == 0
    payload = _evidence("evidence_esquema_negativo.json")
    payload["verified"] = True
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, schema)
