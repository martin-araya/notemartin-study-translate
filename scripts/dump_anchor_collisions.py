"""Vuelca las colisiones de anclas a Markdown legible para revisión humana.

`build_anchors.py` escribe `anchors.json/` como directorio de un archivo
por documento, y las colisiones globales en
`anchors.json/_collisions.json`. Ese archivo cuenta **colisiones entre
documentos**, y medido sobre el corpus beta eso da 3 110 anclas
«en colisión» — cifra que parece alarming y no lo es: `api-api` aparece
en 1 113 rutas distintas porque cada página de la referencia de Angular
tiene su propio encabezado `## API`. Un fragmento solo se resuelve
**dentro** del documento que lo contiene, así que reutilizar un slug
entre documentos distintos no rompe nada.

Lo que sí rompe la navegación es la repetición **dentro** del mismo
documento: dos encabezados que generan el mismo ancla hacen que el
enlace lleve al primero. Este script mide las dos cosas y las separa:

- `intra_document`: la colisión que importa.
- `cross_document`: el recuento histórico, que se conserva por
  trazabilidad pero se etiqueta como no bloqueante.

    python3 scripts/dump_anchor_collisions.py \\
        --anchors anchors.json --out reports/beta/anchor-collisions.md
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def load_collisions(source) -> tuple[dict[str, list[dict]], int]:
    """Colisiones por ancla de salida, y el número de documentos con mapa.

    `build_anchors.py` escribe `anchors.json/` como **directorio** de un
    archivo por documento, y las colisiones aparte en
    `anchors.json/_collisions.json`, con la forma

        {"kind": ..., "total": N,
         "collisions": [{"slug": ..., "documents": [{path, ...}, ...]}]}

    Se aceptan las tres entradas posibles —el directorio, ese archivo, o
    un `anchors.json` monolítico— para que el informe se pueda regenerar
    sin recordar dónde está cada cosa.
    """
    path = Path(source)
    documents = 0

    if path.is_dir():
        collisions_path = path / "_collisions.json"
        documents = sum(
            1 for p in path.glob("*.json") if p.name != "_collisions.json"
        )
        if not collisions_path.exists():
            return {}, documents
        doc = json.loads(collisions_path.read_text(encoding="utf-8"))
    else:
        doc = json.loads(path.read_text(encoding="utf-8"))
        raw_docs = doc.get("documents") or doc.get("files") or {}
        documents = len(raw_docs) if isinstance(raw_docs, (dict, list)) else 0

    if isinstance(doc, dict) and isinstance(doc.get("collisions"), list):
        raw = doc["collisions"]
    else:
        raw = doc.get("_collisions") or doc.get("collisions") or []
        if isinstance(raw, dict):
            return {k: (v if isinstance(v, list) else [v]) for k, v in raw.items()}, documents

    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in raw:
        if not isinstance(item, dict):
            continue
        slug = item.get("slug") or item.get("anchor") or item.get("new_anchor")
        if not slug:
            continue
        entries = item.get("documents")
        if isinstance(entries, list) and entries:
            for e in entries:
                if isinstance(e, dict):
                    grouped[slug].append({
                        "path": e.get("path") or e.get("source_path"),
                        "heading": e.get("heading") or e.get("source_heading") or e.get("title") or "",
                    })
                else:
                    grouped[slug].append({"path": e, "heading": ""})
        else:
            grouped[slug].append({"path": slug, "heading": ""})
    return dict(grouped), documents


def source_rows(entry) -> tuple[str, str]:
    """(ruta, título) de una entrada de colisión, tolerante al formato."""
    if isinstance(entry, dict):
        return (
            str(entry.get("path") or entry.get("source_path") or "?"),
            str(entry.get("heading") or entry.get("source_heading") or entry.get("title") or ""),
        )
    return (str(entry), "")


def intra_document_collisions(anchors_dir: Path) -> list[dict]:
    """Encabezados del mismo documento que comparten ancla de salida.

    Esta es la colisión que rompe la navegación: el fragmento lleva al
    primer encabezado con ese slug y el segundo deja de ser alcanzable.
    """
    findings: list[dict] = []
    if not anchors_dir.is_dir():
        return findings
    for p in sorted(anchors_dir.glob("*.json")):
        if p.name == "_collisions.json":
            continue
        try:
            doc = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        seen: dict[str, list[str]] = defaultdict(list)
        for a in doc.get("anchors", []):
            slug = a.get("new_slug") or a.get("old_slug")
            if slug:
                seen[slug].append(str(a.get("new_text") or a.get("old_text") or ""))
        for slug, titles in seen.items():
            if len(titles) > 1:
                findings.append({
                    "path": doc.get("path", p.stem),
                    "document_id": doc.get("document_id"),
                    "slug": slug,
                    "occurrences": len(titles),
                    "titles": titles,
                })
    findings.sort(key=lambda f: (-f["occurrences"], f["path"]))
    return findings


def render_cross(groups: dict[str, list[dict]], total_documents: int) -> list[str]:
    multi = {a: rows for a, rows in groups.items()
             if len({source_rows(r)[0] for r in rows}) > 1}
    paths = {source_rows(r)[0] for rows in multi.values() for r in rows}
    return [
        "## Colisiones entre documentos (no bloqueantes)",
        "",
        "Un fragmento solo se resuelve dentro del documento que lo contiene. "
        "Reutilizar un slug entre rutas distintas no rompe la navegación, así "
        "que este recuento **no bloquea** la reescritura. Se conserva por "
        "trazabilidad.",
        "",
        "| Métrica | Valor |",
        "|---|---|",
        f"| Documentos con mapa de anclas | {total_documents} |",
        f"| Anclas compartidas entre documentos | {len(multi)} |",
        f"| Rutas implicadas | {len(paths)} |",
        "",
    ]


def render(groups: dict[str, list[dict]], total_documents: int,
           intra: list[dict] | None = None) -> str:
    intra = intra or []
    documents = {f["path"] for f in intra}
    paths = {source_rows(r)[0] for rows in groups.values() for r in rows}
    lines = [
        "# Colisiones de anclas",
        "",
        "## Colisiones dentro de un documento (bloqueantes)",
        "",
        "Dos encabezados del mismo documento que generan la misma ancla: el "
        "fragmento lleva al primero y el segundo deja de ser alcanzable. Es "
        "lo que hay que decidir antes de reescribir (INV-09).",
        "",
        "| Métrica | Valor |",
        "|---|---|",
        f"| Documentos con encabezado repetido | {len(documents)} |",
        f"| Anclas repetidas dentro de un documento | {len(intra)} |",
        "",
    ]

    if not intra:
        lines += ["Ninguna. No hay colisiones intra-documento en este corpus.", ""]
    else:
        lines += ["| Documento | Ancla | Veces | Títulos |", "|---|---|---|---|"]
        for f in intra[:400]:
            titles = "<br>".join(t[:60] for t in f["titles"][:5])
            lines.append(
                f"| `{f['path']}` | `{f['slug']}` | {f['occurrences']} | {titles} |"
            )
        if len(intra) > 400:
            lines.append(f"| … | | | {len(intra) - 400} más |")

    lines += [""] + render_cross(groups, total_documents)
    lines += [
        "## Lo que este informe no afirma",
        "",
        "- **No** reescribe nada.",
        "- **No** decide qué encabezado gana una colisión intra-documento: "
        "requiere ver el documento y decidir con el usuario.",
        "- **No** demuestra que la resolución en Markdown se conserve al "
        "importar en Notion (INV-15).",
    ]
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="dump_anchor_collisions.py")
    p.add_argument("--anchors", required=True)
    p.add_argument("--out", required=True)
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    groups, documents = load_collisions(args.anchors)
    source = Path(args.anchors)
    anchors_dir = source if source.is_dir() else source.parent
    intra = intra_document_collisions(anchors_dir)
    md = render(groups, documents, intra)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    cross = {a: r for a, r in groups.items() if len({source_rows(x)[0] for x in r}) > 1}
    print(f"ok: {len(intra)} colisiones intra-documento, "
          f"{len(cross)} entre documentos -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())