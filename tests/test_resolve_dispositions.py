"""Pruebas de scripts/resolve_dispositions.py (cierre de G-BETA).

`detect_language.py` deja tres categorías sin decidir: `unknown`,
`mixed_or_code` y `too_short`. Este script las resuelve. Las pruebas
comprueban que la resolución se basa en prosa real y no en la forma del
segmento, y que un literal protegido nunca se convierte en prosa
traducible.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from resolve_dispositions import (  # noqa: E402
    mask_literals,
    prose_of,
    resolve,
    word_count,
)

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "resolve_dispositions.py"


def test_un_tipo_generico_no_es_prosa() -> None:
    disposition, reason = resolve("`Type<any>`")
    assert disposition == "code_skip"
    assert "literal" in reason


def test_un_tipo_generico_con_dobles_acentes() -> None:
    disposition, _ = resolve("`` MetadataReducer<boolean, boolean> ``")
    assert disposition == "code_skip"


def test_una_ruta_de_modulo_no_es_prosa() -> None:
    assert resolve("@angular/core")[0] == "code_skip"
    assert resolve("app/dashboard/page.tsx")[0] == "code_skip"


def test_un_vacio_es_no_text() -> None:
    assert resolve("")[0] == "no_text"
    assert resolve("   \n  ")[0] == "no_text"


def test_una_etiqueta_de_enlace_sola_es_literal() -> None:
    """`[headers](#headers)` no tiene prosa: solo destino y etiqueta idéntica."""
    disposition, _ = resolve("[headers](#headers)")
    assert disposition == "code_skip"


def test_un_autolink_con_ancla_html_es_literal() -> None:
    texto = "[More overrides](#more-overrides) <a id=\"more-overrides\"></a>"
    assert resolve(texto)[0] == "code_skip"


def test_prosa_con_referencias_inline_sigue_traducible() -> None:
    """Diez referencias inline no convierten un párrafo real en literal.

    Es el caso que la categoría `mixed_or_code` selecciona mal: la prosa
    traducible es menor del 25 % del texto, pero existe y es prosa.
    """
    texto = (
        "The `input` signal accepts a `number` and returns a `Signal`; "
        "pass the `initialValue` option to seed the control with `0` so "
        "the field renders empty until the user types something."
    )
    disposition, reason = resolve(texto)
    assert disposition == "translatable", reason


def test_prosa_corta_queda_too_short() -> None:
    disposition, reason = resolve("Use now")
    assert disposition == "too_short"
    assert "2 palabras" in reason


def test_una_oracion_real_es_traducible() -> None:
    disposition, reason = resolve(
        "Options for configuring server-side rendering."
    )
    assert disposition == "translatable"
    assert "palabras" in reason


def test_un_altern_text_en_espanol_no_se_rompe() -> None:
    """Una imagen con alt en español conserva su alt y no inventa prosa.

    El alt es texto visible para lectores de pantalla y la política de
    recursos locales exige decidirlo explícitamente, no descartarlo.
    """
    texto = (
        "![Resultado de la búsqueda antes de la reorganización: los "
        "vecinos aproximados no corresponden con las ciudades realmente "
        "cercanas.](resúmenes/assets/07_Create_Vector_Indexes/p054_xI1.png)"
    )
    prose = prose_of(texto)
    assert "Resultado de la búsqueda" in prose
    assert not prose.strip().startswith("![")


def test_mascara_no_une_palabras_separadas_por_literal() -> None:
    """Enmascarar por espacio, no por vacío, evita `foo`+`bar` → `foobar`."""
    masked = mask_literals("use `foo` bar")
    assert "foobar" not in masked
    assert word_count(prose_of("use `foo` bar")) == 2


def test_una_url_sola_es_literal() -> None:
    assert resolve("https://example.com/docs")[0] == "code_skip"


def test_la_version_sola_es_literal() -> None:
    assert resolve("v20.2")[0] == "code_skip"


def test_cli_escribe_solo_con_apply(tmp_path: Path = None) -> None:
    import tempfile

    base = Path(tempfile.gettempdir()) / "nst-resolve"
    base.mkdir(parents=True, exist_ok=True)
    doc = {
        "files": [
            {
                "path": "a.md",
                "document_id": "doc-1",
                "segments": [
                    {"segment_id": "s1", "translatable_text": "`Type<any>`",
                     "disposition": "mixed_or_code"},
                    {"segment_id": "s2", "disposition": "translatable",
                     "translatable_text": "Do not translate this one."},
                    {"segment_id": "s3",
                     "translatable_text": "Options for configuring server-side rendering.",
                     "disposition": "unknown"},
                ],
            }
        ]
    }
    src = base / "segments.json"
    src.write_text(json.dumps(doc), encoding="utf-8")
    out = base / "resolved.json"
    if out.exists():
        out.unlink()

    dry = subprocess.run(
        [sys.executable, str(SCRIPT), "--segments", str(src), "--out", str(out), "--dry-run"],
        capture_output=True, text=True, check=False,
    )
    assert dry.returncode == 0, dry.stderr
    assert not out.exists()

    applied = subprocess.run(
        [sys.executable, str(SCRIPT), "--segments", str(src), "--out", str(out), "--apply"],
        capture_output=True, text=True, check=False,
    )
    assert applied.returncode == 0, applied.stderr
    report = json.loads(applied.stdout)
    assert report["written"] is True
    assert report["transitions"]["mixed_or_code"] == {"code_skip": 1}
    assert report["transitions"]["unknown"] == {"translatable": 1}

    result = json.loads(out.read_text(encoding="utf-8"))
    segs = {s["segment_id"]: s for s in result["files"][0]["segments"]}
    assert segs["s1"]["disposition"] == "code_skip"
    assert segs["s1"]["previous_disposition"] == "mixed_or_code"
    assert segs["s2"]["disposition"] == "translatable"
    assert "previous_disposition" not in segs["s2"]
    assert segs["s3"]["disposition"] == "translatable"


def test_el_reporte_se_escribe_tambien_en_dry_run() -> None:
    """`--report` documenta la ejecución; un dry run también necesita evidencia."""
    import tempfile

    base = Path(tempfile.gettempdir()) / "nst-resolve-report"
    base.mkdir(parents=True, exist_ok=True)
    doc = {"files": [{"path": "a.md", "document_id": "d", "segments": [
        {"segment_id": "s1", "translatable_text": "`Type<any>`", "disposition": "mixed_or_code"}
    ]}]}
    src = base / "segments.json"
    src.write_text(json.dumps(doc), encoding="utf-8")
    out = base / "resolved.json"
    if out.exists():
        out.unlink()
    report = base / "dispositions.json"
    if report.exists():
        report.unlink()

    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--segments", str(src),
         "--out", str(out), "--report", str(report), "--dry-run"],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert not out.exists()
    assert report.exists()
    assert json.loads(report.read_text(encoding="utf-8"))["written"] is False


def test_el_texto_original_no_se_altera(tmp_path: Path = None) -> None:
    """La resolución cambia la disposición, nunca los bytes del segmento."""
    import tempfile

    base = Path(tempfile.gettempdir()) / "nst-resolve-keep"
    base.mkdir(parents=True, exist_ok=True)
    original = "Options for configuring server-side rendering."
    doc = {"files": [{"path": "a.md", "document_id": "d", "segments": [
        {"segment_id": "s1", "translatable_text": original, "disposition": "unknown"}
    ]}]}
    src = base / "segments.json"
    src.write_text(json.dumps(doc), encoding="utf-8")
    out = base / "resolved.json"
    subprocess.run(
        [sys.executable, str(SCRIPT), "--segments", str(src), "--out", str(out), "--apply"],
        capture_output=True, text=True, check=False,
    )
    result = json.loads(out.read_text(encoding="utf-8"))
    assert result["files"][0]["segments"][0]["translatable_text"] == original

# --------------------------------------------------------------------------
# El agregado por archivo no puede contradecir a sus propios segmentos
# --------------------------------------------------------------------------
#
# `detect_language.py` escribe `file_disposition` y
# `file_disposition_counts` al clasificar. Después `resolve_dispositions.py`
# cambia disposiciones de segmento y el agregado se queda con el valor
# anterior. En el corpus beta, `oracle/resúmenes/09_…` declaraba 189
# segmentos traducibles y tenía 255: el agregado era el número que se leía
# al informar y no era cierto.


def _documento() -> dict:
    return {
        "document_id": "doc-1",
        "path": "oracle/x.md",
        "source_hash": "a" * 64,
        "file_disposition": "already_target",
        "file_disposition_counts": {"already_target": 3, "unknown": 1},
        "segments": [
            {"segment_id": "seg-1", "translatable_text": "already target", "disposition": "already_target"},
            {"segment_id": "seg-2", "translatable_text": "", "disposition": "no_text"},
            {"segment_id": "seg-3", "translatable_text": "", "disposition": "no_text"},
            {"segment_id": "seg-4", "translatable_text": "`code`", "disposition": "unknown"},
        ],
    }


def _resolver(tmp_dir: Path, doc: dict, name: str) -> dict:
    src = tmp_dir / f"{name}_in.json"
    out = tmp_dir / f"{name}_out.json"
    src.write_text(json.dumps({"files": [doc]}, indent=2), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), "--segments", str(src), "--out", str(out), "--apply"],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(out.read_text(encoding="utf-8"))["files"][0]


def test_el_agregado_se_recalcula_tras_resolver(tmp_path: Path) -> None:
    resolved = _resolver(tmp_path, _documento(), "agregado")
    assert resolved["file_disposition_counts"] == {"already_target": 1, "no_text": 2, "code_skip": 1}
    assert resolved["file_disposition"] == "mixed"


def test_el_agregado_coincide_con_los_segmentos(tmp_path: Path) -> None:
    """La invariante que se puede comprobar siempre: el agregado es
    derivable de los segmentos del mismo archivo."""
    resolved = _resolver(tmp_path, _documento(), "coincide")
    counts = {}
    for seg in resolved["segments"]:
        counts[seg["disposition"]] = counts.get(seg["disposition"], 0) + 1
    assert resolved["file_disposition_counts"] == counts


def test_un_documento_sin_agregado_lo_recibe(tmp_path: Path) -> None:
    doc = _documento()
    del doc["file_disposition"]
    del doc["file_disposition_counts"]
    resolved = _resolver(tmp_path, doc, "nuevo")
    assert resolved["file_disposition"] == "mixed"
    assert sum(resolved["file_disposition_counts"].values()) == 4
