"""Pruebas del perfil multilingüe (fase 104)."""

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
PILOT = ROOT / "tests" / "fixtures" / "mixed_lang"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def _pipeline(recognized: str | None = None) -> dict:
    inv = TMP / "inv-mixed.json"
    seg = TMP / "segments-mixed.json"
    classified = TMP / "classified-mixed.json"
    rc1 = run([str(INVENTORY), "--source", str(PILOT), "--out", str(inv)]).returncode
    rc2 = run([str(PREPARE), "--inventory", str(inv), "--segments", str(seg)]).returncode
    cmd = [str(DETECT), "--segments", str(seg), "--out", str(classified)]
    if recognized:
        cmd += ["--recognized", recognized]
    rc3 = run(cmd).returncode
    assert rc1 == 0 and rc2 == 0 and rc3 == 0, (rc1, rc2, rc3)
    return json.loads(classified.read_text(encoding="utf-8"))


def test_reconocidos_por_defecto_solo_en() -> None:
    payload = _pipeline()
    recognized = payload.get("recognized_source_languages", [])
    assert recognized == ["en"], recognized


def test_reconocidos_con_fr_clasifica_fr() -> None:
    payload = _pipeline(recognized="en,fr")
    french_file = next(f for f in payload["files"] if f["path"] == "02-french.md")
    fr_count = sum(1 for s in french_file["segments"] if s.get("language") == "fr")
    assert fr_count > 0, "con --recognized en,fr los segmentos franceses deben etiquetarse fr"


def test_archivo_en_puro_se_etiqueta_en() -> None:
    payload = _pipeline(recognized="en,fr")
    en_file = next(f for f in payload["files"] if f["path"] == "01-english.md")
    en_count = sum(1 for s in en_file["segments"] if s.get("language") == "en")
    assert en_count > 0


def test_mixed_profile_rechaza_paquete_con_dos_idiomas() -> None:
    inv = TMP / "inv-mp.json"
    seg = TMP / "segments-mp.json"
    classified = TMP / "classified-mp.json"
    out = TMP / "packets-mp.json"
    profile = TMP / "mixed_profile_strict.json"
    profile.write_text(
        json.dumps(
            {
                "enabled": True,
                "allowed_source_languages": ["en", "fr"],
                "forbid_double_translation": True,
            }
        ),
        encoding="utf-8",
    )
    rc1 = run([str(INVENTORY), "--source", str(PILOT), "--out", str(inv)]).returncode
    rc2 = run([str(PREPARE), "--inventory", str(inv), "--segments", str(seg)]).returncode
    cmd = [str(DETECT), "--segments", str(seg), "--out", str(classified), "--recognized", "en,fr"]
    rc3 = run(cmd).returncode
    rc4 = run(
        [
            str(PACKETIZE),
            "--segments", str(classified),
            "--out", str(out),
            "--mixed-profile", str(profile),
        ]
    )
    assert rc1 == rc2 == rc3 == 0
    payload = json.loads(Path(out).read_text(encoding="utf-8"))
    fr_packet_count = sum(1 for p in payload["packets"] if p.get("source_language") == "fr")
    en_packet_count = sum(1 for p in payload["packets"] if p.get("source_language") == "en")
    assert fr_packet_count >= 1
    assert en_packet_count >= 1
    for p in payload["packets"]:
        assert p.get("source_language") in {"fr", "en", "es"}, p


def test_archivo_es_no_se_retraduce() -> None:
    inv = TMP / "inv-es.json"
    seg = TMP / "segments-es.json"
    classified = TMP / "classified-es.json"
    out = TMP / "packets-es.json"
    profile = TMP / "mixed_profile_es.json"
    profile.write_text(
        json.dumps(
            {
                "enabled": True,
                "allowed_source_languages": ["en", "fr"],
                "forbid_double_translation": True,
            }
        ),
        encoding="utf-8",
    )
    rc1 = run([str(INVENTORY), "--source", str(PILOT), "--out", str(inv)]).returncode
    rc2 = run([str(PREPARE), "--inventory", str(inv), "--segments", str(seg)]).returncode
    rc3 = run([str(DETECT), "--segments", str(seg), "--out", str(classified), "--recognized", "en,fr"]).returncode
    rc4 = run([str(PACKETIZE), "--segments", str(classified), "--out", str(out),
               "--mixed-profile", str(profile)]).returncode
    assert rc1 == rc2 == rc3 == rc4 == 0
    payload = json.loads(Path(out).read_text(encoding="utf-8"))
    for p in payload["packets"]:
        segments = p["segments"]
        for seg_id in segments:
            doc = next(f for f in json.loads(Path(classified).read_text(encoding="utf-8"))["files"]
                       if seg_id in [s["segment_id"] for s in f["segments"]])
            seg_obj = next(s for s in doc["segments"] if s["segment_id"] == seg_id)
            assert seg_obj.get("language") != "es" or seg_obj.get("disposition") == "already_target", (
                f"un paquete traducible no debe contener segmentos 'es': {seg_id}"
            )


def test_schema_profile_tiene_mixed_profile() -> None:
    schema = json.loads((ROOT / "schemas" / "profile.schema.json").read_text(encoding="utf-8"))
    assert "mixed_profile" in schema["properties"]
    assert "reviewer_status" in schema["properties"]
    assert "source_language_policy" in schema["properties"]
    assert "citations_policy" in schema["properties"]
