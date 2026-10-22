"""Pruebas del invalidador transitivo (fase 119)."""

from __future__ import annotations

import tempfile
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INVALIDATE = ROOT / "scripts" / "invalidate_cache.py"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def _seed(cache_root: Path, entries: list[tuple[str, str, str, str]]) -> None:
    """Llena el caché con entradas; cada tupla es
    (segment_id, source_hash, glossary_hash, locale)."""
    if cache_root.exists():
        shutil.rmtree(cache_root)
    cache_root.mkdir(parents=True, exist_ok=True)
    scripts = ROOT / "scripts" / "translation_cache.py"
    for seg, src, gls, loc in entries:
        proc = subprocess.run(
            [sys.executable, str(scripts),
             "store", "--segment", seg,
             "--source-hash", src, "--glossary-hash", gls,
             "--locale", loc, "--content", "x",
             "--root", str(cache_root)],
            capture_output=True, text=True, check=False,
        )
        assert proc.returncode == 0


def test_glossary_change_invalida_entradas() -> None:
    cache = TMP / "inv-1"
    sha_old = "1" * 64
    sha_new = "2" * 64
    _seed(cache, [
        ("seg-1", "a" * 64, sha_old, "es-ES"),
        ("seg-2", "b" * 64, sha_old, "es-ES"),
        ("seg-3", "a" * 64, sha_new, "es-ES"),
    ])
    out = TMP / "inv-plan-1.json"
    if out.exists():
        out.unlink()
    proc = subprocess.run(
        [sys.executable, str(INVALIDATE),
         "--cache-root", str(cache),
         "--glossary-old", sha_old,
         "--glossary-new", sha_new,
         "--out", str(out)],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 1, proc.stdout
    plan = json.loads(out.read_text(encoding="utf-8"))
    assert plan["counts"]["direct"] == 2
    assert plan["counts"]["transitive"] == 0


def test_glossary_sin_cambio_no_invalida() -> None:
    cache = TMP / "inv-2"
    sha = "1" * 64
    _seed(cache, [("seg-1", "a" * 64, sha, "es-ES")])
    proc = subprocess.run(
        [sys.executable, str(INVALIDATE),
         "--cache-root", str(cache),
         "--glossary-old", sha, "--glossary-new", sha],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 0


def test_anchors_old_new_con_ancla_en_entrada() -> None:
    """Si el cambio del anchor coincide con un anchor registrado en la
    entrada del caché, la entrada queda invalidada.

    La entrada se construye con ``translation_cache.store()``, no a mano: el
    campo ``anchors`` no estaba en el esquema y el almacén no lo escribía, así
    que esta comprobación solo se podía probar con una entrada fabricada a
    mano, es decir, con una entrada que la herramienta real nunca produce.
    """
    cache = TMP / "inv-anchors"
    sha = "1" * 64
    cache.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(ROOT / "scripts"))
    import translation_cache

    entry = translation_cache.store(
        "seg-tip", "a" * 64, sha, "es-ES", "Pista inicial", cache,
        packet_id="pkt-1", anchors=["tip"],
    )
    assert entry["anchors"] == ["tip"]

    # La entrada cumple el esquema de caché, con el campo que la fase 119 lee.
    schema = json.loads((ROOT / "schemas" / "cache_entry.schema.json").read_text(encoding="utf-8"))
    import jsonschema

    jsonschema.validate(entry, schema)

    src_old = TMP / "anc-old.json"
    src_new = TMP / "anc-new.json"
    src_old.write_text(
        json.dumps({"anchors": {"tip": {"target": "old_target", "translation": "Tip"}}}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    src_new.write_text(
        json.dumps({"anchors": {"tip": {"target": "new_target", "translation": "Pista"}}}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    out = TMP / "inv-plan-anc.json"
    if out.exists():
        out.unlink()
    proc = subprocess.run(
        [sys.executable, str(INVALIDATE),
         "--cache-root", str(cache),
         "--anchors-old", str(src_old),
         "--anchors-new", str(src_new),
         "--out", str(out)],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 1, proc.stdout
    plan = json.loads(out.read_text(encoding="utf-8"))
    assert plan["counts"]["transitive"] >= 1, plan


def test_anchors_sin_cambio_no_invalida() -> None:
    cache = TMP / "inv-anchors-2"
    sha = "1" * 64
    _seed(cache, [("seg-x", "a" * 64, sha, "es-ES")])
    same = TMP / "anc-same.json"
    same.write_text(
        json.dumps({"anchors": {"tip": {"translation": "Tip"}}}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    proc = subprocess.run(
        [sys.executable, str(INVALIDATE),
         "--cache-root", str(cache),
         "--anchors-old", str(same),
         "--anchors-new", str(same)],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 0


def test_idempotencia() -> None:
    cache = TMP / "inv-idem"
    sha_old = "1" * 64
    sha_new = "2" * 64
    _seed(cache, [("seg-x", "a" * 64, sha_old, "es-ES")])
    out1 = TMP / "inv-idem-1.json"
    out2 = TMP / "inv-idem-2.json"
    for f in (out1, out2):
        if f.exists():
            f.unlink()
    args = [sys.executable, str(INVALIDATE),
            "--cache-root", str(cache),
            "--glossary-old", sha_old, "--glossary-new", sha_new]
    p1 = subprocess.run(args + ["--out", str(out1)], capture_output=True, text=True, check=False)
    p2 = subprocess.run(args + ["--out", str(out2)], capture_output=True, text=True, check=False)
    assert p1.returncode == p2.returncode == 1
    pl1 = json.loads(out1.read_text(encoding="utf-8"))
    pl2 = json.loads(out2.read_text(encoding="utf-8"))
    assert pl1["counts"] == pl2["counts"]
    assert pl1["direct_invalidations"] == pl2["direct_invalidations"]


def test_cache_vacio_es_ok() -> None:
    cache = TMP / "inv-empty"
    if cache.exists():
        shutil.rmtree(cache)
    proc = subprocess.run(
        [sys.executable, str(INVALIDATE),
         "--cache-root", str(cache),
         "--glossary-old", "a" * 64, "--glossary-new", "b" * 64],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 0
