"""Registra una ejecución real de traducción para compararla (fase 145).

El registro **no** contiene la prosa traducida: guarda metadatos de
procedencia, el hash de cada segmento, su longitud, el número de
marcadores de protección y una vista previa truncada. El texto completo se
queda en el ``work_root`` de la ejecución, que es donde vive.

    2 = el run no tiene manifiesto legible
    3 = se pidió evidencia sintética sin --allow-synthetic
    4 = el manifiesto no declara la procedencia mínima (modelo, prompt,
        glosario o perfil)

Uso::

    python scripts/record_model_run.py \\
        --run work_root/run-0000beef \\
        --out reports/maintenance/model_runs/run-0000beef.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from delivery_common import now_iso, write_atomic  # noqa: E402
from redaction import safe_segment_id, truncate_for_log  # noqa: E402

PREVIEW_LIMIT = 120


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="record_model_run.py")
    p.add_argument("--run", required=True, help="Directorio de la ejecución con manifest.json")
    p.add_argument("--out", required=True)
    p.add_argument("--translations", default=None,
                   help="Directorio de traducciones. Por defecto <run>/translations")
    p.add_argument("--evidence", choices=["real", "synthetic"], default="real")
    p.add_argument("--allow-synthetic", action="store_true")
    p.add_argument("--note", default=None)
    return p.parse_args(argv)


def load_json(path: Path) -> dict | None:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def collect_segments(translations: Path) -> tuple[dict, list[str]]:
    segments: dict[str, dict] = {}
    problems: list[str] = []
    for path in sorted(Path(translations).glob("*.json")):
        document = load_json(path)
        if document is None:
            problems.append(f"traducción ilegible: {path.name}")
            continue
        for entry in document.get("entries") or []:
            sid = safe_segment_id(entry.get("segment_id"))
            text = entry.get("translated_text") or ""
            segments[sid] = {
                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "chars": len(text),
                "markers": text.count("§"),
                "preview": truncate_for_log(text, limit=PREVIEW_LIMIT),
                "document_id": document.get("document_id"),
            }
    return segments, problems


def record_run(run_dir: Path, translations: Path, evidence: str,
               allow_synthetic: bool, note: str | None = None) -> dict:
    manifest = load_json(run_dir / "manifest.json") or {}
    segments, problems = collect_segments(translations)
    model_meta = manifest.get("model_metadata") or {}
    return {
        "generated_at": now_iso(),
        "run_id": manifest.get("run_id"),
        "run_dir": str(run_dir),
        "translations_root": str(translations),
        "evidence_kind": "real_runs" if evidence == "real" else "synthetic",
        "synthetic": evidence != "real",
        "note": note,
        "problems": problems,
        "skill_version": manifest.get("skill_version"),
        "manifest_version": manifest.get("manifest_version"),
        "parser": manifest.get("parser"),
        "anchor_policy": manifest.get("anchor_policy"),
        "provider": model_meta.get("provider"),
        "model": model_meta.get("model"),
        "prompt_version": model_meta.get("prompt_version"),
        "glossary_hash": (manifest.get("glossary_snapshot") or {}).get("hash"),
        "profile_hash": (manifest.get("profile_snapshot") or {}).get("hash"),
        "source_hashes": {
            record.get("path"): record.get("source_hash")
            for record in manifest.get("files") or []
            if record.get("path")
        },
        "segments": segments,
        "counts": {
            "segments": len(segments),
            "documents": len({s.get("document_id") for s in segments.values()}),
        },
        "texts_stored": False,
        "note_policy": (
            "El texto completo no se copia a reports/: vive en translations_root. "
            "Este registro solo guarda hashes, longitudes y vistas previas truncadas."
        ),
    }


def missing_provenance(recording: dict) -> list[str]:
    required = {
        "model": recording.get("model"),
        "prompt_version": recording.get("prompt_version"),
        "glossary_hash": recording.get("glossary_hash"),
        "profile_hash": recording.get("profile_hash"),
    }
    return [name for name, value in required.items() if not value]


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.evidence == "synthetic" and not args.allow_synthetic:
        print(
            "error: la evidencia sintética no se registra sin --allow-synthetic, "
            "y su resultado no puede alimentar el comparador",
            file=sys.stderr,
        )
        return 3

    run_dir = Path(args.run)
    translations = Path(args.translations) if args.translations else run_dir / "translations"
    if not (run_dir / "manifest.json").exists():
        print(f"error: no existe manifest.json en {run_dir}", file=sys.stderr)
        return 2

    recording = record_run(run_dir, translations, args.evidence, args.allow_synthetic, args.note)
    missing = missing_provenance(recording)
    if missing:
        print(f"error: procedencia incompleta en el manifiesto: {missing}", file=sys.stderr)
        return 4

    write_atomic(Path(args.out), recording)
    print(
        f"ok: ejecución {recording['run_id']} registrada "
        f"({recording['counts']['segments']} segmentos, evidence={recording['evidence_kind']})"
        f" -> {args.out}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())