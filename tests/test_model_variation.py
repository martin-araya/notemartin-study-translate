"""Pruebas de la variación entre modelos (fase 145).

Comprueban las dos mitades de la aceptación: registrar ejecuciones reales y
**no** comparar respuestas sintéticas con producción.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from compare_model_runs import compare, compatibility  # noqa: E402
from compare_model_runs import main as compare_main  # noqa: E402
from record_model_run import main as record_main  # noqa: E402
from record_model_run import missing_provenance, record_run  # noqa: E402

MANIFEST = {
    "run_id": "run-0000aaaa",
    "manifest_version": "translate/v1",
    "skill_version": "0.2.0",
    "parser": {"name": "markdown-it-py", "version": "3.0.0"},
    "anchor_policy": {"algorithm": "github-slug-v1", "version": "v1"},
    "model_metadata": {"provider": "proveedor-a", "model": "modelo-a",
                       "prompt_version": "1.0.0"},
    "glossary_snapshot": {"version": 1, "hash": "a" * 64, "frozen": True},
    "profile_snapshot": {"hash": "b" * 64},
    "files": [{"path": "docs/a.md", "source_hash": "c" * 64}],
}


def _run(root: Path, run_id: str, entries: list[dict], *, model: str = "modelo-a",
         prompt_version: str = "1.0.0", glossary_hash: str | None = None) -> Path:
    run_dir = root / run_id
    (run_dir / "translations").mkdir(parents=True, exist_ok=True)
    manifest = json.loads(json.dumps(MANIFEST))
    manifest["run_id"] = run_id
    manifest["model_metadata"]["model"] = model
    manifest["model_metadata"]["prompt_version"] = prompt_version
    manifest["glossary_snapshot"]["hash"] = glossary_hash or manifest["glossary_snapshot"]["hash"]
    (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (run_dir / "translations" / "docs_a.json").write_text(json.dumps({
        "document_id": "docs_a",
        "path": "docs/a.md",
        "entries": entries,
    }), encoding="utf-8")
    return run_dir


def _entry(sid: str, text: str) -> dict:
    return {"segment_id": sid, "original_text": "x", "translated_text": text}


def _record(root: Path, run_dir: Path, evidence: str = "real") -> dict:
    return record_run(run_dir, run_dir / "translations", evidence, allow_synthetic=True)


# --------------------------------------------------------------------------
# registro
# --------------------------------------------------------------------------

def test_el_registro_no_copia_el_texto_completo(tmp_path: Path) -> None:
    largo = "Frase de prueba con §L0§ marcador. " * 20
    run_dir = _run(tmp_path, "run-0000aaaa", [_entry("seg-00000001", largo)])
    recording = _record(tmp_path, run_dir)
    assert recording["texts_stored"] is False
    assert len(recording["segments"]["seg-00000001"]["preview"]) < len(largo)
    assert recording["segments"]["seg-00000001"]["chars"] == len(largo)


def test_el_registro_guarda_la_procedencia(tmp_path: Path) -> None:
    run_dir = _run(tmp_path, "run-0000aaaa", [_entry("seg-00000001", "texto")])
    recording = _record(tmp_path, run_dir)
    assert recording["evidence_kind"] == "real_runs"
    assert recording["synthetic"] is False
    assert recording["model"] == "modelo-a"
    assert recording["prompt_version"] == "1.0.0"
    assert recording["source_hashes"] == {"docs/a.md": "c" * 64}
    assert missing_provenance(recording) == []


def test_la_evidencia_sintetica_no_se_registra_sin_permiso(tmp_path: Path) -> None:
    run_dir = _run(tmp_path, "run-0000aaaa", [_entry("seg-00000001", "texto")])
    assert record_main(["--run", str(run_dir), "--out", str(tmp_path / "r.json"),
                      "--evidence", "synthetic"]) == 3


def test_la_cli_exige_manifiesto(tmp_path: Path) -> None:
    assert record_main(["--run", str(tmp_path / "no"), "--out", str(tmp_path / "r.json")]) == 2


def test_la_cli_rechaza_procedencia_incompleta(tmp_path: Path) -> None:
    run_dir = _run(tmp_path, "run-0000aaaa", [_entry("seg-00000001", "texto")])
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    manifest["model_metadata"]["prompt_version"] = ""
    (run_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    assert record_main(["--run", str(run_dir), "--out", str(tmp_path / "r.json")]) == 4


# --------------------------------------------------------------------------
# comparación
# --------------------------------------------------------------------------

def _write(path: Path, payload: dict) -> str:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


def test_dos_ejecuciones_identicas_dan_variacion_cero(tmp_path: Path) -> None:
    entries = [_entry("seg-00000001", "Primera."), _entry("seg-00000002", "Segunda.")]
    a = _record(tmp_path, _run(tmp_path, "run-0000aaaa", entries))
    b = _record(tmp_path, _run(tmp_path, "run-0000bbbb", entries))
    out = tmp_path / "variation.json"
    assert compare_main(["--run-a", _write(tmp_path / "a.json", a),
                 "--run-b", _write(tmp_path / "b.json", b),
                 "--out", str(out)]) == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["variation_rate"] == 0.0
    assert report["diverged"] == 0
    assert report["no_semantic_claim"] is True


def test_dos_ejecuciones_divergentes_se_cuentan(tmp_path: Path) -> None:
    a = _record(tmp_path, _run(tmp_path, "run-0000aaaa",
                               [_entry("seg-00000001", "Primera."), _entry("seg-00000002", "Segunda.")]))
    b = _record(tmp_path, _run(tmp_path, "run-0000bbbb",
                               [_entry("seg-00000001", "Primera."), _entry("seg-00000002", "Otra.")]))
    out = tmp_path / "variation.json"
    assert compare_main(["--run-a", _write(tmp_path / "a.json", a),
                 "--run-b", _write(tmp_path / "b.json", b),
                 "--out", str(out)]) == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["diverged"] == 1
    assert report["diverged_segments"] == ["seg-00000002"]
    assert report["variation_rate"] == 0.5


def test_un_segmento_ausente_cuenta_como_divergencia(tmp_path: Path) -> None:
    a = _record(tmp_path, _run(tmp_path, "run-0000aaaa",
                               [_entry("seg-00000001", "Primera."), _entry("seg-00000002", "Segunda.")]))
    b = _record(tmp_path, _run(tmp_path, "run-0000bbbb", [_entry("seg-00000001", "Primera.")]))
    report = compare(a, b)
    assert report["missing_in_b"] == ["seg-00000002"]
    assert report["variation_rate"] > 0


def test_una_ejecucion_sintetica_se_rechaza(tmp_path: Path) -> None:
    entries = [_entry("seg-00000001", "Primera.")]
    a = _record(tmp_path, _run(tmp_path, "run-0000aaaa", entries))
    synthetic = _record(tmp_path, _run(tmp_path, "run-0000cccc", entries), evidence="synthetic")
    out = tmp_path / "variation.json"
    code = compare_main(["--run-a", _write(tmp_path / "a.json", a),
                 "--run-b", _write(tmp_path / "b.json", synthetic),
                 "--out", str(out)])
    assert code == 3
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["comparable"] is False
    assert report["two_real_runs"] is False


def test_un_glosario_distinto_hace_las_ejecuciones_no_comparables(tmp_path: Path) -> None:
    entries = [_entry("seg-00000001", "Primera.")]
    a = _record(tmp_path, _run(tmp_path, "run-0000aaaa", entries))
    b = _record(tmp_path, _run(tmp_path, "run-0000bbbb", entries, glossary_hash="f" * 64))
    assert compatibility(a, b)
    out = tmp_path / "variation.json"
    assert compare_main(["--run-a", _write(tmp_path / "a.json", a),
                 "--run-b", _write(tmp_path / "b.json", b),
                 "--out", str(out)]) == 5


def test_un_prompt_distinto_hace_las_ejecuciones_no_comparables(tmp_path: Path) -> None:
    entries = [_entry("seg-00000001", "Primera.")]
    a = _record(tmp_path, _run(tmp_path, "run-0000aaaa", entries))
    b = _record(tmp_path, _run(tmp_path, "run-0000bbbb", entries, prompt_version="2.0.0"))
    out = tmp_path / "variation.json"
    assert compare_main(["--run-a", _write(tmp_path / "a.json", a),
                 "--run-b", _write(tmp_path / "b.json", b),
                 "--out", str(out)]) == 5


def test_la_razon_de_longitudes_va_marcada_como_senal(tmp_path: Path) -> None:
    a = _record(tmp_path, _run(tmp_path, "run-0000aaaa", [_entry("seg-00000001", "corta")]))
    b = _record(tmp_path, _run(tmp_path, "run-0000bbbb", [_entry("seg-00000001", "mucho más larga")]))
    report = compare(a, b)
    assert report["length_ratio"]["signal_only"] is True
    assert "no demuestra" in report["length_ratio"]["meaning"]


def test_el_informe_declara_los_dos_modelos(tmp_path: Path) -> None:
    entries = [_entry("seg-00000001", "Primera.")]
    a = _record(tmp_path, _run(tmp_path, "run-0000aaaa", entries, model="modelo-a"))
    b = _record(tmp_path, _run(tmp_path, "run-0000bbbb", entries, model="modelo-b"))
    report = compare(a, b)
    assert report["models"]["a"]["model"] == "modelo-a"
    assert report["models"]["b"]["model"] == "modelo-b"
    assert report["same_model"] is False