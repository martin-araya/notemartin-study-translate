"""Pruebas para scripts/packetize.py (fase 022)."""

from __future__ import annotations

import tempfile
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INVENTORY = ROOT / "scripts" / "inventory.py"
PREPARE = ROOT / "scripts" / "prepare.py"
DETECT = ROOT / "scripts" / "detect_language.py"
PACKETIZE = ROOT / "scripts" / "packetize.py"
PILOT = ROOT / "tests" / "fixtures" / "pilot"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def full_pipeline() -> dict:
    inv = TMP / "inv.json"
    seg = TMP / "segments.json"
    classified = TMP / "classified.json"
    packets = TMP / "packets.json"
    assert run([str(INVENTORY), "--source", str(PILOT), "--out", str(inv)]).returncode == 0
    assert run([str(PREPARE), "--inventory", str(inv), "--segments", str(seg)]).returncode == 0
    assert run([str(DETECT), "--segments", str(seg), "--out", str(classified)]).returncode == 0
    assert run([str(PACKETIZE), "--segments", str(classified), "--out", str(packets)]).returncode == 0
    return json.loads(packets.read_text(encoding="utf-8"))


def test_paquetes_se_generan_sin_error() -> None:
    data = full_pipeline()
    assert data["total_packets"] >= 1
    assert data["validation_errors"] == []


def test_cada_paquete_tiene_owner_y_no_excede_presupuesto() -> None:
    data = full_pipeline()
    budget = data["context_budget"]
    import re
    for p in data["packets"]:
        assert re.match(r"^pack-[0-9a-f]{8}$", p["owner"])
        if not p["overflow"]:
            assert p["total_chars"] <= budget, f"{p['packet_id']} excede presupuesto"


def test_marcadores_aparecen_pares_balanceados() -> None:
    data = full_pipeline()
    for p in data["packets"]:
        text = p["translatable_text_with_markers"]
        assert text.count("§§") % 2 == 0, f"{p['packet_id']} número impar de marcadores"


def test_no_mezcla_literales_con_otros_paquetes() -> None:
    data = full_pipeline()
    for p in data["packets"]:
        assert "owner" in p
        assert "document_id" in p
        assert "path" in p


def test_segmentos_already_target_no_aparecen() -> None:
    data = full_pipeline()
    classified = json.loads((TMP / "classified.json").read_text(encoding="utf-8"))
    already_target_ids = {
        s["segment_id"]
        for f in classified["files"]
        for s in f["segments"]
        if s.get("disposition") == "already_target"
    }
    for p in data["packets"]:
        for sid in p["segments"]:
            assert sid not in already_target_ids, f"{sid} es already_target y no debe estar en paquetes"


def test_marcadores_pueden_ser_falsificados_y_validador_rechaza() -> None:
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from packetize import validate_packet
    data = full_pipeline()
    packets = data["packets"]
    assert packets
    target = dict(packets[0])
    target["translatable_text_with_markers"] = target["translatable_text_with_markers"].replace("§§", "XX", 1)
    errors = validate_packet(target, [])
    assert errors


def test_marcadores_pueden_ser_perdidos_y_validador_rechaza() -> None:
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from packetize import validate_packet
    data = full_pipeline()
    packets = data["packets"]
    assert packets
    target = dict(packets[0])
    pkt_with_segments = json.loads((TMP / "packets.json").read_text(encoding="utf-8"))
    classified = json.loads((TMP / "classified.json").read_text(encoding="utf-8"))
    target = dict(packets[0])
    seg_data = None
    for f in classified["files"]:
        if f["document_id"] == target["document_id"]:
            seg_data = f
            break
    segs_by_id = {s["segment_id"]: s for s in (seg_data or {}).get("segments", [])}
    source_segments = [segs_by_id[sid] for sid in target["segments"] if sid in segs_by_id]
    target["translatable_text_with_markers"] = ""
    errors = validate_packet(target, source_segments)
    assert errors
