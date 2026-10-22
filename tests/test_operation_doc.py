"""Pruebas del procedimiento §9 de operation.md (fase 057).

Verifica:

- ``operation.md`` contiene la sección §9 con palabras clave
  ``last_segment_id``, ``idempotencia`` y ``cobertura programática``.
- ``scripts/checkpoint.py`` persiste ``last_segment_id`` en el estado.
- ``scripts/translate_pilot.py`` no duplica segmentos en re-ejecuciones.
- La cobertura del manifiesto es programáticamente verificable.
"""

from __future__ import annotations

import tempfile
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
OPERATION = ROOT / "references" / "operation.md"
PILOT = ROOT / "tests" / "fixtures" / "pilot"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def test_operation_md_incluye_seccion_limite_de_contexto() -> None:
    text = OPERATION.read_text(encoding="utf-8")
    assert "## 9. Límite de contexto y parada segura" in text
    lowered = text.lower()
    for needle in ("last_segment_id", "idempotencia", "cobertura programática"):
        assert needle in lowered, f"falta la frase clave {needle!r} en operation.md"


def test_operation_md_enumera_criterios_de_pausa() -> None:
    text = OPERATION.read_text(encoding="utf-8")
    for needle in ("Presupuesto", "Criterios de pausa", "Reanudación", "Idempotencia", "Cobertura programática"):
        assert needle in text


def test_checkpoint_incluye_last_segment_id() -> None:
    work = TMP / "ckp_57"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    state = {
        "run_id": "run-57",
        "last_segment_id": "seg-abc-123",
        "files_state": {},
    }
    state_path = TMP / "state_57.json"
    state_path.write_text(json.dumps(state), encoding="utf-8")
    proc = run([
        str(SCRIPTS / "checkpoint.py"),
        "save",
        "--state", str(state_path),
        "--work-root", str(work),
    ])
    assert proc.returncode == 0, proc.stderr

    proc = run([
        str(SCRIPTS / "checkpoint.py"),
        "load",
        "--work-root", str(work),
        "--run-id", "run-57",
        "--out", str(TMP / "ckp_57_loaded.json"),
    ])
    assert proc.returncode == 0, proc.stderr
    loaded = json.loads((TMP / "ckp_57_loaded.json").read_text(encoding="utf-8"))
    assert loaded["last_segment_id"] == "seg-abc-123"


def test_translate_pilot_no_duplica_segmentos() -> None:
    inv = TMP / "inv_57.json"
    seg = TMP / "seg_57.json"
    snaps = TMP / "snaps_57.json"
    classified = TMP / "classified_57.json"
    packets = TMP / "packets_57.json"
    translations = TMP / "trans_57"
    profile = TMP / "profile_57.json"

    if translations.exists():
        shutil.rmtree(translations)
    translations.mkdir(parents=True)

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
        "paths": {"source_root": str(PILOT), "work_root": "/tmp", "output_root": "/tmp"},
        "exclusions": [],
        "context_budget": 1500,
        "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
    }, indent=2), encoding="utf-8")

    assert run([str(SCRIPTS / "inventory.py"), "--source", str(PILOT), "--out", str(inv)]).returncode == 0
    assert run([str(SCRIPTS / "prepare.py"),
                "--inventory", str(inv),
                "--segments", str(seg),
                "--snapshots", str(snaps)]).returncode == 0
    assert run([str(SCRIPTS / "detect_language.py"),
                "--segments", str(seg),
                "--out", str(classified)]).returncode == 0
    assert run([str(SCRIPTS / "build_packets.py"),
                "--segments", str(classified),
                "--profile", str(profile),
                "--out", str(packets)]).returncode == 0

    assert run([str(SCRIPTS / "translate_pilot.py"),
                "--packets", str(packets),
                "--segments", str(classified),
                "--out", str(translations),
                "--mode", "identity"]).returncode == 0

    first_data = json.loads((translations / sorted(translations.iterdir())[0].name).read_text(encoding="utf-8"))
    first_count = len(first_data["entries"])

    assert run([str(SCRIPTS / "translate_pilot.py"),
                "--packets", str(packets),
                "--segments", str(classified),
                "--out", str(translations),
                "--mode", "identity"]).returncode == 0

    second_data = json.loads((translations / sorted(translations.iterdir())[0].name).read_text(encoding="utf-8"))
    assert len(second_data["entries"]) == first_count


def test_cobertura_coincide_con_inventario() -> None:
    inv = TMP / "inv_cov.json"
    assert run([str(SCRIPTS / "inventory.py"), "--source", str(PILOT), "--out", str(inv)]).returncode == 0
    data = json.loads(inv.read_text(encoding="utf-8"))
    manifest = {
        "run_id": "run-cov",
        "files": [{
            "path": f["path"],
            "source_hash": f["sha256"],
            "current_state": "approved",
            "state_history": [{"state": "inventoried", "timestamp": "2026-10-19T20:00:00Z", "reason": "init"}],
            "last_transition_at": "2026-10-19T20:00:00Z",
        } for f in data["files"]],
        "coverage": {"total": len(data["files"]), "integrated": len(data["files"]), "blocked": 0, "excluded": 0, "invalid": 0, "pending": 0},
        "integrity_ok": True,
    }
    manifest_path = TMP / "manifest_cov.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    integrity_out = TMP / "integrity_cov.json"
    proc = run([
        str(SCRIPTS / "check_integrity.py"),
        "--manifest", str(manifest_path),
        "--out", str(integrity_out),
    ])
    assert proc.returncode == 0
    payload = json.loads(integrity_out.read_text(encoding="utf-8"))
    assert payload["coverage"]["total"] == len(data["files"])
    assert payload["coverage"]["integrated"] == len(data["files"])
