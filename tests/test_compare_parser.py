"""Pruebas de la comparación de versiones del parser (fase 144).

La aceptación es negativa: **no promueve si cambian rangos o slugs sin
migrar los dependientes**. Los adaptadores de
`tests/fixtures/parser_alt/` simulan esas diferencias sin instalar una
versión alternativa de `markdown-it-py`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from compare_parser import compare, extract, main  # noqa: E402

CORPUS = ROOT / "tests" / "fixtures" / "pilot"
ADAPTERS = ROOT / "tests" / "fixtures" / "parser_alt"


def test_la_extraccion_es_determinista() -> None:
    first = extract(CORPUS, sample=3, seed=42)
    second = extract(CORPUS, sample=3, seed=42)
    assert first == second
    assert len(first["documents"]) == 3


def test_la_extraccion_declara_rangos_y_slugs() -> None:
    features = extract(CORPUS, sample=1, seed=1)["documents"]
    document = next(iter(features.values()))
    assert document["ranges"], "un documento real debe tener tokens con map"
    assert document["slugs"], "un documento real debe tener encabezados"


def test_baseline_contra_si_mismo_promociona(tmp_path: Path) -> None:
    out = tmp_path / "parser.json"
    assert main(["--corpus", str(CORPUS), "--sample", "3", "--out", str(out)]) == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["promotion"] == "allowed"
    assert report["changed_ranges"] == [] and report["changed_slugs"] == []


def test_un_rango_distinto_bloquea_la_promocion(tmp_path: Path) -> None:
    out = tmp_path / "parser.json"
    code = main([
        "--corpus", str(CORPUS), "--sample", "3",
        "--candidate-adapter", str(ADAPTERS / "ranges_shift.py"),
        "--out", str(out),
    ])
    assert code == 4
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["promotion"] == "blocked"
    assert report["changed_ranges"]
    assert "anchors.json" in report["dependents_to_migrate"]


def test_un_slug_distinto_bloquea_la_promocion(tmp_path: Path) -> None:
    out = tmp_path / "parser.json"
    code = main([
        "--corpus", str(CORPUS), "--sample", "3",
        "--candidate-adapter", str(ADAPTERS / "slug_change.py"),
        "--out", str(out),
    ])
    assert code == 4
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["changed_slugs"]
    assert report["dependents_to_migrate"]


def test_un_recuento_distinto_tambien_bloquea(tmp_path: Path) -> None:
    out = tmp_path / "parser.json"
    code = main([
        "--corpus", str(CORPUS), "--sample", "3",
        "--candidate-adapter", str(ADAPTERS / "counts_shift.py"),
        "--out", str(out),
    ])
    assert code == 4
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["changed_counts"]
    assert report["changed_ranges"] == []


def test_un_corpus_inexistente_falla(tmp_path: Path) -> None:
    out = tmp_path / "parser.json"
    assert main(["--corpus", str(tmp_path / "no"), "--out", str(out)]) == 2


def test_un_interprete_inexistente_falla(tmp_path: Path) -> None:
    out = tmp_path / "parser.json"
    code = main([
        "--corpus", str(CORPUS), "--sample", "1",
        "--candidate-interpreter", "/no/existe/python",
        "--out", str(out),
    ])
    assert code in (3, 5)
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["error"]["side"] == "candidate"


def test_la_comparacion_deja_cargar_una_candidata_externa() -> None:
    baseline = {"parser": "3.0.0", "documents": {"a.md": {
        "tokens": 10, "tokens_with_map": 5, "lines": 3,
        "ranges": [{"type": "p", "lines": [0, 1]}], "slugs": ["a"],
        "fence_blocks": 0, "inline_code": 0,
    }}}
    candidate = {"parser": "4.0.0", "documents": {"a.md": dict(baseline["documents"]["a.md"])}}
    assert compare(baseline, candidate)["promotion"] == "allowed"
    drifted = {"parser": "4.0.0", "documents": {"a.md": {
        **baseline["documents"]["a.md"], "slugs": ["b"],
    }}}
    result = compare(baseline, drifted)
    assert result["promotion"] == "blocked"
    assert result["changed_slugs"] == ["a.md"]
    assert result["dependents_to_migrate"]


def test_el_informe_registra_las_versiones_de_parser() -> None:
    report = extract(CORPUS, sample=1, seed=1)
    assert report["parser"] in ("3.0.0", "unknown", "not-installed")