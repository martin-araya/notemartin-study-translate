"""Pruebas para scripts/build_anchors.py (fase 038 y endurecimiento 054)."""

from __future__ import annotations

import tempfile
import json
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD_ANCHORS = ROOT / "scripts" / "build_anchors.py"
REWRITE = ROOT / "scripts" / "rewrite_references.py"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def make_snapshots(headings: list[dict], document_id: str = "doc-test", path: str = "test.md") -> dict:
    return {
        "source_root": "/tmp/x",
        "files": [{
            "document_id": document_id,
            "path": path,
            "headings": headings,
            "links": [],
            "tables": [],
            "footnotes": [],
            "structure_hash": "x",
        }],
    }


def make_multi_doc_snapshots(docs: list[dict]) -> dict:
    files: list[dict] = []
    for d in docs:
        files.append({
            "document_id": d["document_id"],
            "path": d["path"],
            "headings": d["headings"],
            "links": [],
            "tables": [],
            "footnotes": [],
            "structure_hash": "x",
        })
    return {"source_root": "/tmp/x", "files": files}


def write_temp(payload: dict, name: str) -> Path:
    path = TMP / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def read_anchors(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_tildes_se_transliteran() -> None:
    snapshots = make_snapshots([
        {"level": 2, "text": "Uso Básico", "line_range": {"start": 0, "end": 1}},
    ])
    snaps_path = write_temp(snapshots, "snaps_tildes")
    out = TMP / "anchors_tildes"
    assert run([str(BUILD_ANCHORS), "--snapshots", str(snaps_path), "--out", str(out)]).returncode == 0
    data = read_anchors(out / "doc-test.json")
    assert data["anchors"][0]["new_slug"] == "uso-basico"


def test_headings_duplicados_reciben_sufijo() -> None:
    snapshots = make_snapshots([
        {"level": 2, "text": "Instalación", "line_range": {"start": 0, "end": 1}},
        {"level": 2, "text": "Instalación", "line_range": {"start": 2, "end": 3}},
        {"level": 2, "text": "Instalación", "line_range": {"start": 4, "end": 5}},
    ])
    snaps_path = write_temp(snapshots, "snaps_dupl")
    out = TMP / "anchors_dupl"
    assert run([str(BUILD_ANCHORS), "--snapshots", str(snaps_path), "--out", str(out)]).returncode == 0
    data = read_anchors(out / "doc-test.json")
    slugs = [a["new_slug"] for a in data["anchors"]]
    assert slugs == ["instalacion", "instalacion-1", "instalacion-2"]


def test_codigo_inline_en_heading() -> None:
    snapshots = make_snapshots([
        {"level": 3, "text": "Uso de `commit()`", "line_range": {"start": 0, "end": 1}},
    ])
    snaps_path = write_temp(snapshots, "snaps_code")
    out = TMP / "anchors_code"
    assert run([str(BUILD_ANCHORS), "--snapshots", str(snaps_path), "--out", str(out)]).returncode == 0
    data = read_anchors(out / "doc-test.json")
    assert data["anchors"][0]["new_slug"] == "uso-de-commit"


def test_anchor_explicito_se_preserva() -> None:
    snapshots = make_snapshots([
        {"level": 2, "text": "Section Title", "anchor": "custom-anchor", "line_range": {"start": 0, "end": 1}},
    ])
    snaps_path = write_temp(snapshots, "snaps_explicit")
    out = TMP / "anchors_explicit"
    assert run([str(BUILD_ANCHORS), "--snapshots", str(snaps_path), "--out", str(out)]).returncode == 0
    data = read_anchors(out / "doc-test.json")
    a = data["anchors"][0]
    assert a["source"] == "explicit"
    assert a["new_slug"] == "custom-anchor"


def test_normaliza_diacriticos_explicitamente() -> None:
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from build_anchors import github_slug
    assert "ano" == github_slug("Año")
    assert "nino" == github_slug("Niño")


def test_cross_doc_collision_no_sobrescribe_destino() -> None:
    snapshots = make_multi_doc_snapshots([
        {"document_id": "doc-a", "path": "a.md", "headings": [{"level": 2, "text": "Instalación", "line_range": {"start": 0, "end": 1}}]},
        {"document_id": "doc-b", "path": "b.md", "headings": [{"level": 2, "text": "Instalación", "line_range": {"start": 0, "end": 1}}]},
    ])
    snaps_path = write_temp(snapshots, "snaps_cdc")
    out = TMP / "anchors_cdc"
    if out.exists():
        shutil.rmtree(out)
    proc = run([str(BUILD_ANCHORS), "--snapshots", str(snaps_path), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr

    assert (out / "doc-a.json").exists()
    assert (out / "doc-b.json").exists()
    data_a = read_anchors(out / "doc-a.json")
    data_b = read_anchors(out / "doc-b.json")
    assert data_a["anchors"][0]["new_slug"] == "instalacion"
    assert data_b["anchors"][0]["new_slug"] == "instalacion"

    collisions_path = out / "_collisions.json"
    assert collisions_path.exists()
    collisions = read_anchors(collisions_path)
    assert collisions["kind"] == "cross_doc_collision"
    assert collisions["total"] >= 1
    slug = collisions["collisions"][0]["slug"]
    assert slug == "instalacion"


def test_unicode_collision_bloqueada_con_rewrite() -> None:
    snapshots = make_multi_doc_snapshots([
        {"document_id": "doc-u1", "path": "u1.md", "headings": [{"level": 2, "text": "Año", "line_range": {"start": 0, "end": 1}}]},
        {"document_id": "doc-u2", "path": "u2.md", "headings": [{"level": 2, "text": "Ano", "line_range": {"start": 0, "end": 1}}]},
    ])
    snaps_path = write_temp(snapshots, "snaps_unicode_col")
    out = TMP / "anchors_unicode_col"
    if out.exists():
        shutil.rmtree(out)
    assert run([str(BUILD_ANCHORS), "--snapshots", str(snaps_path), "--out", str(out)]).returncode == 0

    data_u1 = read_anchors(out / "doc-u1.json")
    data_u2 = read_anchors(out / "doc-u2.json")
    assert data_u1["anchors"][0]["new_slug"] == data_u2["anchors"][0]["new_slug"]


def test_ambiguous_link_no_reescrito() -> None:
    snapshots = make_multi_doc_snapshots([
        {"document_id": "doc-x", "path": "x.md", "headings": [{"level": 2, "text": "intro", "line_range": {"start": 0, "end": 1}}]},
        {"document_id": "doc-y", "path": "y.md", "headings": [{"level": 2, "text": "intro", "line_range": {"start": 0, "end": 1}}]},
    ])
    snaps_path = write_temp(snapshots, "snaps_ambig")
    out = TMP / "anchors_ambig"
    if out.exists():
        shutil.rmtree(out)
    assert run([str(BUILD_ANCHORS), "--snapshots", str(snaps_path), "--out", str(out)]).returncode == 0

    src = TMP / "ambig_src"
    out_dir = TMP / "ambig_out"
    if src.exists():
        shutil.rmtree(src)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    src.mkdir(parents=True)
    out_dir.mkdir(parents=True)
    (src / "x.md").write_text("[ver](#intro)\n", encoding="utf-8")
    (src / "y.md").write_text("[ver](#intro)\n", encoding="utf-8")

    report = TMP / "ambig_report.json"
    proc = run([str(REWRITE),
                "--source", str(src),
                "--output-dir", str(out_dir),
                "--anchors", str(out),
                "--report", str(report)])
    assert proc.returncode == 0, proc.stderr
    rep = json.loads(report.read_text(encoding="utf-8"))
    assert rep["ambiguous_total"] >= 1
    assert "intro" in rep["ambiguous_slugs"]
    assert (out_dir / "x.md").read_text(encoding="utf-8") == "[ver](#intro)\n"
    assert (out_dir / "y.md").read_text(encoding="utf-8") == "[ver](#intro)\n"


def test_explicit_anchor_no_colisiona_con_implicit() -> None:
    snapshots = make_snapshots([
        {"level": 2, "text": "Instalación", "line_range": {"start": 0, "end": 1}},
        {"level": 2, "text": "Other", "anchor": "instalacion", "line_range": {"start": 2, "end": 3}},
    ])
    snaps_path = write_temp(snapshots, "snaps_exp_collision")
    out = TMP / "anchors_exp_col"
    if out.exists():
        shutil.rmtree(out)
    proc = run([str(BUILD_ANCHORS), "--snapshots", str(snaps_path), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr

    data = read_anchors(out / "doc-test.json")
    slugs = [a["new_slug"] for a in data["anchors"]]
    assert slugs[0] == "instalacion"
    assert slugs[1] == "instalacion-1"


def test_long_heading_slug_truncado() -> None:
    snapshots = make_snapshots([
        {"level": 2, "text": "a" * 500, "line_range": {"start": 0, "end": 1}},
    ])
    snaps_path = write_temp(snapshots, "snaps_long")
    out = TMP / "anchors_long"
    if out.exists():
        shutil.rmtree(out)
    proc = run([str(BUILD_ANCHORS), "--snapshots", str(snaps_path), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr
    data = read_anchors(out / "doc-test.json")
    slug = data["anchors"][0]["new_slug"]
    assert len(slug) > 0
    assert len(slug) <= 256
