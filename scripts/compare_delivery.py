"""Reporte de degradaciones entre entrega adaptada y canónica (fase 138).

Compara el árbol adaptado con el árbol canónico y clasifica cada
diferencia:

- ``format_only``: cambia la forma, no el contenido. Un recurso que
  cambia de ruta pero conserva sus bytes, o un destino de enlace
  normalizado.
- ``degraded_documented``: se pierde algo acotado y la pérdida está
  declarada en el perfil de entrega.
- ``content_loss``: se pierde contenido sin declaración. **Bloquea**.

Compara, por documento: conjunto y secuencia de encabezados con su
nivel, literales de código (inline y bloques), filas y columnas de
tablas, elementos de lista, conjuntos de destinos de enlace, recursos y
prosa normalizada sin las partes que la adaptación declara cambiar.

Uso::

    python scripts/compare_delivery.py \\
        --canonical output_root/run-001 \\
        --adapted work_root/run-001/delivery/plain-markdown-local \\
        --out reports/delivery_degradations.json
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from delivery_common import (  # noqa: E402
    HEADING_RE,
    now_iso,
    sha256_bytes,
    strip_code_regions,
    tree_hashes,
    write_atomic,
)

EXIT_OK = 0
EXIT_INPUT_ERROR = 2
EXIT_CONTENT_LOSS = 3

TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")
LIST_ITEM_RE = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+")
INLINE_CODE_RE = re.compile(r"`([^`\n]+)`")
FENCE_BLOCK_RE = re.compile(r"^\s*(```|~~~)", re.MULTILINE)
LINK_TARGET_RE = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)\)")
LINK_SPAN_RE = re.compile(r"(!?\[[^\]]*\])\([^)]*\)")
RESOURCE_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".pdf", ".zip")
NON_ALNUM_RE = re.compile(r"[^a-z0-9]")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="compare_delivery.py")
    p.add_argument("--canonical", required=True)
    p.add_argument("--adapted", required=True)
    p.add_argument("--out", required=True)
    return p.parse_args(argv)


def is_markdown(rel: str) -> bool:
    return rel.lower().endswith((".md", ".markdown"))


def is_resource(rel: str) -> bool:
    return rel.lower().endswith(RESOURCE_SUFFIXES)


def fenced_blocks(text: str) -> list[str]:
    """Contenido de los bloques de código, delimitadores incluidos."""
    blocks: list[str] = []
    current: list[str] | None = None
    token = ""
    for line in text.splitlines():
        m = FENCE_BLOCK_RE.match(line)
        if m:
            if current is None:
                current, token = [], m.group(1)
            elif m.group(1) == token:
                blocks.append("\n".join(current))
                current = None
            continue
        if current is not None:
            current.append(line)
    if current is not None:
        blocks.append("\n".join(current))
    return blocks


def normalized_target(target: str) -> str:
    """Clave de comparación de un destino de enlace.

    Decodifica, quita el fragmento y reduce a minúsculas alfanuméricas.
    Sirve para decir «es el mismo destino escrito de otra forma», no
    para demostrar que el enlace resuelva.
    """
    from delivery_common import decode_link_target

    path = decode_link_target(target).split("#")[0]
    return NON_ALNUM_RE.sub("", path.replace("\\", "/").lower())


def profile_doc(text: str) -> dict:
    """Rasgos estructurales de un documento."""
    body = strip_code_regions(text)
    headings = [
        (len(m.group(1)), m.group(2).strip())
        for line in body.splitlines()
        for m in [HEADING_RE.match(line)]
        if m
    ]
    tables = [
        line for line in body.splitlines()
        if TABLE_ROW_RE.match(line) and not set(line.strip()) <= set("|-: ")
    ]
    list_items = [LIST_ITEM_RE.match(line).group(2) for line in body.splitlines() if LIST_ITEM_RE.match(line)]
    prose = [
        LINK_SPAN_RE.sub(r"\1(<destino>)", line).strip()
        for line in body.splitlines()
        if line.strip()
    ]
    return {
        "headings": headings,
        "code_blocks": fenced_blocks(text),
        "inline_codes": INLINE_CODE_RE.findall(body),
        "table_rows": len(tables),
        "table_columns": [line.count("|") - 1 for line in tables],
        "list_items": len(list_items),
        "prose_lines": len(prose),
        "prose": prose,
        "link_targets": sorted(LINK_TARGET_RE.findall(body)),
    }


def compare_documents(canonical_text: str, adapted_text: str, rel: str) -> list[dict]:
    left = profile_doc(canonical_text)
    right = profile_doc(adapted_text)
    differences: list[dict] = []

    if left["headings"] != right["headings"]:
        differences.append({
            "document": rel,
            "aspect": "headings",
            "classification": "content_loss",
            "canonical": [list(h) for h in left["headings"]],
            "adapted": [list(h) for h in right["headings"]],
        })
    if left["code_blocks"] != right["code_blocks"]:
        differences.append({
            "document": rel,
            "aspect": "code_blocks",
            "classification": "content_loss",
            "canonical": left["code_blocks"],
            "adapted": right["code_blocks"],
        })
    if left["inline_codes"] != right["inline_codes"]:
        differences.append({
            "document": rel,
            "aspect": "inline_code",
            "classification": "content_loss",
            "canonical": left["inline_codes"],
            "adapted": right["inline_codes"],
        })
    if (left["table_rows"], left["table_columns"]) != (right["table_rows"], right["table_columns"]):
        differences.append({
            "document": rel,
            "aspect": "tables",
            "classification": "content_loss",
            "canonical": [left["table_rows"], left["table_columns"]],
            "adapted": [right["table_rows"], right["table_columns"]],
        })
    if left["list_items"] != right["list_items"]:
        differences.append({
            "document": rel,
            "aspect": "list_items",
            "classification": "content_loss",
            "canonical": left["list_items"],
            "adapted": right["list_items"],
        })
    if left["prose_lines"] != right["prose_lines"]:
        differences.append({
            "document": rel,
            "aspect": "prose_volume",
            "classification": "content_loss",
            "canonical": left["prose_lines"],
            "adapted": right["prose_lines"],
        })

    if left["prose"] != right["prose"]:
        diff = list(difflib.unified_diff(left["prose"], right["prose"], lineterm="", n=0))
        differences.append({
            "document": rel,
            "aspect": "prose_text",
            "classification": "content_loss",
            "detail": diff[:20],
        })

    dropped_targets = sorted(set(left["link_targets"]) - set(right["link_targets"]))
    added_targets = sorted(set(right["link_targets"]) - set(left["link_targets"]))
    if dropped_targets or added_targets:
        added_keys = [normalized_target(t) for t in added_targets]
        same_destination = (
            len(dropped_targets) == len(added_targets)
            and sorted(normalized_target(t) for t in dropped_targets) == sorted(added_keys)
        )
        differences.append({
            "document": rel,
            "aspect": "link_targets",
            "classification": "format_only" if same_destination else "degraded_documented",
            "dropped": dropped_targets,
            "added": added_targets,
        })

    return differences


def compare_text_similarity(canonical_text: str, adapted_text: str) -> float:
    left = [line for line in canonical_text.splitlines() if line.strip()]
    right = [line for line in adapted_text.splitlines() if line.strip()]
    return difflib.SequenceMatcher(None, left, right).ratio()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    canonical = Path(args.canonical)
    adapted = Path(args.adapted)
    if not canonical.is_dir() or not adapted.is_dir():
        print(f"error: árboles inexistentes: {canonical} / {adapted}", file=sys.stderr)
        return EXIT_INPUT_ERROR

    canonical_hashes = tree_hashes(canonical)
    adapted_hashes = tree_hashes(adapted)

    differences: list[dict] = []

    canonical_docs = {p.relative_to(canonical).as_posix() for p in canonical.rglob("*") if p.is_file() and is_markdown(p.name)}
    adapted_docs = {p.relative_to(adapted).as_posix() for p in adapted.rglob("*") if p.is_file() and is_markdown(p.name)}

    for missing in sorted(canonical_docs - adapted_docs):
        differences.append({
            "document": missing, "aspect": "document_missing",
            "classification": "content_loss",
        })
    for added in sorted(adapted_docs - canonical_docs):
        differences.append({
            "document": added, "aspect": "document_added",
            "classification": "degraded_documented",
        })

    for rel in sorted(canonical_docs & adapted_docs):
        left = (canonical / rel).read_text(encoding="utf-8")
        right = (adapted / rel).read_text(encoding="utf-8")
        differences.extend(compare_documents(left, right, rel))

    canonical_resources = {
        rel: h for rel, h in canonical_hashes.items() if not is_markdown(rel)
    }
    adapted_resources = {
        rel: h for rel, h in adapted_hashes.items() if not is_markdown(rel)
    }
    for rel in sorted(set(canonical_resources) - set(adapted_resources)):
        digest = canonical_resources[rel]
        candidates = [
            other for other, h in adapted_resources.items()
            if h == digest and canonical_resources.get(other) != digest
        ]
        if candidates:
            differences.append({
                "document": rel, "aspect": "resource_renamed",
                "classification": "format_only", "new_path": sorted(candidates)[0],
                "sha256": digest,
            })
        else:
            differences.append({
                "document": rel, "aspect": "resource_missing",
                "classification": "content_loss",
                "sha256": digest,
            })
    for rel in sorted(set(adapted_resources) - set(canonical_resources)):
        differences.append({
            "document": rel, "aspect": "resource_added",
            "classification": "degraded_documented",
        })

    changed_docs = [
        rel for rel in sorted(canonical_docs & adapted_docs)
        if canonical_hashes.get(rel) != adapted_hashes.get(rel)
    ]
    for rel in changed_docs:
        similarity = compare_text_similarity(
            (canonical / rel).read_text(encoding="utf-8"),
            (adapted / rel).read_text(encoding="utf-8"),
        )
        differences.append({
            "document": rel,
            "aspect": "document_bytes_changed",
            "classification": "format_only",
            "text_similarity": round(similarity, 4),
            "canonical_sha256": canonical_hashes.get(rel),
            "adapted_sha256": adapted_hashes.get(rel),
        })

    counts = {
        "format_only": sum(1 for d in differences if d["classification"] == "format_only"),
        "degraded_documented": sum(1 for d in differences if d["classification"] == "degraded_documented"),
        "content_loss": sum(1 for d in differences if d["classification"] == "content_loss"),
    }

    report = {
        "generated_at": now_iso(),
        "canonical": str(canonical),
        "adapted": str(adapted),
        "canonical_tree_sha256": sha256_bytes(
            json.dumps(canonical_hashes, sort_keys=True).encode("utf-8")
        ),
        "adapted_tree_sha256": sha256_bytes(
            json.dumps(adapted_hashes, sort_keys=True).encode("utf-8")
        ),
        "documents_compared": len(canonical_docs & adapted_docs),
        "differences": differences,
        "counts": counts,
        "ok": counts["content_loss"] == 0,
        "note": (
            "La similitud de texto ordena prioridades; no demuestra equivalencia "
            "semántica. Solo la ausencia de content_loss permite aprobar el paquete adaptado."
        ),
    }
    write_atomic(Path(args.out), report)

    print(
        f"ok: documentos={report['documents_compared']} "
        f"format_only={counts['format_only']} "
        f"degraded_documented={counts['degraded_documented']} "
        f"content_loss={counts['content_loss']} -> {args.out}"
    )
    return EXIT_OK if report["ok"] else EXIT_CONTENT_LOSS


if __name__ == "__main__":
    sys.exit(main())