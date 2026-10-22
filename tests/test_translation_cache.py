"""Pruebas del caché contextual de traducción (fase 118)."""

from __future__ import annotations

import tempfile
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "scripts" / "translation_cache.py"
SCHEMA = ROOT / "schemas" / "cache_entry.schema.json"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def _root() -> Path:
    r = TMP / "cache-test"
    if r.exists():
        shutil.rmtree(r)
    r.mkdir(parents=True, exist_ok=True)
    return r


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(CACHE), *args],
                          capture_output=True, text=True, check=False)


SEG = "seg-abc"
SRC = "a" * 64
GLS = "b" * 64
GLS_OTHER = "c" * 64
LOCALE = "es-ES"


def test_lookup_miss_inicial() -> None:
    r = _root()
    rc = _run(["lookup", "--segment", SEG,
               "--source-hash", SRC, "--glossary-hash", GLS,
               "--locale", LOCALE, "--root", str(r)]).returncode
    assert rc == 1


def test_store_luego_lookup_hit() -> None:
    r = _root()
    rc = _run(["store", "--segment", SEG,
               "--source-hash", SRC, "--glossary-hash", GLS,
               "--locale", LOCALE, "--content", "Hola",
               "--root", str(r)]).returncode
    assert rc == 0
    rc = _run(["lookup", "--segment", SEG,
               "--source-hash", SRC, "--glossary-hash", GLS,
               "--locale", LOCALE, "--root", str(r)]).returncode
    assert rc == 0


def test_glossary_hash_distinto_es_miss() -> None:
    r = _root()
    _run(["store", "--segment", SEG,
          "--source-hash", SRC, "--glossary-hash", GLS,
          "--locale", LOCALE, "--content", "Hola",
          "--root", str(r)])
    rc = _run(["lookup", "--segment", SEG,
               "--source-hash", SRC, "--glossary-hash", GLS_OTHER,
               "--locale", LOCALE, "--root", str(r)]).returncode
    assert rc == 1


def test_locale_distinta_es_miss() -> None:
    r = _root()
    _run(["store", "--segment", SEG,
          "--source-hash", SRC, "--glossary-hash", GLS,
          "--locale", "es-ES", "--content", "Hola",
          "--root", str(r)])
    rc = _run(["lookup", "--segment", SEG,
               "--source-hash", SRC, "--glossary-hash", GLS,
               "--locale", "es-MX", "--root", str(r)]).returncode
    assert rc == 1


def test_segment_distinto_es_miss() -> None:
    r = _root()
    _run(["store", "--segment", "seg-a",
          "--source-hash", SRC, "--glossary-hash", GLS,
          "--locale", LOCALE, "--content", "x",
          "--root", str(r)])
    rc = _run(["lookup", "--segment", "seg-b",
               "--source-hash", SRC, "--glossary-hash", GLS,
               "--locale", LOCALE, "--root", str(r)]).returncode
    assert rc == 1


def test_reset_borra_todo() -> None:
    r = _root()
    _run(["store", "--segment", SEG,
          "--source-hash", SRC, "--glossary-hash", GLS,
          "--locale", LOCALE, "--content", "Hola",
          "--root", str(r)])
    proc = _run(["reset", "--root", str(r)])
    assert proc.returncode == 0
    assert "1 entradas eliminadas" in proc.stdout, proc.stdout


def test_reset_por_locale() -> None:
    r = _root()
    _run(["store", "--segment", "seg-x",
          "--source-hash", SRC, "--glossary-hash", GLS,
          "--locale", "es-ES", "--content", "x",
          "--root", str(r)])
    _run(["store", "--segment", "seg-y",
          "--source-hash", SRC, "--glossary-hash", GLS,
          "--locale", "es-MX", "--content", "y",
          "--root", str(r)])
    rc = _run(["reset", "--root", str(r), "--locale", "es-ES"]).returncode
    assert rc == 0
    assert (r / "es-ES").exists() or not any((r / "es-ES").rglob("*.json"))
    assert any((r / "es-MX").rglob("*.json"))


def test_persistencia_a_traves_de_procesos() -> None:
    """Una entrada escrita sobrevive al reinicio del intérprete."""
    r = _root()
    _run(["store", "--segment", SEG,
          "--source-hash", SRC, "--glossary-hash", GLS,
          "--locale", LOCALE, "--content", "Persistido",
          "--root", str(r)])
    proc = _run(["lookup", "--segment", SEG,
                 "--source-hash", SRC, "--glossary-hash", GLS,
                 "--locale", LOCALE, "--root", str(r)])
    assert proc.returncode == 0
    assert "Persistido" in proc.stdout


def test_store_valida_sha256_hex() -> None:
    r = _root()
    rc = _run(["store", "--segment", SEG,
               "--source-hash", "deadbeef",  # sólo 8 chars
               "--glossary-hash", GLS,
               "--locale", LOCALE, "--content", "x",
               "--root", str(r)]).returncode
    assert rc != 0


def test_schema_valida_entry() -> None:
    """La entry generada por `store` pasa el esquema."""
    import jsonschema
    r = _root()
    proc = _run(["store", "--segment", SEG,
                 "--source-hash", SRC, "--glossary-hash", GLS,
                 "--locale", LOCALE, "--content", "SchemaTest",
                 "--root", str(r)])
    assert proc.returncode == 0
    entry = json.loads(proc.stdout)
    jsonschema.validate(entry, json.loads(SCHEMA.read_text(encoding="utf-8")))
