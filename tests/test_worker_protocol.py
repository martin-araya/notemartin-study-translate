"""Pruebas del protocolo de workers (fase 113)."""

from __future__ import annotations

import tempfile
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKER = ROOT / "scripts" / "worker.py"
PACKETS = ROOT / "tests" / "fixtures" / "scale" / "packets_workers.json"
PARTS = ROOT / "tests" / "fixtures" / "scale" / "parts"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def _run_worker(
    worker_id: str,
    ids_file: Path,
    out: Path,
    glossary: Path | None = None,
    content_dir: Path | None = None,
) -> int:
    out.mkdir(parents=True, exist_ok=True)
    args = [sys.executable, str(WORKER),
            "--id", worker_id,
            "--packets", str(PACKETS),
            "--packet-ids", str(ids_file),
            "--out", str(out)]
    if glossary:
        args += ["--glossary", str(glossary)]
    if content_dir:
        args += ["--content-dir", str(content_dir)]
    return subprocess.run(args, capture_output=True, text=True, check=False).returncode


def test_un_esqueleto_vacio_no_cuenta_como_traducido() -> None:
    """Un candidato sin contenido no propone transición ni se declara `done`.

    Con esta condición, ejecutar el pipeline de escala sobre un corpus
    produciría un informe verde sin haber traducido nada.
    """
    out = TMP / "W1"
    if out.exists():
        shutil.rmtree(out)
    rc = _run_worker("W1", PARTS / "W1.txt", out)
    assert rc == 0
    for pid in ("pack-33d416f2", "pack-9779fcf2"):
        cand = json.loads((out / "translations" / f"{pid}.json").read_text(encoding="utf-8"))
        assert cand["packet_id"] == pid
        assert cand["worker_id"] == "W1"
        assert cand["content"] is None
        assert cand["to_state"] is None
        assert cand["status"] == "pending_translation"
    state = json.loads((out / "state.json").read_text(encoding="utf-8"))
    assert state["status"] == "pending_translation"
    assert state["translated_count"] == 0
    assert state["pending_translation"] == state["packet_count"]


def test_con_contenido_real_el_candidato_pasa_a_deterministic_pass() -> None:
    content = TMP / "worker-content"
    if content.exists():
        shutil.rmtree(content)
    content.mkdir(parents=True)
    ids = [line for line in (PARTS / "W1.txt").read_text(encoding="utf-8").split() if line]
    for pid in ids:
        payload = {"packet_id": pid, "entries": [{"segment_id": "seg-00000001", "translated_text": "traducido"}]}
        (content / f"{pid}.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    out = TMP / "W1-contenido"
    if out.exists():
        shutil.rmtree(out)
    rc = _run_worker("W1", PARTS / "W1.txt", out, content_dir=content)
    assert rc == 0
    for pid in ids:
        cand = json.loads((out / "translations" / f"{pid}.json").read_text(encoding="utf-8"))
        assert cand["to_state"] == "deterministic_pass"
        assert cand["status"] == "translated"
        assert cand["content"]["packet_id"] == pid
        assert cand["evidence"]["content_sha256"]
    state = json.loads((out / "state.json").read_text(encoding="utf-8"))
    assert state["status"] == "done"
    assert state["translated_count"] == len(ids)


def test_worker_no_modifica_glosario() -> None:
    """El glosario debe tener el mismo hash antes y después del worker."""
    glossary_src = TMP / "glossary-test.json"
    glossary_src.write_text(
        json.dumps({"entries": [{"source": "api"}]}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    out = TMP / "W2"
    if out.exists():
        shutil.rmtree(out)
    rc = _run_worker("W2", PARTS / "W2.txt", out, glossary=glossary_src)
    assert rc == 0
    state = json.loads((out / "state.json").read_text(encoding="utf-8"))
    assert state["glossary_hash_at_start"] == state["glossary_hash_at_end"]


def test_particiones_son_disjuntas() -> None:
    """W1, W2, W3 reciben conjuntos disjuntos según los fixtures."""
    ids1 = (PARTS / "W1.txt").read_text(encoding="utf-8").split()
    ids2 = (PARTS / "W2.txt").read_text(encoding="utf-8").split()
    ids3 = (PARTS / "W3.txt").read_text(encoding="utf-8").split()
    union = set(ids1) | set(ids2) | set(ids3)
    intersection = set(ids1) & set(ids2) | set(ids1) & set(ids3) | set(ids2) & set(ids3)
    assert not intersection, f"intersección no vacía: {intersection}"
    # Suma debe coincidir con el total del paquete.
    packets = json.loads(PACKETS.read_text(encoding="utf-8"))
    all_ids = {p["packet_id"] for p in packets["packets"]}
    assert union == all_ids, f"unión {union} != all_ids {all_ids}"


def test_worker_isla_subdirectorios() -> None:
    """Cada worker escribe solo en su subdirectorio."""
    out1 = TMP / "iso-W1"
    out2 = TMP / "iso-W2"
    out3 = TMP / "iso-W3"
    for o in (out1, out2, out3):
        if o.exists():
            shutil.rmtree(o)
    _run_worker("W1", PARTS / "W1.txt", out1)
    _run_worker("W2", PARTS / "W2.txt", out2)
    _run_worker("W3", PARTS / "W3.txt", out3)
    # Ningún worker escribe en el subdirectorio de otro.
    for o in (out1, out2, out3):
        for child in o.iterdir():
            name = child.name
            assert name.startswith("W") or name in ("translations", "state.json", "errors.jsonl"), name
    # Verificar que cada translations solo tenga los packet_id de su partición.
    w1_expected = set((PARTS / "W1.txt").read_text().split())
    translations = {p.stem for p in (out1 / "translations").glob("*.json")}
    assert translations == w1_expected


def test_worker_rechaza_packet_id_desconocido() -> None:
    out = TMP / "W-bad"
    if out.exists():
        shutil.rmtree(out)
    bad_ids = TMP / "bad-ids.txt"
    bad_ids.write_text("pack-NOT-EXISTS\n", encoding="utf-8")
    rc = _run_worker("Wbad", bad_ids, out)
    assert rc != 0


def test_worker_reporta_un_estado_del_protocolo() -> None:
    """`status` distingue los tres finales: traducido, pendiente y fallido."""
    out = TMP / "W-final"
    if out.exists():
        shutil.rmtree(out)
    _run_worker("Wfinal", PARTS / "W1.txt", out)
    state = json.loads((out / "state.json").read_text(encoding="utf-8"))
    assert state["status"] in {"done", "pending_translation", "failed"}
