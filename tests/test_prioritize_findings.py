"""Pruebas de scripts/prioritize_findings.py (fase 122)."""

from __future__ import annotations

import tempfile
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "prioritize_findings.py"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def _write_manifest(mp: Path, *, gates: list[dict], issues: list[dict], semantics: list[dict]) -> None:
    payload = {
        "files": [
            {"path": p, "gates": g, "issues": i}
            for (p, g, i) in zip(
                ["a.md", "b.md", "c.md"], gates, issues
            )
        ],
        "semantic_findings": semantics,
        "run_id": "run-aaaaaaaa",
        "skill_version": "0.6.0",
    }
    mp.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_gate_pending_siempre_visible() -> None:
    """Un hallazgo gate_pending no se oculta por baja prioridad."""
    mp = TMP / "prio1.json"
    _write_manifest(
        mp,
        gates=[
            [
                {"name": "literals", "status": "block"},
                {"name": "structure", "status": "block"},
            ],
            [],
            [],
        ],
        issues=[
            [{"severity": "info", "segment_id": "seg-low-1", "message": "typo"}],
            [],
            [],
        ],
        semantics=[
            {
                "dimension": "negation",
                "severity": "info",
                "segment_id": "seg-low-1",
                "path": "a.md",
                "message": "negation maybe lost",
            }
        ],
    )
    out = TMP / "prio1.md"
    proc = run([str(SCRIPT), "--manifest", str(mp), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr or proc.stdout
    text = out.read_text(encoding="utf-8")
    assert "gate_pending" in text.lower() or "## Gate pendiente" in text or "gate pendiente" in text.lower()
    assert "seg-low-1" in text


def test_orden_riesgo_alto_precede_bajo() -> None:
    """Los riesgos altos preceden a los bajos pero no eliminan la sección de gate."""
    mp = TMP / "prio2.json"
    _write_manifest(
        mp,
        gates=[
            [],
            [],
            [],
        ],
        issues=[
            [{"severity": "warning", "segment_id": "seg-typo-1", "message": "typo", "category": "typo"}],
            [{"severity": "error", "segment_id": "seg-neg-1", "message": "negation flipped", "category": "negation_invertida"}],
            [{"severity": "info", "segment_id": "seg-info-1", "message": "minor"}],
        ],
        semantics=[],
    )
    out = TMP / "prio2.md"
    proc = run([str(SCRIPT), "--manifest", str(mp), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr or proc.stdout
    text = out.read_text(encoding="utf-8")
    # El orden debe poner riesgos altos antes; ``seg-typo-1`` (typo, riesgo bajo)
    # no debe preceder a ``seg-neg-1`` (negación invertida, riesgo alto).
    # Adicionalmente, el segmento con severity=error debe salir antes.
    pos_neg = text.find("seg-neg-1")
    pos_typo = text.find("seg-typo-1")
    assert pos_neg != -1 and pos_typo != -1
    assert pos_neg < pos_typo, (
        f"negación invertida debe preceder a typo: neg={pos_neg} typo={pos_typo}"
    )


def test_prioridades_deterministas() -> None:
    """Dos llamadas iguales producen el mismo orden."""
    mp = TMP / "prio3.json"
    _write_manifest(
        mp,
        gates=[[], [], []],
        issues=[
            [
                {"severity": "warning", "segment_id": "seg-w-1", "message": "w1", "category": "negation_soft"},
                {"severity": "warning", "segment_id": "seg-w-2", "message": "w2", "category": "negation_soft"},
            ],
            [],
            [],
        ],
        semantics=[],
    )
    out_a = TMP / "prio3a.md"
    out_b = TMP / "prio3b.md"
    assert run([str(SCRIPT), "--manifest", str(mp), "--out", str(out_a)]).returncode == 0
    assert run([str(SCRIPT), "--manifest", str(mp), "--out", str(out_b)]).returncode == 0
    text_a = out_a.read_text(encoding="utf-8")
    text_b = out_b.read_text(encoding="utf-8")
    assert text_a == text_b


def test_segmentos_bloqueados_visibles() -> None:
    mp = TMP / "prio4.json"
    _write_manifest(
        mp,
        gates=[
            [],
            [],
            [],
        ],
        issues=[
            [],
            [{"severity": "info", "segment_id": "seg-info-1", "message": "nothing"}],
            [],
        ],
        semantics=[],
    )
    # Anota blocked en el manifest
    payload = json.loads(mp.read_text(encoding="utf-8"))
    payload["files"][1]["current_state"] = "blocked"
    mp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    out = TMP / "prio4.md"
    assert run([str(SCRIPT), "--manifest", str(mp), "--out", str(out)]).returncode == 0
    text = out.read_text(encoding="utf-8")
    assert "blocked" in text.lower() or "bloqueado" in text.lower()
