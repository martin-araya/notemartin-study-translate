"""Pruebas del paquete ZIP de entrega (fases 135 y 136).

Cubre:

- El paquete contiene el árbol con un único directorio raíz.
- Los artefactos operativos quedan fuera y su exclusión se declara.
- El mismo árbol produce el mismo ZIP byte a byte.
- Rutas absolutas, escapes, symlinks, duplicados y miembros no
  declarados se detectan al validar.
- Un documento fuera del alcance aprobado se detecta.
- El hash de un miembro alterado se detecta.
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
EXPORT = ROOT / "scripts" / "export_zip.py"
VALIDATE = ROOT / "scripts" / "validate_zip_package.py"
SCHEMA = ROOT / "schemas" / "delivery_package.schema.json"
CANONICAL = ROOT / "tests" / "fixtures" / "delivery" / "canonical"
TMP = Path(tempfile.gettempdir()) / "nst-tests"

RUN_ID = "run-fixture-001"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def make_tree(name: str, *, dirty: bool = False) -> Path:
    target = TMP / name
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(CANONICAL, target)
    if dirty:
        (target / "reports").mkdir()
        (target / "reports" / "summary.md").write_text("resumen interno\n", encoding="utf-8")
        (target / "manifest.json").write_text("{}\n", encoding="utf-8")
        (target / "glossary.json").write_text("{}\n", encoding="utf-8")
        (target / ".DS_Store").write_bytes(b"basura")
        (target / "notas.tmp").write_text("parcial\n", encoding="utf-8")
    return target


def build_manifest(tree: Path, states=("approved",)) -> Path:
    state = states[0]
    files = []
    for path in sorted(tree.rglob("*.md")):
        rel = path.relative_to(tree).as_posix()
        if rel.startswith("reports/"):
            continue
        files.append({
            "path": rel,
            "source_hash": hashlib.sha256(path.read_bytes()).hexdigest(),
            "current_state": state,
            "state_history": [{"state": state, "timestamp": "2026-10-20T11:00:00Z", "reason": "prueba"}],
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
    target = TMP / "zip_manifest.json"
    target.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return target


def export(tree: Path, name: str, manifest: Path, *, expect: int = 0, **extra):
    zip_path = TMP / f"{name}.zip"
    package_path = TMP / f"{name}_package.json"
    args = [
        str(EXPORT),
        "--tree", str(tree),
        "--manifest", str(manifest),
        "--run-id", RUN_ID,
        "--destination-id", "notion-manual",
        "--out", str(zip_path),
        "--package-manifest", str(package_path),
    ]
    for key, value in extra.items():
        args += [f"--{key.replace('_', '-')}", str(value)]
    proc = run(args)
    assert proc.returncode == expect, proc.stderr
    package = json.loads(package_path.read_text(encoding="utf-8")) if package_path.exists() else None
    return proc, zip_path, package, package_path


def validate(zip_path: Path, package_path: Path, manifest: Path, name: str, expect: int = 0):
    out = TMP / f"{name}_validation.json"
    proc = run([
        str(VALIDATE), "--zip", str(zip_path), "--package-manifest", str(package_path),
        "--manifest", str(manifest), "--out", str(out),
    ])
    assert proc.returncode == expect, proc.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    return proc, payload


def test_paquete_incluye_arbol_con_un_solo_raiz() -> None:
    tree = make_tree("zip_limpio")
    manifest = build_manifest(tree)
    _proc, zip_path, package, package_path = export(tree, "zip_limpio", manifest)
    import jsonschema

    jsonschema.validate(package, json.loads(SCHEMA.read_text(encoding="utf-8")))
    assert package["top_level_dir"] == RUN_ID
    assert package["guide_outside_package"] is True
    assert package["remote_status"] == "no_verificado"
    with zipfile.ZipFile(zip_path) as zf:
        names = sorted(zf.namelist())
    assert names == [
        f"{RUN_ID}/guias/instalacion.md",
        f"{RUN_ID}/imagenes/diagrama.png",
        f"{RUN_ID}/index.md",
    ]
    _proc, result = validate(zip_path, package_path, manifest, "zip_limpio")
    assert result["ok"] is True
    assert result["observed_members"] == result["declared_members"] == 3


def test_los_artefactos_operativos_quedan_fuera() -> None:
    tree = make_tree("zip_sucio", dirty=True)
    manifest = build_manifest(tree)
    _proc, zip_path, package, package_path = export(tree, "zip_sucio", manifest)
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
    assert not any("reports/" in n for n in names)
    assert not any(n.endswith("manifest.json") for n in names)
    assert not any(n.endswith("glossary.json") for n in names)
    excluded = {e["path"] for e in package["excluded"]}
    assert {"reports/summary.md", "manifest.json", "glossary.json", ".DS_Store", "notas.tmp"} <= excluded
    _proc, result = validate(zip_path, package_path, manifest, "zip_sucio")
    assert result["ok"] is True


def test_el_zip_es_determinista() -> None:
    tree = make_tree("zip_det_a")
    manifest = build_manifest(tree)
    _proc, zip_a, _package_a, _pkg_a = export(tree, "zip_det_a", manifest)
    _proc, zip_b, _package_b, _pkg_b = export(tree, "zip_det_a2", manifest)
    assert zip_a.read_bytes() == zip_b.read_bytes()
    assert hashlib.sha256(zip_a.read_bytes()).hexdigest() == hashlib.sha256(zip_b.read_bytes()).hexdigest()


def test_el_paquete_cumple_el_esquema() -> None:
    import jsonschema

    tree = make_tree("zip_esquema")
    manifest = build_manifest(tree)
    _proc, _zip_path, package, _pkg = export(tree, "zip_esquema", manifest)
    jsonschema.validate(package, json.loads(SCHEMA.read_text(encoding="utf-8")))


def test_miembro_alterado_se_detecta() -> None:
    tree = make_tree("zip_alterado")
    manifest = build_manifest(tree)
    _proc, zip_path, _package, package_path = export(tree, "zip_alterado", manifest)
    tampered = TMP / "zip_alterado_tampered.zip"
    with zipfile.ZipFile(zip_path) as src, zipfile.ZipFile(tampered, "w") as dst:
        for item in src.infolist():
            data = src.read(item.filename)
            if item.filename.endswith("index.md"):
                data = data + b"\nlinea inyectada\n"
            dst.writestr(item, data)
    _proc, result = validate(tampered, package_path, manifest, "zip_alterado", expect=3)
    assert any(v["check"] == "hash_mismatch" for v in result["violations"])


def test_miembro_no_declarado_se_detecta() -> None:
    tree = make_tree("zip_extra")
    manifest = build_manifest(tree)
    _proc, zip_path, _package, package_path = export(tree, "zip_extra", manifest)
    tampered = TMP / "zip_extra_tampered.zip"
    with zipfile.ZipFile(zip_path) as src, zipfile.ZipFile(tampered, "w") as dst:
        for item in src.infolist():
            dst.writestr(item, src.read(item.filename))
        dst.writestr(f"{RUN_ID}/colado.md", "no declarado\n")
    _proc, result = validate(tampered, package_path, manifest, "zip_extra", expect=3)
    checks = {v["check"] for v in result["violations"]}
    assert "undeclared_member" in checks


def test_escape_de_ruta_se_detecta() -> None:
    tree = make_tree("zip_escape")
    manifest = build_manifest(tree)
    _proc, zip_path, _package, package_path = export(tree, "zip_escape", manifest)
    tampered = TMP / "zip_escape_tampered.zip"
    with zipfile.ZipFile(zip_path) as src, zipfile.ZipFile(tampered, "w") as dst:
        for item in src.infolist():
            dst.writestr(item, src.read(item.filename))
        dst.writestr(f"{RUN_ID}/../../fuera.md", "escape\n")
    _proc, result = validate(tampered, package_path, manifest, "zip_escape", expect=3)
    assert any(v["check"] == "unsafe_path" for v in result["violations"])


def test_symlink_se_detecta() -> None:
    tree = make_tree("zip_symlink")
    manifest = build_manifest(tree)
    _proc, zip_path, _package, package_path = export(tree, "zip_symlink", manifest)
    tampered = TMP / "zip_symlink_tampered.zip"
    with zipfile.ZipFile(zip_path) as src, zipfile.ZipFile(tampered, "w") as dst:
        for item in src.infolist():
            dst.writestr(item, src.read(item.filename))
        info = zipfile.ZipInfo(f"{RUN_ID}/enlace.png")
        info.external_attr = (0o120777 << 16)
        dst.writestr(info, "/etc/passwd")
    _proc, result = validate(tampered, package_path, manifest, "zip_symlink", expect=3)
    assert any(v["check"] == "symlink_member" for v in result["violations"])


def test_documento_fuera_de_alcance_se_detecta() -> None:
    tree = make_tree("zip_alcance")
    manifest = build_manifest(tree, states=("inventoried",))
    _proc, zip_path, _package, package_path = export(tree, "zip_alcance", manifest)
    _proc, result = validate(zip_path, package_path, manifest, "zip_alcance", expect=3)
    assert any(v["check"] == "document_outside_scope" for v in result["violations"])


def test_el_esquema_rechaza_ruta_con_escape() -> None:
    import jsonschema

    tree = make_tree("zip_escape_esquema")
    manifest = build_manifest(tree)
    _proc, _zip_path, package, _pkg = export(tree, "zip_escape_esquema", manifest)
    package["members"][0]["path"] = "../fuera.md"
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    try:
        jsonschema.validate(package, schema)
    except jsonschema.ValidationError:
        return
    raise AssertionError("el esquema debe rechazar una ruta con escape")
