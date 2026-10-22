"""Detector de idioma residual en candidatos traducidos (fase 126).

El detector es **solo una alerta** sobre ``translations/``:

- Identifica palabras y secuencias en inglés (idioma origen) que
  aparecen en candidatos al español.
- Excluye el contenido dentro de code fences / code inline.
- Excluye los términos del glosario cuya ``preservation_policy`` sea
  ``keep-original``, que es el valor del enum de
  ``schemas/glossary.schema.json``.
- Asigna ``info`` para 1-3 palabras consecutivas y ``warning`` para
  4 o más.
- Nunca modifica ``translations/``. La señal se vuelca en
  ``reports/residual_language.md`` y en el payload JSON indicado
  por ``--out``.

Las heurísticas viven en ``scripts/text_signals.py`` (núcleo) porque
``verify_already_target.py`` necesita las mismas señales y pertenece al flujo
básico: un detector opcional no puede ser dependencia del núcleo.

Sólo se ejecuta con el módulo de revisión ampliado activo
(``gate_review.py --mode expanded``) o cuando el usuario lo invoca.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from text_signals import (
    DECLARED_ENGLISH_WORDS,
    ENGLISH_FUNCTIONAL_WORDS,
    ENGLISH_MORPHOLOGY,
    SPANISH_STOPWORDS,
    english_runs,
    looks_english,
    protect_literal_spans,
    severity_for,
)

# Valor del enum `preservation_policy` de `schemas/glossary.schema.json`.
# La versión anterior leía "preserve", que ese enum no contiene: la
# exención nunca se activaba sobre un glosario válido.
PRESERVE_POLICY = "keep-original"

EN_TOKEN_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9_\-]*\b")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="detect_residual_language.py")
    p.add_argument("--translations", required=True)
    p.add_argument("--glossary", required=True)
    p.add_argument("--out", required=True, help="Ruta del JSON de salida.")
    p.add_argument("--report", help="Markdown descriptivo opcional.")
    return p.parse_args(argv)


# Alias conservados para el contrato de la fase 126 y sus pruebas.
_protect_literal_spans = protect_literal_spans
_english_runs = english_runs
_looks_english = looks_english
_severity_for = severity_for


def _in_protected(idx: int, spans: list[tuple[int, int]]) -> bool:
    for start, end in spans:
        if start <= idx < end:
            return True
        if idx < start:
            break
    return False


def _load_preserve_terms(glossary_path: Path) -> set[str]:
    """Términos que el glosario manda conservar en el idioma de origen."""
    payload = json.loads(glossary_path.read_text(encoding="utf-8"))
    preserve: set[str] = set()
    for entry in payload.get("entries", []):
        if entry.get("preservation_policy") != PRESERVE_POLICY:
            continue
        source_term = entry.get("source_term")
        if source_term:
            preserve.add(source_term.lower())
        preferred = (entry.get("preferred") or {}).get("term")
        if preferred:
            preserve.add(preferred.lower())
    return preserve


def _snippet(text: str, start: int, end: int, max_len: int = 80) -> str:
    snippet = text[start:end].strip()
    if len(snippet) > max_len:
        snippet = snippet[: max_len - 1] + "…"
    return snippet


def _now() -> str:
    import datetime as _dt

    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def scan_translations(translations_dir: Path, glossary_path: Path) -> dict:
    preserve = _load_preserve_terms(glossary_path)
    signals: list[dict] = []
    warnings = 0
    info = 0
    for tp in sorted(translations_dir.glob("*.json")):
        try:
            payload = json.loads(tp.read_text(encoding="utf-8"))
        except Exception:
            continue
        doc_id = payload.get("document_id") or tp.stem
        for entry in payload.get("entries", []):
            seg_id = entry.get("segment_id")
            text = entry.get("translated_text") or ""
            for start, end, words in english_runs(text, preserve):
                if not looks_english(words):
                    continue
                severity = severity_for(words)
                if severity == "warning":
                    warnings += 1
                else:
                    info += 1
                signals.append(
                    {
                        "segment_id": seg_id,
                        "document_id": doc_id,
                        "severity": severity,
                        "snippet": _snippet(text, start, end),
                        "tokens": words,
                        "byte_range": {"start": start, "end": end},
                    }
                )
    return {
        "generated_at": _now(),
        "preserve_policy": PRESERVE_POLICY,
        "warnings": warnings,
        "info": info,
        "signals": signals,
        "protected_terms_count": len(preserve),
        "evidence_kinds": {
            "functional_word": len(ENGLISH_FUNCTIONAL_WORDS),
            "morphology_suffixes": len(ENGLISH_MORPHOLOGY),
            "declared_terms": len(DECLARED_ENGLISH_WORDS),
        },
    }


def _render_markdown(payload: dict) -> str:
    lines = ["# Detector de idioma residual (fase 126)", ""]
    lines.append(
        f"Resumen: `warning`={payload['warnings']} · `info`={payload['info']} · "
        f"términos protegidos={payload['protected_terms_count']} "
        f"(política `{payload['preserve_policy']}`)"
    )
    lines.append("")
    if not payload["signals"]:
        lines.append("_(sin señales)_")
        return "\n".join(lines) + "\n"
    lines.append("| # | severidad | document_id | segment_id | snippet |")
    lines.append("|---|---|---|---|---|")
    for idx, s in enumerate(payload["signals"], start=1):
        snippet = s["snippet"].replace("|", "\\|")
        lines.append(
            f"| {idx} | {s['severity']} | `{s['document_id']}` | `{s['segment_id']}` | {snippet} |"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = scan_translations(Path(args.translations), Path(args.glossary))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    if args.report:
        Path(args.report).write_text(_render_markdown(payload), encoding="utf-8")
    print(f"ok: warnings={payload['warnings']} info={payload['info']} -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())