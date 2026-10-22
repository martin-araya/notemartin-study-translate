"""Pruebas del planificador de paquetes (fase 112)."""

from __future__ import annotations

import tempfile
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEDULER = ROOT / "scripts" / "schedule_packets.py"
SCHEMA = ROOT / "schemas" / "packet_schedule.schema.json"
ACYCLIC = ROOT / "tests" / "fixtures" / "schedule" / "acyclic_packets.json"
CYCLIC = ROOT / "tests" / "fixtures" / "schedule" / "cyclic_packets.json"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def _plan(src_packets: Path, glossary: Path | None, suffix: str) -> tuple[dict, int]:
    out = TMP / f"plan-{suffix}.json"
    if out.exists():
        out.unlink()
    args = [sys.executable, str(SCHEDULER), "--packets", str(src_packets),
            "--out", str(out), "--pair", "en-es"]
    if glossary:
        args += ["--glossary", str(glossary)]
    rc = subprocess.run(args, capture_output=True, text=True, check=False).returncode
    return json.loads(out.read_text(encoding="utf-8")), rc


def test_orden_topologico_acyclic() -> None:
    plan, rc = _plan(ACYCLIC, None, "acyclic")
    assert rc == 0
    assert plan["cycles"] == []
    assert len(plan["order"]) == 4
    # bbbb2222 referencias a basic-types.md (aaaa1111) → bbbb antes que aaaa? No:
    # la regla es "depends on", así que aaaa debe ir ANTES que bbbb.
    aaa_idx = plan["order"].index("pack-aaaa1111")
    bbb_idx = plan["order"].index("pack-bbbb2222")
    assert aaa_idx < bbb_idx, f"pack-aaaa debe ir antes que pack-bbbb (aaa={aaa_idx}, bbb={bbb_idx})"


def test_glossary_hashes_siempre_presentes() -> None:
    plan, _ = _plan(ACYCLIC, None, "hash")
    assert plan["glossary_hash"]
    assert plan["order"]
    assert "phases" in plan
    assert "glossary_dependent" in plan["phases"]
    assert "anchor_dependent" in plan["phases"]
    assert "free" in plan["phases"]


def test_ciclo_es_rechazado() -> None:
    """El script detecta el ciclo intro ↔ functions y devuelve código no cero."""
    out = TMP / "plan-cyclic.json"
    if out.exists():
        out.unlink()
    rc = subprocess.run(
        [sys.executable, str(SCHEDULER),
         "--packets", str(CYCLIC),
         "--out", str(out)],
        capture_output=True, text=True, check=False,
    ).returncode
    assert rc != 0
    plan = json.loads(out.read_text(encoding="utf-8"))
    assert plan["cycles"], "se esperaba al menos un ciclo"
    assert plan["order"] == [], "el orden debe estar vacío cuando hay ciclos"


def test_glossary_deps_marcar_paquetes_con_termino() -> None:
    glossary = TMP / "glossary-simple.json"
    # Usar términos exactos que aparecen en singular.
    glossary.write_text(
        json.dumps({"entries": [{"source": "variable"}, {"source": "parameter"}]}, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )
    plan, rc = _plan(ACYCLIC, glossary, "glossary-deps")
    assert rc == 0
    deps = set(plan["phases"]["glossary_dependent"])
    assert "pack-aaaa1111" in deps  # "Variables..."
    assert "pack-bbbb2222" in deps  # "parameters..."
    assert "pack-dddd4444" not in deps


def test_expected_glossary_hash_guardado() -> None:
    expected = "a" * 64
    out = TMP / "plan-expect.json"
    if out.exists():
        out.unlink()
    rc = subprocess.run(
        [sys.executable, str(SCHEDULER),
         "--packets", str(ACYCLIC),
         "--out", str(out),
         "--expected-glossary-hash", expected],
        capture_output=True, text=True, check=False,
    ).returncode
    assert rc == 0
    plan = json.loads(out.read_text(encoding="utf-8"))
    assert plan["expected_glossary_hash"] == expected


def test_packets_inexistentes_devuelve_error() -> None:
    rc = subprocess.run(
        [sys.executable, str(SCHEDULER),
         "--packets", "/tmp/no-existe-12345.json",
         "--out", str(TMP / "plan-empty.json")],
        capture_output=True, text=True, check=False,
    ).returncode
    assert rc == 2


def test_schema_valida_payload() -> None:
    import jsonschema
    plan, _ = _plan(ACYCLIC, None, "validate")
    jsonschema.validate(plan, json.loads(SCHEMA.read_text(encoding="utf-8")))


def test_paquete_solo_phase_free_si_sin_anclas_ni_glosario() -> None:
    plan, rc = _plan(ACYCLIC, None, "only-free")
    assert rc == 0
    free = plan["phases"]["free"]
    # Al menos dddd no tiene anclas en su texto.
    assert "pack-dddd4444" in free
