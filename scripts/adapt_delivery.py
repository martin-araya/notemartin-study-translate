"""Adaptación local opt-in para un destino de entrega (fase 134).

Aplica las reglas de un perfil de entrega a una **copia** del árbol
canónico. Garantías del contrato:

- El árbol canónico no se escribe nunca. Se comprueba que destino y
  canónico sean rutas disjuntas antes de copiar nada.
- Sin reglas activas la copia es byte a byte idéntica al canónico.
- Ninguna regla toca prosa traducida, bloques de código ni inline code:
  los destinos de enlace dentro de código protegido se calculan sobre
  una copia del texto con las regiones de código en blanco, así que sus
  offsets siguen siendo válidos sobre el original.
- Una regla que declare ``lossiness: content_loss`` se rechaza. El
  esquema también la rechaza.
- Las colisiones de destino abortan con código 4 en lugar de
  sobrescribir un recurso.

Uso::

    python scripts/adapt_delivery.py \
        --canonical output_root/run-001 \
        --profile references/delivery-plain-markdown-local.json \
        --destination-out work_root/run-001/delivery/plain-markdown-local \
        --out reports/delivery/adaptation_report.json
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from delivery_common import (  # noqa: E402
    ascii_slug,
    decode_link_target,
    is_external,
    is_within,
    iter_link_spans,
    now_iso,
    replace_spans,
    tree_hashes,
    write_atomic,
)

PROFILE_SCHEMA = ROOT / "schemas" / "delivery_profile.schema.json"

EXIT_OK = 0
EXIT_INPUT_ERROR = 2
EXIT_RULE_REJECTED = 3
EXIT_COLLISION = 4

KNOWN_RULES = ("relative-resource-paths", "ascii-resource-names")
LOSSY_REJECTED = "content_loss"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="adapt_delivery.py")
    p.add_argument("--canonical", required=True, help="Árbol canónico de solo lectura.")
    p.add_argument("--profile", required=True, help="Perfil de entrega JSON.")
    p.add_argument("--destination-out", required=True, help="Árbol adaptado a generar.")
    p.add_argument("--out", required=True, help="Informe de adaptación.")
    p.add_argument("--enable", action="append", default=[],
                   help="Regla a activar. Repetible. Si se omite se usan default_rules.")
    p.add_argument("--dry-run", action="store_true",
                   help="Calcula los cambios sin escribir el árbol adaptado.")
    return p.parse_args(argv)


def load_profile(path: str) -> dict:
    target = Path(path)
    if not target.exists():
        raise FileNotFoundError(f"perfil inexistente: {path}")
    profile = json.loads(target.read_text(encoding="utf-8"))
    try:
        import jsonschema
    except ImportError:
        return profile
    schema = json.loads(PROFILE_SCHEMA.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    errors = [e.message for e in validator.iter_errors(profile)]
    if errors:
        raise ValueError("perfil inválido: " + "; ".join(errors[:5]))
    return profile


def select_rules(profile: dict, requested: list[str]) -> tuple[list[dict], list[str]]:
    declared = {r["rule_id"]: r for r in profile.get("rules") or []}
    wanted = requested or list(profile.get("default_rules") or [])
    reasons: list[str] = []
    chosen: list[dict] = []
    for rule_id in wanted:
        rule = declared.get(rule_id)
        if rule is None:
            reasons.append(f"regla no declarada en el perfil: {rule_id}")
            continue
        if rule_id not in KNOWN_RULES:
            reasons.append(f"regla sin implementación: {rule_id}")
            continue
        if not rule.get("rationale"):
            reasons.append(f"regla sin justificación: {rule_id}")
            continue
        if rule.get("lossiness") == LOSSY_REJECTED:
            reasons.append(f"regla con pérdida de contenido rechazada: {rule_id}")
            continue
        chosen.append(rule)
    return chosen, reasons


def _doc_texts(root: Path) -> dict[str, str]:
    return {
        p.relative_to(root).as_posix(): p.read_text(encoding="utf-8")
        for p in sorted(root.rglob("*.md"))
        if p.is_file()
    }


def rule_relative_resource_paths(tree: Path) -> list[dict]:
    """Normaliza destinos de recursos: separadores y prefijos ``./``.

    Solo cambia el destino del enlace. La etiqueta, el resto de la línea
    y el contenido del recurso quedan intactos. Las referencias dentro
    de código protegido no se tocan.

    Dos exclusiones deliberadas, comprobadas contra el corpus real:

    - La codificación porcentual se conserva: un espacio literal en el
      destino rompería el enlace Markdown, que exige ``%20`` o
      delimitadores angulares.
    - Un destino que empieza por ``/`` es una ruta de la raíz del sitio
      de origen. Quitarle la barra produciría un enlace local que no
      resuelve, así que se deja intacto. Es deuda de entrada, no una
      regla de formato.
    """
    changes: list[dict] = []
    for rel, text in _doc_texts(tree).items():
        spans: list[tuple[int, int, str]] = []
        for _is_image, _label, raw, start, end in iter_link_spans(text, mask_inline=True):
            if is_external(raw):
                continue
            target_path, _sep, fragment = raw.partition("#")
            if not target_path or target_path.startswith("/"):
                continue
            normalized = target_path.replace("\\", "/")
            if normalized.startswith("./"):
                normalized = normalized[2:]
            if normalized == target_path:
                continue
            suffix = f"#{fragment}" if fragment else ""
            new_target = normalized + suffix
            spans.append((start, end, new_target))
            changes.append({"document": rel, "old": raw, "new": new_target})
        if spans:
            (tree / rel).write_text(replace_spans(text, spans), encoding="utf-8")
    return changes


def rule_ascii_resource_names(tree: Path) -> list[dict]:
    """Renombra recursos a ASCII minúsculas y actualiza las referencias.

    Los bytes del recurso no cambian; solo su ruta. Si dos recursos
    colisionan en el mismo directorio, la regla aborta.
    """
    changes: list[dict] = []
    renames: dict[str, str] = {}
    for path in sorted(tree.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        rel = path.relative_to(tree).as_posix()
        if rel.lower().endswith((".md", ".markdown")):
            continue
        if "/" in path.name:
            continue
        new_name = ascii_slug(path.name)
        if new_name == path.name:
            continue
        parent_rel = path.parent.relative_to(tree).as_posix()
        new_rel = path.name if parent_rel == "." else f"{parent_rel}/{new_name}"
        if new_rel in renames.values() or (tree / new_rel).exists():
            raise FileExistsError(
                f"colisión de recursos al normalizar nombres: {rel} -> {new_rel}"
            )
        renames[rel] = new_rel
        changes.append({"resource": rel, "old": rel, "new": new_rel})

    for old_rel, new_rel in renames.items():
        src = tree / old_rel
        dst = tree / new_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))

    if renames:
        for rel, text in _doc_texts(tree).items():
            spans: list[tuple[int, int, str]] = []
            for _is_image, _label, raw, start, end in iter_link_spans(text, mask_inline=True):
                if is_external(raw):
                    continue
                target_path, _sep, fragment = raw.partition("#")
                base = decode_link_target(target_path).replace("\\", "/")
                if base not in renames:
                    continue
                new_target = renames[base] + (f"#{fragment}" if fragment else "")
                spans.append((start, end, new_target))
                changes.append({"document": rel, "old": raw, "new": new_target})
            if spans:
                (tree / rel).write_text(replace_spans(text, spans), encoding="utf-8")
    return changes


RULE_IMPLEMENTATIONS = {
    "relative-resource-paths": rule_relative_resource_paths,
    "ascii-resource-names": rule_ascii_resource_names,
}


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    canonical = Path(args.canonical)
    destination = Path(args.destination_out)

    if not canonical.is_dir():
        print(f"error: árbol canónico inexistente: {canonical}", file=sys.stderr)
        return EXIT_INPUT_ERROR
    if is_within(destination, canonical) or is_within(canonical, destination):
        print(
            "error: el destino adaptado debe ser disjunto del árbol canónico",
            file=sys.stderr,
        )
        return EXIT_INPUT_ERROR

    try:
        profile = load_profile(args.profile)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_INPUT_ERROR

    if profile.get("kind") == "canonical" and args.enable:
        print("error: un perfil canónico no aplica reglas", file=sys.stderr)
        return EXIT_INPUT_ERROR

    rules, reasons = select_rules(profile, args.enable)
    before = tree_hashes(canonical)

    rejected_only = bool(reasons) and not rules
    changes: list[dict] = []
    collision: str | None = None

    if rejected_only:
        destination = None
        adapted_hashes: dict[str, str] = {}
        byte_identical = None
    else:
        if destination.exists():
            shutil.rmtree(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not args.dry_run:
            shutil.copytree(canonical, destination, symlinks=False)
            for rule in rules:
                try:
                    for change in RULE_IMPLEMENTATIONS[rule["rule_id"]](destination):
                        change["rule_id"] = rule["rule_id"]
                        change["lossiness"] = rule["lossiness"]
                        changes.append(change)
                except FileExistsError as exc:
                    collision = str(exc)
                    break
        else:
            for rule in rules:
                changes.append({"rule_id": rule["rule_id"], "dry_run": True})
        adapted_hashes = tree_hashes(destination) if destination.exists() else {}
        byte_identical = adapted_hashes == before

    after = tree_hashes(canonical)
    canonical_untouched = before == after

    report = {
        "generated_at": now_iso(),
        "profile_id": profile.get("profile_id"),
        "profile_version": profile.get("version"),
        "kind": profile.get("kind"),
        "canonical": str(canonical),
        "adapted": str(destination) if destination else None,
        "dry_run": bool(args.dry_run),
        "rules_enabled": [r["rule_id"] for r in rules],
        "rules_skipped": reasons,
        "changes": changes,
        "change_count": len(changes),
        "canonical_hashes_before": before,
        "canonical_hashes_after": after,
        "canonical_untouched": canonical_untouched,
        "byte_identical": byte_identical,
    }
    write_atomic(Path(args.out), report)

    if rejected_only:
        print("error: " + "; ".join(reasons), file=sys.stderr)
        return EXIT_RULE_REJECTED
    if collision:
        print(f"error: {collision}", file=sys.stderr)
        return EXIT_COLLISION
    if not canonical_untouched:
        print("error: el árbol canónico cambió durante la adaptación", file=sys.stderr)
        return EXIT_RULE_REJECTED
    print(
        f"ok: reglas={len(rules)} cambios={len(changes)} "
        f"byte_identical={byte_identical} -> {args.out}"
    )
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())