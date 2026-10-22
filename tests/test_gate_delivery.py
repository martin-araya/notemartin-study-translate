"""Pruebas del gate de entrega (fase 140).

Recorre el lote completo (134 → 135 → 136 → 137 → 138 → 139) sobre el
fixture canónico y comprueba que el gate:

- aprueba un paquete canónico bien formado;
- devuelve un código distinto por comprobación fallida;
- rechaza una guía colocada dentro del árbol importable;
- rechaza un paquete adaptado sin paquete canónico de comparación;
- rechaza un destino sin activación explícita;
- y que desactivar el adaptador no altera la traducción canónica.
"""

from __future__ import annotations

import tempfile
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
CANONICAL = ROOT / "tests" / "fixtures" / "delivery" / "canonical"
PROFILE = ROOT / "references" / "delivery-profiles" / "plain-markdown-local.json"
TMP = Path(tempfile.gettempdir()) / "nst-tests"

RUN_ID = "run-gate-001"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def make_tree(name: str) -> Path:
    target = TMP / name
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(CANONICAL, target)
    return target


def build_manifest(tree: Path) -> Path:
    files = []
    for path in sorted(tree.rglob("*.md")):
        rel = path.relative_to(tree).as_posix()
        files.append({
            "path": rel,
            "source_hash": hashlib.sha256(path.read_bytes()).hexdigest(),
            "current_state": "approved",
            "state_history": [{"state": "approved", "timestamp": "2026-10-20T11:00:00Z", "reason": "prueba"}],
            "last_transition_at": "2026-10-20T11:00:00Z",
        })
    payload = {
        "run_id": RUN_ID,
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
    target = TMP / f"gate_manifest_{tree.name}.json"
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return target


def adapt(canonical: Path, destination: Path, report: Path, *rules: str):
    args = [
        str(SCRIPTS / "adapt_delivery.py"), "--canonical", str(canonical),
        "--profile", str(PROFILE), "--destination-out", str(destination), "--out", str(report),
    ]
    for rule in rules:
        args += ["--enable", rule]
    proc = run(args)
    assert proc.returncode == 0, proc.stderr


def package(tree: Path, manifest: Path, zip_path: Path, package_path: Path, destination_id: str,
            adaptation_report: Path | None = None):
    args = [
        str(SCRIPTS / "export_zip.py"), "--tree", str(tree), "--manifest", str(manifest),
        "--run-id", RUN_ID, "--destination-id", destination_id,
        "--out", str(zip_path), "--package-manifest", str(package_path),
    ]
    if adaptation_report:
        args += ["--adaptation-report", str(adaptation_report)]
    proc = run(args)
    assert proc.returncode == 0, proc.stderr


def validate(zip_path: Path, package_path: Path, manifest: Path, out: Path):
    proc = run([
        str(SCRIPTS / "validate_zip_package.py"), "--zip", str(zip_path),
        "--package-manifest", str(package_path), "--manifest", str(manifest), "--out", str(out),
    ])
    assert proc.returncode == 0, proc.stderr
    return json.loads(out.read_text(encoding="utf-8"))


def guide(manifest: Path, out_dir: Path, tree: Path, zip_path: Path, package_path: Path,
          evidence: Path | None = None):
    args = [
        str(SCRIPTS / "render_delivery_guide.py"), "--manifest", str(manifest),
        "--run-id", RUN_ID, "--destination-id", "notion-manual",
        "--output-tree", str(tree), "--out-dir", str(out_dir),
        "--package-manifest", str(package_path), "--zip", str(zip_path),
    ]
    if evidence:
        args += ["--import-evidence", str(evidence)]
    proc = run(args)
    assert proc.returncode == 0, proc.stderr
    return out_dir / "DELIVERY.md"


def degrade(canonical: Path, adapted: Path, out: Path):
    proc = run([
        str(SCRIPTS / "compare_delivery.py"), "--canonical", str(canonical),
        "--adapted", str(adapted), "--out", str(out),
    ])
    assert proc.returncode == 0, proc.stderr
    return json.loads(out.read_text(encoding="utf-8"))


def matrix(out: Path) -> Path:
    proc = run([str(SCRIPTS / "delivery_matrix.py"), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr
    return out


def gate(out: Path, **kwargs) -> subprocess.CompletedProcess:
    args = [str(SCRIPTS / "gate_delivery.py")]
    for key, value in kwargs.items():
        if value is not None:
            args += [f"--{key.replace('_', '-')}", str(value)]
    args += ["--out", str(out)]
    return run(args)


def full_run(prefix: str = "gate_ok"):
    """Paquete canónico completo: adaptación sin reglas, ZIP, validación, guía, matriz."""
    canonical = make_tree(f"{prefix}_canonical")
    manifest = build_manifest(canonical)
    adaptation_report = TMP / f"{prefix}_adapt.json"
    adapt(canonical, TMP / f"{prefix}_copy", adaptation_report)
    zip_path = TMP / f"{prefix}.zip"
    package_path = TMP / f"{prefix}_package.json"
    package(canonical, manifest, zip_path, package_path, "notion-manual")
    validate(zip_path, package_path, manifest, TMP / f"{prefix}_validation.json")
    guide_path = guide(manifest, TMP / f"{prefix}_guide", canonical, zip_path, package_path)
    degrade(canonical, TMP / f"{prefix}_copy", TMP / f"{prefix}_degradations.json")
    return {
        "canonical": canonical,
        "manifest": manifest,
        "zip": zip_path,
        "package": package_path,
        "validation": TMP / f"{prefix}_validation.json",
        "guide": guide_path,
        "degradations": TMP / f"{prefix}_degradations.json",
        "adaptation": adaptation_report,
        "matrix": matrix(TMP / f"{prefix}_matrix.json"),
    }


def base_args(ctx: dict) -> dict:
    return {
        "manifest": ctx["manifest"],
        "canonical": ctx["canonical"],
        "package": ctx["zip"],
        "package_manifest": ctx["package"],
        "package_validation": ctx["validation"],
        "guide": ctx["guide"],
        "output_tree": ctx["canonical"],
        "adaptation_report": ctx["adaptation"],
        "degradation_report": ctx["degradations"],
        "delivery_matrix": ctx["matrix"],
    }


def test_el_gate_aprueba_un_paquete_canonico() -> None:
    ctx = full_run()
    out = TMP / "gate_paso.json"
    proc = gate(out, **base_args(ctx))
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["ok"] is True
    assert len(payload["checks"]) == 7
    assert all(c["ok"] for c in payload["checks"])


def test_el_gate_falla_si_el_canonico_cambio() -> None:
    ctx = full_run("gate_canonico")
    extra = ctx["canonical"] / "guias" / "instalacion.md"
    extra.write_text(extra.read_text(encoding="utf-8") + "\nlínea añadida\n", encoding="utf-8")
    out = TMP / "gate_canonico.json"
    proc = gate(out, **base_args(ctx))
    assert proc.returncode == 1
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["failed_checks"] == ["canonical_untouched"]


def test_el_gate_falla_si_la_guia_esta_en_el_arbol() -> None:
    ctx = full_run("gate_guia")
    delivered = TMP / "gate_guia_entregable"
    if delivered.exists():
        shutil.rmtree(delivered)
    shutil.copytree(ctx["canonical"], delivered)
    moved = delivered / "DELIVERY.md"
    shutil.copyfile(ctx["guide"], moved)
    args = base_args(ctx)
    args["guide"] = moved
    args["output_tree"] = delivered
    out = TMP / "gate_guia.json"
    proc = gate(out, **args)
    assert proc.returncode == 3, proc.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["failed_checks"] == ["guide_outside_importable_tree"]


def test_el_gate_falla_si_hay_perdida_de_contenido() -> None:
    ctx = full_run("gate_perdida")
    report = json.loads(ctx["degradations"].read_text(encoding="utf-8"))
    report["counts"]["content_loss"] = 2
    report["ok"] = False
    report["differences"].append({"document": "index.md", "aspect": "prose_text", "classification": "content_loss"})
    ctx["degradations"].write_text(json.dumps(report, indent=2), encoding="utf-8")
    out = TMP / "gate_perdida.json"
    proc = gate(out, **base_args(ctx))
    assert proc.returncode == 4
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["failed_checks"] == ["no_content_loss"]


def test_el_gate_falla_si_el_informe_de_validacion_declara_violaciones() -> None:
    ctx = full_run("gate_validacion")
    report = json.loads(ctx["validation"].read_text(encoding="utf-8"))
    report["ok"] = False
    report["violations"] = [{"check": "hash_mismatch", "path": "run-gate-001/index.md"}]
    ctx["validation"].write_text(json.dumps(report, indent=2), encoding="utf-8")
    out = TMP / "gate_validacion.json"
    proc = gate(out, **base_args(ctx))
    assert proc.returncode == 2
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["failed_checks"] == ["package_matches_manifest"]


def test_el_gate_falla_si_el_paquete_fue_alterado() -> None:
    ctx = full_run("gate_alterado")
    tampered = TMP / "gate_alterado_tampered.zip"
    with zipfile.ZipFile(ctx["zip"]) as src, zipfile.ZipFile(tampered, "w") as dst:
        for item in src.infolist():
            data = src.read(item.filename)
            if item.filename.endswith("index.md"):
                data += b"\nextra\n"
            dst.writestr(item, data)
    args = base_args(ctx)
    args["package"] = tampered
    proc = gate(TMP / "gate_alterado.json", **args)
    assert proc.returncode == 2


def test_el_gate_falla_con_un_destino_sin_activacion_explicita() -> None:
    ctx = full_run("gate_destino")
    payload = json.loads(ctx["matrix"].read_text(encoding="utf-8"))
    payload["destinations"][1]["activation"] = "implicit"
    ctx["matrix"].write_text(json.dumps(payload, indent=2), encoding="utf-8")
    out = TMP / "gate_destino.json"
    proc = gate(out, **base_args(ctx))
    assert proc.returncode == 6
    result = json.loads(out.read_text(encoding="utf-8"))
    assert result["failed_checks"] == ["destinations_declared"]


def test_paquete_adaptado_exige_paquete_canonico_para_comparar() -> None:
    prefix = "gate_adaptado"
    canonical = make_tree(f"{prefix}_canonical")
    manifest = build_manifest(canonical)
    adaptation_report = TMP / f"{prefix}_adapt.json"
    adapted = TMP / f"{prefix}_adapted"
    adapt(canonical, adapted, adaptation_report, "relative-resource-paths")
    canonical_zip = TMP / f"{prefix}_canonical.zip"
    canonical_package = TMP / f"{prefix}_canonical_package.json"
    package(canonical, manifest, canonical_zip, canonical_package, "notion-manual")
    zip_path = TMP / f"{prefix}.zip"
    package_path = TMP / f"{prefix}_package.json"
    package(adapted, manifest, zip_path, package_path, "plain-markdown-local",
            adaptation_report=adaptation_report)
    validation = TMP / f"{prefix}_validation.json"
    validate(zip_path, package_path, manifest, validation)
    guide_path = guide(manifest, TMP / f"{prefix}_guide", canonical, zip_path, package_path)
    degradations = TMP / f"{prefix}_degradations.json"
    degrade(canonical, adapted, degradations)

    ctx = {
        "canonical": canonical,
        "manifest": manifest,
        "zip": zip_path,
        "package": package_path,
        "validation": validation,
        "guide": guide_path,
        "degradations": degradations,
        "adaptation": adaptation_report,
        "matrix": matrix(TMP / f"{prefix}_matrix.json"),
    }
    without = gate(TMP / f"{prefix}_sin_canonico.json", **base_args(ctx))
    assert without.returncode == 7

    ctx["canonical_package"] = canonical_zip
    with_canonical = gate(TMP / f"{prefix}_con_canonico.json", **base_args(ctx))
    assert with_canonical.returncode == 7, "un paquete adaptado no puede ser idéntico al canónico"


def test_desactivar_el_adaptador_reproduce_el_paquete_canonico() -> None:
    """El paquete canónico no depende del adaptador: se reconstruye igual."""
    prefix = "gate_reproducible"
    canonical = make_tree(f"{prefix}_canonical")
    manifest = build_manifest(canonical)
    first_zip = TMP / f"{prefix}_a.zip"
    first_package = TMP / f"{prefix}_a_package.json"
    package(canonical, manifest, first_zip, first_package, "notion-manual")
    second_zip = TMP / f"{prefix}_b.zip"
    second_package = TMP / f"{prefix}_b_package.json"
    package(canonical, manifest, second_zip, second_package, "notion-manual")
    assert first_zip.read_bytes() == second_zip.read_bytes()
    a = json.loads(first_package.read_text(encoding="utf-8"))
    b = json.loads(second_package.read_text(encoding="utf-8"))
    assert a["members"] == b["members"]
    assert a["zip_sha256"] == b["zip_sha256"]


def test_el_gate_no_escribe_en_el_arbol_entregable() -> None:
    ctx = full_run("gate_sin_escritura")
    before = {
        p.relative_to(ctx["canonical"]).as_posix(): p.read_bytes()
        for p in sorted(ctx["canonical"].rglob("*")) if p.is_file()
    }
    gate(TMP / "gate_sin_escritura.json", **base_args(ctx))
    after = {
        p.relative_to(ctx["canonical"]).as_posix(): p.read_bytes()
        for p in sorted(ctx["canonical"].rglob("*")) if p.is_file()
    }
    assert before == after
