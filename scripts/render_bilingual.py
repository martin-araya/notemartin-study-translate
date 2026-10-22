"""Genera un informe bilingüe lado a lado (fase 121).

Produce ``reports/bilingual/<name>.md`` con una tabla Markdown
con columnas ``segment_id | heading_path | source_hash | candidate
| candidate_hash``. Cada fila conserva exactamente el texto traducido
de ``translations/<doc_id>.json``. El informe es de solo lectura:
no modifica traducciones ni glosarios.

Convenciones:

- Orden estable: por ``document_id`` (lexicográfico), luego por la
  posición de aparición del segmento en el archivo fuente
  (``byte_range.start``).
- Pipes ``|`` dentro de celdas se escapan como ``\\|`` para que la
  tabla Markdown siga siendo válida.
- Tabla de contenidos inicial con anclas Markdown calculadas sobre
  ``document_id-segment_id`` (slug simple, ASCII lowercase).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


SLUG_RE = re.compile(r"[^a-z0-9]+")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="render_bilingual.py")
    p.add_argument("--translations", required=True, help="Directorio translations/.")
    p.add_argument("--manifest", help="manifest.json opcional, para ordenar por source_hash y reportar.")
    p.add_argument("--out", required=True, help="Ruta del Markdown de salida.")
    return p.parse_args(argv)


def _slug(text: str) -> str:
    return SLUG_RE.sub("-", text.strip().lower()).strip("-") or "x"


def _cell(text: str) -> str:
    if not text:
        return "_(vacío)_"
    cleaned = text.replace("\r\n", "\n").replace("\n", "<br>")
    if not cleaned.strip():
        return "_(whitespace)_"
    return cleaned.replace("\\", "\\\\").replace("|", "\\|").replace("\t", " ")


def _anchor(document_id: str, segment_id: str) -> str:
    return f"{_slug(document_id)}-{_slug(segment_id)}"


def _heading_path_text(heading_path: list | None) -> str:
    if not heading_path:
        return "_(raíz)_"
    parts = []
    for h in heading_path:
        if not isinstance(h, dict):
            continue
        txt = (h.get("text") or "").strip()
        if txt:
            parts.append(txt)
    return " > ".join(parts) if parts else "_(raíz)_"


def _load_translations(translations_dir: Path) -> list[dict]:
    rows: list[dict] = []
    for doc_path in sorted(translations_dir.glob("*.json")):
        try:
            payload = json.loads(doc_path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"warn: omitiendo {doc_path.name}: json inválido ({exc})", file=sys.stderr)
            continue
        document_id = payload.get("document_id") or doc_path.stem
        path = payload.get("path") or doc_path.name
        file_source_hash = payload.get("source_hash") or ""
        for entry in payload.get("entries", []):
            original = entry.get("original_text") or entry.get("translatable_text") or ""
            translated = entry.get("translated_text") or ""
            if "flag_loss" in entry and entry["flag_loss"]:
                flag_loss = True
            else:
                flag_loss = bool(entry.get("missing_literals"))
            seg_source_hash = entry.get("source_hash") or _short_hash(original)
            cand_hash = entry.get("candidate_hash") or _short_hash(translated)
            rows.append(
                {
                    "document_id": document_id,
                    "path": path,
                    "file_source_hash": file_source_hash,
                    "segment_id": entry.get("segment_id") or "",
                    "structural_type": entry.get("structural_type") or "paragraph",
                    "heading_path": entry.get("heading_path") or [],
                    "byte_range": entry.get("byte_range") or {"start": 0, "end": 0},
                    "source_hash": seg_source_hash,
                    "original_text": original,
                    "translated_text": translated,
                    "candidate_hash": cand_hash,
                    "flag_loss": flag_loss,
                    "literals_preserved": entry.get("literals_preserved", True),
                }
            )
    rows.sort(
        key=lambda r: (
            r["document_id"],
            r["byte_range"].get("start", 0) if isinstance(r["byte_range"], dict) else 0,
            r["segment_id"],
        )
    )
    return rows


def _format_table(rows: list[dict]) -> str:
    lines = []
    lines.append("| # | segment_id | trayectoria | source_hash | candidato | candidate_hash |")
    lines.append("|---|---|---|---|---|---|")
    for idx, r in enumerate(rows, start=1):
        cand_h = _short_hash(r["translated_text"])
        # source_hash por-archivo y candidate_hash por-segmento van completos
        # para que el revisor pueda verificar sin un validador externo.
        src_h = r["source_hash"] or "_(sin hash)_"
        cand_text = _cell(r["translated_text"])
        if r.get("flag_loss"):
            cand_text = f"{cand_text} _(literales alterados)_"
        anchor = _anchor(r["document_id"], r["segment_id"])
        seg_id_cell = f"[{r['segment_id']}](#{anchor})"
        # Ancla HTML explícita para que el ancla sea resoluble en
        # renderizadores Markdown que ignoran identificadores
        # implícitos en celdas de tabla. AGENTS.md §6 aplica al
        # destino Notion, no a navegación local.
        lines.append(f'<a id="{anchor}"></a>')
        lines.append(
            f"| {idx} | {seg_id_cell} | {_cell(_heading_path_text(r['heading_path']))} | `{_cell(src_h)}` | {cand_text} | `{cand_h}` |"
        )
    return "\n".join(lines)


def _short_hash(text: str) -> str:
    import hashlib

    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return h


def _toc(rows: list[dict]) -> str:
    lines = ["## Tabla de contenidos", ""]
    by_doc: dict[str, list[dict]] = {}
    for r in rows:
        by_doc.setdefault(r["document_id"], []).append(r)
    for doc_id in sorted(by_doc):
        lines.append(f"### `{doc_id}` ({len(by_doc[doc_id])} segmentos)")
        for r in by_doc[doc_id]:
            anchor = _anchor(doc_id, r["segment_id"])
            preview = (r["translated_text"] or "").splitlines()[0][:60]
            if len(r["translated_text"]) > 60:
                preview += "…"
            lines.append(f"- [{r['segment_id']}](#{anchor}) — {preview}")
        lines.append("")
    return "\n".join(lines)


def _empty_doc_text(path: Path, doc_id: str) -> str:
    return f"_(El documento `{path.name}` ({doc_id}) no contiene segmentos traducibles.)_"


def render(rows: list[dict], manifest_path: Path | None) -> str:
    lines: list[str] = []
    lines.append("# Informe bilingüe")
    lines.append("")
    lines.append(
        "Informe local de revisión. No modifica traducciones. Cada fila enlaza al `segment_id`;"
        " los hashes `source_hash` y `candidate_hash` se calculan sobre los bytes del segmento."
    )
    if manifest_path is not None:
        lines.append(f"Manifiesto de referencia: `{manifest_path.name}`.")
    lines.append("")
    if not rows:
        lines.append("_(0 filas)_ El alcance no contiene segmentos traducibles.")
        return "\n".join(lines) + "\n"
    total = len(rows)
    flag = sum(1 for r in rows if r.get("flag_loss"))
    lines.append(f"Resumen: {total} segmentos · {flag} con literales alterados.")
    lines.append("")
    lines.append(_toc(rows))
    lines.append("")
    by_doc: dict[str, list[dict]] = {}
    for r in rows:
        by_doc.setdefault(r["document_id"], []).append(r)
    for doc_id in sorted(by_doc):
        doc_rows = by_doc[doc_id]
        lines.append(f"## `{doc_id}`")
        lines.append("")
        first_path = doc_rows[0]["path"]
        lines.append(f"Path: `{first_path}` · source_hash: `{doc_rows[0]['source_hash'] or '(vacío)'}`")
        lines.append("")
        lines.append(_format_table(doc_rows))
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    translations_dir = Path(args.translations)
    if not translations_dir.is_dir():
        print(f"error: {translations_dir} no es un directorio válido", file=sys.stderr)
        return 2
    rows = _load_translations(translations_dir)
    manifest_path = Path(args.manifest) if args.manifest else None
    body = render(rows, manifest_path)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(body, encoding="utf-8")
    print(f"ok: {len(rows)} filas -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
