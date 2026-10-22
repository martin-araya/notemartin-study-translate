"""Extracción de candidatos terminológicos del corpus.

Genera un borrador de ``glossary.json`` con entradas que cumplen
``schemas/glossary.schema.json`` (Draft 2020-12). Cada entrada incluye
al menos un ejemplo de contexto con ``document_id`` y ``segment_id``.

Categorías extraídas:

- Identificadores (CamelCase, snake_case, kebab-case) que se repiten ≥ 3
  veces en segmentos ``translatable``.
- Siglas en mayúsculas sostenidas de ≥ 2 letras.
- Palabras en backticks (código inline y fence) cuyo lenguaje es
  reconocible.
- Términos con co-ocurrencia de marcadores técnicos.

El borrador queda con ``frozen: false`` hasta la aprobación del piloto.
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

import jsonschema
from jsonschema import Draft202012Validator

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "glossary.schema.json"

CAMEL_RE = re.compile(r"\b[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]*)*\b")
SNAKE_RE = re.compile(r"\b[a-z]+(?:_[a-z]+)+\b")
KEBAB_RE = re.compile(r"\b[a-z]+(?:-[a-z]+)+\b")
ACRONYM_RE = re.compile(r"\b[A-Z]{2,}\b")
TECH_CONTEXT = re.compile(
    r"\b(function|method|class|interface|type|enum|module|package|"
    r"endpoint|router|controller|service|config|parameter|property|"
    r"attribute|namespace|component|element|state)\b",
    re.IGNORECASE,
)


def detect_domain(path: str) -> str:
    parts = path.split("/")
    if len(parts) >= 1 and parts[0]:
        return parts[0]
    return "global"


def normalize_term(term: str) -> str:
    return term.lower()


def extract_candidates(segments_payload: dict, snapshots_payload: dict) -> list[dict]:
    """Recorre segmentos y devuelve una lista de candidatos con contexto."""
    candidates: dict[tuple[str, str, str], dict] = {}

    for f in segments_payload.get("files", []):
        domain = detect_domain(f.get("path", ""))
        for seg in f.get("segments", []):
            disposition = seg.get("disposition")
            if disposition is not None and disposition not in {"translatable", "already_target"}:
                continue
            text = seg.get("translatable_text") or ""
            if not text:
                continue
            for match in re.finditer(r"`([^`]+)`", text):
                value = match.group(1).strip()
                if len(value) < 2 or len(value) > 50:
                    continue
                key = (normalize_term(value), "code_reference", domain)
                candidates[key] = _record(candidates.get(key), f, seg, value, "code_reference", domain)

            for match in re.finditer(r"\*\*([^*]+)\*\*", text):
                value = match.group(1).strip()
                if len(value) < 3:
                    continue
                if TECH_CONTEXT.search(text):
                    key = (normalize_term(value), "tech_term", domain)
                    candidates[key] = _record(candidates.get(key), f, seg, value, "tech_term", domain)

            for match in CAMEL_RE.finditer(text):
                value = match.group(0)
                if len(value) < 4:
                    continue
                key = (normalize_term(value), "identifier", domain)
                candidates[key] = _record(candidates.get(key), f, seg, value, "identifier", domain)

            for match in SNAKE_RE.finditer(text):
                value = match.group(0)
                if len(value) < 4:
                    continue
                key = (normalize_term(value), "identifier", domain)
                candidates[key] = _record(candidates.get(key), f, seg, value, "identifier", domain)

            for match in ACRONYM_RE.finditer(text):
                value = match.group(0)
                if len(value) < 2:
                    continue
                key = (normalize_term(value), "acronym", domain)
                candidates[key] = _record(candidates.get(key), f, seg, value, "acronym", domain)

    return list(candidates.values())


def _record(existing: dict | None, f: dict, seg: dict, value: str, sense: str, domain: str) -> dict:
    if existing is None:
        existing = {
            "source_term": value,
            "domain": domain,
            "sense": sense,
            "occurrences": 0,
            "examples": [],
        }
    existing["occurrences"] += 1
    if len(existing["examples"]) < 3:
        ctx = (seg.get("translatable_text") or "")[:200]
        existing["examples"].append({
            "document_id": f.get("document_id", ""),
            "segment_id": seg.get("segment_id", ""),
            "before": ctx[:60],
            "after": ctx[-60:],
            "note": f"{sense} en dominio {domain}",
        })
    return existing


def build_glossary(candidates: list[dict], max_entries: int) -> dict:
    candidates.sort(key=lambda c: (-c["occurrences"], c["source_term"]))
    selected = candidates[:max_entries]

    entries = []
    for c in selected:
        entry_id = "g-" + hashlib.sha256(
            f"{c['source_term']}|{c['domain']}|{c['sense']}".encode("utf-8")
        ).hexdigest()[:4]
        entries.append({
            "id": entry_id,
            "source_term": c["source_term"],
            "domain": c["domain"],
            "sense": _sense_description(c),
            "preferred": {"lang": "es", "term": _propose_translation(c)},
            "allowed_variants": [],
            "forbidden_forms": [],
            "preservation_policy": "translate",
            "context_examples": c["examples"],
            "justification": f"Término con {c['occurrences']} ocurrencias en el dominio {c['domain']}; se propone equivalente inicial pendiente de revisión humana.",
            "decided_by": "extract_terms.py",
            "decided_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        })

    return {
        "version": 1,
        "frozen": False,
        "allowed_languages": ["es"],
        "entries": entries,
    }


def _sense_description(c: dict) -> str:
    sense = c["sense"]
    domain = c["domain"]
    return f"{sense} observado en dominio {domain} ({c['occurrences']} ocurrencias)"


def _propose_translation(c: dict) -> str:
    sense = c["sense"]
    if sense == "acronym":
        return c["source_term"]
    if sense == "identifier":
        return c["source_term"]
    return c["source_term"]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="extract_terms.py")
    p.add_argument("--inventory", required=True)
    p.add_argument("--snapshots", required=True)
    p.add_argument("--segments", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--max-candidates", type=int, default=50)
    return p.parse_args(argv)


def write_atomic(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    segments = json.loads(Path(args.segments).read_text(encoding="utf-8"))
    snapshots = json.loads(Path(args.snapshots).read_text(encoding="utf-8"))
    Path(args.inventory).read_text(encoding="utf-8")

    candidates = extract_candidates(segments, snapshots)
    glossary = build_glossary(candidates, args.max_candidates)

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(glossary)

    write_atomic(Path(args.out), glossary)
    print(f"ok: {len(glossary['entries'])} entradas -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())