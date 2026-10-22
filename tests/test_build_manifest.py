"""Pruebas de scripts/build_manifest.py (cierre de G-BETA).

La herramienta que construyó el manifiesto del piloto vivía en el
workdir de aquella corrida. Fuera de él no había forma de construir un
manifiesto con procedencia real.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INVENTORY = ROOT / "scripts" / "inventory.py"
PREPARE = ROOT / "scripts" / "prepare.py"
DETECT = ROOT / "scripts" / "detect_language.py"
BUILD_MANIFEST = ROOT / "scripts" / "build_manifest.py"
SCHEMA = ROOT / "schemas" / "manifest.schema.json"
TMP = Path(tempfile.gettempdir()) / "nst-tests"

DOC = "# Guide\n\nAn English paragraph that must be translated by the agent later.\n"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def setup(name: str) -> dict[str, Path]:
    source = TMP / name / "source"
    if source.exists():
        shutil.rmtree(source)
    (source / "docs").mkdir(parents=True)
    (source / "docs" / "a.md").write_text(DOC, encoding="utf-8")

    work = TMP / name / "work"
    work.mkdir(parents=True, exist_ok=True)
    profile = work / "profile.json"
    profile.write_text(json.dumps({
        "target_language": "es",
        "source_language": "auto",
        "markdown_dialect": "commonmark+gfm",
        "slug_algorithm": {"name": "github-slug-v1", "version": "v1"},
        "code_preservation": "strict",
        "frontmatter_policy": "preserve",
        "bilingual_policy": "first-mention-per-document",
        "punctuation_preference": "es-comma-period",
        "review_mode": "assisted",
        "paths": {"source_root": str(source), "work_root": str(work), "output_root": str(TMP / name / "out")},
        "exclusions": [],
        "context_budget": 1500,
        "model_metadata": {"provider": UNKNOWN, "model": UNKNOWN, "prompt_version": "0"},
    }, indent=2), encoding="utf-8")
    glossary = work / "glossary.json"
    glossary.write_text(json.dumps({
        "version": 2,
        "frozen": True,
        "allowed_languages": ["es"],
        "entries": [],
    }, indent=2), encoding="utf-8")

    inv = work / "inventory.json"
    seg = work / "segments.json"
    classified = work / "classified.json"
    assert run([str(INVENTORY), "--source", str(source), "--out", str(inv)]).returncode == 0
    assert run([str(PREPARE), "--inventory", str(inv), "--segments", str(seg), "--snapshots", str(work / "snap.json")]).returncode == 0
    assert run([str(DETECT), "--segments", str(seg), "--out", str(classified)]).returncode == 0
    return {"source": source, "work": work, "inv": inv, "classified": classified, "profile": profile, "glossary": glossary}


UNKNOWN = "unknown"


def build(paths: dict[str, Path], name: str, *extra: str) -> subprocess.CompletedProcess:
    return run([
        str(BUILD_MANIFEST),
        "--inventory", str(paths["inv"]),
        "--segments", str(paths["classified"]),
        "--profile", str(paths["profile"]),
        "--glossary", str(paths["glossary"]),
        "--run-id", "run-0badc0de",
        "--out", str(paths["work"] / f"{name}.json"),
        *extra,
    ])


def test_manifiesto_construido_valida_contra_el_esquema() -> None:
    import jsonschema

    paths = setup("manifest-ok")
    proc = build(paths, "manifest", "--model-provider", "kilo", "--model", "modelo-x", "--prompt-version", "1.0.0")
    assert proc.returncode == 0, proc.stderr
    manifest = json.loads((paths["work"] / "manifest.json").read_text(encoding="utf-8"))
    jsonschema.validate(manifest, json.loads(SCHEMA.read_text(encoding="utf-8")))


def test_la_procedencia_sale_de_los_archivos_reales() -> None:
    import hashlib

    paths = setup("manifest-provenance")
    proc = build(paths, "manifest", "--model-provider", "kilo", "--model", "modelo-x", "--prompt-version", "1.0.0")
    assert proc.returncode == 0, proc.stderr
    manifest = json.loads((paths["work"] / "manifest.json").read_text(encoding="utf-8"))

    record = manifest["files"][0]
    digest = hashlib.sha256((paths["source"] / "docs" / "a.md").read_bytes()).hexdigest()
    assert record["source_hash"] == digest
    assert manifest["profile_snapshot"]["hash"] == hashlib.sha256(paths["profile"].read_bytes()).hexdigest()
    assert manifest["glossary_snapshot"]["hash"] == hashlib.sha256(paths["glossary"].read_bytes()).hexdigest()
    assert manifest["glossary_snapshot"]["version"] == 2
    assert manifest["anchor_policy"] == {"algorithm": "github-slug-v1", "version": "v1"}
    assert manifest["model_metadata"]["provider"] == "kilo"


def test_lo_que_no_se_declara_queda_unknown() -> None:
    paths = setup("manifest-unknown")
    proc = build(paths, "manifest")
    assert proc.returncode == 0, proc.stderr
    manifest = json.loads((paths["work"] / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["model_metadata"] == {
        "provider": UNKNOWN, "model": UNKNOWN, "prompt_version": UNKNOWN,
    }


def test_un_documento_inexistente_aborta() -> None:
    paths = setup("manifest-missing")
    data = json.loads(paths["classified"].read_text(encoding="utf-8"))
    data["files"][0]["path"] = "docs/no-existe.md"
    paths["classified"].write_text(json.dumps(data), encoding="utf-8")
    proc = build(paths, "manifest")
    assert proc.returncode == 1
    assert not (paths["work"] / "manifest.json").exists()


def test_el_historial_empieza_en_inventoried() -> None:
    paths = setup("manifest-history")
    assert build(paths, "manifest").returncode == 0
    manifest = json.loads((paths["work"] / "manifest.json").read_text(encoding="utf-8"))
    history = manifest["files"][0]["state_history"]
    assert history[0]["state"] == "inventoried"
    assert history[-1]["state"] == manifest["files"][0]["current_state"]


def test_no_declara_traducido_antes_de_traducir() -> None:
    """INV-12: construir un manifiesto no es traducir.

    `build_manifest.py` solo lee inventario, segmentos, perfil y glosario.
    Ninguna de esas entradas demuestra que exista una traducción, así que
    el estado terminal que escribe debe ser el último estado que la
    evidencia sostiene: `prepared`. Escribir `translated` aquí hacía que
    un corpus con cero segmentos traducidos se anunciara como traducido
    completo.
    """
    paths = setup("manifest-no-fabricar")
    assert build(paths, "manifest").returncode == 0
    manifest = json.loads((paths["work"] / "manifest.json").read_text(encoding="utf-8"))
    for record in manifest["files"]:
        assert record["current_state"] == "prepared", record["path"]
        states = [h["state"] for h in record["state_history"]]
        assert "translated" not in states, record["path"]


def test_advance_state_puede_llegar_a_traducido_despues() -> None:
    """La secuencia C-RUN sigue siendo alcanzable desde `prepared`."""
    import jsonschema

    paths = setup("manifest-advance")
    assert build(paths, "manifest").returncode == 0
    manifest_path = paths["work"] / "manifest.json"
    report = paths["work"] / "state.json"
    proc = run([
        str(ROOT / "scripts" / "advance_state.py"),
        "--manifest", str(manifest_path),
        "--to", "translated",
        "--reason", "traducción real con glosario congelado",
        "--out", str(report),
        "--apply",
    ])
    assert proc.returncode == 0, proc.stderr
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["files"][0]["current_state"] == "translated"
    jsonschema.validate(manifest, json.loads(SCHEMA.read_text(encoding="utf-8")))


def test_un_run_id_invalido_aborta_sin_escribir() -> None:
    """El esquema exige `run-XXXXXXXX`; el error llega antes de escribir."""
    paths = setup("manifest-run-id")
    proc = build(paths, "manifest-invalid")
    assert proc.returncode == 0
    assert (paths["work"] / "manifest-invalid.json").exists()

    bad = run([
        str(BUILD_MANIFEST),
        "--inventory", str(paths["inv"]),
        "--segments", str(paths["classified"]),
        "--profile", str(paths["profile"]),
        "--glossary", str(paths["glossary"]),
        "--run-id", "run-beta-001",
        "--out", str(paths["work"] / "no-debe-existir.json"),
    ])
    assert bad.returncode == 2
    assert not (paths["work"] / "no-debe-existir.json").exists()


def test_el_motivo_por_defecto_no_afirma_traduccion() -> None:
    """El motivo por defecto no puede describir un trabajo no hecho."""
    paths = setup("manifest-reason")
    assert build(paths, "manifest").returncode == 0
    manifest = json.loads((paths["work"] / "manifest.json").read_text(encoding="utf-8"))
    reasons = [h["reason"] for h in manifest["files"][0]["state_history"]]
    assert not any("traducción por lotes" in r for r in reasons), reasons