"""Pruebas del modo concurrente (fase 116)."""

from __future__ import annotations

import tempfile
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONCURRENT = ROOT / "scripts" / "run_concurrent.py"
PACKETS = ROOT / "tests" / "fixtures" / "scale" / "packets_workers.json"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def test_concurrent_sin_traduccion_no_aprueba_nada() -> None:
    """Sin contenido real, el manifiesto no declara ningún paquete aprobado.

    Antes contaba la partición entera como aprobada: una ejecución sin
    traducciones producía un manifiesto con todos los segmentos aprobados, y
    el gate de escala comparaba ese número con el del modo serie y daba por
    buena una cobertura que no existía.
    """
    workdir = TMP / "conc-1"
    if workdir.exists():
        shutil.rmtree(workdir)
    manifest = TMP / "conc-manifest.json"
    if manifest.exists():
        manifest.unlink()
    rc = subprocess.run(
        [sys.executable, str(CONCURRENT),
         "--packets", str(PACKETS),
         "--workdir", str(workdir),
         "--max-workers", "2",
         "--allow-single-cpu",
         "--manifest", str(manifest)],
        capture_output=True, text=True, check=False,
    ).returncode
    assert rc == 0, rc
    assert (workdir / "concurrent_summary.json").exists()
    assert manifest.exists()
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["mode"] == "concurrent"
    assert payload["max_workers"] == 2
    assert payload["approved_segment_ids"] == []
    assert payload["approved_count"] == 0
    packets = json.loads(PACKETS.read_text(encoding="utf-8"))
    assert sorted(payload["pending_segment_ids"]) == sorted(
        p["packet_id"] for p in packets["packets"]
    )
    assert payload["packet_count"] == len(packets["packets"])


def test_concurrent_propaga_content_dir_y_aprueba_lo_traducido() -> None:
    """`--content-dir` llega a los workers y solo se aprueba lo entregado."""
    packets = json.loads(PACKETS.read_text(encoding="utf-8"))
    todos = sorted(p["packet_id"] for p in packets["packets"])
    entregados = set(todos[:2])

    content_dir = TMP / "conc-content"
    if content_dir.exists():
        shutil.rmtree(content_dir)
    content_dir.mkdir(parents=True)
    for pid in entregados:
        (content_dir / f"{pid}.json").write_text(
            json.dumps({"packet_id": pid, "translations": {"§§A0§§": "texto"}},
                       ensure_ascii=False),
            encoding="utf-8",
        )

    workdir = TMP / "conc-content-run"
    if workdir.exists():
        shutil.rmtree(workdir)
    manifest = TMP / "conc-content-manifest.json"
    proc = subprocess.run(
        [sys.executable, str(CONCURRENT),
         "--packets", str(PACKETS),
         "--workdir", str(workdir),
         "--max-workers", "2",
         "--allow-single-cpu",
         "--content-dir", str(content_dir),
         "--manifest", str(manifest)],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["approved_segment_ids"] == sorted(entregados)
    assert set(payload["pending_segment_ids"]) == set(todos) - entregados
    assert payload["current_state_distribution"]["approved"] == len(entregados)
    assert payload["current_state_distribution"]["pending_translation"] == len(todos) - len(entregados)


def test_particiones_son_disjuntas_y_totalizan_los_paquetes() -> None:
    """El orquestador reparte los packet_id entre los hilos sin solapamiento."""
    workdir = TMP / "conc-part"
    if workdir.exists():
        shutil.rmtree(workdir)
    subprocess.run(
        [sys.executable, str(CONCURRENT),
         "--packets", str(PACKETS),
         "--workdir", str(workdir),
         "--max-workers", "3",
         "--allow-single-cpu"],
        capture_output=True, text=True, check=True,
    )
    workers = [d for d in (workdir / "workers").iterdir() if d.is_dir()]
    seen = []
    for w in workers:
        part = (w / "partition.txt").read_text(encoding="utf-8").split()
        seen.extend(part)
    packets = json.loads(PACKETS.read_text(encoding="utf-8"))
    expected = sorted(p["packet_id"] for p in packets["packets"])
    assert sorted(seen) == expected
    assert len(seen) == len(set(seen))


def test_rechaza_single_cpu_por_defecto() -> None:
    workdir = TMP / "conc-single"
    if workdir.exists():
        shutil.rmtree(workdir)
    rc = subprocess.run(
        [sys.executable, str(CONCURRENT),
         "--packets", str(PACKETS),
         "--workdir", str(workdir),
         "--max-workers", "2"],
        capture_output=True, text=True, check=False,
    ).returncode
    # cpu_count puede ser 1 en CI; el rechazo ocurre cuando <= 1.
    if (os.cpu_count() or 1) <= 1:
        assert rc == 2
    else:
        assert rc == 0


def test_log_persiste_eventos_por_hilo() -> None:
    workdir = TMP / "conc-log"
    if workdir.exists():
        shutil.rmtree(workdir)
    subprocess.run(
        [sys.executable, str(CONCURRENT),
         "--packets", str(PACKETS),
         "--workdir", str(workdir),
         "--max-workers", "2",
         "--allow-single-cpu"],
        capture_output=True, text=True, check=True,
    )
    log_path = workdir / "concurrency_log.json"
    assert log_path.exists()
    events = [json.loads(line)["event"] for line in log_path.read_text(encoding="utf-8").splitlines()]
    assert "started" in events
    assert "worker_finished" in events


def test_modo_concurrent_acepta_allow_single_cpu() -> None:
    workdir = TMP / "conc-allow"
    if workdir.exists():
        shutil.rmtree(workdir)
    rc = subprocess.run(
        [sys.executable, str(CONCURRENT),
         "--packets", str(PACKETS),
         "--workdir", str(workdir),
         "--max-workers", "1",
         "--allow-single-cpu"],
        capture_output=True, text=True, check=False,
    ).returncode
    assert rc == 0


def test_doc_concurrency_policy_existe_y_define_backoff() -> None:
    doc = ROOT / "references" / "concurrency-policy.md"
    assert doc.exists()
    text = doc.read_text(encoding="utf-8")
    for sec in ("Modelo de paralelismo", "Límites", "Saturación", "No pérdida"):
        assert sec in text, f"falta la sección « {sec} »"
    assert "backoff" in text.lower()
    assert "ThreadPoolExecutor" in text or "thread" in text.lower()
