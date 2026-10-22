"""Pruebas para scripts/export.py (fase 047)."""

from __future__ import annotations

import tempfile
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INVENTORY = ROOT / "scripts" / "inventory.py"
PREPARE = ROOT / "scripts" / "prepare.py"
DETECT = ROOT / "scripts" / "detect_language.py"
BUILD = ROOT / "scripts" / "build_packets.py"
TRANSLATE = ROOT / "scripts" / "translate_pilot.py"
EXPORT = ROOT / "scripts" / "export.py"
PILOT = ROOT / "tests" / "fixtures" / "pilot"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def setup_pipeline(source: Path | None = None, suffix: str = "") -> dict[str, Path]:
    src = source or PILOT
    inv = TMP / f"inv{suffix}.json"
    seg = TMP / f"segments{suffix}.json"
    classified = TMP / f"classified{suffix}.json"
    snaps = TMP / f"snapshots{suffix}.json"
    packets = TMP / f"packets{suffix}.json"
    translations = TMP / f"translations{suffix}"
    profile = TMP / f"profile{suffix}.json"
    manifest = TMP / f"manifest{suffix}.json"
    glossary = TMP / f"glossary{suffix}.json"

    profile.write_text(json.dumps({
        "target_language": "es",
        "source_language": "auto",
        "markdown_dialect": "commonmark+gfm",
        "slug_algorithm": {"name": "github", "version": "v1"},
        "code_preservation": "strict",
        "frontmatter_policy": "preserve",
        "bilingual_policy": "first-mention-per-document",
        "punctuation_preference": "es-comma-period",
        "review_mode": "assisted",
        "paths": {"source_root": str(src), "work_root": "/tmp", "output_root": "/tmp"},
        "exclusions": [],
        "context_budget": 1500,
        "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
    }, indent=2), encoding="utf-8")

    assert run([str(INVENTORY), "--source", str(src), "--out", str(inv)]).returncode == 0
    assert run([str(PREPARE), "--inventory", str(inv), "--segments", str(seg), "--snapshots", str(snaps)]).returncode == 0
    assert run([str(DETECT), "--segments", str(seg), "--out", str(classified)]).returncode == 0
    assert run([str(BUILD),
                "--segments", str(classified),
                "--profile", str(profile),
                "--out", str(packets)]).returncode == 0
    if translations.exists():
        shutil.rmtree(translations)
    translations.mkdir(parents=True)
    assert run([str(TRANSLATE),
                "--packets", str(packets),
                "--segments", str(classified),
                "--out", str(translations),
                "--mode", "identity"]).returncode == 0

    doc_ids = json.loads(classified.read_text(encoding="utf-8"))["files"]
    files = [{
        "path": f["path"],
        "document_id": f["document_id"],
        "source_hash": f["source_hash"],
        "current_state": "approved",
        "state_history": [{"state": "inventoried", "timestamp": "2026-10-19T20:00:00Z", "reason": "init"}, {"state": "approved", "timestamp": "2026-10-19T20:01:00Z", "reason": "done"}],
        "last_transition_at": "2026-10-19T20:01:00Z",
    } for f in doc_ids]
    manifest_payload = {
        "run_id": "run-export",
        "created_at": "2026-10-19T20:00:00Z",
        "skill_version": "0.1.0",
        "parser": {"name": "markdown-it-py", "version": "3.0.0"},
        "anchor_policy": {"algorithm": "github", "version": "v1"},
        "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
        "glossary_snapshot": {"version": 1, "hash": "x", "frozen": True},
        "profile_snapshot": {"hash": "x"},
        "inputs": {"source_root": str(src), "total_files": len(files), "total_bytes": 0, "hashes_indexed": True},
        "files": files,
    }
    manifest.write_text(json.dumps(manifest_payload, indent=2), encoding="utf-8")

    glossary_payload = {
        "version": 1, "frozen": True, "allowed_languages": ["es"], "entries": [],
    }
    glossary.write_text(json.dumps(glossary_payload, indent=2), encoding="utf-8")

    return {"packets": packets, "snapshots": snaps, "segments": classified, "translations": translations, "manifest": manifest, "glossary": glossary, "source": PILOT, "inv": inv}


def test_export_exitoso() -> None:
    paths = setup_pipeline()
    output_root = TMP / "export_out1"
    if output_root.exists():
        shutil.rmtree(output_root)
    report = TMP / "export_report1.json"
    proc = run([
        str(EXPORT),
        "--source-root", str(paths["source"]),
        "--translations", str(paths["translations"]),
        "--inventory", str(paths["inv"]),
        "--manifest", str(paths["manifest"]),
        "--segments", str(paths["segments"]),
        "--packets", str(paths["packets"]),
        "--snapshots", str(paths["snapshots"]),
        "--anchors", str(TMP / "anchors_export"),
        "--glossary", str(paths["glossary"]),
        "--output-root", str(output_root),
        "--run-id", "run-export-1",
        "--report", str(report),
    ])
    assert proc.returncode == 0, proc.stderr
    final = output_root / "run-export-1"
    assert final.exists()
    files = list(final.glob("*.md"))
    assert files


def test_export_promueve_el_manifiesto_a_exported() -> None:
    """Exportar tiene que dejar los archivos en `exported`.

    Sin esto el estado final de la secuencia C-RUN no lo escribía
    ninguna herramienta y el manifiesto se quedaba en `approved` con un
    árbol entregado al lado.
    """
    paths = setup_pipeline()
    output_root = TMP / "export_out_promoted"
    if output_root.exists():
        shutil.rmtree(output_root)
    report = TMP / "export_report_promoted.json"
    proc = run([
        str(EXPORT),
        "--source-root", str(paths["source"]),
        "--translations", str(paths["translations"]),
        "--inventory", str(paths["inv"]),
        "--manifest", str(paths["manifest"]),
        "--segments", str(paths["segments"]),
        "--packets", str(paths["packets"]),
        "--snapshots", str(paths["snapshots"]),
        "--anchors", str(TMP / "anchors_export_promoted"),
        "--glossary", str(paths["glossary"]),
        "--output-root", str(output_root),
        "--run-id", "run-export-promoted",
        "--report", str(report),
    ])
    assert proc.returncode == 0, proc.stderr

    manifest = json.loads(paths["manifest"].read_text(encoding="utf-8"))
    final = output_root / "run-export-promoted"
    for record in manifest["files"]:
        assert record["current_state"] == "exported", f"{record['path']} no quedó exportado"
        digest = record["output_sha256"]
        delivered = final / record["path"]
        assert delivered.exists(), f"{record['path']} no está en el árbol entregado"
        assert __import__("hashlib").sha256(delivered.read_bytes()).hexdigest() == digest
        assert record["state_history"][-1]["state"] == "exported"

    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["not_promoted"] == []


def test_export_aborta_si_flag_loss() -> None:
    paths = setup_pipeline()
    target = next(paths["translations"].glob("*.json"))
    data = json.loads(target.read_text(encoding="utf-8"))
    if data["entries"]:
        data["entries"][0]["flag_loss"] = True
        data["entries"][0]["missing_literals"] = ["fake_literal"]
    target.write_text(json.dumps(data, indent=2), encoding="utf-8")
    output_root = TMP / "export_out2"
    if output_root.exists():
        shutil.rmtree(output_root)
    report = TMP / "export_report2.json"
    proc = run([
        str(EXPORT),
        "--source-root", str(paths["source"]),
        "--translations", str(paths["translations"]),
        "--inventory", str(paths["inv"]),
        "--manifest", str(paths["manifest"]),
        "--segments", str(paths["segments"]),
        "--packets", str(paths["packets"]),
        "--snapshots", str(paths["snapshots"]),
        "--anchors", str(TMP / "anchors_export_2"),
        "--glossary", str(paths["glossary"]),
        "--output-root", str(output_root),
        "--run-id", "run-export-2",
        "--report", str(report),
    ])
    assert proc.returncode != 0
    assert not (output_root / "run-export-2").exists()


def test_export_aborta_si_destino_existe_sin_force() -> None:
    paths = setup_pipeline()
    output_root = TMP / "export_out3"
    target = output_root / "run-export-3"
    target.mkdir(parents=True, exist_ok=True)
    # El destino tiene que contener algo: un directorio vacío no choca con
    # nadie, y la comprobación de conflicto no lo ve.
    (target / "notas-personales.md").write_text("edición local\n", encoding="utf-8")
    report = TMP / "export_report3.json"
    proc = run([
        str(EXPORT),
        "--source-root", str(paths["source"]),
        "--translations", str(paths["translations"]),
        "--inventory", str(paths["inv"]),
        "--manifest", str(paths["manifest"]),
        "--segments", str(paths["segments"]),
        "--packets", str(paths["packets"]),
        "--snapshots", str(paths["snapshots"]),
        "--anchors", str(TMP / "anchors_export_3"),
        "--glossary", str(paths["glossary"]),
        "--output-root", str(output_root),
        "--run-id", "run-export-3",
        "--report", str(report),
    ])
    assert proc.returncode != 0


# --------------------------------------------------------------------------
# La estructura del árbol entregado se compara (INV-06)
# --------------------------------------------------------------------------
#
# `export.py` pasaba `--output-dir <output_root>` a su `validate.py`
# interno, es decir, el padre del directorio del run, mientras que
# ensamblaba en `output_root/<run_id>/`. El chequeo `structure` no
# encontraba ningún documento y pasaba en vacío: la paridad estructural
# entre lo entregado y la fuente no se comprobaba nunca dentro de la
# herramienta que entrega.


def test_la_validacion_interna_compara_el_arbol_entregado() -> None:
    """El informe de la validación interna no puede reportar documentos
    sin ensamblar: si los reportara, estaría mirando el directorio
    equivocado."""
    paths = setup_pipeline(suffix="_struct")
    output_root = TMP / "export_out_struct"
    if output_root.exists():
        shutil.rmtree(output_root)
    report = TMP / "export_report_struct.json"
    proc = run([
        str(EXPORT),
        "--source-root", str(paths["source"]),
        "--translations", str(paths["translations"]),
        "--inventory", str(paths["inv"]),
        "--manifest", str(paths["manifest"]),
        "--segments", str(paths["segments"]),
        "--packets", str(paths["packets"]),
        "--snapshots", str(paths["snapshots"]),
        "--anchors", str(TMP / "anchors_struct"),
        "--glossary", str(paths["glossary"]),
        "--output-root", str(output_root),
        "--run-id", "run-export-struct",
        "--report", str(report),
    ])
    assert proc.returncode == 0, proc.stderr

    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["structure_check"]["ok"] is True
    assert payload["structure_check"]["documents_compared"] == len(payload["assembled_files"])

    post = json.loads((TMP / "export_report_struct.structure.json").read_text(encoding="utf-8"))
    structure = post["results"]["structure"]
    assert structure["errors"] == []
    sin_ensamblar = [
        e for e in structure["errors"] + structure["info"]
        if "sin ensamblar" in e.get("message", "")
    ]
    assert sin_ensamblar == [], (
        f"{len(sin_ensamblar)} documentos quedaron sin comparar: la validación "
        "no miró el árbol entregado"
    )


def test_un_documento_que_no_se_entrega_aborta_la_exportacion() -> None:
    """Si un documento del alcance no llega al árbol entregado, la
    exportación se niega a promoverlo en vez de entregar un corpus
    incompleto con los gates en verde."""
    paths = setup_pipeline(suffix="_diverge")

    segments = json.loads(paths["segments"].read_text(encoding="utf-8"))
    dropped = segments["files"].pop()
    paths["segments"].write_text(json.dumps(segments, indent=2), encoding="utf-8")

    output_root = TMP / "export_out_diverge"
    if output_root.exists():
        shutil.rmtree(output_root)
    report = TMP / "export_report_diverge.json"
    proc = run([
        str(EXPORT),
        "--source-root", str(paths["source"]),
        "--translations", str(paths["translations"]),
        "--inventory", str(paths["inv"]),
        "--manifest", str(paths["manifest"]),
        "--segments", str(paths["segments"]),
        "--packets", str(paths["packets"]),
        "--snapshots", str(paths["snapshots"]),
        "--anchors", str(TMP / "anchors_diverge"),
        "--glossary", str(paths["glossary"]),
        "--output-root", str(output_root),
        "--run-id", "run-export-diverge",
        "--report", str(report),
    ])
    assert proc.returncode != 0, "un documento sin entregar debe impedir la promoción"
    assert not (output_root / "run-export-diverge").exists(), (
        f"dejó un árbol con {dropped['path']} ausente"
    )
