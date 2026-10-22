"""Pruebas de `check_structure` sobre corpus anidados (fase 041, cierre G-BETA).

El defecto que estas pruebas cierran: `check_structure` recorria
`source_dir.glob("*.md")`, que no es recursivo, y buscaba el snapshot por
`src.name` en vez de por la ruta relativa. Sobre cualquier corpus anidado
-no vacío, y el piloto lo es al 100 %- no inspeccionaba ni un archivo y
devolvía `structure: 0 errores`.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INVENTORY = ROOT / "scripts" / "inventory.py"
PREPARE = ROOT / "scripts" / "prepare.py"
DETECT = ROOT / "scripts" / "detect_language.py"
BUILD = ROOT / "scripts" / "build_packets.py"
TRANSLATE = ROOT / "scripts" / "translate_pilot.py"
VALIDATE = ROOT / "scripts" / "validate.py"
TMP = Path(tempfile.gettempdir()) / "nst-tests"

SOURCE_DOC = """# Título original

Texto de apoyo con un [enlace interno](#seccion-interna).

## Sección interna

- primer elemento
- segundo elemento

```python
valor = 1
```

| Columna A | Columna B |
| --- | --- |
| a1 | b1 |
"""

PROFILE = {
    "target_language": "es",
    "source_language": "auto",
    "markdown_dialect": "commonmark+gfm",
    "slug_algorithm": {"name": "github", "version": "v1"},
    "code_preservation": "strict",
    "frontmatter_policy": "preserve",
    "bilingual_policy": "first-mention-per-document",
    "punctuation_preference": "es-comma-period",
    "review_mode": "assisted",
    "exclusions": [],
    "context_budget": 1500,
    "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
}


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def build_corpus(name: str) -> dict[str, Path]:
    source = TMP / name / "source"
    if source.exists():
        shutil.rmtree(source)
    nested = source / "angular" / "guide" / "deep"
    nested.mkdir(parents=True)
    (nested / "doc.md").write_text(SOURCE_DOC, encoding="utf-8")

    work = TMP / name / "work"
    work.mkdir(parents=True, exist_ok=True)
    profile = work / "profile.json"
    payload = dict(PROFILE)
    payload["paths"] = {
        "source_root": str(source),
        "work_root": str(work),
        "output_root": str(TMP / name / "output"),
    }
    profile.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    inv = work / "inventory.json"
    seg = work / "segments.json"
    snaps = work / "snapshots.json"
    classified = work / "classified.json"
    packets = work / "packets.json"
    translations = work / "translations"
    manifest = work / "manifest.json"

    assert run([str(INVENTORY), "--source", str(source), "--out", str(inv)]).returncode == 0
    assert run([str(PREPARE), "--inventory", str(inv), "--segments", str(seg), "--snapshots", str(snaps)]).returncode == 0
    assert run([str(DETECT), "--segments", str(seg), "--out", str(classified)]).returncode == 0
    assert run([str(BUILD), "--segments", str(classified), "--profile", str(profile), "--out", str(packets)]).returncode == 0
    if translations.exists():
        shutil.rmtree(translations)
    translations.mkdir(parents=True)
    assert run([str(TRANSLATE), "--packets", str(packets), "--segments", str(classified),
                "--out", str(translations), "--mode", "identity"]).returncode == 0

    docs = json.loads(classified.read_text(encoding="utf-8"))["files"]
    files = [{
        "path": f["path"],
        "document_id": f["document_id"],
        "source_hash": f["source_hash"],
        "current_state": "translated",
        "state_history": [
            {"state": "inventoried", "timestamp": "2026-10-20T00:00:00Z", "reason": "init"},
            {"state": "translated", "timestamp": "2026-10-20T00:01:00Z", "reason": "done"},
        ],
        "last_transition_at": "2026-10-20T00:01:00Z",
    } for f in docs]
    manifest.write_text(json.dumps({
        "run_id": "run-structure",
        "created_at": "2026-10-20T00:00:00Z",
        "manifest_version": "translate/v1",
        "skill_version": "0.2.0",
        "parser": {"name": "markdown-it-py", "version": "3.0.0"},
        "anchor_policy": {"algorithm": "github-slug-v1", "version": "v1"},
        "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
        "glossary_snapshot": {"version": 1, "hash": "0" * 64, "frozen": True},
        "profile_snapshot": {"hash": "0" * 64},
        "inputs": {"source_root": str(source), "total_files": len(files), "total_bytes": 0, "hashes_indexed": True},
        "files": files,
    }, indent=2), encoding="utf-8")

    return {
        "source": source,
        "output": TMP / name / "output",
        "packets": packets,
        "segments": classified,
        "snapshots": snaps,
        "translations": translations,
        "manifest": manifest,
        "relative": "angular/guide/deep/doc.md",
    }


def write_output(paths: dict[str, Path], body: str) -> None:
    target = paths["output"] / paths["relative"]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")


def validate(paths: dict[str, Path], out_name: str, *extra: str) -> dict:
    out = TMP / out_name
    args = [
        str(VALIDATE),
        "--source", str(paths["source"]),
        "--output-dir", str(paths["output"]),
        "--packets", str(paths["packets"]),
        "--segments", str(paths["segments"]),
        "--translations", str(paths["translations"]),
        "--snapshots", str(paths["snapshots"]),
        "--anchors", str(TMP / "anchors"),
        "--manifest", str(paths["manifest"]),
        "--out", str(out),
        "--checks", "structure",
        *extra,
    ]
    proc = run(args)
    assert proc.returncode in (0, 1), f"validate.py terminó con {proc.returncode}: {proc.stderr}"
    return json.loads(out.read_text(encoding="utf-8"))


def test_corpus_anidado_se_inspecciona() -> None:
    """Con la salida presente, la estructura intacta no da errores."""
    paths = build_corpus("str-ok")
    write_output(paths, SOURCE_DOC)
    report = validate(paths, "validate_structure_ok.json")
    assert [e for e in report["errors"] if e["check"] == "structure"] == []


def test_encabezado_perdido_en_salida_se_detecta() -> None:
    """El defecto que `prepare.py` ya corrigió debe seguir detectable.

    Reintroducirlo a mano en el ensamblado tiene que sacar `structure` en rojo.
    """
    paths = build_corpus("str-head")
    mutilado = SOURCE_DOC.replace("# Título original\n\n", "")
    write_output(paths, mutilado)
    report = validate(paths, "validate_structure_head.json")
    errors = [e for e in report["errors"] if e["check"] == "structure"]
    assert errors, "encabezado perdido en la salida no detectado"


def test_tabla_recortada_en_salida_se_detecta() -> None:
    paths = build_corpus("str-table")
    recortada = SOURCE_DOC.split("| Columna A | Columna B |")[0]
    write_output(paths, recortada)
    report = validate(paths, "validate_structure_table.json")
    errors = [e for e in report["errors"] if e["check"] == "structure"]
    assert errors, "tabla recortada no detectada"


def test_fence_perdida_en_salida_se_detecta() -> None:
    paths = build_corpus("str-fence")
    sin_fence = SOURCE_DOC.replace("```python\nvalor = 1\n```\n\n", "")
    write_output(paths, sin_fence)
    report = validate(paths, "validate_structure_fence.json")
    errors = [e for e in report["errors"] if e["check"] == "structure"]
    assert errors, "bloque de codigo perdido no detectado"


def test_texto_traducido_no_altera_la_firma() -> None:
    """Cambiar el texto de los títulos y del prosa no es un cambio estructural."""
    paths = build_corpus("str-translated")
    traducido = (
        "# Titulo traducido\n\n"
        "Texto de apoyo con un [enlace interno](#seccion-interna).\n\n"
        "## Seccion interna\n\n"
        "- primer elemento\n"
        "- segundo elemento\n\n"
        "```python\nvalor = 1\n```\n\n"
        "| Columna A | Columna B |\n| --- | --- |\n| a1 | b1 |\n"
    )
    write_output(paths, traducido)
    report = validate(paths, "validate_structure_translated.json")
    assert [e for e in report["errors"] if e["check"] == "structure"] == []


def test_documento_sin_ensamblar_es_info_y_con_flag_es_error() -> None:
    """Sin `--require-assembled`, la ausencia es información: `export.py`
    valida antes de ensamblar. Con el flag, es error."""
    paths = build_corpus("str-missing")
    if paths["output"].exists():
        shutil.rmtree(paths["output"])
    paths["output"].mkdir(parents=True, exist_ok=True)

    report = validate(paths, "validate_structure_info.json")
    assert [e for e in report["errors"] if e["check"] == "structure"] == []
    assert report["results"]["structure"]["info"], "falta la lista de no ensamblados"

    estricto = validate(paths, "validate_structure_strict.json", "--require-assembled")
    errors = [e for e in estricto["errors"] if e["check"] == "structure"]
    assert errors, "documento sin ensamblar no detectado con --require-assembled"

# --------------------------------------------------------------------------
# Un documento traducible también se compara (INV-06)
# --------------------------------------------------------------------------
#
# `check_structure` se saltaba el documento entero cuando tenía al menos un
# segmento `translatable`, para no marcar «sin headings ni enlaces» en un
# documento de prosa al que el scraper le perdió las cabeceras. El efecto
# secundario es que la comparación fuente↔ensamblado nunca se hacía para los
# documentos que la traducción toca: son exactamente los que un
# ensamblado puede dañar. Medido sobre la corrida beta, de 2 682
# documentos se comparaban 4.


def _marcar_traducible(paths: dict[str, Path]) -> None:
    """Deja el documento con prosa traducible, como el corpus real."""
    segments = json.loads(paths["segments"].read_text(encoding="utf-8"))
    for record in segments["files"]:
        if record["path"] != paths["relative"]:
            continue
        for seg in record["segments"]:
            if seg.get("translatable_text"):
                seg["disposition"] = "translatable"
    paths["segments"].write_text(json.dumps(segments, indent=2), encoding="utf-8")


def test_un_documento_traducible_se_compara_contra_la_fuente() -> None:
    paths = build_corpus("str-traducible")
    _marcar_traducible(paths)
    write_output(paths, SOURCE_DOC)
    report = validate(paths, "validate_structure_traducible.json")
    assert [e for e in report["errors"] if e["check"] == "structure"] == []


def test_un_encabezado_perdido_en_un_documento_traducible_se_detecta() -> None:
    paths = build_corpus("str-traducible-head")
    _marcar_traducible(paths)
    write_output(paths, SOURCE_DOC.replace("# Título original\n\n", ""))
    report = validate(paths, "validate_structure_traducible_head.json")
    errors = [e for e in report["errors"] if e["check"] == "structure"]
    assert errors, (
        "el encabezado perdido no se detectó porque el documento traducible "
        "se saltaba antes de comparar"
    )


def test_un_documento_traducible_sin_ensamblar_es_error_con_require_assembled() -> None:
    paths = build_corpus("str-traducible-sin-archivo")
    _marcar_traducible(paths)
    report = validate(paths, "validate_structure_traducible_sin.json", "--require-assembled")
    errors = [e for e in report["errors"] if e["check"] == "structure"]
    assert errors, "un documento traducible sin ensamblar debe ser error, no información"


def test_la_comparacion_cubre_todo_el_corpus_real() -> None:
    """Ninguna disposición puede sacar un documento de la comparación.

    Se recorre el mismo criterio de salto que usa el validador sobre el
    corpus de prueba y se exige que solo queden fuera los documentos que no
    aportan forma traducible: stubs sin encabezados ni enlaces.
    """
    paths = build_corpus("str-cobertura")
    _marcar_traducible(paths)
    snapshots = json.loads(paths["snapshots"].read_text(encoding="utf-8"))
    sys.path.insert(0, str(ROOT / "scripts"))
    from validate import structure_signature

    segments = json.loads(paths["segments"].read_text(encoding="utf-8"))
    translatable = {
        f["path"] for f in segments["files"]
        if any(s.get("disposition") == "translatable" for s in f["segments"])
    }
    comparados = 0
    for entry in snapshots["files"]:
        rel = entry["path"]
        source = paths["source"] / rel
        text = source.read_text(encoding="utf-8")
        size = source.stat().st_size
        headings = len(entry.get("headings") or [])
        links = len(entry.get("links") or [])
        tables = len(entry.get("tables") or [])
        fences = structure_signature(text).get("fences")
        if size < 250 and headings == 0 and links == 0:
            continue
        if (tables or fences) and headings == 0 and links == 0:
            continue
        comparados += 1
    assert comparados == len(snapshots["files"]), (
        f"solo {comparados} de {len(snapshots['files'])} documentos pasan el filtro "
        "de comparación; los traducibles no pueden quedar fuera"
    )


def test_el_informe_dice_cuantos_documentos_comparo() -> None:
    """Sin un contador positivo, el informe no distingue «comparado e
    idéntico» de «nunca alcanzado»."""
    paths = build_corpus("str-contador")
    _marcar_traducible(paths)
    write_output(paths, SOURCE_DOC)
    report = validate(paths, "validate_structure_contador.json")
    structure = report["results"]["structure"]
    assert structure["compared"] == 1
    assert structure["unassembled_count"] == 0
