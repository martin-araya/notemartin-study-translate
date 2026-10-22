"""Pruebas del aislamiento regional (fase 107)."""

from __future__ import annotations

import tempfile
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVAL_REGIONAL = ROOT / "scripts" / "eval_regional.py"
CHECK_ISOLATION = ROOT / "scripts" / "check_cache_isolation.py"
TMP = Path(tempfile.gettempdir()) / "nst-tests"
CORPUS_EN = ROOT / "tests" / "fixtures" / "regional-cache"


def _simulate_variant(variant: str, target: Path) -> dict:
    target.mkdir(parents=True, exist_ok=True)
    # Use the existing es-{es,mx,ar} fixtures as the source for each variant.
    src = ROOT / "tests" / "fixtures" / f"{variant.lower()}"
    result = subprocess.run(
        [sys.executable, str(EVAL_REGIONAL), "--variant", variant,
         "--corpus", str(src), "--out", str(target)],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    return json.loads((target / "eval.json").read_text(encoding="utf-8"))


def test_regional_eval_emite_artefactos() -> None:
    out = TMP / "reg-mx"
    if out.exists():
        shutil.rmtree(out)
    payload = _simulate_variant("es-MX", out)
    assert payload["variant"] == "es-MX"
    assert payload["metrics"]["total_segments"] > 0
    assert (out / "summary.md").exists()
    assert (out / "packets.json").exists()


def test_cache_isolation_entre_tres_variantes() -> None:
    a = TMP / "reg-iso-es"
    b = TMP / "reg-iso-mx"
    c = TMP / "reg-iso-ar"
    for p in (a, b, c):
        if p.exists():
            shutil.rmtree(p)
    _simulate_variant("es-ES", a)
    _simulate_variant("es-MX", b)
    _simulate_variant("es-AR", c)
    runs = f"{a},{b},{c}"
    result = subprocess.run(
        [sys.executable, str(CHECK_ISOLATION), "--runs", runs, "--strict",
         "--report", str(TMP / "iso.json")],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, (result.stdout, result.stderr)
    report = json.loads((TMP / "iso.json").read_text(encoding="utf-8"))
    assert report["isolated"], report
    assert report["issues"] == []


def test_paquete_vacio_o_minimo_se_respeta() -> None:
    """El paquete vacío o casi vacío se sigue creando, sin
    propagación entre variantes."""
    out = TMP / "reg-minimal"
    if out.exists():
        shutil.rmtree(out)
    payload = _simulate_variant("es-AR", out)
    for p in payload["packets"]:
        assert p["source_language"] in {"en", "fr", "es", "mixed"}, p


def test_eval_no_subreview_entre_variantes() -> None:
    """Dos ejecuciones con misma variante pero diferente corpus no
    deben compartir packet_id cuando el corpus es distinto."""
    out1 = TMP / "reg-iso-ar1"
    out2 = TMP / "reg-iso-ar2"
    for p in (out1, out2):
        if p.exists():
            shutil.rmtree(p)
    src1 = ROOT / "tests" / "fixtures" / "es-ar"
    src2 = ROOT / "tests" / "fixtures" / "regional-cache"
    r1 = subprocess.run(
        [sys.executable, str(EVAL_REGIONAL), "--variant", "es-AR",
         "--corpus", str(src1), "--out", str(out1)],
        capture_output=True, text=True, check=False,
    )
    r2 = subprocess.run(
        [sys.executable, str(EVAL_REGIONAL), "--variant", "es-AR",
         "--corpus", str(src2), "--out", str(out2)],
        capture_output=True, text=True, check=False,
    )
    assert r1.returncode == 0 and r2.returncode == 0
    p1 = json.loads((out1 / "eval.json").read_text(encoding="utf-8"))
    p2 = json.loads((out2 / "eval.json").read_text(encoding="utf-8"))
    ids1 = {p["packet_id"] for p in p1["packets"]}
    ids2 = {p["packet_id"] for p in p2["packets"]}
    assert ids1.isdisjoint(ids2), (
        f"el mismo packet_id no debe aparecer entre corpus distintos: {ids1 & ids2}"
    )
