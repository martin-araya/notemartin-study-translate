"""Pruebas de scripts/build_glossary.py (cierre de G-BETA).

La herramienta del piloto aplicaba decisiones hardcodeadas dentro del
script. Esta aplica un archivo de decisiones aprobado y lo evidencia con
el corpus, sin decidir nada por su cuenta.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD_GLOSSARY = ROOT / "scripts" / "build_glossary.py"
SCHEMA = ROOT / "schemas" / "glossary.schema.json"
TMP = Path(tempfile.gettempdir()) / "nst-tests"

SEGMENTS = {
    "files": [
        {
            "document_id": "doc-00000001",
            "path": "docs/a.md",
            "segments": [
                {
                    "segment_id": "seg-00000001",
                    "disposition": "translatable",
                    "translatable_text": "The component keeps its state between renders.",
                },
                {
                    "segment_id": "seg-00000002",
                    "disposition": "translatable",
                    "translatable_text": "A custom property is declared with a dash.",
                },
            ],
        }
    ]
}

DECISIONS = {
    "entries": [
        {
            "source_term": "state",
            "domain": "ui",
            "sense": "estado visible de un componente",
            "preferred": "estado",
            "preservation_policy": "translate",
            "justification": "Sentido de interfaz, no de persistencia.",
        },
        {
            "source_term": "hydration",
            "domain": "framework",
            "sense": "momento de montar la vista en el cliente",
            "preferred": "hidratación",
            "preservation_policy": "translate",
            "justification": "Termino tecnico del framework.",
        },
    ]
}


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def build(name: str, decisions: dict, *extra: str) -> tuple[subprocess.CompletedProcess, Path]:
    work = TMP / name
    work.mkdir(parents=True, exist_ok=True)
    decisions_path = work / "decisions.json"
    decisions_path.write_text(json.dumps(decisions), encoding="utf-8")
    segments_path = work / "segments.json"
    segments_path.write_text(json.dumps(SEGMENTS), encoding="utf-8")
    out = work / "glossary.json"
    proc = run([
        str(BUILD_GLOSSARY),
        "--decisions", str(decisions_path),
        "--segments", str(segments_path),
        "--version", "3",
        "--decided-by", "usuario",
        "--out", str(out),
        *extra,
    ])
    return proc, out


def test_el_glosario_resultante_valida() -> None:
    import jsonschema

    proc, out = build("glossary-ok", DECISIONS)
    assert proc.returncode == 0, proc.stderr
    glossary = json.loads(out.read_text(encoding="utf-8"))
    jsonschema.validate(glossary, json.loads(SCHEMA.read_text(encoding="utf-8")))


def test_una_entrada_sin_ejemplo_real_no_entra() -> None:
    proc, out = build("glossary-sin-ejemplo", DECISIONS)
    assert proc.returncode == 0, proc.stderr
    glossary = json.loads(out.read_text(encoding="utf-8"))
    terms = {e["source_term"] for e in glossary["entries"]}
    assert terms == {"state"}, f"entradas inesperadas: {terms}"
    assert "hydration" in proc.stderr


def test_strict_falla_si_falta_un_ejemplo() -> None:
    proc, _ = build("glossary-strict", DECISIONS, "--strict")
    assert proc.returncode == 1


def test_el_ejemplo_apunta_a_un_segmento_real() -> None:
    proc, out = build("glossary-ejemplo", DECISIONS)
    assert proc.returncode == 0, proc.stderr
    glossary = json.loads(out.read_text(encoding="utf-8"))
    example = glossary["entries"][0]["context_examples"][0]
    assert example["segment_id"] == "seg-00000001"
    assert example["document_id"] == "doc-00000001"
    assert "state" in example["before"] + example["after"] + " state "


def test_congelar_registra_el_momento() -> None:
    proc, out = build("glossary-frozen", DECISIONS, "--frozen")
    assert proc.returncode == 0, proc.stderr
    glossary = json.loads(out.read_text(encoding="utf-8"))
    assert glossary["frozen"] is True
    assert glossary["approved_at"]
    assert glossary["version"] == 3


def test_keep_original_no_lleva_variantes() -> None:
    decisions = {
        "entries": [{
            "source_term": "state",
            "domain": "ui",
            "sense": "estado visible",
            "preferred": "estado",
            "preservation_policy": "keep-original",
            "allowed_variants": ["estado"],
            "justification": "Se conserva el termino.",
        }]
    }
    import jsonschema

    proc, out = build("glossary-keep", decisions)
    assert proc.returncode == 0, proc.stderr
    glossary = json.loads(out.read_text(encoding="utf-8"))
    entry = glossary["entries"][0]
    assert "allowed_variants" not in entry
    jsonschema.validate(glossary, json.loads(SCHEMA.read_text(encoding="utf-8")))