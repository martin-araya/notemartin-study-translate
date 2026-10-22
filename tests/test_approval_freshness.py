"""Pruebas para scripts/check_approval_freshness.py (fase 124)."""

from __future__ import annotations

import tempfile
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "check_approval_freshness.py"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write_manifest(mp: Path, *, approvals: list[dict], file_hashes: dict[str, str]) -> None:
    payload = {
        "run_id": "run-aaaaaaaa",
        "skill_version": "0.6.0",
        "parser": {"name": "x", "version": "1"},
        "anchor_policy": {"algorithm": "github", "version": "v1"},
        "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
        "glossary_snapshot": {"version": 1, "hash": "a" * 64, "frozen": True},
        "profile_snapshot": {"hash": "b" * 64},
        "inputs": {"source_root": "/tmp", "total_files": 1, "total_bytes": 1, "hashes_indexed": True},
        "decisions": [
            {
                "decision_id": "dec-aaaa1111",
                "author": "tester",
                "role": "reviewer",
                "pair": "en -> es",
                "scope": "global",
                "reason": "Aprobación de prueba",
                "reviewed_hashes": ["c" * 64],
                "decided_at": "2026-10-20T00:00:00Z",
                "kind": "approve",
            }
        ],
        "approvals": approvals,
        "files": [
            {"path": p, "source_hash": h, "current_state": "approved",
             "state_history": [{"state": "approved", "timestamp": "2026-10-20T00:00:00Z", "reason": "ok"}],
             "last_transition_at": "2026-10-20T00:00:00Z"} for p, h in file_hashes.items()
        ],
    }
    mp.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_translations(td: Path, doc_id: str, source_hash: str) -> None:
    payload = {
        "document_id": doc_id,
        "path": f"{doc_id}.md",
        "source_hash": source_hash,
        "version": 1,
        "entries": [
            {
                "segment_id": "seg-aaaa1111",
                "original_text": "Hello.",
                "translated_text": "Hola.",
                "source_hash": _sha("Hello."),
                "candidate_hash": _sha("Hola."),
            }
        ],
    }
    td.mkdir(parents=True, exist_ok=True)
    (td / f"{doc_id}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_aprobacion_vigente_pasa() -> None:
    src_hash = _sha("v1")
    cand_hash = _sha("v1-translated")
    mp = TMP / "ap1.json"
    _write_manifest(
        mp,
        approvals=[
            {
                "decision_id": "dec-aaaa1111",
                "approval_id": "app-aaaa1111",
                "target_hash": src_hash,
                "approved_at": "2026-10-20T00:00:00Z",
                "artifact": "doc-x.md",
            }
        ],
        file_hashes={"doc-x.md": src_hash},
    )

    out = TMP / "ap1.json"
    proc = run([str(SCRIPT), "--manifest", str(mp), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert all(a["status"] == "valid" for a in payload["approvals"])


def test_fuente_editada_invalida_aprobacion() -> None:
    src_hash_v1 = _sha("v1")
    src_hash_v2 = _sha("v2")
    mp = TMP / "ap2.json"
    _write_manifest(
        mp,
        approvals=[
            {
                "decision_id": "dec-aaaa1111",
                "approval_id": "app-aaaa1111",
                "target_hash": src_hash_v1,
                "approved_at": "2026-10-20T00:00:00Z",
                "artifact": "doc-y.md",
            }
        ],
        file_hashes={"doc-y.md": src_hash_v2},
    )
    out = TMP / "ap2_out.json"
    proc = run([str(SCRIPT), "--manifest", str(mp), "--out", str(out)])
    assert proc.returncode != 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["approvals"][0]["status"] == "stale"


def test_glosario_editado_invalida_aprobacion() -> None:
    glossary_hash_v1 = "d" * 64
    glossary_hash_v2 = "e" * 64
    src_hash = _sha("v1")
    mp = TMP / "ap3.json"
    payload = {
        "run_id": "run-aaaaaaaa",
        "skill_version": "0.6.0",
        "parser": {"name": "x", "version": "1"},
        "anchor_policy": {"algorithm": "github", "version": "v1"},
        "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
        "glossary_snapshot": {"version": 1, "hash": glossary_hash_v1, "frozen": True},
        "profile_snapshot": {"hash": "b" * 64},
        "inputs": {"source_root": "/tmp", "total_files": 1, "total_bytes": 1, "hashes_indexed": True},
        "decisions": [
            {
                "decision_id": "dec-aaaa1111",
                "author": "tester",
                "role": "reviewer",
                "pair": "en -> es",
                "scope": "global",
                "reason": "Aprobación de prueba",
                "reviewed_hashes": ["c" * 64],
                "decided_at": "2026-10-20T00:00:00Z",
                "kind": "approve",
            }
        ],
        "approvals": [
            {
                "decision_id": "dec-aaaa1111",
                "approval_id": "app-aaaa1111",
                "target_hash": src_hash,
                "target_glossary_hash": glossary_hash_v1,
                "approved_at": "2026-10-20T00:00:00Z",
                "artifact": "doc-z.md",
            }
        ],
        "files": [
            {"path": "doc-z.md", "source_hash": src_hash, "current_state": "approved",
             "state_history": [{"state": "approved", "timestamp": "2026-10-20T00:00:00Z", "reason": "ok"}],
             "last_transition_at": "2026-10-20T00:00:00Z"}
        ],
        "current_glossary_hash": glossary_hash_v2,
    }
    mp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    out = TMP / "ap3_out.json"
    proc = run([str(SCRIPT), "--manifest", str(mp), "--out", str(out)])
    assert proc.returncode != 0
    p = json.loads(out.read_text(encoding="utf-8"))
    assert p["approvals"][0]["status"] == "stale"


def test_aprobacion_con_mismo_hash_es_valida_independiente_del_glosario() -> None:
    """Si la aprobación no fija ``target_glossary_hash``, el glosario no la invalida."""
    src_hash = _sha("v1")
    mp = TMP / "ap4.json"
    payload = {
        "run_id": "run-aaaaaaaa",
        "skill_version": "0.6.0",
        "parser": {"name": "x", "version": "1"},
        "anchor_policy": {"algorithm": "github", "version": "v1"},
        "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
        "glossary_snapshot": {"version": 1, "hash": "d" * 64, "frozen": False},
        "profile_snapshot": {"hash": "b" * 64},
        "inputs": {"source_root": "/tmp", "total_files": 1, "total_bytes": 1, "hashes_indexed": True},
        "decisions": [
            {
                "decision_id": "dec-aaaa1111",
                "author": "tester",
                "role": "reviewer",
                "pair": "en -> es",
                "scope": "global",
                "reason": "Aprobación sin glosario",
                "reviewed_hashes": ["c" * 64],
                "decided_at": "2026-10-20T00:00:00Z",
                "kind": "approve",
            }
        ],
        "approvals": [
            {
                "decision_id": "dec-aaaa1111",
                "approval_id": "app-aaaa1111",
                "target_hash": src_hash,
                "approved_at": "2026-10-20T00:00:00Z",
                "artifact": "doc-w.md",
            }
        ],
        "files": [
            {"path": "doc-w.md", "source_hash": src_hash, "current_state": "approved",
             "state_history": [{"state": "approved", "timestamp": "2026-10-20T00:00:00Z", "reason": "ok"}],
             "last_transition_at": "2026-10-20T00:00:00Z"}
        ],
        "current_glossary_hash": "f" * 64,
    }
    mp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    out = TMP / "ap4_out.json"
    proc = run([str(SCRIPT), "--manifest", str(mp), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr
    p = json.loads(out.read_text(encoding="utf-8"))
    assert p["approvals"][0]["status"] == "valid"
