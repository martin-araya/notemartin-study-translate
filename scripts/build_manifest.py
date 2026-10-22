"""Construye el manifiesto de una corrida a partir de artefactos reales.

No inventa conteos ni procedencias: toma el hash de cada documento de sus
bytes en `source_root`, el hash del perfil y del glosario de los archivos
que existen, y la versión de la skill del contrato de release. Lo que el
entorno no expone se escribe `unknown` en vez de rellenarse.

    python3 scripts/build_manifest.py \\
        --inventory inventory.json --segments segments_classified.json \\
        --profile profile.json --glossary glossary.json \\
        --run-id run-0badc0de --model-provider kilo \\
        --model miniMax-M3 --prompt-version 1.0.0 --out manifest.json

La herramienta que escribió el manifiesto del piloto vivía en el
workdir de la corrida y no formaba parte de la skill: sin ella no había
manifiesto que construir fuera de aquel piloto.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UNKNOWN = "unknown"

# El perfil nombra la familia del algoritmo; el manifiesto registra el
# identificador exacto que ejecuta `build_anchors.py`. Sin esta
# correspondencia, el manifiesto declararía `github` y las anclas se
# habrían calculado con `github-slug-v1`.
ANCHOR_ALGORITHM_IDS = {
    "github": "github-slug-v1",
    "gitiles": "gitiles-slug-v1",
    "commonmark-default": "commonmark-default-slug-v1",
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_atomic(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="build_manifest.py")
    p.add_argument("--inventory", required=True)
    p.add_argument("--segments", required=True)
    p.add_argument("--profile", required=True)
    p.add_argument("--glossary", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--model-provider", default=UNKNOWN)
    p.add_argument("--model", default=UNKNOWN)
    p.add_argument("--prompt-version", default=UNKNOWN)
    p.add_argument("--reason", default="segmentos construidos con el perfil activo")
    return p.parse_args(argv)


def valid_run_id(run_id: str) -> bool:
    """`run-XXXXXXXX` con ocho dígitos hexadecimales, como el esquema exige.

    El esquema ya rechazaba otros formatos, pero después de escribir el
    archivo: un `run-beta-001` dejaba un manifiesto inválido en disco.
    """
    return re.fullmatch(r"run-[0-9a-f]{8}", run_id or "") is not None


def skill_version() -> str:
    contract = ROOT / "release_contract.json"
    if contract.exists():
        return json.loads(contract.read_text(encoding="utf-8")).get("skill_version", UNKNOWN)
    return UNKNOWN


def anchor_policy(profile: dict) -> dict:
    slug = profile.get("slug_algorithm") or {}
    name = slug.get("name", "github")
    return {
        "algorithm": ANCHOR_ALGORITHM_IDS.get(name, name),
        "version": slug.get("version", "v1"),
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not valid_run_id(args.run_id):
        print(
            f"error: run_id inválido: {args.run_id!r}. El esquema exige "
            "run- seguido de ocho dígitos hexadecimales (ej. run-0badc0de)",
            file=sys.stderr,
        )
        return 2
    inventory = json.loads(Path(args.inventory).read_text(encoding="utf-8"))
    segments = json.loads(Path(args.segments).read_text(encoding="utf-8"))
    glossary_bytes = Path(args.glossary).read_bytes()
    profile_bytes = Path(args.profile).read_bytes()
    glossary = json.loads(glossary_bytes.decode("utf-8"))
    profile = json.loads(profile_bytes.decode("utf-8"))

    source_root = Path(inventory["source_root"])
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    inventoried_at = inventory.get("generated_at") or now

    files: list[dict] = []
    missing: list[str] = []
    for entry in segments.get("files", []):
        rel = entry["path"]
        source = source_root / rel
        if not source.exists():
            missing.append(rel)
            continue
        files.append({
            "path": rel,
            "document_id": entry["document_id"],
            "source_hash": sha256_bytes(source.read_bytes()),
            # El manifiesto se construye antes de que exista traducción.
            # `translated` solo lo escribe advance_state.py cuando una
            # traducción real está en disco (INV-12).
            "current_state": "prepared",
            "state_history": [
                {"state": "inventoried", "timestamp": inventoried_at, "reason": "inventario del alcance autorizado"},
                {"state": "prepared", "timestamp": inventoried_at, "reason": "segmentos y hallazgos con el perfil activo"},
            ],
            "last_transition_at": inventoried_at,
            "segment_count": len(entry.get("segments", [])),
        })

    if missing:
        print(f"error: {len(missing)} documentos del alcance no existen en la fuente", file=sys.stderr)
        for rel in missing[:10]:
            print(f"  {rel}", file=sys.stderr)
        return 1

    manifest = {
        "run_id": args.run_id,
        "created_at": now,
        "manifest_version": "translate/v1",
        "skill_version": skill_version(),
        "parser": {"name": "markdown-it-py", "version": "3.0.0"},
        "anchor_policy": anchor_policy(profile),
        "model_metadata": {
            "provider": args.model_provider,
            "model": args.model,
            "prompt_version": args.prompt_version,
        },
        "glossary_snapshot": {
            "version": glossary.get("version", 1),
            "hash": sha256_bytes(glossary_bytes),
            "frozen": bool(glossary.get("frozen", False)),
        },
        "profile_snapshot": {"hash": sha256_bytes(profile_bytes)},
        "inputs": {
            "source_root": str(source_root),
            "total_files": len(files),
            "total_bytes": sum(f.get("bytes", 0) for f in inventory.get("files", [])),
            "hashes_indexed": True,
        },
        "files": files,
    }

    write_atomic(Path(args.out), manifest)
    print(f"ok: manifiesto con {len(files)} archivos -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())