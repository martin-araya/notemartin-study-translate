"""Pruebas de protección de ediciones manuales (fase 056).

Cubre:

- Destino previamente exportado y luego editado: export aborta con
  ``new-destination`` por defecto.
- ``--merge-strategy preserve`` respalda los archivos editados y los
  omite de la nueva exportación.
- ``--merge-strategy new-destination`` rechaza destino con ediciones.
- Catálogo ``output_hashes.json`` se escribe al cierre exitoso.
- Destino huérfano (sin catálogo) se trata como edición.
"""

from __future__ import annotations

import tempfile
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXPORT = ROOT / "scripts" / "export.py"
PILOT = ROOT / "tests" / "fixtures" / "pilot"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def fresh(name: str) -> Path:
    out = TMP / name
    if out.exists():
        shutil.rmtree(out)
    return out


def _pipeline_paths() -> dict[str, Path]:
    return {
        "inv": TMP / "inv_e.json",
        "seg": TMP / "seg_e.json",
        "snaps": TMP / "snaps_e.json",
        "classified": TMP / "classified_e.json",
        "packets": TMP / "packets_e.json",
        "translations": TMP / "trans_e",
        "profile": TMP / "profile_e.json",
        "manifest": TMP / "manifest_e.json",
        "glossary": TMP / "glossary_e.json",
    }


def setup_minimal_pipeline(run_id: str) -> dict[str, Path]:
    paths = _pipeline_paths()
    if paths["translations"].exists():
        shutil.rmtree(paths["translations"])
    paths["translations"].mkdir(parents=True)

    paths["profile"].write_text(json.dumps({
        "target_language": "es",
        "source_language": "auto",
        "markdown_dialect": "commonmark+gfm",
        "slug_algorithm": {"name": "github", "version": "v1"},
        "code_preservation": "strict",
        "frontmatter_policy": "preserve",
        "bilingual_policy": "first-mention-per-document",
        "punctuation_preference": "es-comma-period",
        "review_mode": "assisted",
        "paths": {"source_root": str(PILOT), "work_root": "/tmp", "output_root": "/tmp"},
        "exclusions": [],
        "context_budget": 1500,
        "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
    }, indent=2), encoding="utf-8")

    assert run([str(ROOT / "scripts" / "inventory.py"), "--source", str(PILOT), "--out", str(paths["inv"])]).returncode == 0
    assert run([str(ROOT / "scripts" / "prepare.py"),
                "--inventory", str(paths["inv"]),
                "--segments", str(paths["seg"]),
                "--snapshots", str(paths["snaps"])]).returncode == 0
    assert run([str(ROOT / "scripts" / "detect_language.py"),
                "--segments", str(paths["seg"]),
                "--out", str(paths["classified"])]).returncode == 0
    assert run([str(ROOT / "scripts" / "build_packets.py"),
                "--segments", str(paths["classified"]),
                "--profile", str(paths["profile"]),
                "--out", str(paths["packets"])]).returncode == 0
    assert run([str(ROOT / "scripts" / "translate_pilot.py"),
                "--packets", str(paths["packets"]),
                "--segments", str(paths["classified"]),
                "--out", str(paths["translations"]),
                "--mode", "identity"]).returncode == 0

    doc_ids = json.loads(paths["classified"].read_text(encoding="utf-8"))["files"]
    files = [{
        "path": f["path"],
        "document_id": f["document_id"],
        "source_hash": f["source_hash"],
        "current_state": "approved",
        "state_history": [{"state": "inventoried", "timestamp": "2026-10-19T20:00:00Z", "reason": "init"},
                          {"state": "approved", "timestamp": "2026-10-19T20:01:00Z", "reason": "done"}],
        "last_transition_at": "2026-10-19T20:01:00Z",
    } for f in doc_ids]
    paths["manifest"].write_text(json.dumps({
        "run_id": run_id,
        "created_at": "2026-10-19T20:00:00Z",
        "skill_version": "0.1.0",
        "parser": {"name": "markdown-it-py", "version": "3.0.0"},
        "anchor_policy": {"algorithm": "github", "version": "v1"},
        "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
        "glossary_snapshot": {"version": 1, "hash": "x", "frozen": True},
        "profile_snapshot": {"hash": "x"},
        "inputs": {"source_root": str(PILOT), "total_files": len(files), "total_bytes": 0, "hashes_indexed": True},
        "files": files,
    }, indent=2), encoding="utf-8")
    paths["glossary"].write_text(json.dumps({"version": 1, "frozen": True, "allowed_languages": ["es"], "entries": []}), encoding="utf-8")
    return paths


def export_call(paths: dict[str, Path], output_root: Path, run_id: str, extra: list[str] | None = None) -> subprocess.CompletedProcess:
    args = [
        str(EXPORT),
        "--source-root", str(PILOT),
        "--translations", str(paths["translations"]),
        "--inventory", str(paths["inv"]),
        "--manifest", str(paths["manifest"]),
        "--segments", str(paths["classified"]),
        "--packets", str(paths["packets"]),
        "--snapshots", str(paths["snaps"]),
        "--anchors", str(TMP / f"anchors_e_{run_id}"),
        "--glossary", str(paths["glossary"]),
        "--output-root", str(output_root),
        "--run-id", run_id,
        "--report", str(output_root / f"{run_id}.report.json"),
    ]
    if extra:
        args.extend(extra)
    return run(args)


def test_export_aborta_si_destino_editado() -> None:
    paths = setup_minimal_pipeline("run-edit-1")
    output_root = TMP / "export_edit_1"
    if output_root.exists():
        shutil.rmtree(output_root)
    assert export_call(paths, output_root, "run-edit-1").returncode == 0

    target = output_root / "run-edit-1"
    assert (target / "output_hashes.json").exists()
    edited_file = next(target.glob("*.md"))
    edited_file.write_text("# edited by user\n", encoding="utf-8")

    proc = export_call(paths, output_root, "run-edit-1")
    assert proc.returncode != 0
    assert "edited" in proc.stderr.lower() or "force" in proc.stderr.lower()


def test_export_con_merge_strategy_preserve_no_sobrescribe_editado() -> None:
    paths = setup_minimal_pipeline("run-edit-2")
    output_root = TMP / "export_edit_2"
    if output_root.exists():
        shutil.rmtree(output_root)
    assert export_call(paths, output_root, "run-edit-2").returncode == 0

    target = output_root / "run-edit-2"
    edited_file = next(target.glob("*.md"))
    user_content = "# USER EDIT\n"
    edited_file.write_text(user_content, encoding="utf-8")

    proc = export_call(paths, output_root, "run-edit-2", extra=["--merge-strategy", "preserve", "--force"])
    assert proc.returncode == 0, proc.stderr
    backup = output_root / "run-edit-2_edited_backup"
    assert backup.exists()
    backup_files = list(backup.rglob("*.md"))
    assert backup_files
    assert user_content in backup_files[0].read_text(encoding="utf-8")


def test_export_con_merge_strategy_new_destination_rechaza_edicion() -> None:
    paths = setup_minimal_pipeline("run-edit-3")
    output_root = TMP / "export_edit_3"
    if output_root.exists():
        shutil.rmtree(output_root)
    assert export_call(paths, output_root, "run-edit-3").returncode == 0

    target = output_root / "run-edit-3"
    edited_file = next(target.glob("*.md"))
    edited_file.write_text("# EDITED\n", encoding="utf-8")

    proc = export_call(paths, output_root, "run-edit-3", extra=["--merge-strategy", "new-destination"])
    assert proc.returncode != 0


def test_export_sin_catalogo_tratado_como_huerfano() -> None:
    paths = setup_minimal_pipeline("run-edit-4")
    output_root = TMP / "export_edit_4"
    target = output_root / "run-edit-4"
    if output_root.exists():
        shutil.rmtree(output_root)
    target.mkdir(parents=True)
    (target / "stale.md").write_text("# stale\n", encoding="utf-8")

    proc = export_call(paths, output_root, "run-edit-4")
    assert proc.returncode != 0
    assert "edited" in proc.stderr.lower() or "force" in proc.stderr.lower()


def test_export_escribe_catalogo_al_cierre() -> None:
    paths = setup_minimal_pipeline("run-edit-5")
    output_root = TMP / "export_edit_5"
    if output_root.exists():
        shutil.rmtree(output_root)
    assert export_call(paths, output_root, "run-edit-5").returncode == 0

    target = output_root / "run-edit-5"
    catalog = target / "output_hashes.json"
    assert catalog.exists()
    payload = json.loads(catalog.read_text(encoding="utf-8"))
    assert payload["run_id"] == "run-edit-5"
    for rel, hash_value in payload["hashes"].items():
        path = target / rel
        if path.is_file():
            import hashlib
            assert hashlib.sha256(path.read_bytes()).hexdigest() == hash_value
