"""Evaluador regional para variantes del español (fase 107).

Ejecuta la cadena determinista del núcleo (inventario → preparación
→ clasificación → paquetería) sobre el corpus piloto de una variante
regional concreta y vuelca los resultados en un directorio de
reportes. NO traduce prosa; su objetivo es asegurar que la
configuración regional produce paquetes consistentes y que distintas
variantes no comparten caché ni identificadores.

Uso::

    python3 scripts/eval_regional.py \
        --variant es-MX \
        --corpus tests/fixtures/es-mx \
        --out reports/es-mx

El módulo también tolera múltiples variantes, una por ejecución
separada, y respeta el aislamiento total de directorios.
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
VARIANTS = ("es-ES", "es-MX", "es-AR", "es")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="eval_regional.py")
    p.add_argument("--variant", required=True, choices=VARIANTS)
    p.add_argument("--corpus", required=True, help="Carpeta del corpus piloto.")
    p.add_argument("--out", required=True, help="Directorio de salida.")
    p.add_argument("--recognized", default="en")
    p.add_argument("--no-clean", action="store_true")
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
    out_dir = Path(args.out)
    if not args.no_clean and out_dir.exists():
        for f in out_dir.glob("**/*"):
            if f.is_file():
                f.unlink()
    out_dir.mkdir(parents=True, exist_ok=True)
    inv = out_dir / "inventory.json"
    seg = out_dir / "segments.json"
    classified = out_dir / "classified.json"
    packets = out_dir / "packets.json"

    inv_rc = run_module(["scripts/inventory.py", "--source", args.corpus, "--out", str(inv)]).returncode
    seg_rc = run_module(["scripts/prepare.py", "--inventory", str(inv), "--segments", str(seg)]).returncode
    det_rc = run_module(
        ["scripts/detect_language.py", "--segments", str(seg), "--out", str(classified), "--recognized", args.recognized]
    ).returncode
    pack_rc = run_module(["scripts/packetize.py", "--segments", str(classified), "--out", str(packets)]).returncode

    classified_payload = json.loads(classified.read_text(encoding="utf-8"))
    inventories = json.loads(inv.read_text(encoding="utf-8"))
    inventory_entries = inventories.get("files", inventories.get("entries", []))
    inventory_entries = [f for f in inventory_entries if isinstance(f, dict)]

    # Hash de cada paquete para validar aislamiento entre variantes
    packet_ids = []
    packets_payload = json.loads(packets.read_text(encoding="utf-8"))
    for pkt in packets_payload.get("packets", []):
        packet_ids.append(
            {
                "packet_id": pkt["packet_id"],
                "source_language": pkt.get("source_language"),
                "sha256_short": hashlib.sha256(
                    (pkt["packet_id"] + args.variant).encode("utf-8")
                ).hexdigest()[:16],
                "total_chars": pkt.get("total_chars", 0),
            }
        )

    metrics = {
        "total_segments": sum(len(f["segments"]) for f in classified_payload.get("files", [])),
        "by_language": {},
        "by_disposition": {},
        "inventory": {
            "total_files": len(inventory_entries),
            "total_bytes": sum(f.get("size", f.get("bytes", 0)) for f in inventory_entries),
        },
    }
    for f in classified_payload.get("files", []):
        for s in f.get("segments", []):
            metrics["by_language"][s.get("language", "?")] = (
                metrics["by_language"].get(s.get("language", "?"), 0) + 1
            )
            metrics["by_disposition"][s.get("disposition", "?")] = (
                metrics["by_disposition"].get(s.get("disposition", "?"), 0) + 1
            )

    eval_payload = {
        "variant": args.variant,
        "corpus": str(Path(args.corpus).resolve().relative_to(ROOT))
        if Path(args.corpus).resolve().is_relative_to(ROOT)
        else str(Path(args.corpus).resolve()),
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "evaluation_kind": "assisted",
        "reviewer_status": "assisted_only_pending_human",
        "human_reviewer": None,
        "disclaimer": (
            "Revisión asistida; sin firma nativa. La fase 109 exige un firmante "
            "antes de marcar la fila como estable."
        ),
        "returncodes": {
            "inventory": inv_rc,
            "prepare": seg_rc,
            "detect_language": det_rc,
            "packetize": pack_rc,
        },
        "metrics": metrics,
        "packets": packet_ids,
        "locale": {
            "variant": args.variant,
            "voseo": args.variant == "es-AR",
            "vosotros": args.variant == "es-ES",
            "neutralize_colloquialisms": False,
        },
    }
    write_atomic(out_dir / "eval.json", eval_payload)
    summary_lines = [
        f"# Resumen regional — {args.variant}",
        "",
        f"- Variante: **{args.variant}**",
        f"- Revisor humano nativo: **(sin designar)**",
        f"- Estado: **{eval_payload['reviewer_status']}**",
        "",
        f"- Segmentos totales: {metrics['total_segments']}",
        f"- Por idioma: {metrics['by_language']}",
        f"- Por disposición: {metrics['by_disposition']}",
        f"- Paquetes: {len(packet_ids)}",
        "",
        "## Códigos de retorno",
        "",
        f"- inventory: {inv_rc}",
        f"- prepare: {seg_rc}",
        f"- detect_language: {det_rc}",
        f"- packetize: {pack_rc}",
        "",
        "> " + eval_payload["disclaimer"],
        "",
        "## Decisiones pendientes",
        "",
        "- Designar un nativo por variante para cerrar la fase 109.",
        "- Activar `check_cache_isolation.py` sobre `reports/es-{es,mx,ar}`.",
    ]
    (out_dir / "summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    rcs = eval_payload["returncodes"].values()
    print(f"ok: eval_regional {args.variant} -> {out_dir}/eval.json")
    return 0 if all(r == 0 for r in rcs) else 1


if __name__ == "__main__":
    sys.exit(main())
