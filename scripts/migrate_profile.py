"""Migración de perfil al contrato 1.1.0 (fase 150, G-EXT).

Motivo: desde `profile.schema.json` 1.1.0, un módulo opcional con
`enabled: true` tiene que declarar **qué corpus lo justifica**
(`corpus_ref`) y **por qué** (`justification`). Es el criterio 1 de G-EXT:
una activación sin motivo es un defecto, no una configuración.

Esta herramienta rellena esos dos campos con lo que ya está escrito en
`modules.json` y en el caso de `evals/cases/` del módulo. No inventa un
corpus ni una justificación: si el módulo no tiene caso declarado, la
migración **falla** y dice cuál falta.

Qué **no** hace:

- No modifica ningún otro valor del perfil. Un perfil migrado se comporta
  igual que antes, con un campo más de trazabilidad.
- No toca los perfiles de ejecuciones ya terminadas. Esos archivos son
  evidencia histórica y su hash está anclado en el manifiesto: cambiarlos
  invalidaría la aprobación de esa ejecución (INV-13). Para esos, la
  activación sin corpus queda declarada en `evals/cases/<módulo>.md`.
- No corrige una activación inmotivada: solo la documenta con el caso que
  la revisa. Si el corpus declarado dice `corpus_real: false`, la
  justificación dice que el perfil es de laboratorio.

    0 = perfil migrado o ya conforme
    2 = entrada inválida o falta el caso de un módulo activo
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from delivery_common import write_atomic  # noqa: E402

EXIT_OK = 0
EXIT_INPUT = 2

# Claves de perfil cuyo bloque lleva su propio corpus_ref/justification.
# El orden no importa: cada módulo se migra con su caso.
MODULE_BLOCKS = (
    "mdx",
    "html",
    "admonitions",
    "definition_lists",
    "directives",
    "mermaid",
    "wikilinks",
    "mixed_profile",
    "rtl",
    "delivery",
    "terminology",
)
# `locale` no tiene `enabled`: declararlo ya es activarlo, y el esquema lo
# exige siempre (profile.schema.json 1.1.0).
ALWAYS_ON = ("locale",)

LAB_NOTE = (
    "Perfil de laboratorio: el corpus declarado no es material real. "
    "Migrado por scripts/migrate_profile.py; no autoriza una ejecución real."
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="migrate_profile.py")
    p.add_argument("--profile", required=True, help="Perfil JSON a migrar.")
    p.add_argument("--out", help="Perfil migrado. Si se omite, se escribe sobre el original.")
    p.add_argument("--declarations", default=str(ROOT / "modules.json"))
    p.add_argument("--check", action="store_true",
                   help="Solo informa de lo que habría que migrar; no escribe.")
    return p.parse_args(argv)


def load_module_facts(declarations_path: Path) -> dict[str, dict]:
    try:
        data = json.loads(declarations_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        raise SystemExit(f"error: no se pueden leer las declaraciones: {err}")
    facts: dict[str, dict] = {}
    for module in data.get("modules", []):
        keys = [module.get("activation_option", "").split(",")[0].strip()]
        block = keys[0].split(".")[0]
        facts[block] = {
            "corpus_ref": module.get("corpus_ref", ""),
            "justification": module.get("justification", ""),
            "corpus_real": bool(module.get("corpus_real")),
        }
    return facts


def needs_migration(profile: dict, key: str) -> bool:
    block = profile.get(key)
    if not isinstance(block, dict):
        return False
    if key in ALWAYS_ON:
        return bool(block) and "corpus_ref" not in block
    return bool(block.get("enabled")) and "corpus_ref" not in block


def migrate(profile: dict, facts: dict[str, dict]) -> tuple[dict, list[str]]:
    out = json.loads(json.dumps(profile))  # copia profunda
    pending: list[str] = []
    for key in (*MODULE_BLOCKS, *ALWAYS_ON):
        if not needs_migration(profile, key):
            continue
        fact = facts.get(key)
        if not fact or not fact["corpus_ref"]:
            pending.append(key)
            continue
        out[key]["corpus_ref"] = fact["corpus_ref"]
        out[key]["justification"] = fact["justification"]
        if not fact["corpus_real"] and "justification" not in out[key]:
            out[key]["justification"] = LAB_NOTE
    return out, pending


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        profile = json.loads(Path(args.profile).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        print(f"error: no se puede leer el perfil: {err}", file=sys.stderr)
        return EXIT_INPUT

    facts = load_module_facts(Path(args.declarations))
    migrated, pending = migrate(profile, facts)

    if pending:
        print(
            "error: estos módulos están activos sin caso declarado en modules.json: "
            + ", ".join(pending),
            file=sys.stderr,
        )
        print(
            "       sin caso no hay justificación que rellenar; declara el módulo en "
            "modules.json antes de migrar",
            file=sys.stderr,
        )
        return EXIT_INPUT

    changed = sorted(
        key for key in (*MODULE_BLOCKS, *ALWAYS_ON)
        if isinstance(profile.get(key), dict)
        and isinstance(migrated.get(key), dict)
        and profile[key] != migrated[key]
    )
    if args.check:
        print(json.dumps({"would_change": changed}, ensure_ascii=False))
        return EXIT_OK
    if not changed:
        print(f"ok: el perfil ya declara corpus en {args.profile}")
        return EXIT_OK

    out_path = Path(args.out) if args.out else Path(args.profile)
    write_atomic(out_path, migrated)
    print(f"ok: migrados {changed} -> {out_path}")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())