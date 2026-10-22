"""Pruebas de scripts/receive_translations.py (cierre de G-BETA).

El script que recibe lo que el agente produce tiene que rechazar la
respuesta mal formada antes de que llegue al ensamblado. Un validador
permisivo convierte una omisión en cobertura aparentemente completa, que
es exactamente lo que INV-04 prohíbe.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from receive_translations import expected_literals, validate_packet  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "receive_translations.py"

BASE = Path(tempfile.gettempdir()) / "nst-receive"


def make_packet(**over):
    packet = {
        "packet_id": "pack-test",
        "document_id": "doc-1",
        "path": "a.md",
        "markers": "§§",
        "segments": ["seg-a", "seg-b"],
        "translatable_text_with_markers": "Options for rendering. Use §§animate.enter§§ here.",
    }
    packet.update(over)
    packet["_source_files"] = [{
        "document_id": "doc-1",
        "segments": [
            {"segment_id": "seg-a", "translatable_text": "Options for rendering."},
            {"segment_id": "seg-b", "translatable_text": "Use `animate.enter` here."},
        ],
    }]
    return packet


def test_una_respuesta_completa_se_acepta() -> None:
    packet = make_packet()
    response = {"translations": [
        {"segment_id": "seg-a", "translated_text": "Opciones para el renderizado."},
        {"segment_id": "seg-b", "translated_text": "Usa §§animate.enter§§ aquí."},
    ]}
    entries, findings = validate_packet(packet, response)
    assert findings == []
    assert len(entries) == 2
    assert all(e["literals_preserved"] for e in entries)


def test_un_segmento_ausente_es_hallazgo() -> None:
    packet = make_packet()
    response = {"translations": [
        {"segment_id": "seg-a", "translated_text": "Opciones para el renderizado."},
    ]}
    _, findings = validate_packet(packet, response)
    kinds = [f["kind"] for f in findings]
    assert "segmento_ausente" in kinds


def test_un_segment_id_ajeno_se_rechaza() -> None:
    packet = make_packet()
    response = {"translations": [
        {"segment_id": "seg-a", "translated_text": "Opciones."},
        {"segment_id": "seg-b", "translated_text": "Usa §§animate.enter§§ aquí."},
        {"segment_id": "seg-inventado", "translated_text": "No pedido."},
    ]}
    entries, findings = validate_packet(packet, response)
    assert [f["kind"] for f in findings] == ["segment_id_ajeno"]
    assert all(e["segment_id"] != "seg-inventado" for e in entries)


def test_los_marcadores_se_retiran_de_la_respuesta_persistente() -> None:
    """El validador exige translated_text sin ``§§...§§``."""
    import shutil

    base = BASE / "markers"
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True)
    (base / "packets.json").write_text(json.dumps({"packets": [make_packet()]}), encoding="utf-8")
    (base / "segments.json").write_text(json.dumps({"files": [{
        "document_id": "doc-1", "path": "a.md", "source_hash": "0" * 64,
        "segments": [
            {"segment_id": "seg-a", "translatable_text": "Options for rendering."},
            {"segment_id": "seg-b", "translatable_text": "Use `animate.enter` here."},
        ],
    }]}), encoding="utf-8")
    (base / "responses.json").write_text(json.dumps([
        {"packet_id": "pack-test", "translations": [
            {"segment_id": "seg-a", "translated_text": "Opciones para el renderizado."},
            {"segment_id": "seg-b", "translated_text": "Usa §§animate.enter§§ aquí."},
        ]}
    ]), encoding="utf-8")
    out = base / "translations"

    proc = subprocess.run([
        sys.executable, str(SCRIPT),
        "--packets", str(base / "packets.json"),
        "--segments", str(base / "segments.json"),
        "--responses", str(base / "responses.json"),
        "--translations", str(out),
        "--apply",
    ], capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr

    written = json.loads((out / "doc-1.json").read_text(encoding="utf-8"))
    assert all("§§" not in e["translated_text"] for e in written["entries"]), [e["translated_text"] for e in written["entries"]]
    # El literal protegido sigue presente, sin envoltorio.
    assert "animate.enter" in next(e["translated_text"] for e in written["entries"] if e["segment_id"] == "seg-b")


def test_un_literal_perdido_marca_flag_loss() -> None:
    packet = make_packet()
    response = {"translations": [
        {"segment_id": "seg-a", "translated_text": "Opciones."},
        {"segment_id": "seg-b", "translated_text": "Usa aquí."},
    ]}
    entries, findings = validate_packet(packet, response)
    assert "literal_perdido" in [f["kind"] for f in findings]
    assert all(e["flag_loss"] for e in entries)
    assert all(not e["literals_preserved"] for e in entries)


def test_un_marcador_desequilibrado_se_rechaza() -> None:
    packet = make_packet()
    response = {"translations": [
        {"segment_id": "seg-a", "translated_text": "Opciones."},
        {"segment_id": "seg-b", "translated_text": "Usa §§animate.enter aquí."},
    ]}
    _, findings = validate_packet(packet, response)
    assert "marcador_desequilibrado" in [f["kind"] for f in findings]


def test_un_segmento_duplicado_se_rechaza() -> None:
    packet = make_packet()
    response = {"translations": [
        {"segment_id": "seg-a", "translated_text": "Opciones."},
        {"segment_id": "seg-a", "translated_text": "Otra vez."},
        {"segment_id": "seg-b", "translated_text": "Usa §§animate.enter§§ aquí."},
    ]}
    _, findings = validate_packet(packet, response)
    assert "segmento_duplicado" in [f["kind"] for f in findings]


def test_una_respuesta_no_texto_se_rechaza() -> None:
    packet = make_packet()
    response = {"translations": [
        {"segment_id": "seg-a", "translated_text": None},
        {"segment_id": "seg-b", "translated_text": "Usa §§animate.enter§§ aquí."},
    ]}
    _, findings = validate_packet(packet, response)
    assert "respuesta_no_texto" in [f["kind"] for f in findings]


def test_los_literals_esperados_son_los_del_paquete() -> None:
    packet = make_packet()
    assert expected_literals(packet) == ["animate.enter"]


def test_el_texto_de_origen_se_conserva() -> None:
    packet = make_packet()
    response = {"translations": [
        {"segment_id": "seg-a", "translated_text": "Opciones para el renderizado."},
        {"segment_id": "seg-b", "translated_text": "Usa §§animate.enter§§ aquí."},
    ]}
    entries, _ = validate_packet(packet, response)
    by_id = {e["segment_id"]: e for e in entries}
    assert by_id["seg-a"]["original_text"] == "Options for rendering."


def test_el_cli_persiste_y_es_atomico() -> None:
    import shutil

    if BASE.exists():
        shutil.rmtree(BASE)
    BASE.mkdir(parents=True)

    packets = {"packets": [make_packet()]}
    packets["packets"][0].pop("_source_files", None)
    (BASE / "packets.json").write_text(json.dumps(packets), encoding="utf-8")

    segments = {"files": [{
        "document_id": "doc-1",
        "path": "a.md",
        "source_hash": "0" * 64,
        "segments": [
            {"segment_id": "seg-a", "translatable_text": "Options for rendering."},
            {"segment_id": "seg-b", "translatable_text": "Use `animate.enter` here."},
        ],
    }]}
    (BASE / "segments.json").write_text(json.dumps(segments), encoding="utf-8")

    (BASE / "responses.json").write_text(json.dumps([
        {"packet_id": "pack-test", "translations": [
            {"segment_id": "seg-a", "translated_text": "Opciones para el renderizado."},
            {"segment_id": "seg-b", "translated_text": "Usa §§animate.enter§§ aquí."},
        ]}
    ]), encoding="utf-8")

    out = BASE / "translations"
    proc = subprocess.run([
        sys.executable, str(SCRIPT),
        "--packets", str(BASE / "packets.json"),
        "--segments", str(BASE / "segments.json"),
        "--responses", str(BASE / "responses.json"),
        "--translations", str(out),
        "--apply",
    ], capture_output=True, text=True, check=False)

    assert proc.returncode == 0, proc.stderr
    report = json.loads(proc.stdout)
    assert report["packets_accepted"] == 1
    assert report["segments_accepted"] == 2
    assert not (out / "doc-1.json.tmp").exists()

    written = json.loads((out / "doc-1.json").read_text(encoding="utf-8"))
    assert len(written["entries"]) == 2


def test_el_cli_sin_apply_no_escribe() -> None:
    import shutil

    base = BASE / "dry"
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True)

    packets = {"packets": [make_packet()]}
    packets["packets"][0].pop("_source_files", None)
    (base / "packets.json").write_text(json.dumps(packets), encoding="utf-8")
    (base / "segments.json").write_text(json.dumps({"files": [{
        "document_id": "doc-1", "path": "a.md", "source_hash": "0" * 64, "segments": [],
    }]}), encoding="utf-8")
    (base / "responses.json").write_text(json.dumps([]), encoding="utf-8")

    out = base / "translations"
    proc = subprocess.run([
        sys.executable, str(SCRIPT),
        "--packets", str(base / "packets.json"),
        "--segments", str(base / "segments.json"),
        "--responses", str(base / "responses.json"),
        "--translations", str(out),
        "--dry-run",
    ], capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr
    assert not out.exists()


def test_un_paquete_ajeno_se_rechaza() -> None:
    import shutil

    base = BASE / "ajeno"
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True)

    (base / "packets.json").write_text(json.dumps({"packets": []}), encoding="utf-8")
    (base / "segments.json").write_text(json.dumps({"files": []}), encoding="utf-8")
    (base / "responses.json").write_text(json.dumps([
        {"packet_id": "pack-inventado", "translations": []}
    ]), encoding="utf-8")

    proc = subprocess.run([
        sys.executable, str(SCRIPT),
        "--packets", str(base / "packets.json"),
        "--segments", str(base / "segments.json"),
        "--responses", str(base / "responses.json"),
        "--translations", str(base / "translations"),
        "--apply",
    ], capture_output=True, text=True, check=False)

    assert proc.returncode == 1
    report = json.loads(proc.stdout)
    assert "paquete_ajeno" in report["findings_by_kind"]