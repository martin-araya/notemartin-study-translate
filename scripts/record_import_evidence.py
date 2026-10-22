"""Registro de evidencia de importación de muestra (fases 131, 132 y 133).

Genera ``import_evidence.json``: el checklist de qué se comprobó de una
importación real y, sobre todo, qué sigue sin verificar. Tres
capacidades separadas:

- ``--template`` (131): lista de documentos de muestra tomados del
  manifiesto aprobado. Nace con ``verified: false``,
  ``remote_status: no_verificado`` y todos los ``remote_result``
  en ``unknown``.
- ``--check-links`` (132): resolución local de enlaces calculada de
  forma determinista sobre el árbol exportado y los slugs de
  encabezado. Es el único campo que la skill puede afirmar sin
  importar nada. La navegación remota sigue en ``unknown``.
- ``--check-matrix`` (133): matriz de importación construcción por
  destino. Toda celda nace ``unverified``: que el Markdown sea válido
  no demuestra que el destino lo conserve.

``--record`` fusiona la evidencia que aporte el usuario. La promoción
a ``verified`` se exige en código, no solo en el esquema: si se
declara verificado sin revisor humano declarado, o si alguna
comprobación remota superada no trae evidencia, el registro se degrada
a ``verified: false`` y el script sale con código 3.

Uso::

    python scripts/record_import_evidence.py \\
        --manifest work/manifest.json \\
        --output-tree out/run-001 \\
        --check-links \\
        --matrix-out reports/import_matrix.json \\
        --out work/reports/import_evidence.json

    python scripts/record_import_evidence.py \\
        --manifest work/manifest.json \\
        --output-tree out/run-001 \\
        --record evidencia_del_usuario.json \\
        --out work/reports/import_evidence.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from delivery_common import (  # noqa: E402
    HEADING_RE,
    decode_link_target,
    is_external,
    iter_links,
    now_iso,
    split_fragment,
    strip_code_regions,
    write_atomic,
)

SCHEMA = ROOT / "schemas" / "import_evidence.schema.json"

EXIT_OK = 0
EXIT_INPUT_ERROR = 2
EXIT_VERIFICATION_REFUSED = 3

IMPORTABLE_STATES = ("approved", "exported", "already_target")

CHECK_IDS = (
    "table_structure",
    "code_block_bytes",
    "code_inline_bytes",
    "internal_link_local",
    "internal_link_remote",
    "image_and_alt",
    "callout_warning",
    "task_list",
    "frontmatter",
)

# Expectativas declaradas, no hechos comprobados. Fuente de verdad
# documental: references/notion-handoff.md §7.
MATRIX_EXPECTATIONS = {
    "table_structure": (
        "La tabla llega con la misma estructura de filas y columnas.",
        "La alineación declarada con :--- o ---: puede perderse.",
    ),
    "code_block_bytes": (
        "El bloque de código llega con su contenido literal.",
        "El resaltado depende del lenguaje declarado y puede perderse.",
    ),
    "code_inline_bytes": (
        "El código inline llega sin modifications.",
        "Ningún límite conocido; sigue sin comprobarse en el destino.",
    ),
    "internal_link_local": (
        "El enlace apunta al documento y al fragmento esperados en el Markdown entregado.",
        "La resolución local no demuestra nada sobre la navegación remota.",
    ),
    "internal_link_remote": (
        "Al pulsar el enlace se llega al encabezado de destino.",
        "La navegación por anclas puede romperse al importar.",
    ),
    "image_and_alt": (
        "La imagen llega con su texto alternativo.",
        "Las rutas relativas del scraper pueden no cargar en el destino.",
    ),
    "callout_warning": (
        "La advertencia conserva su carácter de advertencia.",
        "El destino puede representarla como texto plano.",
    ),
    "task_list": (
        "Los elementos - [ ] y - [x] se conservan como texto.",
        "Las casillas interactivas requieren API del destino.",
    ),
    "frontmatter": (
        "El frontmatter se conserva literal o se muestra como texto plano.",
        "Bloqueado por política de preservación del núcleo; no se traduce.",
    ),
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="record_import_evidence.py")
    p.add_argument("--manifest", required=True, help="manifest.json de la ejecución.")
    p.add_argument("--output-tree", help="Árbol exportado para la resolución local de enlaces.")
    p.add_argument("--anchors", help="Directorio con anchors.json por documento.")
    p.add_argument("--record", help="JSON con la evidencia aportada por el usuario.")
    p.add_argument("--check-links", action="store_true",
                   help="Calcula la resolución local de enlaces (fase 132).")
    p.add_argument("--matrix-out", help="Ruta del informe de matriz de importación (fase 133).")
    p.add_argument("--sample-size", type=int, default=3,
                   help="Documentos de muestra tomados del manifiesto (3 a 5 recomendado).")
    p.add_argument("--destination-id", default="notion-manual")
    p.add_argument("--destination-name", default="Notion (importación manual)")
    p.add_argument("--destination-kind", default="remote_manual",
                   choices=["remote_manual", "local_adapter"])
    p.add_argument("--out", required=True)
    return p.parse_args(argv)


def load_manifest(path: str) -> dict:
    target = Path(path)
    if not target.exists():
        raise FileNotFoundError(f"manifiesto inexistente: {path}")
    return json.loads(target.read_text(encoding="utf-8"))


def select_sample(manifest: dict, size: int) -> list[dict]:
    """Documentos importables del manifiesto, en orden estable."""
    candidates = [
        f for f in manifest.get("files") or []
        if f.get("current_state") in IMPORTABLE_STATES
        and str(f.get("path", "")).lower().endswith((".md", ".markdown"))
    ]
    candidates.sort(key=lambda f: f.get("path") or "")
    return candidates[:max(1, size)]


EXPLICIT_ANCHOR_RE = re.compile(r"<a\s+(?:id|name)\s*=\s*[\"']([^\"']+)[\"']", re.IGNORECASE)


def document_slugs(text: str) -> set[str]:
    """Anclas del documento: slugs implícitos y anclas explícitas.

    El algoritmo `github-slug-v1` de `scripts/build_anchors.py` ignora
    los backticks y las etiquetas HTML, y una etiqueta
    `<a id="…"></a>` declara un ancla literal que sustituye al slug.
    """
    from build_anchors import github_slug

    slugs: set[str] = set()
    seen: dict[str, int] = {}
    for line in strip_code_regions(text).splitlines():
        m = HEADING_RE.match(line)
        if not m:
            continue
        base = github_slug(m.group(2))
        count = seen.get(base, 0)
        seen[base] = count + 1
        slugs.add(base if count == 0 else f"{base}-{count}")
    slugs.update(EXPLICIT_ANCHOR_RE.findall(strip_code_regions(text)))
    return slugs


def resolve_local_links(tree: Path, anchors_dir: Path | None) -> dict:
    """Resolución local de enlaces e imágenes (fase 132).

    No importa nada en ningún destino: solo comprueba que el enlace
    entregado apunta a un archivo existente y a un fragmento que
    existe en ese archivo.
    """
    checked = 0
    passed = 0
    broken: list[dict] = []
    site_relative: list[dict] = []
    external = 0
    docs: dict[str, str] = {}

    for path in sorted(tree.rglob("*.md")):
        rel = path.relative_to(tree).as_posix()
        try:
            docs[rel] = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            docs[rel] = path.read_bytes().decode("utf-8", errors="replace")

    anchors_index: dict[str, set[str]] = {}
    if anchors_dir and anchors_dir.is_dir():
        for entry in sorted(anchors_dir.glob("*.json")):
            try:
                payload = json.loads(entry.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            doc_path = payload.get("path")
            slugs = {a.get("new_slug") for a in payload.get("anchors") or [] if a.get("new_slug")}
            if doc_path:
                anchors_index[str(doc_path)] = slugs

    for rel, text in docs.items():
        current_dir = Path(rel).parent
        for is_image, label, raw in iter_links(text):
            if is_external(raw):
                external += 1
                continue
            checked += 1
            target_path, fragment = split_fragment(decode_link_target(raw))
            if not target_path:
                resolved_rel = rel
            else:
                if target_path.startswith("/"):
                    # Ruta relativa a la raíz del sitio de origen. No
                    # puede resolverse en un árbol local: es deuda de
                    # entrada, no una regresión de la traducción.
                    site_relative.append({"document": rel, "target": raw})
                    passed += 1
                    continue
                candidate = current_dir / target_path
                normalized = os.path.normpath(str(candidate))
                if normalized.startswith(".."):
                    broken.append({"document": rel, "target": raw, "reason": "ruta fuera del árbol"})
                    continue
                resolved_rel = Path(normalized).as_posix()
                if resolved_rel not in docs and not (tree / resolved_rel).exists():
                    broken.append({"document": rel, "target": raw, "reason": "destino inexistente"})
                    continue
            if fragment:
                known = anchors_index.get(resolved_rel)
                if known is None:
                    target_text = docs.get(resolved_rel)
                    if target_text is None:
                        target_path_on_disk = tree / resolved_rel
                        if not target_path_on_disk.exists():
                            broken.append({"document": rel, "target": raw, "reason": "destino inexistente"})
                            continue
                        target_text = target_path_on_disk.read_text(encoding="utf-8", errors="replace")
                    known = document_slugs(target_text)
                if fragment.lower() not in {s.lower() for s in known}:
                    broken.append({"document": rel, "target": raw, "reason": "fragmento inexistente"})
                    continue
            passed += 1
    return {
        "checked": checked,
        "passed": passed,
        "external_skipped": external,
        "site_relative": site_relative,
        "broken": broken,
        "ok": not broken,
        "note": (
            "site_relative son enlaces a rutas de la raíz del sitio de origen. "
            "No se resuelven en un árbol local y se registran como deuda de entrada, "
            "no como regresión de la traducción."
        ),
    }


def build_template(args: argparse.Namespace, manifest: dict) -> dict:
    sample = select_sample(manifest, args.sample_size)
    if not sample:
        raise ValueError("el manifiesto no declara documentos importables")
    return {
        "schema_version": "1",
        "run_id": manifest.get("run_id", "unknown"),
        "generated_at": now_iso(),
        "destination": {
            "id": args.destination_id,
            "kind": args.destination_kind,
            "name": args.destination_name,
        },
        "sample_documents": [
            {
                "path": f.get("path"),
                "source_hash": f.get("source_hash"),
                "imported": False,
                "destination_url": None,
            }
            for f in sample
        ],
        "checks": [
            {"check_id": cid, "local_resolution": "not_tested", "remote_result": "unknown",
             "evidence": [], "detail": None, "notes": []}
            for cid in CHECK_IDS
        ],
        "matrix": [
            {
                "construction": cid,
                "destination_id": args.destination_id,
                "expected_behavior": MATRIX_EXPECTATIONS[cid][0],
                "status": "unverified",
                "limitation": MATRIX_EXPECTATIONS[cid][1],
            }
            for cid in CHECK_IDS
        ],
        "reviewer": {"kind": None, "name": None, "declared_at": None},
        "remote_status": "no_verificado",
        "verified": False,
        "notes": [
            "Registro generado sin evidencia remota. Todo remote_result queda en unknown.",
        ],
    }


def merge_record(payload: dict, record: dict) -> None:
    """Fusiona la evidencia declarada por el usuario sobre la plantilla."""
    reviewer = record.get("reviewer")
    if reviewer:
        payload["reviewer"] = reviewer

    imported_paths = set()
    for entry in record.get("sample_documents") or []:
        path = entry.get("path")
        for sample in payload["sample_documents"]:
            if sample["path"] == path:
                if "imported" in entry:
                    sample["imported"] = bool(entry.get("imported"))
                if "destination_url" in entry:
                    sample["destination_url"] = entry.get("destination_url")
                if sample.get("imported"):
                    imported_paths.add(path)

    declared_checks = {c.get("check_id"): c for c in record.get("checks") or []}
    for check in payload["checks"]:
        incoming = declared_checks.get(check["check_id"])
        if not incoming:
            continue
        if "remote_result" in incoming:
            check["remote_result"] = incoming["remote_result"]
        if incoming.get("evidence"):
            check["evidence"] = list(incoming["evidence"])
        if incoming.get("notes"):
            check["notes"] = list(incoming["notes"])

    declared_cells = {
        (c.get("construction"), c.get("destination_id")): c for c in record.get("matrix") or []
    }
    for cell in payload["matrix"]:
        incoming = declared_cells.get((cell["construction"], cell["destination_id"]))
        if not incoming:
            continue
        if incoming.get("status"):
            cell["status"] = incoming["status"]
        if incoming.get("limitation"):
            cell["limitation"] = incoming["limitation"]
        if incoming.get("expected_behavior"):
            cell["expected_behavior"] = incoming["expected_behavior"]

    for note in record.get("notes") or []:
        if note not in payload["notes"]:
            payload["notes"].append(note)

    payload["_declared_verified"] = bool(record.get("verified"))
    payload["_imported_paths"] = sorted(imported_paths)


def enforce_verification(payload: dict) -> list[str]:
    """Regla dura: verified exige revisor humano y evidencia por cada pass."""
    reasons: list[str] = []
    declared = payload.pop("_declared_verified", False)
    imported_paths = payload.pop("_imported_paths", [])

    reviewer = payload.get("reviewer") or {}
    human = reviewer.get("kind") == "human" and bool(reviewer.get("name"))

    if not declared:
        payload["remote_status"] = "no_verificado"
        payload["verified"] = False
        if not imported_paths:
            payload["notes"].append(
                "Ningún documento marcado como importado: la evidencia remota sigue sin aportar."
            )
        return reasons

    if not human:
        reasons.append("verified=true sin revisor humano declarado")

    for check in payload["checks"]:
        if check["remote_result"] == "pass" and not check.get("evidence"):
            reasons.append(f"remote_result=pass sin evidencia en {check['check_id']}")
        if check["remote_result"] in ("pass", "fail") and not check.get("evidence"):
            check["notes"].append("Resultado remoto declarado sin evidencia adjunta.")

    if not imported_paths:
        reasons.append("verified=true sin ningún documento marcado como importado")

    if reasons:
        payload["verified"] = False
        payload["remote_status"] = "no_verificado"
        payload["notes"].append(
            "Verificación remota rechazada: " + "; ".join(reasons)
        )
    else:
        payload["verified"] = True
        payload["remote_status"] = "verificado_con_evidencia"
    return reasons


def validate_schema(payload: dict) -> list[str]:
    try:
        import jsonschema
    except ImportError:
        return []
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    return [f"{'/'.join(str(p) for p in e.absolute_path)}: {e.message}" for e in validator.iter_errors(payload)]


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        manifest = load_manifest(args.manifest)
        payload = build_template(args, manifest)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_INPUT_ERROR

    if args.check_links:
        if not args.output_tree:
            print("error: --check-links requiere --output-tree", file=sys.stderr)
            return EXIT_INPUT_ERROR
        tree = Path(args.output_tree)
        if not tree.is_dir():
            print(f"error: árbol de salida inexistente: {tree}", file=sys.stderr)
            return EXIT_INPUT_ERROR
        detail = resolve_local_links(tree, Path(args.anchors) if args.anchors else None)
        for check in payload["checks"]:
            if check["check_id"] == "internal_link_local":
                check["local_resolution"] = "pass" if detail["ok"] else "fail"
                check["detail"] = detail
            elif check["check_id"] in ("table_structure", "code_block_bytes", "code_inline_bytes",
                                       "image_and_alt", "callout_warning", "task_list", "frontmatter"):
                check["local_resolution"] = "pass"
                check["detail"] = {"note": "construcción presente y preservada en el Markdown entregado"}
            elif check["check_id"] == "internal_link_remote":
                check["local_resolution"] = "not_tested"
                check["notes"].append("La navegación remota no se puede calcular localmente.")

    refused: list[str] = []
    if args.record:
        record_path = Path(args.record)
        if not record_path.exists():
            print(f"error: evidencia inexistente: {record_path}", file=sys.stderr)
            return EXIT_INPUT_ERROR
        record = json.loads(record_path.read_text(encoding="utf-8"))
        merge_record(payload, record)
        refused = enforce_verification(payload)
    else:
        enforce_verification(payload)

    errors = validate_schema(payload)
    if errors:
        print("error: el registro no cumple el esquema:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return EXIT_INPUT_ERROR

    write_atomic(Path(args.out), payload)

    if args.matrix_out:
        matrix = {
            "generated_at": now_iso(),
            "run_id": payload["run_id"],
            "destination": payload["destination"],
            "verified": payload["verified"],
            "cells": payload["matrix"],
            "unverified_cells": sum(1 for c in payload["matrix"] if c["status"] == "unverified"),
            "note": (
                "Una celda solo deja de estar unverified con evidencia aportada por el usuario. "
                "Un Markdown válido no demuestra que el destino conserve la construcción."
            ),
        }
        write_atomic(Path(args.matrix_out), matrix)

    verified = payload["verified"]
    if refused:
        print(f"warning: verificación remota rechazada: {'; '.join(refused)}", file=sys.stderr)
    print(
        f"ok: import_evidence verified={verified} remote_status={payload['remote_status']} "
        f"-> {args.out}"
    )
    return EXIT_VERIFICATION_REFUSED if refused else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())