"""Pruebas de scripts/repair_state_field.py.

El manifiesto del piloto quedó con `state: approved` y
`current_state: translated` porque `approve_pilot.py` escribía solo el
campo que el esquema declara como complementario. Esta herramienta adopta
el estado divergente, pero únicamente cuando el historial del archivo
contiene esa transición: la evidencia de que la aprobación ocurrió está
en el historial.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPAIR = ROOT / "scripts" / "repair_state_field.py"
SCHEMA = ROOT / "schemas" / "manifest.schema.json"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def manifest(records: list[dict], name: str) -> Path:
    payload = {
        "run_id": "run-0badc0de",
        "created_at": "2026-10-20T00:00:00Z",
        "manifest_version": "translate/v1",
        "skill_version": "0.2.0",
        "parser": {"name": "markdown-it-py", "version": "3.0.0"},
        "anchor_policy": {"algorithm": "github-slug-v1", "version": "v1"},
        "model_metadata": {"provider": "kilo", "model": "x", "prompt_version": "1.0.0"},
        "glossary_snapshot": {"version": 2, "hash": "0" * 64, "frozen": True},
        "profile_snapshot": {"hash": "0" * 64},
        "inputs": {"source_root": "/tmp/src", "total_files": len(records), "total_bytes": 1, "hashes_indexed": True},
        "files": records,
    }
    path = TMP / f"repair_{name}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def record(path: str, current: str, state: str | None, history: list[str]) -> dict:
    entry = {
        "path": path,
        "document_id": f"doc-{abs(hash(path)) % 100000000:08d}",
        "source_hash": "a" * 64,
        "current_state": current,
        "state_history": [
            {"state": h, "timestamp": "2026-10-20T00:00:00Z", "reason": h}
            for h in history
        ],
        "last_transition_at": "2026-10-20T00:00:00Z",
    }
    if state:
        entry["state"] = state
    return entry


def repair(path: Path, name: str, *extra: str) -> tuple[subprocess.CompletedProcess, dict]:
    """`--out` recibe el manifiesto reparado; el informe va por stdout."""
    out = TMP / f"repair_{name}_out.json"
    proc = run([str(REPAIR), "--in", str(path), "--out", str(out), *extra])
    report = json.loads(proc.stdout) if proc.stdout.strip().startswith("{") else {}
    return proc, report


def test_se_adopta_el_estado_con_evidencia_en_el_historial() -> None:
    path = manifest([record("docs/a.md", "translated", "approved", ["inventoried", "translated", "approved"])], "ok")
    proc, payload = repair(path, "ok", "--apply")
    assert proc.returncode == 0, proc.stderr
    assert payload["repaired"] == 1
    out = json.loads((TMP / "repair_ok_out.json").read_text(encoding="utf-8"))
    assert out["files"][0]["current_state"] == "approved"
    assert out["files"][0]["state"] == "approved"


def test_sin_evidencia_no_se_toca_nada() -> None:
    """`state: approved` sin transición de aprobación en el historial es un
    campo huérfano: no se adopta.

    Con la reparación bidireccional tampoco se conserva: el historial
    sostiene `translated`, así que `approved` se degrada. Lo que no ocurre
    en ningún caso es que el documento pase a `approved`.
    """
    path = manifest([record("docs/b.md", "translated", "approved", ["inventoried", "translated"])], "sin-evidencia")
    proc, payload = repair(path, "sin-evidencia", "--apply")
    assert proc.returncode == 0
    assert payload["repaired"] == 0, "no se adopta un estado sin historial que lo sostenga"
    out = json.loads((TMP / "repair_sin-evidencia_out.json").read_text(encoding="utf-8"))
    assert out["files"][0]["current_state"] == "translated"
    assert out["files"][0]["state"] == "translated"
    assert payload["degraded"] == 1


def test_un_manifiesto_sano_no_cambia() -> None:
    path = manifest([record("docs/c.md", "approved", "approved", ["inventoried", "approved"])], "sano")
    proc, payload = repair(path, "sano", "--apply")
    assert proc.returncode == 0
    assert payload["repaired"] == 0
    assert payload["unchanged"] == 1


def test_es_idempotente() -> None:
    path = manifest([record("docs/d.md", "translated", "approved", ["inventoried", "approved"])], "idem")
    assert repair(path, "idem", "--apply")[0].returncode == 0
    first = (TMP / "repair_idem_out.json").read_text(encoding="utf-8")
    second_path = TMP / "repair_idem_out.json"
    proc = run([str(REPAIR), "--in", str(second_path), "--out", str(TMP / "repair_idem2.json"), "--apply"])
    assert proc.returncode == 0
    assert json.loads((TMP / "repair_idem2.json").read_text(encoding="utf-8"))["files"][0]["notes"] == \
        json.loads(first)["files"][0]["notes"], "la segunda pasada añadió otra nota"


def test_el_resultado_valida_contra_el_esquema() -> None:
    import jsonschema

    path = manifest([record("docs/e.md", "translated", "approved", ["inventoried", "approved"])], "esquema")
    assert repair(path, "esquema", "--apply")[0].returncode == 0
    out = json.loads((TMP / "repair_esquema_out.json").read_text(encoding="utf-8"))
    jsonschema.validate(out, json.loads(SCHEMA.read_text(encoding="utf-8")))


def test_sin_apply_no_escribe() -> None:
    path = manifest([record("docs/f.md", "translated", "approved", ["inventoried", "approved"])], "simulacion")
    proc, payload = repair(path, "simulacion")
    assert proc.returncode == 0
    assert payload["written"] is False
    assert not (TMP / "repair_simulacion_out.json").exists()
    assert json.loads(path.read_text(encoding="utf-8"))["files"][0]["current_state"] == "translated"


# --------------------------------------------------------------------------
# Divergencia en la dirección contraria (INV-12)
# --------------------------------------------------------------------------
#
# En la corrida beta quedaron 2608 de 2682 registros con `state:
# translated` y `current_state: prepared`, sin transición que lo sostenga
# en el historial. Todos los gates leen `current_state`, así que la
# divergencia pasaba desapercibida; cualquier lector de `state` —un
# informe, una herramienta externa, una persona— leía 2608 documentos
# traducidos que no lo están. La dirección inversa (que el script ya
# cubría) no era la que quedaba en el corpus real.


def test_un_state_que_el_historial_no_sostiene_se_degrada() -> None:
    path = manifest([record("docs/g.md", "prepared", "translated", ["inventoried", "prepared"])], "degradado")
    proc, payload = repair(path, "degradado", "--apply")
    assert proc.returncode == 0, proc.stderr
    assert payload["degraded"] == 1
    out = json.loads((TMP / "repair_degradado_out.json").read_text(encoding="utf-8"))
    assert out["files"][0]["current_state"] == "prepared"
    assert out["files"][0]["state"] == "prepared"


def test_la_degradacion_no_afirma_nada_nuevo() -> None:
    """Degradar `state` deja el historial intacto: no inventa la transición."""
    path = manifest([record("docs/h.md", "prepared", "translated", ["inventoried", "prepared"])], "historial")
    assert repair(path, "historial", "--apply")[0].returncode == 0
    out = json.loads((TMP / "repair_historial_out.json").read_text(encoding="utf-8"))
    assert [h["state"] for h in out["files"][0]["state_history"]] == ["inventoried", "prepared"]


def test_la_degradacion_es_idempotente() -> None:
    path = manifest([record("docs/i.md", "prepared", "translated", ["inventoried", "prepared"])], "deg-idem")
    assert repair(path, "deg-idem", "--apply")[0].returncode == 0
    once = json.loads((TMP / "repair_deg-idem_out.json").read_text(encoding="utf-8"))
    proc = run([str(REPAIR), "--in", str(TMP / "repair_deg-idem_out.json"),
                "--out", str(TMP / "repair_deg-idem2.json"), "--apply"])
    assert proc.returncode == 0
    twice = json.loads((TMP / "repair_deg-idem2.json").read_text(encoding="utf-8"))
    assert twice["files"][0]["notes"] == once["files"][0]["notes"]
    assert json.loads(proc.stdout)["degraded"] == 0


def test_la_degradacion_valida_contra_el_esquema() -> None:
    import jsonschema

    path = manifest([record("docs/j.md", "prepared", "translated", ["inventoried", "prepared"])], "deg-esquema")
    assert repair(path, "deg-esquema", "--apply")[0].returncode == 0
    out = json.loads((TMP / "repair_deg-esquema_out.json").read_text(encoding="utf-8"))
    jsonschema.validate(out, json.loads(SCHEMA.read_text(encoding="utf-8")))


def test_un_historial_que_si_sostiene_el_state_no_se_degrada() -> None:
    """Con historial que apoya `translated`, no hay nada que degradar."""
    path = manifest([record("docs/k.md", "translated", "translated", ["inventoried", "prepared", "translated"])], "coherente")
    proc, payload = repair(path, "coherente", "--apply")
    assert proc.returncode == 0
    assert payload["degraded"] == 0
    assert payload["repaired"] == 0