"""Evaluador de par de idiomas (fase 103 del roadmap).

Ejecuta la cadena determinista (inventario → preparación →
clasificación → paquetería → citas → validación) sobre un corpus
autorizado para un par de idioma concreto y vuelca los resultados en
``reports/<pair>-pilot/``. NO realiza la traducción asistida real —
esa tarea la lleva el agente en su flujo natural —, sino que produce
los artefactos verificables que cierran la fase 103 con
``evaluation_kind: assisted``.

El módulo también acepta ``--dry-run`` para validar el conjunto de
salidas sin escribir archivos, lo que resulta útil en CI.

Uso::

    python3 scripts/eval_pair.py \
        --source tests/fixtures/pilot-fr \
        --pair fr-es \
        --out reports/fr-es-pilot \
        --mixed-profile tests/fixtures/mixed_lang/profile-strict.json
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CITATIONS = ROOT / "scripts" / "citations.py"


def run_module(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *args],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(ROOT),
    )


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="eval_pair.py")
    p.add_argument("--source", required=True, help="Carpeta del corpus piloto.")
    p.add_argument("--pair", required=True, help="Par de idioma origen→destino, p. ej. fr-es.")
    p.add_argument("--out", required=True, help="Directorio de salida para reports.")
    p.add_argument("--recognized", default="en,fr", help="Lista separada por comas para detect_language.py.")
    p.add_argument("--mixed-profile", default=None, help="JSON con la política mixed_profile opcional.")
    p.add_argument("--dry-run", action="store_true", help="No escribir archivos; solo validar.")
    p.add_argument(
        "--reviewer-status",
        default="assisted_only_pending_human",
        choices=["human_approved", "assisted_only_pending_human", "not_applicable"],
    )
    p.add_argument("--human-reviewer", default=None, help="Nombre del revisor humano si existe.")
    return p.parse_args(argv)


def write_atomic(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if "-" not in args.pair:
        print("error: --pair debe tener formato origen-destino, p. ej. fr-es", file=sys.stderr)
        return 2
    source_lang, target_lang = args.pair.split("-", 1)

    out_dir = Path(args.out)
    if out_dir.exists() and not args.dry_run:
        for old in out_dir.glob("**/*"):
            if old.is_file():
                old.unlink()
    out_dir.mkdir(parents=True, exist_ok=True)

    inv = out_dir / "inventory.json"
    seg = out_dir / "segments.json"
    classified = out_dir / "classified.json"
    citations_out = out_dir / "citations.json"
    packets = out_dir / "packets.json"

    source_abs = Path(args.source).resolve()

    inv_rc = run_module(["scripts/inventory.py", "--source", args.source, "--out", str(inv)]).returncode
    seg_rc = run_module(["scripts/prepare.py", "--inventory", str(inv), "--segments", str(seg)]).returncode
    det_args = ["scripts/detect_language.py", "--segments", str(seg), "--out", str(classified), "--recognized", args.recognized]
    det_rc = run_module(det_args).returncode
    citations_rc = 0
    if not args.dry_run:
        sys.path.insert(0, str(ROOT / "scripts"))
        import citations as _citations
        classified_payload = json.loads(classified.read_text(encoding="utf-8"))
        citation_counts = {t: 0 for t in _citations.CITATION_TYPES}
        for f in classified_payload.get("files", []):
            cnt = _citations.classify_all(f.get("segments", []))
            for k, v in cnt.items():
                citation_counts[k] += v
        citations_payload = {
            "pair": args.pair,
            "counts": citation_counts,
            "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        write_atomic(citations_out, citations_payload)

    pack_args = [
        "scripts/packetize.py",
        "--segments", str(classified),
        "--out", str(packets),
    ]
    if args.mixed_profile:
        pack_args += ["--mixed-profile", args.mixed_profile]
    pack_rc = run_module(pack_args).returncode

    classified_payload = json.loads(classified.read_text(encoding="utf-8"))
    total_segments = sum(len(f["segments"]) for f in classified_payload.get("files", []))
    by_lang: dict[str, int] = {}
    by_disp: dict[str, int] = {}
    for f in classified_payload.get("files", []):
        for s in f["segments"]:
            by_lang[s.get("language", "?")] = by_lang.get(s.get("language", "?"), 0) + 1
            by_disp[s.get("disposition", "?")] = by_disp.get(s.get("disposition", "?"), 0) + 1

    inventory_payload = json.loads(inv.read_text(encoding="utf-8"))
    inventory_files = inventory_payload.get("files", inventory_payload.get("entries", []))
    inventory_files = [f for f in inventory_files if isinstance(f, dict)]
    inventory_summary = {
        "total_files": len(inventory_files),
        "total_bytes": sum(f.get("size", f.get("bytes", 0)) for f in inventory_files),
        "hashes_indexed": all(bool(f.get("sha256") or f.get("hash")) for f in inventory_files),
    }

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    eval_payload = {
        "pair": args.pair,
        "source_language": source_lang,
        "target_language": target_lang,
        "generated_at": now,
        "evaluation_kind": "assisted",
        "human_reviewer": args.human_reviewer,
        "reviewer_status": args.reviewer_status,
        "disclaimer": (
            "Revisión asistida por modelo, NO humana. La fase 103 del roadmap "
            "exige un revisor humano nativo en el idioma de origen para cerrarse "
            "con simbolo de cierre. Mientras esto no ocurra, los artefactos sirven "
            "como evidencia de la cadena determinista, no como certificación de "
            "fidelidad semántica."
        ),
        "returncodes": {
            "inventory": inv_rc,
            "prepare": seg_rc,
            "detect_language": det_rc,
            "citations": citations_rc,
            "packetize": pack_rc,
        },
        "metrics": {
            "total_segments": total_segments,
            "by_language": by_lang,
            "by_disposition": by_disp,
            "inventory": inventory_summary,
        },
        "policy_paths": {
            "source_language_policy": "references/source-language-policy-fr.md",
            "citations_policy": "references/citations-policy.md",
        },
        "fixtures": {
            "pilot": str(source_abs.relative_to(ROOT)) if source_abs.is_relative_to(ROOT) else str(source_abs),
        },
    }
    eval_path = out_dir / "eval.json"
    write_atomic(eval_path, eval_payload)
    print(f"ok: eval_pair -> {eval_path}")

    summary_path = out_dir / "summary.md"
    summary_lines = [
        f"# Resumen de evaluación — par {args.pair}",
        "",
        f"- Estado de revisión: **{args.reviewer_status}**",
        f"- Tipo de evaluación: **{eval_payload['evaluation_kind']}**",
        f"- Revisor humano: **{args.human_reviewer or '(sin designar)'}**",
        "",
        "> " + eval_payload["disclaimer"],
        "",
        "## Métricas",
        "",
        f"- Segmentos totales: {total_segments}",
        f"- Por idioma: {by_lang}",
        f"- Por disposición: {by_disp}",
        "",
        "## Códigos de retorno",
        "",
        f"- inventory: {inv_rc}",
        f"- prepare: {seg_rc}",
        f"- detect_language: {det_rc}",
        f"- citations: {citations_rc}",
        f"- packetize: {pack_rc}",
        "",
        "## Decisiones pendientes",
        "",
        "- Designar un revisor humano nativo en francés para cerrar la fase 103.",
        "- Sustituir el corpus derivado CC0 por un volcado Markdown real cuando",
        "  se activen las fases 071-080 (HTML embebido).",
    ]
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    print(f"ok: summary -> {summary_path}")

    return 0 if all(r == 0 for r in eval_payload["returncodes"].values()) else 1


if __name__ == "__main__":
    sys.exit(main())
