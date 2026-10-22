"""Pruebas de scripts/advance_state.py (cierre de G-BETA, contrato C-RUN).

La secuencia de estados del contrato no la recorría ninguna herramienta:
`approve_pilot.py` saltaba de `translated` a `approved` y `export.py` no
tocaba el manifiesto, así que `deterministic_pass`, `semantic_pass` y
`exported` eran estados que nadie podía escribir.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADVANCE = ROOT / "scripts" / "advance_state.py"
SCHEMA = ROOT / "schemas" / "manifest.schema.json"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def manifest_with(state: str, name: str) -> Path:
    payload = {
        "run_id": "run-0badc0de",
        "created_at": "2026-10-20T00:00:00Z",
        "manifest_version": "translate/v1",
        "skill_version": "0.2.0",
        "parser": {"name": "markdown-it-py", "version": "3.0.0"},
        "anchor_policy": {"algorithm": "github-slug-v1", "version": "v1"},
        "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
        "glossary_snapshot": {"version": 1, "hash": "0" * 64, "frozen": True},
        "profile_snapshot": {"hash": "0" * 64},
        "inputs": {"source_root": "/tmp/src", "total_files": 1, "total_bytes": 1, "hashes_indexed": True},
        "files": [{
            "path": "docs/a.md",
            "document_id": "doc-00000001",
            "source_hash": "a" * 64,
            "current_state": state,
            "state_history": [{"state": state, "timestamp": "2026-10-20T00:00:00Z", "reason": "origen"}],
            "last_transition_at": "2026-10-20T00:00:00Z",
        }],
    }
    path = TMP / f"advance_{name}.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def advance(manifest: Path, to_state: str, name: str, *extra: str) -> subprocess.CompletedProcess:
    out = TMP / f"advance_{name}.report.json"
    return run([
        str(ADVANCE), "--manifest", str(manifest), "--to", to_state,
        "--reason", f"prueba {name}", "--out", str(out), *extra,
    ])


def test_secuencia_completa_se_recorre() -> None:
    """La secuencia entera sigue siendo recorrible, con su evidencia.

    Hasta la corrección de INV-12 esta prueba avanzaba a `semantic_pass` y
    `approved` sin revisión ni firma, es decir, legitimaba el defecto que
    corregía. Ahora cada estado que afirma lectura exige la evidencia que
    afirma: revisión para `semantic_pass`, revisión y firma humana para
    `approved`.
    """
    manifest = manifest_with("inventoried", "secuencia")
    base = Path(tempfile.gettempdir()) / "nst-sec"
    if base.exists():
        shutil.rmtree(base)
    translations = base / "translations"
    translations.mkdir(parents=True)
    (translations / "doc-00000001.json").write_text(
        json.dumps({"document_id": "doc-00000001", "entries": [{"segment_id": "seg-1"}]}),
        encoding="utf-8",
    )
    segments = base / "segments.json"
    segments.write_text(json.dumps({"files": [{
        "document_id": "doc-00000001",
        "path": "docs/a.md",
        "segments": [{"segment_id": "seg-1", "disposition": "translatable"}],
    }]}), encoding="utf-8")
    ledger = base / "review.json"
    ledger.write_text(json.dumps({"reviews": [{
        "path": "docs/a.md", "verdict": "accept",
        "segments_reviewed": 1, "reviewed_at": "2026-10-22T10:00:00Z",
    }]}), encoding="utf-8")
    _firmar(manifest)

    for to_state in ["prepared", "translated", "deterministic_pass"]:
        proc = advance(manifest, to_state, "secuencia", "--translations", str(translations), "--apply")
        assert proc.returncode == 0, f"{to_state}: {proc.stderr}"
    for to_state in ["semantic_pass", "approved"]:
        proc = advance(
            manifest, to_state, "secuencia",
            "--translations", str(translations), "--segments", str(segments),
            "--review", str(ledger), "--apply",
        )
        assert proc.returncode == 0, f"{to_state}: {proc.stderr}"
        data = json.loads(manifest.read_text(encoding="utf-8"))
        assert data["files"][0]["current_state"] == to_state

    proc = advance(manifest, "exported", "secuencia", "--apply")
    assert proc.returncode == 0, proc.stderr
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["files"][0]["current_state"] == "exported"
    import jsonschema

    jsonschema.validate(data, json.loads(SCHEMA.read_text(encoding="utf-8")))


def test_saltar_estados_se_rechaza() -> None:
    manifest = manifest_with("translated", "salto")
    proc = advance(manifest, "exported", "salto", "--apply")
    assert proc.returncode == 1
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["files"][0]["current_state"] == "translated"


def test_de_translated_a_approved_se_rechaza() -> None:
    """El salto que hacía `approve_pilot.py` es exactamente este."""
    manifest = manifest_with("translated", "piloto")
    proc = advance(manifest, "approved", "piloto", "--apply")
    assert proc.returncode == 1
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["files"][0]["current_state"] == "translated"


def test_bloqueado_no_puede_exportarse() -> None:
    manifest = manifest_with("blocked", "bloqueado")
    proc = advance(manifest, "exported", "bloqueado", "--apply")
    assert proc.returncode == 1
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["files"][0]["current_state"] == "blocked"


def test_sin_apply_no_escribe() -> None:
    manifest = manifest_with("translated", "simulacion")
    before = manifest.read_text(encoding="utf-8")
    proc = advance(manifest, "deterministic_pass", "simulacion")
    assert proc.returncode == 0
    assert manifest.read_text(encoding="utf-8") == before
    report = json.loads((TMP / "advance_simulacion.report.json").read_text(encoding="utf-8"))
    assert report["applied"] is False
    assert report["transitioned"] == 1


def test_el_historial_registra_el_motivo() -> None:
    manifest = manifest_with("semantic_pass", "motivo")
    base = Path(tempfile.gettempdir()) / "nst-motivo"
    if base.exists():
        shutil.rmtree(base)
    translations = base / "translations"
    translations.mkdir(parents=True)
    (translations / "doc-00000001.json").write_text(
        json.dumps({"document_id": "doc-00000001", "entries": [{"segment_id": "seg-1"}]}),
        encoding="utf-8",
    )
    segments = base / "segments.json"
    segments.write_text(json.dumps({"files": [{
        "document_id": "doc-00000001",
        "path": "docs/a.md",
        "segments": [{"segment_id": "seg-1", "disposition": "translatable"}],
    }]}), encoding="utf-8")
    ledger = base / "review.json"
    ledger.write_text(json.dumps({"reviews": [{
        "path": "docs/a.md", "verdict": "accept",
        "segments_reviewed": 1, "reviewed_at": "2026-10-22T10:00:00Z",
    }]}), encoding="utf-8")
    _firmar(manifest)

    proc = advance(
        manifest, "approved", "motivo",
        "--translations", str(translations), "--segments", str(segments),
        "--review", str(ledger), "--apply",
    )
    assert proc.returncode == 0, proc.stderr
    data = json.loads(manifest.read_text(encoding="utf-8"))
    history = data["files"][0]["state_history"]
    assert history[-1]["state"] == "approved"
    assert "prueba motivo" in history[-1]["reason"]


def test_transicion_ilegal_en_un_archivo_no_arrastra_a_los_demas() -> None:
    manifest = manifest_with("approved", "mixtas")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["files"].append({
        "path": "docs/b.md",
        "document_id": "doc-00000002",
        "source_hash": "b" * 64,
        "current_state": "blocked",
        "state_history": [{"state": "blocked", "timestamp": "2026-10-20T00:00:00Z", "reason": "bloqueo"}],
        "last_transition_at": "2026-10-20T00:00:00Z",
    })
    manifest.write_text(json.dumps(data, indent=2), encoding="utf-8")

    proc = advance(manifest, "exported", "mixtas", "--apply")
    assert proc.returncode == 0, proc.stderr
    after = json.loads(manifest.read_text(encoding="utf-8"))
    states = {f["path"]: f["current_state"] for f in after["files"]}
    assert states == {"docs/a.md": "exported", "docs/b.md": "blocked"}

def test_no_avanza_sin_evidencia_de_traduccion() -> None:
    """INV-12: avanzar a `translated` exige traducción real en disco.

    `advance_state --from prepared` movía los 2682 archivos del corpus
    beta a `translated` con cero segmentos traducidos, porque la
    secuencia legal no distingue «el agente dijo que terminó» de «hay
    un archivo de traducción con entradas». Con `--translations` la
    comprobación existe y los archivos sin traducción quedan fuera.

    Un archivo ``doc-X.json`` con ``entries: []`` no es evidencia
    suficiente: ``advance_state --to translated`` exige al menos una
    entrada, y un fichero vacío queda como ``prepared``.
    """
    import json as _json
    import tempfile

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
    from advance_state import load_translation_evidence, select_files

    base = Path(tempfile.gettempdir()) / "nst-advance-evidence"
    if base.exists():
        shutil.rmtree(base)
    trans = base / "translations"
    trans.mkdir(parents=True)
    (trans / "doc-1.json").write_text(
        _json.dumps({"document_id": "doc-1", "entries": [{"segment_id": "seg-a"}]}),
        encoding="utf-8",
    )
    (trans / "doc-3.json").write_text(
        _json.dumps({"document_id": "doc-3", "entries": []}), encoding="utf-8"
    )

    manifest = {"files": [
        {"path": "a.md", "document_id": "doc-1", "current_state": "prepared"},
        {"path": "b.md", "document_id": "doc-2", "current_state": "prepared"},
        {"path": "c.md", "document_id": "doc-3", "current_state": "prepared"},
    ]}

    evidence = load_translation_evidence(str(trans))
    # sólo doc-1 tiene entradas reales; doc-3 queda fuera porque su
    # archivo está vacío y doc-2 directamente no existe.
    assert evidence == {"doc-1"}

    selected, rejected = select_files(manifest, "prepared", "translated", evidence)
    assert [r["document_id"] for r in selected] == ["doc-1"]
    assert {r["document_id"] for r in rejected} == {"doc-2", "doc-3"}

    # Sin el flag de evidencia el comportamiento histórico se conserva.
    selected_all, _ = select_files(manifest, "prepared", "translated", None)
    assert len(selected_all) == 3


def test_descartar_no_exige_evidencia() -> None:
    """Marcar `blocked` no afirma trabajo hecho: no necesita traducción."""
    import json as _json
    import tempfile

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
    from advance_state import select_files

    base = Path(tempfile.gettempdir()) / "nst-advance-blocked"
    if base.exists():
        shutil.rmtree(base)
    trans = base / "translations"
    trans.mkdir(parents=True)

    manifest = {"files": [
        {"path": "a.md", "document_id": "doc-1", "current_state": "prepared"},
    ]}
    selected, _ = select_files(manifest, "prepared", "blocked", set())
    assert len(selected) == 1


def test_un_archivo_de_traduccion_corrupto_no_cuenta_como_evidencia() -> None:
    """Un JSON ilegible no añade identificadores a la evidencia.

    Informa de un fallo de persistencia, no de traducción hecha: el
    nombre del archivo no puede reclamarse como evidencia porque no se
    sabe qué hay dentro.
    """
    import tempfile

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
    from advance_state import load_translation_evidence

    base = Path(tempfile.gettempdir()) / "nst-advance-corrupt"
    if base.exists():
        shutil.rmtree(base)
    trans = base / "translations"
    trans.mkdir(parents=True)
    (trans / "doc-1.json").write_text("{no es json", encoding="utf-8")
    (trans / "doc-2.json").write_text('{"document_id":"doc-2","entries":[{"segment_id":"s"}]}', encoding="utf-8")

    evidence = load_translation_evidence(str(trans))
    assert "doc-1" not in evidence
    assert "doc-2" in evidence


def test_un_directorio_inexistente_es_evidencia_vacia() -> None:
    import tempfile

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
    from advance_state import load_translation_evidence

    assert load_translation_evidence(str(Path(tempfile.gettempdir()) / "nst-no-existe-xyz")) == set()
    assert load_translation_evidence(None) is None


def test_la_evidencia_se_indexa_por_path_y_translation_id() -> None:
    """Los archivos ambiguos persisten bajo ``trl-XYZ``, no ``document_id``.

    El ``file_record`` del manifiesto solo conoce ``document_id`` y
    ``path``, así que la evidencia debe poder consultarse por cualquiera
    de las dos. Si solo se indexara por nombre de archivo, los stubs
    de Tailwind (todos ``doc-085fb377``) parecerían no tener
    evidencia aunque sus 21 traducciones estén en ``translations/``.
    """
    import json as _json
    import tempfile

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
    from advance_state import load_translation_evidence, select_files

    base = Path(tempfile.gettempdir()) / "nst-advance-collision"
    if base.exists():
        shutil.rmtree(base)
    trans = base / "translations"
    trans.mkdir(parents=True)
    (trans / "trl-aaaaaaaaaaaa.json").write_text(_json.dumps({
        "document_id": "doc-085fb377", "path": "tailwindcss/installation/index.md",
        "translation_id": "trl-aaaaaaaaaaaa",
        "entries": [{"segment_id": "seg-1"}],
    }), encoding="utf-8")
    (trans / "trl-bbbbbbbbbbbb.json").write_text(_json.dumps({
        "document_id": "doc-085fb377", "path": "tailwindcss/installation/tailwind-cli.md",
        "translation_id": "trl-bbbbbbbbbbbb",
        "entries": [{"segment_id": "seg-1"}],
    }), encoding="utf-8")

    manifest = {"files": [
        {"path": "tailwindcss/installation/index.md", "document_id": "doc-085fb377", "current_state": "prepared"},
        {"path": "tailwindcss/installation/tailwind-cli.md", "document_id": "doc-085fb377", "current_state": "prepared"},
    ]}

    evidence = load_translation_evidence(str(trans))
    assert "trl-aaaaaaaaaaaa" in evidence
    assert "trl-bbbbbbbbbbbb" in evidence
    assert "doc-085fb377" in evidence
    assert "tailwindcss/installation/index.md" in evidence

    selected, _ = select_files(manifest, "prepared", "translated", evidence)
    assert [r["path"] for r in selected] == [
        "tailwindcss/installation/index.md",
        "tailwindcss/installation/tailwind-cli.md",
    ]


# --------------------------------------------------------------------------
# INV-12: afirmar revisión sin revisión, y afirmar aprobación sin firma humana
# --------------------------------------------------------------------------
#
# `--translations` impedía escribir `translated` sin traducción en disco,
# pero `semantic_pass` y `approved` solo exigían eso: bastaba un archivo de
# traducción con una entrada para escribir que el corpus estaba revisado y
# aprobado. Es la misma fábrica de progreso ya corregida dos veces en la
# corrida beta, ahora por la otra puerta.


def _corpus(tmp_name: str, paths: list[str], state: str) -> tuple[Path, Path, Path]:
    """Manifiesto de N documentos, segmentos traducibles y traducciones."""
    base = Path(tempfile.gettempdir()) / tmp_name
    if base.exists():
        shutil.rmtree(base)
    translations = base / "translations"
    translations.mkdir(parents=True)

    files = []
    segments_files = []
    for index, rel in enumerate(paths, start=1):
        doc_id = f"doc-{index:08d}"
        files.append({
            "path": rel,
            "document_id": doc_id,
            "source_hash": f"{index:064x}",
            "current_state": state,
            "state_history": [{"state": state, "timestamp": "2026-10-20T00:00:00Z", "reason": "origen"}],
            "last_transition_at": "2026-10-20T00:00:00Z",
        })
        segments_files.append({
            "document_id": doc_id,
            "path": rel,
            "segments": [
                {"segment_id": f"seg-{index}-{n}", "disposition": "translatable",
                 "byte_range": {"start": 0, "end": 10}}
                for n in range(2)
            ],
        })
        (translations / f"{doc_id}.json").write_text(
            json.dumps({"document_id": doc_id, "path": rel, "entries": [{"segment_id": f"seg-{index}-0"}]}),
            encoding="utf-8",
        )

    manifest = base / "manifest.json"
    manifest.write_text(json.dumps({
"run_id": "run-0000abcd",
        "created_at": "2026-10-20T00:00:00Z",
        "manifest_version": "translate/v1",
        "skill_version": "0.2.3",
        "parser": {"name": "markdown-it-py", "version": "3.0.0"},
        "anchor_policy": {"algorithm": "github-slug-v1", "version": "v1"},
        "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
        "glossary_snapshot": {"version": 1, "hash": "0" * 64, "frozen": True},
        "profile_snapshot": {"hash": "0" * 64},
        "inputs": {"source_root": str(base), "total_files": len(paths), "total_bytes": 1, "hashes_indexed": True},
        "files": files,
    }, indent=2), encoding="utf-8")

    segments = base / "segments.json"
    segments.write_text(json.dumps({"files": segments_files}, indent=2), encoding="utf-8")
    return manifest, segments, translations


def _ledger(tmp_name: str, reviews: list[dict]) -> Path:
    path = Path(tempfile.gettempdir()) / tmp_name
    path.write_text(json.dumps({"run_id": "run-review", "reviews": reviews}, indent=2), encoding="utf-8")
    return path


def _firmar(manifest: Path, con_decision: bool = True, con_reviewer: bool = True) -> None:
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if con_decision:
        data["decisions"] = [{
            "decision_id": "dec-a1b2c3d4",
            "author": "alias-revisor",
            "role": "reviewer",
            "pair": "en->es",
            "scope": "global",
            "reason": "revision contrastada con la fuente, sin dudas bloqueantes",
            "reviewed_hashes": ["a" * 64],
            "decided_at": "2026-10-22T10:00:00Z",
            "kind": "approve",
        }]
    if con_reviewer:
        data["reviewers"] = [{
            "pair": "en-es",
            "name": "alias-revisor",
            "kind": "human",
            "signed_at": "2026-10-22T10:00:00Z",
            "scope": "global",
        }]
    manifest.write_text(json.dumps(data, indent=2), encoding="utf-8")


def test_avanzar_a_semantic_pass_sin_revision_es_error() -> None:
    """Sin `--review` no se escribe que algo se revisó."""
    manifest, segments, translations = _corpus("nst-review-sin-ledger", ["a.md"], "deterministic_pass")
    proc = run([
        str(ADVANCE), "--manifest", str(manifest), "--to", "semantic_pass",
        "--reason", "revision contrastada", "--translations", str(translations),
        "--segments", str(segments), "--apply",
    ])
    assert proc.returncode == 1
    assert "review" in proc.stderr.lower()
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["files"][0]["current_state"] == "deterministic_pass"


def test_avanzar_a_semantic_pass_con_cobertura_completa() -> None:
    manifest, segments, translations = _corpus("nst-review-cubierto", ["a.md", "b.md"], "deterministic_pass")
    ledger = _ledger("nst-review-cubierto.json", [
        {"path": "a.md", "verdict": "accept", "segments_reviewed": 2, "reviewed_at": "2026-10-22T10:00:00Z"},
        {"path": "b.md", "verdict": "accept", "segments_reviewed": 2, "reviewed_at": "2026-10-22T10:00:00Z"},
    ])
    proc = run([
        str(ADVANCE), "--manifest", str(manifest), "--to", "semantic_pass",
        "--reason", "revision contrastada", "--translations", str(translations),
        "--segments", str(segments), "--review", str(ledger), "--apply",
    ])
    assert proc.returncode == 0, proc.stderr
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert {f["current_state"] for f in data["files"]} == {"semantic_pass"}


def test_cobertura_parcial_no_arrastra_a_los_demas() -> None:
    """Un documento revisado avanza; el no revisado se queda atrás."""
    manifest, segments, translations = _corpus("nst-review-parcial", ["a.md", "b.md"], "deterministic_pass")
    ledger = _ledger("nst-review-parcial.json", [
        {"path": "a.md", "verdict": "accept", "segments_reviewed": 2, "reviewed_at": "2026-10-22T10:00:00Z"},
    ])
    proc = run([
        str(ADVANCE), "--manifest", str(manifest), "--to", "semantic_pass",
        "--reason", "revision parcial", "--translations", str(translations),
        "--segments", str(segments), "--review", str(ledger), "--apply",
    ])
    assert proc.returncode == 0, proc.stderr
    states = {f["path"]: f["current_state"] for f in json.loads(manifest.read_text(encoding="utf-8"))["files"]}
    assert states == {"a.md": "semantic_pass", "b.md": "deterministic_pass"}


def test_un_ledger_que_se_declare_cubierto_mas_de_lo_que_hay_es_error() -> None:
    """El denominador sale del archivo de segmentos, no del propio ledger.

    Si el ledger declarara su propio total, un ledger vacío declararía
    cobertura completa y el gate dejaría de medir nada.
    """
    manifest, segments, translations = _corpus("nst-review-mentira", ["a.md"], "deterministic_pass")
    ledger = _ledger("nst-review-mentira.json", [
        {"path": "a.md", "verdict": "accept", "segments_reviewed": 0, "reviewed_at": "2026-10-22T10:00:00Z"},
    ])
    proc = run([
        str(ADVANCE), "--manifest", str(manifest), "--to", "semantic_pass",
        "--reason", "ledger autoinflado", "--translations", str(translations),
        "--segments", str(segments), "--review", str(ledger), "--apply",
    ])
    assert proc.returncode == 1
    assert json.loads(manifest.read_text(encoding="utf-8"))["files"][0]["current_state"] == "deterministic_pass"


def test_un_segmento_rechazado_no_pasa_a_semantic_pass() -> None:
    manifest, segments, translations = _corpus("nst-review-rechazo", ["a.md"], "deterministic_pass")
    ledger = _ledger("nst-review-rechazo.json", [
        {"path": "a.md", "verdict": "reject_with_reason", "segments_reviewed": 2,
         "reason": "negacion invertida", "reviewed_at": "2026-10-22T10:00:00Z"},
    ])
    proc = run([
        str(ADVANCE), "--manifest", str(manifest), "--to", "semantic_pass",
        "--reason", "rechazos abiertos", "--translations", str(translations),
        "--segments", str(segments), "--review", str(ledger), "--apply",
    ])
    assert proc.returncode == 1
    assert json.loads(manifest.read_text(encoding="utf-8"))["files"][0]["current_state"] == "deterministic_pass"


def test_avanzar_a_approved_exige_firma_humana() -> None:
    """Revisión asistida no es aprobación: sin firmante humano no se escribe."""
    manifest, segments, translations = _corpus("nst-aprob-sin-firma", ["a.md"], "semantic_pass")
    ledger = _ledger("nst-aprob-sin-firma.json", [
        {"path": "a.md", "verdict": "accept", "segments_reviewed": 2, "reviewed_at": "2026-10-22T10:00:00Z"},
    ])
    proc = run([
        str(ADVANCE), "--manifest", str(manifest), "--to", "approved",
        "--reason", "sin dudas bloqueantes", "--translations", str(translations),
        "--segments", str(segments), "--review", str(ledger), "--apply",
    ])
    assert proc.returncode == 1
    lowered = proc.stderr.lower()
    assert "firma" in lowered or "human" in lowered
    assert json.loads(manifest.read_text(encoding="utf-8"))["files"][0]["current_state"] == "semantic_pass"


def test_una_decision_sin_reviewer_humano_no_basta() -> None:
    """`kind: assisted` en `reviewers[]` no es una firma humana."""
    manifest, segments, translations = _corpus("nst-aprob-sin-reviewer", ["a.md"], "semantic_pass")
    ledger = _ledger("nst-aprob-sin-reviewer.json", [
        {"path": "a.md", "verdict": "accept", "segments_reviewed": 2, "reviewed_at": "2026-10-22T10:00:00Z"},
    ])
    _firmar(manifest, con_decision=True, con_reviewer=False)
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["reviewers"] = [{
        "pair": "en-es", "name": "agente", "kind": "assisted",
        "signed_at": "2026-10-22T10:00:00Z", "scope": "global",
    }]
    manifest.write_text(json.dumps(data, indent=2), encoding="utf-8")

    proc = run([
        str(ADVANCE), "--manifest", str(manifest), "--to", "approved",
        "--reason", "solo revision asistida", "--translations", str(translations),
        "--segments", str(segments), "--review", str(ledger), "--apply",
    ])
    assert proc.returncode == 1
    assert json.loads(manifest.read_text(encoding="utf-8"))["files"][0]["current_state"] == "semantic_pass"


def test_una_decision_sin_reviewed_hashes_no_basta() -> None:
    """Una decisión sin hashes revisados no cubre nada (fase 123)."""
    manifest, segments, translations = _corpus("nst-aprob-sin-hashes", ["a.md"], "semantic_pass")
    ledger = _ledger("nst-aprob-sin-hashes.json", [
        {"path": "a.md", "verdict": "accept", "segments_reviewed": 2, "reviewed_at": "2026-10-22T10:00:00Z"},
    ])
    _firmar(manifest)
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["decisions"][0]["reviewed_hashes"] = []
    manifest.write_text(json.dumps(data, indent=2), encoding="utf-8")

    proc = run([
        str(ADVANCE), "--manifest", str(manifest), "--to", "approved",
        "--reason", "decision sin hashes", "--translations", str(translations),
        "--segments", str(segments), "--review", str(ledger), "--apply",
    ])
    assert proc.returncode == 1
    assert json.loads(manifest.read_text(encoding="utf-8"))["files"][0]["current_state"] == "semantic_pass"


def test_una_decision_que_cubre_una_ruta_no_aprueba_el_resto() -> None:
    """`scope` es el alcance real de la firma, no una formalidad."""
    manifest, segments, translations = _corpus("nst-aprob-alcance", ["a.md", "b.md"], "semantic_pass")
    ledger = _ledger("nst-aprob-alcance.json", [
        {"path": "a.md", "verdict": "accept", "segments_reviewed": 2, "reviewed_at": "2026-10-22T10:00:00Z"},
        {"path": "b.md", "verdict": "accept", "segments_reviewed": 2, "reviewed_at": "2026-10-22T10:00:00Z"},
    ])
    _firmar(manifest)
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["decisions"][0]["scope"] = ["a.md"]
    data["reviewers"][0]["scope"] = ["a.md"]
    manifest.write_text(json.dumps(data, indent=2), encoding="utf-8")

    proc = run([
        str(ADVANCE), "--manifest", str(manifest), "--to", "approved",
        "--reason", "firma parcial", "--translations", str(translations),
        "--segments", str(segments), "--review", str(ledger), "--apply",
    ])
    assert proc.returncode == 0, proc.stderr
    states = {f["path"]: f["current_state"] for f in json.loads(manifest.read_text(encoding="utf-8"))["files"]}
    assert states == {"a.md": "approved", "b.md": "semantic_pass"}


def test_avanzar_a_approved_con_revision_y_firma() -> None:
    manifest, segments, translations = _corpus("nst-aprob-ok", ["a.md"], "semantic_pass")
    ledger = _ledger("nst-aprob-ok.json", [
        {"path": "a.md", "verdict": "accept", "segments_reviewed": 2, "reviewed_at": "2026-10-22T10:00:00Z"},
    ])
    _firmar(manifest)
    proc = run([
        str(ADVANCE), "--manifest", str(manifest), "--to", "approved",
        "--reason", "revisado y firmado por una persona", "--translations", str(translations),
        "--segments", str(segments), "--review", str(ledger), "--apply",
    ])
    assert proc.returncode == 0, proc.stderr
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["files"][0]["current_state"] == "approved"
    import jsonschema
    jsonschema.validate(data, json.loads(SCHEMA.read_text(encoding="utf-8")))


def test_deterministic_pass_no_exige_revision() -> None:
    """La validación determinista es previa: no se inventa una exigencia falsa."""
    manifest, segments, translations = _corpus("nst-det-sin-review", ["a.md"], "translated")
    proc = run([
        str(ADVANCE), "--manifest", str(manifest), "--to", "deterministic_pass",
        "--reason", "validate.py sin errores", "--translations", str(translations),
        "--segments", str(segments), "--apply",
    ])
    assert proc.returncode == 0, proc.stderr
    assert json.loads(manifest.read_text(encoding="utf-8"))["files"][0]["current_state"] == "deterministic_pass"


def test_semantic_pass_sin_segments_no_puede_medir_cobertura() -> None:
    """Sin denominador no hay cobertura que medir: se rechaza, no se pasa."""
    manifest, _, translations = _corpus("nst-review-sin-segments", ["a.md"], "deterministic_pass")
    ledger = _ledger("nst-review-sin-segments.json", [
        {"path": "a.md", "verdict": "accept", "segments_reviewed": 99, "reviewed_at": "2026-10-22T10:00:00Z"},
    ])
    proc = run([
        str(ADVANCE), "--manifest", str(manifest), "--to", "semantic_pass",
        "--reason", "sin denominador", "--translations", str(translations),
        "--review", str(ledger), "--apply",
    ])
    assert proc.returncode == 1
    assert json.loads(manifest.read_text(encoding="utf-8"))["files"][0]["current_state"] == "deterministic_pass"
