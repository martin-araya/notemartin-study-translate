"""Agrupa inconsistencias terminológicas por sentido y dominio (fase 125).

Consume el directorio ``translations/`` y un ``glossary.json``
congelado para producir ``reports/inconsistencies.md``. Una sección
por dominio; dentro, una entrada por ``sense_id`` con la lista de
variantes observadas y los archivos que las usan.

El reporte **nunca** aplica una traducción retroactivamente.
Solo expone la divergencia y propone (no aplica) decisiones
pendientes.

Variables de agrupación:

- ``sense_id`` cuando el glosario lo declara.
- ``domain`` siempre que el glosario lo tenga.
- En su defecto, por término fuente (palabra completa).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

WORD_RE = re.compile(r"\b[\w][\w\-]*\b", re.UNICODE)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="group_inconsistencies.py")
    p.add_argument("--translations", required=True)
    p.add_argument("--glossary", required=True)
    p.add_argument("--out", required=True)
    return p.parse_args(argv)


def _glossary_index(glossary: dict) -> dict:
    index: dict = {}
    for entry in glossary.get("entries", []):
        src = (entry.get("source_term") or "").lower()
        if not src:
            continue
        index[src] = {
            "entry_id": entry.get("id"),
            "preferred": (entry.get("preferred") or {}).get("term"),
            "allowed_variants": list(entry.get("allowed_variants") or []),
            "forbidden_forms": list(entry.get("forbidden_forms") or []),
            "domain": entry.get("domain"),
            "sense": entry.get("sense"),
            "sense_id": entry.get("sense_id") or entry.get("sense") or src,
        }
    return index


def _collect(translations_dir: Path, glossary_index: dict) -> dict:
    grouped: dict = defaultdict(
        lambda: {"docs": defaultdict(list), "variants": defaultdict(set), "forbidden": set()}
    )
    for tp in sorted(translations_dir.glob("*.json")):
        try:
            payload = json.loads(tp.read_text(encoding="utf-8"))
        except Exception:
            continue
        doc = payload.get("document_id") or tp.stem
        for entry in payload.get("entries", []):
            original = entry.get("original_text") or ""
            translated = entry.get("translated_text") or ""
            for token in WORD_RE.findall(original):
                meta = glossary_index.get(token.lower())
                if not meta:
                    continue
                sense_id = meta["sense_id"]
                key = (meta.get("domain") or "unclassified", sense_id)
                grouped[key]["meta"] = meta
                grouped[key]["docs"][doc].append(
                    {
                        "segment_id": entry.get("segment_id"),
                        "original_text": original,
                        "translated_text": translated,
                    }
                )
                for variant in [meta["preferred"]] + meta["allowed_variants"]:
                    if not variant:
                        continue
                    if variant.lower() in translated.lower():
                        grouped[key]["variants"][variant.lower()].add((variant, doc))
                for f in meta["forbidden_forms"]:
                    if f and f.lower() in translated.lower():
                        grouped[key]["forbidden"].add((f, doc))
    return grouped


def _render(sense_id: str, domain: str, data: dict) -> str:
    lines: list[str] = []
    meta = data.get("meta") or {}
    lines.append(f"### {meta.get('preferred') or sense_id} (`{domain} / {sense_id}`)")
    lines.append("")
    lines.append(f"- Equivalente preferido: `{meta.get('preferred') or '(vacío)'}`")
    lines.append(f"- Variantes permitidas: {meta.get('allowed_variants') or '_(ninguna)_'}")
    lines.append(f"- Formas prohibidas: {meta.get('forbidden_forms') or '_(ninguna)_'}")
    lines.append("")
    docs_by_variant = data.get("variants") or {}
    docs_seen = sorted({d for variants in docs_by_variant.values() for _, d in variants})
    if docs_seen:
        lines.append(f"**Documentos con este sentido:** {', '.join(docs_seen)}")
        lines.append("")
    variants = data.get("variants") or {}
    if not variants:
        lines.append("_(sin variantes observadas todavía)_")
    else:
        lines.append("**Variantes observadas:**")
        for key, docs in sorted(variants.items()):
            sample = list(docs)[0][0] if docs else key
            lines.append(f"- `{sample}` en {len({d for _, d in docs})} documentos.")
    lines.append("")
    forbidden = data.get("forbidden") or set()
    if forbidden:
        lines.append("**Formas prohibidas detectadas:**")
        for sample, doc in sorted(forbidden):
            lines.append(f"- `{sample}` en `{doc}` _(requiere revisión)_")
        lines.append("")
    lines.append("**Propuesta de decisión (no aplicada automáticamente):**")
    lines.append("- _Verificar con el revisor del par; congelar en `glossary.json` antes de re-firmar._")
    lines.append("")
    return "\n".join(lines)


def render(grouped: dict) -> str:
    out: list[str] = ["# Inconsistencias terminológicas (fase 125)", ""]
    if not grouped:
        out.append("_(sin inconsistencias detectadas)_")
        return "\n".join(out) + "\n"
    by_domain: dict = defaultdict(list)
    for (domain, sense_id), data in grouped.items():
        by_domain[domain].append((sense_id, data))
    for domain in sorted(by_domain):
        out.append(f"## Dominio `{domain}`")
        out.append("")
        for sense_id, data in sorted(by_domain[domain], key=lambda kv: kv[0]):
            out.append(_render(sense_id, domain, data))
    out.append("---")
    out.append("")
    out.append("El reporte es de solo lectura. Cada variante propuesta debe aprobarse explícitamente en `glossary.json` antes de reasignar aprobaciones (fase 124).")
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    glossary = json.loads(Path(args.glossary).read_text(encoding="utf-8"))
    index = _glossary_index(glossary)
    grouped = _collect(Path(args.translations), index)
    body = render(grouped)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(body, encoding="utf-8")
    print(f"ok: {len(grouped)} grupos -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
