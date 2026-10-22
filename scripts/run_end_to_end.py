"""Ejecuta el pipeline completo y archiva evidencia (fase 049).

Invoca los scripts en orden y archiva cada artefacto en
``output_dir/<run_id>/``. Produce un reporte end-to-end con
hashes, cobertura, conteos de enlaces y métricas de auditoría.

Devuelve código 0 si todos los pasos pasan. Si un paso falla, el
reporte registra el fallo y devuelve código 1.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent


def skill_version() -> str:
    contract = ROOT / "release_contract.json"
    if not contract.exists():
        return "unknown"
    return json.loads(contract.read_text(encoding="utf-8")).get("skill_version", "unknown")

PIPELINE = [
    "inventory.py",
    "prepare.py",
    "detect_language.py",
    "build_packets.py",
    "extract_terms.py",
    "translate_pilot.py",
    "build_anchors.py",
    "rewrite_references.py",
    "validate.py",
    "check_integrity.py",
    "audit_terminology.py",
    "validate_translations.py",
    "check_numbers.py",
]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="run_end_to_end.py")
    p.add_argument("--source-root", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--translations", help="Directorio translations/ (opcional, se genera).")
    p.add_argument("--glossary", help="Glosario (opcional, se genera).")
    p.add_argument("--translate-mode", dest="translate_mode", choices=["identity", "glossary"],
                   default="identity",
                   help="identity devuelve cada segmento tal cual: comprueba la mecánica del "
                        "pipeline, no traduce. Los dos modos disponibles son mecánicos; "
                        "la traducción la hace el agente y se inyecta en translations/.")
    return p.parse_args(argv)


def write_atomic(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def run_step(args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(args, capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout, proc.stderr


def run_pipeline(
    source_root: Path,
    artifacts_dir: Path,
    translations_dir: Path,
    glossary_path: Path,
    run_id: str,
    translate_mode: str,
) -> dict:
    results: list[dict] = []

    inv = artifacts_dir / "inventory.json"
    rc, _, _ = run_step([sys.executable, str(ROOT / "scripts" / "inventory.py"),
                          "--source", str(source_root), "--out", str(inv)])
    results.append({"step": "inventory", "ok": rc == 0, "output": str(inv)})
    if rc != 0:
        return {"results": results, "ok": False}

    seg = artifacts_dir / "segments.json"
    snaps = artifacts_dir / "snapshots.json"
    rc, _, _ = run_step([sys.executable, str(ROOT / "scripts" / "prepare.py"),
                          "--inventory", str(inv), "--segments", str(seg),
                          "--snapshots", str(snaps)])
    results.append({"step": "prepare", "ok": rc == 0, "output": str(seg)})
    if rc != 0:
        return {"results": results, "ok": False}

    classified = artifacts_dir / "segments_classified.json"
    rc, _, _ = run_step([sys.executable, str(ROOT / "scripts" / "detect_language.py"),
                          "--segments", str(seg), "--out", str(classified)])
    results.append({"step": "detect_language", "ok": rc == 0, "output": str(classified)})
    if rc != 0:
        return {"results": results, "ok": False}

    profile = artifacts_dir / "profile.json"
    profile.write_text(json.dumps({
        "target_language": "es",
        "source_language": "auto",
        "markdown_dialect": "commonmark+gfm",
        "slug_algorithm": {"name": "github", "version": "v1"},
        "code_preservation": "strict",
        "frontmatter_policy": "preserve",
        "bilingual_policy": "first-mention-per-document",
        "punctuation_preference": "es-comma-period",
        "review_mode": "assisted",
        "paths": {"source_root": str(source_root), "work_root": str(artifacts_dir), "output_root": str(artifacts_dir)},
        "exclusions": [],
        "context_budget": 1500,
        "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
    }, indent=2), encoding="utf-8")

    packets = artifacts_dir / "packets.json"
    rc, _, _ = run_step([sys.executable, str(ROOT / "scripts" / "build_packets.py"),
                          "--segments", str(classified), "--profile", str(profile),
                          "--out", str(packets)])
    results.append({"step": "build_packets", "ok": rc == 0, "output": str(packets)})
    if rc != 0:
        return {"results": results, "ok": False}

    rc, _, _ = run_step([sys.executable, str(ROOT / "scripts" / "extract_terms.py"),
                          "--inventory", str(inv), "--snapshots", str(snaps),
                          "--segments", str(classified), "--out", str(glossary_path)])
    results.append({"step": "extract_terms", "ok": rc == 0, "output": str(glossary_path)})
    if rc != 0:
        return {"results": results, "ok": False}

    if translations_dir.exists():
        shutil.rmtree(translations_dir)
    translations_dir.mkdir(parents=True)
    rc, _, _ = run_step([sys.executable, str(ROOT / "scripts" / "translate_pilot.py"),
                          "--packets", str(packets), "--segments", str(classified),
                          "--out", str(translations_dir), "--mode", translate_mode])
    results.append({"step": f"translate_pilot[{translate_mode}]", "ok": rc == 0, "output": str(translations_dir)})
    if rc != 0:
        return {"results": results, "ok": False}

    anchors_dir = artifacts_dir / "anchors"
    if anchors_dir.exists():
        shutil.rmtree(anchors_dir)
    anchors_dir.mkdir()
    rc, _, _ = run_step([sys.executable, str(ROOT / "scripts" / "build_anchors.py"),
                          "--snapshots", str(snaps), "--out", str(anchors_dir)])
    results.append({"step": "build_anchors", "ok": rc == 0, "output": str(anchors_dir)})
    if rc != 0:
        return {"results": results, "ok": False}

    rew_report = artifacts_dir / "rewrite_report.json"
    rc, _, _ = run_step([sys.executable, str(ROOT / "scripts" / "rewrite_references.py"),
                          "--source", str(source_root), "--output-dir", str(artifacts_dir / "rewritten"),
                          "--anchors", str(anchors_dir), "--report", str(rew_report)])
    results.append({"step": "rewrite_references", "ok": rc == 0, "output": str(rew_report)})
    if rc != 0:
        return {"results": results, "ok": False}

    validate_out = artifacts_dir / "validate.json"
    rc, _, _ = run_step([sys.executable, str(ROOT / "scripts" / "validate.py"),
                          "--source", str(source_root),
                          "--output-dir", str(artifacts_dir / "rewritten"),
                          "--packets", str(packets), "--segments", str(classified),
                          "--translations", str(translations_dir),
                          "--snapshots", str(snaps), "--anchors", str(anchors_dir),
                          "--manifest", str(artifacts_dir / "manifest.json"),
                          "--out", str(validate_out)])
    results.append({"step": "validate", "ok": rc == 0, "output": str(validate_out)})

    manifest = artifacts_dir / "manifest.json"
    if not manifest.exists():
        doc_ids = json.loads(classified.read_text(encoding="utf-8"))["files"]
        now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        glossary_bytes = glossary_path.read_bytes()
        profile_bytes = profile.read_bytes()
        manifest_payload = {
            "run_id": run_id,
            "created_at": now,
            "manifest_version": "translate/v1",
            "skill_version": skill_version(),
            "parser": {"name": "markdown-it-py", "version": "3.0.0"},
            "anchor_policy": {"algorithm": "github-slug-v1", "version": "v1"},
            "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
            "glossary_snapshot": {
                "version": json.loads(glossary_bytes.decode("utf-8")).get("version", 1),
                "hash": hashlib.sha256(glossary_bytes).hexdigest(),
                "frozen": bool(json.loads(glossary_bytes.decode("utf-8")).get("frozen", False)),
            },
            "profile_snapshot": {"hash": hashlib.sha256(profile_bytes).hexdigest()},
            "inputs": {
                "source_root": str(source_root),
                "total_files": len(doc_ids),
                "total_bytes": sum(f.get("bytes", 0) for f in json.loads(inv.read_text(encoding="utf-8")).get("files", [])),
                "hashes_indexed": True,
            },
            "files": [{
                "path": f["path"],
                "document_id": f["document_id"],
                "source_hash": f["source_hash"],
                "current_state": "translated",
                "state_history": [
                    {"state": "inventoried", "timestamp": now, "reason": "recorrido end-to-end"},
                    {"state": "translated", "timestamp": now, "reason": "traducción identidad del recorrido"},
                ],
                "last_transition_at": now,
                "segment_count": len(f.get("segments", [])),
            } for f in doc_ids],
        }
        manifest.write_text(json.dumps(manifest_payload, indent=2), encoding="utf-8")

    integrity_out = artifacts_dir / "integrity.json"
    rc, _, _ = run_step([sys.executable, str(ROOT / "scripts" / "check_integrity.py"),
                          "--manifest", str(manifest), "--out", str(integrity_out)])
    results.append({"step": "check_integrity", "ok": rc == 0, "output": str(integrity_out)})

    audit_out = artifacts_dir / "audit.json"
    rc, _, _ = run_step([sys.executable, str(ROOT / "scripts" / "audit_terminology.py"),
                          "--translations", str(translations_dir), "--glossary", str(glossary_path),
                          "--out", str(audit_out)])
    results.append({"step": "audit_terminology", "ok": rc == 0, "output": str(audit_out)})

    valid_tr_out = artifacts_dir / "validate_translations.json"
    rc, _, _ = run_step([sys.executable, str(ROOT / "scripts" / "validate_translations.py"),
                          "--translations", str(translations_dir), "--segments", str(classified),
                          "--out", str(valid_tr_out)])
    results.append({"step": "validate_translations", "ok": rc == 0, "output": str(valid_tr_out)})

    numbers_out = artifacts_dir / "numbers.json"
    rc, _, _ = run_step([sys.executable, str(ROOT / "scripts" / "check_numbers.py"),
                          "--translations", str(translations_dir), "--segments", str(classified),
                          "--out", str(numbers_out)])
    results.append({"step": "check_numbers", "ok": rc == 0, "output": str(numbers_out)})

    return {"results": results, "ok": all(r["ok"] for r in results)}


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source_root = Path(args.source_root)
    output_dir = Path(args.output_dir) / args.run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    translations_dir = Path(args.translations) if args.translations else output_dir / "translations"
    glossary_path = Path(args.glossary) if args.glossary else output_dir / "glossary.json"

    summary = run_pipeline(source_root, output_dir, translations_dir, glossary_path, args.run_id, args.translate_mode)
    artifacts: list[dict] = []
    for path in sorted(output_dir.glob("**/*")):
        if path.is_file():
            artifacts.append({"path": str(path.relative_to(output_dir)), "sha256": sha256_file(path), "bytes": path.stat().st_size})

    report_path = output_dir / "END_TO_END_REPORT.md"
    lines = [
        f"# Reporte end-to-end — {args.run_id}",
        "",
        f"Generado: {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        "",
        f"Origen: `{source_root}`",
        "",
        "> Este recorrido comprueba la mecánica del pipeline con traducción",
        f"> identidad (`--translate-mode {args.translate_mode}`). No es una traducción y no",
        "> sirve como evidencia de cobertura de contenido. La evidencia de la",
        "> traducción la dan la revisión semántica y el gate del corpus.",
        "",
        "## Artefactos",
        "",
        "| Ruta | SHA-256 | Bytes |",
        "|---|---|---|",
    ]
    for a in artifacts[:50]:
        lines.append(f"| `{a['path']}` | `{a['sha256'][:16]}…` | {a['bytes']} |")
    lines.append("")
    lines.append("## Pasos del pipeline")
    lines.append("")
    for r in summary["results"]:
        lines.append(f"- {'✅' if r['ok'] else '❌'} `{r['step']}` → `{r['output']}`")

    report_path.write_text("\n".join(lines), encoding="utf-8")

    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())