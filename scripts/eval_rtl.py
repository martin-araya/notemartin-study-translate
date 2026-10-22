"""Evaluador del par RTL (fase 108).

Ejecuta la cadena determinista sobre un corpus que contenga texto
RTL (árabe, hebreo, etc.) y vuelca los artefactos en
``reports/rtl/``. La verificación central es que el texto RTL se
preserva byte-a-byte a través del inventario.

Uso::

    python3 scripts/eval_rtl.py \
        --source tests/fixtures/rtl \
        --pair ar-es \
        --out reports/rtl \
        --recognized en,ar
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


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="eval_rtl.py")
    p.add_argument("--source", required=True)
    p.add_argument("--pair", required=True, help="Origen-destino, p. ej. ar-es")
    p.add_argument("--out", required=True)
    p.add_argument("--recognized", default="en,ar")
    p.add_argument("--no-clean", action="store_true")
    p.add_argument(
        "--reviewer-status",
        default="assisted_only_pending_human",
        choices=["human_approved", "assisted_only_pending_human", "not_applicable"],
    )
    p.add_argument("--human-reviewer", default=None)
    return p.parse_args(argv)


def write_atomic(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def run_module(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *args],
        capture_output=True,
        text=True,
        check=False,
        cwd=str(ROOT),
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if "-" not in args.pair:
        print("error: --pair debe tener formato origen-destino, p. ej. ar-es", file=sys.stderr)
        return 2
    source_lang, target_lang = args.pair.split("-", 1)

    out_dir = Path(args.out)
    if not args.no_clean and out_dir.exists():
        for f in out_dir.glob("**/*"):
            if f.is_file():
                f.unlink()
    out_dir.mkdir(parents=True, exist_ok=True)

    inv = out_dir / "inventory.json"
    seg = out_dir / "segments.json"
    classified = out_dir / "classified.json"
    rtl = out_dir / "rtl.json"

    inv_rc = run_module(["scripts/inventory.py", "--source", args.source, "--out", str(inv)]).returncode
    seg_rc = run_module(["scripts/prepare.py", "--inventory", str(inv), "--segments", str(seg)]).returncode
    det_rc = run_module(
        ["scripts/detect_language.py", "--segments", str(seg),
         "--out", str(classified), "--recognized", args.recognized]
    ).returncode

    sys.path.insert(0, str(ROOT / "scripts"))
    import detect_text_direction as dtd

    classified_payload = json.loads(classified.read_text(encoding="utf-8"))
    text_dir_counts = {"ltr": 0, "rtl": 0, "mixed": 0}
    bytes_original_by_path: dict[str, str] = {}
    for f in classified_payload.get("files", []):
        segs = f.get("segments", [])
        counts = dtd.classify_all(segs)
        for k, v in counts.items():
            text_dir_counts[k] += v
        src_path = ROOT / f.get("path", "")
        if src_path.exists():
            bytes_original_by_path[f.get("path")] = hashlib.sha256(src_path.read_bytes()).hexdigest()

    rtl_payload = {
        "text_direction_counts": text_dir_counts,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    write_atomic(rtl, rtl_payload)

    metrics = {
        "total_segments": sum(len(f["segments"]) for f in classified_payload.get("files", [])),
        "by_language": {},
        "by_disposition": {},
        "by_text_direction": text_dir_counts,
    }
    for f in classified_payload.get("files", []):
        for s in f.get("segments", []):
            metrics["by_language"][s.get("language", "?")] = (
                metrics["by_language"].get(s.get("language", "?"), 0) + 1
            )
            metrics["by_disposition"][s.get("disposition", "?")] = (
                metrics["by_disposition"].get(s.get("disposition", "?"), 0) + 1
            )

    inventories = json.loads(inv.read_text(encoding="utf-8"))
    entries = inventories.get("files", inventories.get("entries", []))
    entries = [f for f in entries if isinstance(f, dict)]

    eval_payload = {
        "pair": args.pair,
        "source_language": source_lang,
        "target_language": target_lang,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "evaluation_kind": "assisted",
        "reviewer_status": args.reviewer_status,
        "human_reviewer": args.human_reviewer,
        "disclaimer": (
            "Revisión asistida; sin firma nativa del par. La fase 109 exige un "
            "firmante humano en el idioma de origen. La política RTL preserva "
            "bytes Unicode y aplica marcas de dirección por segmento; no "
            "demuestra fidelidad de render."
        ),
        "policy_paths": {
            "rtl_policy": "references/rtl-policy.md",
            "source_language_policy_placeholder": (
                "references/source-language-policy-fr.md sirve de plantilla. "
                "El equivalente ar→es debe existir antes de human_approved."
            ),
        },
        "returncodes": {
            "inventory": inv_rc,
            "prepare": seg_rc,
            "detect_language": det_rc,
            "detect_text_direction": 0,
        },
        "metrics": metrics,
        "fixtures": {
            "corpus": str(Path(args.source).resolve().relative_to(ROOT))
            if Path(args.source).resolve().is_relative_to(ROOT)
            else str(Path(args.source).resolve()),
            "bytes_original": bytes_original_by_path,
        },
    }
    write_atomic(out_dir / "eval.json", eval_payload)

    summary = [
        f"# Resumen RTL — {args.pair}",
        "",
        f"- Estado de revisión: **{args.reviewer_status}**",
        f"- Tipo de evaluación: **{eval_payload['evaluation_kind']}**",
        f"- Segmentos totales: {metrics['total_segments']}",
        f"- Por dirección: {text_dir_counts}",
        f"- Por idioma: {metrics['by_language']}",
        f"- Por disposición: {metrics['by_disposition']}",
        "",
        "## Códigos de retorno",
        f"- inventory: {inv_rc}",
        f"- prepare: {seg_rc}",
        f"- detect_language: {det_rc}",
        "",
        "> " + eval_payload["disclaimer"],
        "",
        "## Decisiones pendientes",
        "",
        "- Designar un nativo en árabe para cerrar la fase 109.",
        "- Crear `references/source-language-policy-ar.md` (la plantilla fr sirve).",
    ]
    (out_dir / "summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")

    rcs = eval_payload["returncodes"].values()
    print(f"ok: eval_rtl {args.pair} -> {out_dir}/eval.json")
    return 0 if all(r == 0 for r in rcs) else 1


if __name__ == "__main__":
    sys.exit(main())
