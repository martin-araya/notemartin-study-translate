"""Pruebas de `check_source_debt` (fase 041, cierre G-BETA).

La comprobación recorreía `source_dir.glob("*.md")`, así que sobre un
corpus anidado no veía ni un archivo. Además resolvía el ancla contra el
propio documento, lo que no sirve para una ruta relativa a otro archivo.

La deuda del origen nunca es una regresión: se registra aparte y no
bloquea, pero tiene que existir como dato, porque el cierre de G-BETA
distingue "ya estaba roto" de "lo rompimos al traducir".
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
VALIDATE = ROOT / "scripts" / "validate.py"
TMP = Path(tempfile.gettempdir()) / "nst-tests"

MANIFEST = {
    "run_id": "run-debt",
    "created_at": "2026-10-20T00:00:00Z",
    "manifest_version": "translate/v1",
    "skill_version": "0.2.0",
    "parser": {"name": "markdown-it-py", "version": "3.0.0"},
    "anchor_policy": {"algorithm": "github-slug-v1", "version": "v1"},
    "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
    "glossary_snapshot": {"version": 1, "hash": "0" * 64, "frozen": True},
    "profile_snapshot": {"hash": "0" * 64},
    "inputs": {"source_root": "x", "total_files": 0, "total_bytes": 0, "hashes_indexed": True},
    "files": [],
}


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def build(name: str, files: dict[str, str]) -> dict[str, Path]:
    source = TMP / name / "source"
    if source.exists():
        shutil.rmtree(source)
    for rel, body in files.items():
        target = source / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")

    work = TMP / name / "work"
    work.mkdir(parents=True, exist_ok=True)
    inv = work / "inventory.json"
    manifest = work / "manifest.json"
    manifest.write_text(json.dumps(MANIFEST, indent=2), encoding="utf-8")
    (work / "packets.json").write_text(json.dumps({"packets": []}), encoding="utf-8")
    (work / "segments.json").write_text(json.dumps({"files": []}), encoding="utf-8")
    (work / "snapshots.json").write_text(json.dumps({"files": []}), encoding="utf-8")
    (work / "translations").mkdir(exist_ok=True)
    assert run([str(INVENTORY), "--source", str(source), "--out", str(inv)]).returncode == 0
    return {"source": source, "inventory": inv, "manifest": manifest, "work": work}


def debt(paths: dict[str, Path], out_name: str) -> list[dict]:
    out = TMP / out_name
    proc = run([
        str(VALIDATE),
        "--source", str(paths["source"]),
        "--output-dir", str(paths["work"] / "output"),
        "--packets", str(paths["work"] / "packets.json"),
        "--segments", str(paths["work"] / "segments.json"),
        "--translations", str(paths["work"] / "translations"),
        "--snapshots", str(paths["work"] / "snapshots.json"),
        "--anchors", str(paths["work"] / "anchors"),
        "--manifest", str(paths["manifest"]),
        "--out", str(out),
        "--checks", "source-debt",
    ])
    assert proc.returncode in (0, 1), f"validate.py terminó con {proc.returncode}: {proc.stderr}"
    report = json.loads(out.read_text(encoding="utf-8"))
    return report["results"]["source-debt"]["info"]


def test_ancla_local_rota_en_documento_anidado_se_reporta() -> None:
    paths = build("debt-anchor", {
        "guide/nested/page.md": "# Page\n\nSee [below](#missing-section).\n",
    })
    found = debt(paths, "validate_debt_anchor.json")
    assert any("missing-section" in item["message"] for item in found), \
        "ancla rota de un documento anidado no reportada"


def test_ruta_relativa_rota_se_reporta() -> None:
    paths = build("debt-relative", {
        "oracle/resumenes/capitulo.md": "# Capitulo\n\n![Figura](assets/figura.png)\n",
    })
    found = debt(paths, "validate_debt_relative.json")
    assert any("assets/figura.png" in item["message"] for item in found), \
        "ruta relativa rota no reportada"


def test_ruta_relativa_que_existe_no_se_reporta() -> None:
    paths = build("debt-ok", {
        "oracle/resumenes/capitulo.md": "# Capitulo\n\n![Figura](assets/figura.png)\n",
        "oracle/resumenes/assets/figura.png": "no soy texto\n",
    })
    found = debt(paths, "validate_debt_ok.json")
    assert found == [], f"ruta relativa existente reportada como deuda: {found}"


def test_ruta_con_prefijo_del_sitio_no_es_deuda_local() -> None:
    """`/docs/user-guide/editor.png` es una ruta del sitio, no un archivo local.

    Se declara aparte: no se puede comprobar contra el corpus y no es una
    regresión nuestra.
    """
    paths = build("debt-site", {
        "mermaid/index.md": "# Editor\n\n![Editor](/docs/user-guide/editor.png)\n",
    })
    found = debt(paths, "validate_debt_site.json")
    assert not any(item.get("kind") == "source_debt_missing_target" for item in found), \
        "ruta absoluta del sitio tratada como deuda local"
    assert any(item.get("kind") == "source_debt_external" for item in found), \
        "la ruta del sitio no queda declarada"