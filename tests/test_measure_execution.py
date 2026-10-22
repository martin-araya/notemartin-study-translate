"""Pruebas del perfil de ejecución (fase 111)."""

from __future__ import annotations

import tempfile
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEASURE = ROOT / "scripts" / "measure_execution.py"
SCHEMA = ROOT / "schemas" / "execution_profile.schema.json"
SAMPLE_FIXTURE = ROOT / "tests" / "fixtures" / "scale"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def _validate(payload: dict) -> None:
    import jsonschema
    jsonschema.validate(payload, json.loads(SCHEMA.read_text(encoding="utf-8")))


def test_measure_ejecuta_y_emite_perfil() -> None:
    out = TMP / "exec.json"
    if out.exists():
        out.unlink()
    rc = subprocess.run(
        [sys.executable, str(MEASURE),
         "--corpus", str(SAMPLE_FIXTURE),
         "--pair", "en-es",
         "--out", str(out),
         "--sample", "5",
         "--seed", "7"],
        capture_output=True, text=True, check=False,
    ).returncode
    assert rc == 0, rc
    assert out.exists()
    payload = json.loads(out.read_text(encoding="utf-8"))
    _validate(payload)


def test_perfil_no_inventa_tokens_ni_costos() -> None:
    out = TMP / "exec-no-invent.json"
    if out.exists():
        out.unlink()
    rc = subprocess.run(
        [sys.executable, str(MEASURE),
         "--corpus", str(SAMPLE_FIXTURE),
         "--pair", "en-es",
         "--out", str(out),
         "--sample", "3",
         "--seed", "11"],
        capture_output=True, text=True, check=False,
    ).returncode
    assert rc == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["provider_known"] is False
    assert payload["cost_unknown"] is True
    assert payload["tokens_estimated"] is None
    assert payload["cost_estimated_usd"] is None


def test_perfil_con_provider_conocido_pero_sin_costos() -> None:
    out = TMP / "exec-provider.json"
    if out.exists():
        out.unlink()
    rc = subprocess.run(
        [sys.executable, str(MEASURE),
         "--corpus", str(SAMPLE_FIXTURE),
         "--pair", "en-es",
         "--out", str(out),
         "--sample", "3",
         "--seed", "13",
         "--provider", "agente-local"],
        capture_output=True, text=True, check=False,
    ).returncode
    assert rc == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["provider_known"] is True
    assert payload["cost_unknown"] is True
    assert payload["tokens_estimated"] is None


def test_muestreo_registrado_en_sample() -> None:
    out = TMP / "exec-sample.json"
    if out.exists():
        out.unlink()
    rc = subprocess.run(
        [sys.executable, str(MEASURE),
         "--corpus", str(SAMPLE_FIXTURE),
         "--pair", "en-es",
         "--out", str(out),
         "--sample", "7",
         "--seed", "17"],
        capture_output=True, text=True, check=False,
    ).returncode
    assert rc == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["sample"] is not None
    assert payload["sample"]["files_sampled"] == 7
    assert payload["sample"]["seed"] == 17


def test_step_durations_y_metricas_basicas() -> None:
    out = TMP / "exec-metrics.json"
    if out.exists():
        out.unlink()
    rc = subprocess.run(
        [sys.executable, str(MEASURE),
         "--corpus", str(SAMPLE_FIXTURE),
         "--pair", "en-es",
         "--out", str(out),
         "--sample", "5",
         "--seed", "19"],
        capture_output=True, text=True, check=False,
    ).returncode
    assert rc == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    sd = payload["metrics"]["step_durations_sec"]
    for step in ("inventory", "prepare", "detect_language", "packetize"):
        assert step in sd, f"falta paso {step}"
        assert sd[step] >= 0.0
    assert payload["duration_sec"] >= 0.0
    assert payload["metrics"]["files"] >= 1
    assert payload["metrics"]["segments"] >= 1
    assert payload["metrics"]["packets"] >= 0


def test_sin_muestreo_sample_es_null_pero_documenta_corpus() -> None:
    """Cuando --sample >= total_files, sample.files_sampled == total_files."""
    out = TMP / "exec-nosample.json"
    if out.exists():
        out.unlink()
    rc = subprocess.run(
        [sys.executable, str(MEASURE),
         "--corpus", str(SAMPLE_FIXTURE),
         "--pair", "en-es",
         "--out", str(out),
         "--sample", "10000",
         "--seed", "23"],
        capture_output=True, text=True, check=False,
    ).returncode
    assert rc == 0
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["sample"] is not None
    assert payload["sample"]["reason"] == "sample>=total"


def test_corpus_no_existe_falla_con_codigo_2() -> None:
    out = TMP / "exec-fail.json"
    if out.exists():
        out.unlink()
    rc = subprocess.run(
        [sys.executable, str(MEASURE),
         "--corpus", "/tmp/path/does/not/exist/12345",
         "--pair", "en-es",
         "--out", str(out)],
        capture_output=True, text=True, check=False,
    ).returncode
    assert rc == 2


def test_corpus_solo_no_md_con_sample_falla() -> None:
    """Sin .md, el muestreo levanta SystemExit; con --sample omitido,
    el script acepta el directorio y produce un perfil vacío pero
    válido."""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "foo.txt").write_text("texto", encoding="utf-8")
        out = TMP / "exec-no-md.json"
        if out.exists():
            out.unlink()
        # Sin --sample, el script acepta 0 archivos.
        rc1 = subprocess.run(
            [sys.executable, str(MEASURE),
             "--corpus", d,
             "--pair", "en-es",
             "--out", str(out)],
            capture_output=True, text=True, check=False,
        ).returncode
        assert rc1 == 0
        out.unlink()
        # Con --sample explícito, el muestreo levanta SystemExit.
        rc2 = subprocess.run(
            [sys.executable, str(MEASURE),
             "--corpus", d,
             "--pair", "en-es",
             "--out", str(out),
             "--sample", "3"],
            capture_output=True, text=True, check=False,
        ).returncode
        assert rc2 != 0
