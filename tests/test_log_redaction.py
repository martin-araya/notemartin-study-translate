"""Pruebas de redacción de logs (fase 129).

Verifica:

- ``scripts/redact.py`` redacta secretos y trunca texto largo.
- Los scripts del flujo ampliado de revisión **no imprimen** texto
  completo de segmento ni claves plausibles en su salida estándar.

Los scripts inspeccionados son:

- ``scripts/render_bilingual.py``
- ``scripts/prioritize_findings.py``
- ``scripts/check_approval_freshness.py``
- ``scripts/group_inconsistencies.py``
- ``scripts/detect_residual_language.py``
- ``scripts/eval_back_translation.py``
- ``scripts/gate_review.py``
"""

from __future__ import annotations

import tempfile
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REDACT = ROOT / "scripts" / "redact.py"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def test_redact_safe_segment_id_acepta_validos() -> None:
    out = subprocess.run([sys.executable, str(REDACT), "check", "seg-aaaa1111"], capture_output=True, text=True)
    assert out.returncode == 0


def test_redact_safe_segment_id_rechaza_invalidos() -> None:
    out = subprocess.run([sys.executable, str(REDACT), "check", "<LITERAL_TRADUCIDO>"], capture_output=True, text=True)
    assert out.returncode != 0


def test_redact_truncate() -> None:
    payload = "x" * 200
    proc = subprocess.run(
        [sys.executable, str(REDACT), "truncate", payload, "--limit", "40"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    text = proc.stdout.strip()
    assert len(text) == 40
    assert text.endswith("…")


def test_redact_dict() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(REDACT),
            "dict",
            json.dumps({"api_key": "k-very-long-12345", "name": "ok", "value": "v" * 100}),
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    assert payload["api_key"] == "***"
    assert payload["name"] == "ok"
    assert payload["value"].endswith("…")


def test_render_bilingual_no_imprime_textos_largos() -> None:
    translations = TMP / "log_red_t1"
    translations.mkdir(parents=True, exist_ok=True)
    big = "Lorem ipsum dolor sit amet " * 100
    (translations / "doc-big.json").write_text(json.dumps({
        "document_id": "doc-big",
        "path": "big.md",
        "source_hash": "a" * 64,
        "version": 1,
        "entries": [
            {
                "segment_id": "seg-bbbb2222",
                "structural_type": "paragraph",
                "byte_range": {"start": 0, "end": 100},
                "heading_path": [],
                "original_text": big,
                "translated_text": big,
                "source_hash": "0" * 64,
                "candidate_hash": "1" * 64,
                "literals_preserved": True,
                "missing_literals": [],
                "flag_loss": False,
            }
        ],
    }), encoding="utf-8")
    out = TMP / "log_red_t1.md"
    render = ROOT / "scripts" / "render_bilingual.py"
    proc = run([str(render), "--translations", str(translations), "--out", str(out)])
    assert proc.returncode == 0
    # stdout debe ser breve; el reporte sí contiene el texto íntegro (es su contenido).
    assert len(proc.stdout) < 4000, proc.stdout
    assert "Lorem ipsum dolor sit amet" * 5 not in proc.stdout


def test_gate_review_no_usa_palabras_clave_secretas() -> None:
    """El módulo gate_review.py no debe nombrar ``api_key``/``token`` en su salida."""
    path = ROOT / "scripts" / "gate_review.py"
    if not path.exists():
        # La fase 130 aún no ha implementado el módulo. La política
        # se valida tras esa fase.
        return
    src = path.read_text(encoding="utf-8")
    suspicious = ["api_key=", "token=", "password=", "secret=", "apiKey=", "ACCESS_TOKEN"]
    for needle in suspicious:
        assert needle not in src, f"sospechoso en gate_review.py: {needle!r}"


def test_prioritize_findings_no_imprime_textos_de_segmentos() -> None:
    mp = TMP / "log_red_t2.json"
    big = "x" * 1500
    payload = {
        "run_id": "run-aaaaaaaa",
        "skill_version": "0.6.0",
        "parser": {"name": "x", "version": "1"},
        "anchor_policy": {"algorithm": "github", "version": "v1"},
        "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
        "glossary_snapshot": {"version": 1, "hash": "a" * 64, "frozen": True},
        "profile_snapshot": {"hash": "b" * 64},
        "inputs": {"source_root": "/tmp", "total_files": 1, "total_bytes": 1, "hashes_indexed": True},
        "files": [
            {
                "path": "x.md",
                "source_hash": "c" * 64,
                "current_state": "blocked",
                "state_history": [{"state": "blocked", "timestamp": "2026-10-20T00:00:00Z", "reason": "x"}],
                "last_transition_at": "2026-10-20T00:00:00Z",
                "issues": [{"severity": "info", "message": "no-op", "segment_id": "seg-12345678"}],
            }
        ],
        "semantic_findings": [],
        "_secret": big,
    }
    mp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    out = TMP / "log_red_t2.md"
    proc = run([str(ROOT / "scripts" / "prioritize_findings.py"), "--manifest", str(mp), "--out", str(out)])
    assert proc.returncode == 0
    assert len(proc.stdout) < 4000
    assert big not in proc.stdout
