"""Pruebas de scripts/gate_review.py (fase 130).

Cubre los dos modos y los siete códigos de salida:

- ``basic`` reproduce los estados terminales del núcleo y nada más.
- ``expanded`` **compone** ``basic`` y encima exige los artefactos de las
  fases 121-129. Antes los sustituía, de modo que encender el módulo
  perdía la comprobación de estados.
- ``expanded`` sin ``--justification`` sale con 7: el módulo no se activa
  sin un corpus que lo justifique (criterio 1 de G-EXT).
"""

from __future__ import annotations

import tempfile
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "gate_review.py"
TMP = Path(tempfile.gettempdir()) / "nst-tests"
JUSTIFICATION = "corpus angular 1492 documentos: evals/cases/beta.md"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def _write_manifest(mp: Path, *, decisions: list[dict] | None = None,
                    approvals: list[dict] | None = None,
                    files: list[dict] | None = None,
                    glossary_hash: str = "a" * 64) -> None:
    payload = {
        "run_id": "run-aaaaaaaa",
        "skill_version": "0.6.0",
        "parser": {"name": "x", "version": "1"},
        "anchor_policy": {"algorithm": "github", "version": "v1"},
        "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
        "glossary_snapshot": {"version": 1, "hash": glossary_hash, "frozen": True},
        "profile_snapshot": {"hash": "b" * 64},
        "inputs": {"source_root": "/tmp", "total_files": 1, "total_bytes": 1, "hashes_indexed": True},
        "decisions": decisions or [],
        "approvals": approvals or [],
        "files": files if files is not None else [
            {
                "path": "a.md",
                "source_hash": "d" * 64,
                "current_state": "approved",
                "state_history": [{"state": "approved", "timestamp": "2026-10-20T00:00:00Z", "reason": "x"}],
                "last_transition_at": "2026-10-20T00:00:00Z",
            }
        ],
    }
    mp.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_md(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_bilingual_ok(path: Path) -> None:
    _write_md(path, "# Informe bilingüe\n\n## Tabla de contenidos\n\n### a\n\n- `seg-x` — hola\n\n<a id=\"a-seg-x\"></a>\nOK\n")


def _decision_ok() -> dict:
    return {
        "decision_id": "dec-aaaa1111",
        "author": "tester",
        "role": "reviewer",
        "pair": "en -> es",
        "scope": "global",
        "reason": "Aprobado por pruebas automatizadas.",
        "reviewed_hashes": ["c" * 64],
        "decided_at": "2026-10-20T00:00:00Z",
        "kind": "approve",
    }


def _approval_ok(file_hash: str = "d" * 64, glossary_hash: str = "a" * 64) -> dict:
    return {
        "decision_id": "dec-aaaa1111",
        "approval_id": "app-aaaa1111",
        "target_hash": file_hash,
        "target_glossary_hash": glossary_hash,
        "approved_at": "2026-10-20T00:00:00Z",
        "artifact": "a.md",
    }


def _artifacts(tag: str, *, warnings: int = 0, fp: int = 0, fn: int = 0,
               total: int = 6) -> dict[str, str]:
    """Rutas de los artefactos ampliados, válidos salvo lo que se pida."""
    bi = TMP / f"bi_{tag}.md"
    _write_bilingual_ok(bi)
    pri = TMP / f"pri_{tag}.md"
    _write_md(pri, "# Hallazgos priorizados\n\n## Gate pendiente\n\n- ninguno\n")
    inc = TMP / f"inc_{tag}.json"
    inc.write_text(json.dumps({"groups": [{"domain": "api", "sense_id": "s1", "count": 1}]}), encoding="utf-8")
    res = TMP / f"res_{tag}.json"
    res.write_text(json.dumps({"warnings": warnings, "info": 0}), encoding="utf-8")
    bt = TMP / f"bt_{tag}.json"
    bt.write_text(
        json.dumps({"total": total, "true_match": total - fp - fn,
                    "false_positives": fp, "false_negatives": fn}),
        encoding="utf-8",
    )
    return {
        "bilingual": str(bi),
        "prioritized": str(pri),
        "inconsistency": str(inc),
        "residuals": str(res),
        "back_translation": str(bt),
    }


def _expanded_args(manifest: Path, artifacts: dict[str, str], out: Path,
                   *, justification: str | None = JUSTIFICATION) -> list[str]:
    args = [
        str(SCRIPT), "--mode", "expanded", "--manifest", str(manifest),
        "--bilingual-report", artifacts["bilingual"],
        "--prioritized-report", artifacts["prioritized"],
        "--inconsistency-report", artifacts["inconsistency"],
        "--residuals", artifacts["residuals"],
        "--back-translation", artifacts["back_translation"],
        "--out", str(out),
    ]
    if justification is not None:
        args.extend(["--justification", justification])
    return args


def test_basic_pasa_sin_artefactos_ampliados() -> None:
    mp = TMP / "g_basic.json"
    _write_manifest(mp)
    out = TMP / "g_basic_out.json"
    proc = run([str(SCRIPT), "--mode", "basic", "--manifest", str(mp), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr or proc.stdout
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["ok"]


def test_basic_no_llama_a_artefactos_ampliados() -> None:
    """``basic`` no debe leer los flags de ``--bilingual-report`` etc."""
    mp = TMP / "g_basic2.json"
    _write_manifest(mp)
    out = TMP / "g_basic2_out.json"
    proc = run([
        str(SCRIPT), "--mode", "basic", "--manifest", str(mp),
        "--bilingual-report", "/nonexistent.md",
        "--out", str(out),
    ])
    # No debe fallar por el artefacto inexistente.
    assert proc.returncode == 0, proc.stderr


def test_basic_rechaza_un_archivo_bloqueado() -> None:
    """`blocked` y `failed` no son estados de entrega."""
    for state in ("blocked", "failed"):
        mp = TMP / f"g_basic_{state}.json"
        _write_manifest(mp, files=[{
            "path": "a.md",
            "source_hash": "d" * 64,
            "current_state": state,
            "state_history": [{"state": state, "timestamp": "2026-10-20T00:00:00Z", "reason": "x"}],
            "last_transition_at": "2026-10-20T00:00:00Z",
        }])
        out = TMP / f"g_basic_{state}_out.json"
        proc = run([str(SCRIPT), "--mode", "basic", "--manifest", str(mp), "--out", str(out)])
        assert proc.returncode == 1, state
        payload = json.loads(out.read_text(encoding="utf-8"))
        assert not payload["ok"]
        assert any(state in m for m in payload["failures"])


def test_los_estatos_de_entrega_cubren_la_secuencia_del_nucleo() -> None:
    """Cada estado de la secuencia está o entregado o explícitamente rechazado.

    Sin esta prueba, un estado nuevo del núcleo entraría por la puerta de
    atrás: el gate no lo aceptaría ni lo rechazaría, simplemente no lo
    mencionaría.
    """
    sys.path.insert(0, str(ROOT / "scripts"))
    from advance_state import SEQUENCE  # noqa: E402
    from gate_review import DELIVERABLE_STATES  # noqa: E402

    assert "approved" in DELIVERABLE_STATES
    assert {"blocked", "failed"} & DELIVERABLE_STATES == set()
    assert DELIVERABLE_STATES | set(SEQUENCE) == set(SEQUENCE) | DELIVERABLE_STATES
    assert set(SEQUENCE) - DELIVERABLE_STATES


def test_expanded_sin_justification_no_activa_el_modulo() -> None:
    """Criterio 1 de G-EXT: activar sin corpus declarado sale con 7."""
    mp = TMP / "g_exp_sin_just.json"
    _write_manifest(mp, decisions=[_decision_ok()], approvals=[_approval_ok()])
    artifacts = _artifacts("sinjust")
    out = TMP / "g_exp_sin_just_out.json"
    proc = run(_expanded_args(mp, artifacts, out, justification=None))
    assert proc.returncode == 7
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert not payload["ok"]
    assert payload["exit_codes"] == [7]


def test_expanded_falla_sin_informe() -> None:
    mp = TMP / "g_exp1.json"
    _write_manifest(mp, decisions=[_decision_ok()], approvals=[])
    artifacts = _artifacts("exp1")
    artifacts["bilingual"] = str(TMP / "no-existe.md")
    out = TMP / "g_exp1_out.json"
    proc = run(_expanded_args(mp, artifacts, out))
    assert proc.returncode == 1
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert not payload["ok"]
    assert 1 in payload["exit_codes"]


def test_expanded_falla_sin_vista_priorizada() -> None:
    """La fase 122 es obligatoria: antes solo se leía si existía."""
    mp = TMP / "g_exp_prior.json"
    _write_manifest(mp, decisions=[_decision_ok()], approvals=[_approval_ok()])
    artifacts = _artifacts("prior")
    artifacts["prioritized"] = str(TMP / "no-existe-prior.md")
    out = TMP / "g_exp_prior_out.json"
    proc = run(_expanded_args(mp, artifacts, out))
    assert proc.returncode == 1
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert any("prioritized" in f for f in payload["failures"])


def test_expanded_falla_sin_reporte_de_inconsistencias() -> None:
    """La fase 125 también es obligatoria en modo ampliado."""
    mp = TMP / "g_exp_inc.json"
    _write_manifest(mp, decisions=[_decision_ok()], approvals=[_approval_ok()])
    artifacts = _artifacts("inc")
    artifacts["inconsistency"] = str(TMP / "no-existe-inc.json")
    out = TMP / "g_exp_inc_out.json"
    proc = run(_expanded_args(mp, artifacts, out))
    assert proc.returncode == 2
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert any("inconsistencies" in f for f in payload["failures"])


def test_expanded_falla_sin_decision() -> None:
    mp = TMP / "g_exp2.json"
    _write_manifest(mp)
    artifacts = _artifacts("exp2")
    out = TMP / "g_exp2_out.json"
    proc = run(_expanded_args(mp, artifacts, out))
    assert proc.returncode == 2
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert 2 in payload["exit_codes"]


def test_expanded_falla_por_warning_residual() -> None:
    mp = TMP / "g_exp3.json"
    _write_manifest(mp, decisions=[_decision_ok()], approvals=[_approval_ok()])
    artifacts = _artifacts("exp3", warnings=2)
    out = TMP / "g_exp3_out.json"
    proc = run(_expanded_args(mp, artifacts, out))
    assert proc.returncode == 4
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert 4 in payload["exit_codes"]


def test_expanded_falla_por_back_translation_fuera_de_tolerancia() -> None:
    mp = TMP / "g_exp4.json"
    _write_manifest(mp, decisions=[_decision_ok()], approvals=[_approval_ok()])
    # 5 fp + 2 fn sobre 6 totales = 100% de error, fuera de tolerancia.
    artifacts = _artifacts("exp4", fp=5, fn=2)
    out = TMP / "g_exp4_out.json"
    proc = run(_expanded_args(mp, artifacts, out))
    assert proc.returncode == 5
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert 5 in payload["exit_codes"]


def test_expanded_falla_por_recurso_externo() -> None:
    """Código 6: el informe no puede cargar ni citar un recurso remoto."""
    mp = TMP / "g_exp_acc.json"
    _write_manifest(mp, decisions=[_decision_ok()], approvals=[_approval_ok()])
    artifacts = _artifacts("acc")
    _write_md(TMP / "bi_acc.md", "# Informe bilingüe\n\n![x](https://example.org/a.png)\n")
    out = TMP / "g_exp_acc_out.json"
    proc = run(_expanded_args(mp, artifacts, out))
    assert proc.returncode == 6
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert 6 in payload["exit_codes"]


def test_expanded_pasa_con_todo_valido() -> None:
    mp = TMP / "g_exp5.json"
    file_hash = "d" * 64
    _write_manifest(
        mp,
        decisions=[_decision_ok()],
        approvals=[
            {
                "decision_id": "dec-aaaa1111",
                "approval_id": "app-aaaa1111",
                "target_hash": file_hash,
                "target_glossary_hash": "a" * 64,
                "approved_at": "2026-10-20T00:00:00Z",
                "artifact": "a.md",
            }
        ],
        files=[
            {
                "path": "a.md",
                "source_hash": file_hash,
                "current_state": "approved",
                "state_history": [{"state": "approved", "timestamp": "2026-10-20T00:00:00Z", "reason": "x"}],
                "last_transition_at": "2026-10-20T00:00:00Z",
            }
        ],
    )
    artifacts = _artifacts("exp5")
    out = TMP / "g_exp5_out.json"
    proc = run(_expanded_args(mp, artifacts, out))
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["ok"]
    assert payload["justification"] == JUSTIFICATION
    assert payload["checks"]["core_states"]["ok"]


def test_expanded_tambien_comprueba_los_estados_del_nucleo() -> None:
    """Encender el módulo no relaja la comprobación que ya hacía `basic`."""
    mp = TMP / "g_exp_estados.json"
    _write_manifest(
        mp,
        decisions=[_decision_ok()],
        approvals=[_approval_ok()],
        files=[{
            "path": "a.md",
            "source_hash": "d" * 64,
            "current_state": "deterministic_pass",
            "state_history": [{"state": "deterministic_pass", "timestamp": "2026-10-20T00:00:00Z", "reason": "x"}],
            "last_transition_at": "2026-10-20T00:00:00Z",
        }],
    )
    artifacts = _artifacts("estados")
    out = TMP / "g_exp_estados_out.json"
    proc = run(_expanded_args(mp, artifacts, out))
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert not payload["ok"]
    assert any("core_states" in f for f in payload["failures"])
    assert proc.returncode == 2


def test_falla_por_aprobacion_stale() -> None:
    mp = TMP / "g_exp6.json"
    _write_manifest(
        mp,
        decisions=[_decision_ok()],
        approvals=[
            {
                "decision_id": "dec-aaaa1111",
                "approval_id": "app-aaaa1111",
                "target_hash": "e" * 64,
                "approved_at": "2026-10-20T00:00:00Z",
                "artifact": "a.md",
            }
        ],
        files=[
            {
                "path": "a.md",
                "source_hash": "d" * 64,
                "current_state": "approved",
                "state_history": [{"state": "approved", "timestamp": "2026-10-20T00:00:00Z", "reason": "x"}],
                "last_transition_at": "2026-10-20T00:00:00Z",
            }
        ],
    )
    artifacts = _artifacts("exp6")
    out = TMP / "g_exp6_out.json"
    proc = run(_expanded_args(mp, artifacts, out))
    assert proc.returncode == 3
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert 3 in payload["exit_codes"]