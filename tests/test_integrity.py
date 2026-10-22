"""Pruebas para scripts/check_integrity.py (fase 040)."""

from __future__ import annotations

import tempfile
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECK = ROOT / "scripts" / "check_integrity.py"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def write_manifest(states: list[str]) -> Path:
    files = [
        {
            "path": f"file{i}.md",
            "document_id": f"doc-{i}",
            "source_hash": f"hash{i}",
            "current_state": state,
            "state_history": [{"state": state, "timestamp": "2026-10-19T20:00:00Z", "reason": "test"}],
            "last_transition_at": "2026-10-19T20:00:00Z",
        }
        for i, state in enumerate(states)
    ]
    payload = {"run_id": "run-test", "created_at": "2026-10-19T20:00:00Z", "files": files}
    path = TMP / f"manifest_{abs(hash(tuple(states))) % 100000}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def test_integridad_total_aprueba() -> None:
    manifest = write_manifest(["approved", "approved", "already_target"])
    out = TMP / "integrity_ok.json"
    proc = run([str(CHECK), "--manifest", str(manifest), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["integrity_ok"] is True
    assert report["coverage"]["integrated"] == 3
    assert report["coverage"]["blocked"] == 0


def test_archivo_bloqueado_falla_integridad() -> None:
    manifest = write_manifest(["approved", "blocked", "approved"])
    out = TMP / "integrity_blocked.json"
    proc = run([str(CHECK), "--manifest", str(manifest), "--out", str(out)])
    assert proc.returncode == 1
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["integrity_ok"] is False
    assert report["coverage"]["blocked"] == 1


def test_excluded_es_terminal_y_no_bloquea_la_integridad() -> None:
    """`excluded` es un estado terminal con motivo: NO bloquea la
    integridad porque el archivo ha sido dispositionado. La exclusión
    queda registrada en la cobertura para no inflar el numerador.
    """
    manifest = write_manifest(["approved", "excluded"])
    out = TMP / "integrity_excluded.json"
    proc = run([str(CHECK), "--manifest", str(manifest), "--out", str(out)])
    assert proc.returncode == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["integrity_ok"] is True
    assert report["coverage"]["excluded"] == 1
    assert report["coverage"]["integrated"] == 1  # solo approved cuenta
    assert report["coverage"]["total"] == 2


def test_manifiesto_actualizado_con_coverage() -> None:
    manifest = write_manifest(["approved", "already_target"])
    out = TMP / "integrity_updated.json"
    assert run([str(CHECK), "--manifest", str(manifest), "--out", str(out)]).returncode == 0
    updated = json.loads(manifest.read_text(encoding="utf-8"))
    assert "coverage" in updated
    assert "integrity_ok" in updated
    assert updated["integrity_ok"] is True


def test_traducido_sin_aprobar_no_cuenta_como_integrado() -> None:
    """Traducido no es aprobado.

    While the states of the pilot were written by a script that did not
    fill in `current_state`, this check would pass on a corpus that was
    never reviewed. That is exactly what G-BETA must not be able to say.
    """
    manifest = write_manifest(["translated", "translated"])
    out = TMP / "integrity_translated.json"
    proc = run([str(CHECK), "--manifest", str(manifest), "--out", str(out)])
    assert proc.returncode == 1
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["integrity_ok"] is False
    assert report["coverage"]["integrated"] == 0
    assert report["coverage"]["pending"] == 2


def test_estado_desconocido_se_cuenta_como_pendiente() -> None:
    manifest = write_manifest(["approved", "unknown_state"])
    out = TMP / "integrity_unknown.json"
    proc = run([str(CHECK), "--manifest", str(manifest), "--out", str(out)])
    assert proc.returncode == 1
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["coverage"]["integrated"] == 1
    assert report["coverage"]["pending"] == 1


# --------------------------------------------------------------------------
# Divergencia `state` / `current_state` (INV-12)
# --------------------------------------------------------------------------


def _manifest_con_divergencia(name: str, state: str, current: str) -> Path:
    payload = {
        "run_id": "run-0badc0de",
        "created_at": "2026-10-19T20:00:00Z",
        "files": [{
            "path": "docs/a.md",
            "document_id": "doc-1",
            "source_hash": "a" * 64,
            "current_state": current,
            "state": state,
            "state_history": [{"state": current, "timestamp": "2026-10-19T20:00:00Z", "reason": "test"}],
            "last_transition_at": "2026-10-19T20:00:00Z",
        }],
    }
    path = TMP / f"manifest_divergente_{name}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def test_un_registro_que_se_contradice_no_pasa_el_gate() -> None:
    """Un corpus íntegro con un campo que afirma lo contrario no está íntegro.

    Los gates leen `current_state`, así que la divergencia pasaba
    desapercibida; lo que no puede pasar es que el gate la ignore.
    """
    manifest = _manifest_con_divergencia("avanzado", "translated", "prepared")
    out = TMP / "integrity_divergente.json"
    proc = run([str(CHECK), "--manifest", str(manifest), "--out", str(out)])
    assert proc.returncode == 1
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["integrity_ok"] is False
    assert report["divergent_states"] == 1
    assert report["divergent"][0]["path"] == "docs/a.md"


def test_los_registros_coherentes_no_disparan_el_hallazgo() -> None:
    manifest = _manifest_con_divergencia("coherente", "prepared", "prepared")
    out = TMP / "integrity_coherente.json"
    proc = run([str(CHECK), "--manifest", str(manifest), "--out", str(out)])
    assert proc.returncode == 1, "prepared sigue siendo pendiente"
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["divergent_states"] == 0
    assert report["divergent"] == []
