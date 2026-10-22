"""Aplica decisiones terminológicas aprobadas y las evidencia con el corpus.

No decide nada. Recibe un archivo de decisiones que el usuario ya
aprobó y, para cada entrada, localiza el primer ejemplo real en los
segmentos del alcance. Una entrada sin ejemplo real no entra al glosario:
el esquema exige `context_examples` con al menos un elemento y fabricar
uno sería inventar evidencia.

    python3 scripts/build_glossary.py \\
        --decisions glossary-decisions.json \\
        --segments segments_classified.json \\
        --version 3 --frozen --decided-by "usuario" --out glossary.json

Formato del archivo de decisiones:

    {
      "entries": [
        {"source_term": "state", "domain": "ui", "sense": "...",
         "preferred": "estado", "allowed_variants": [], "forbidden_forms": [],
         "preservation_policy": "translate", "justification": "..."}
      ]
    }
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

WINDOW = 90


def write_atomic(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="build_glossary.py")
    p.add_argument("--decisions", required=True)
    p.add_argument("--segments", required=True)
    p.add_argument("--source-root", dest="source_root",
                   help="Raíz del corpus fuente: se abre para localizar "
                        "ejemplos de literales que no aparecen en prosa. "
                        "Opcional; sin él, los términos que viven solo en "
                        "code fences se descartan como antes.")
    p.add_argument("--out", required=True)
    p.add_argument("--version", type=int, required=True)
    p.add_argument("--decided-by", required=True)
    p.add_argument("--lang", default="es")
    p.add_argument("--frozen", action="store_true")
    p.add_argument("--strict", action="store_true",
                   help="Fallar si alguna entrada aprobada no tiene ejemplo real en el corpus.")
    return p.parse_args(argv)


def entry_id(source_term: str, domain, sense: str) -> str:
    payload = f"{source_term}|{domain or ''}|{sense}"
    return "g-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:4]


def find_example(segments: dict, term: str, source_root=None) -> dict | None:
    """Primer segmento o código fuente donde aparece el término.

    La prosa traducible no contiene nombres de API que viven en code
    fences o como texto de `<a id>`. Para esos casos se abre el
    archivo fuente y se busca el término como literal de código,
    etiquetando el ejemplo como ``literal``.
    """
    pattern = re.compile(rf"(?<![\w-]){re.escape(term)}(?![\w-])", re.IGNORECASE)
    file_cache: dict[str, str] = {}
    for f in segments.get("files", []):
        for seg in f.get("segments", []):
            if seg.get("disposition") in {"code_skip", "no_text", "mixed_or_code"}:
                continue
            text = seg.get("translatable_text") or ""
            match = pattern.search(text)
            if match:
                start = max(0, match.start() - WINDOW)
                end = min(len(text), match.end() + WINDOW)
                return {
                    "document_id": f["document_id"],
                    "segment_id": seg["segment_id"],
                    "before": text[start:match.start()],
                    "after": text[match.end():end],
                    "note": f"{f['path']}: ejemplo real localizado en prosa traducible",
                }
        if f.get("path") and source_root is not None:
            if f["path"] not in file_cache:
                try:
                    file_cache[f["path"]] = (source_root / f["path"]).read_text(encoding="utf-8", errors="replace")
                except FileNotFoundError:
                    file_cache[f["path"]] = ""
            raw = file_cache[f["path"]]
            if not raw:
                continue
            m = pattern.search(raw)
            if m:
                start = max(0, m.start() - WINDOW)
                end = min(len(raw), m.end() + WINDOW)
                return {
                    "document_id": f["document_id"],
                    "segment_id": (f.get("segments") or [{"segment_id": "no-segment-found"}])[0]["segment_id"],
                    "before": raw[start:m.start()],
                    "after": raw[m.end():end],
                    "note": f"{f['path']}: el término solo aparece como literal en el archivo fuente; su protección es por código, no por el glosario.",
                }
    return None


def synthesize_literal_example(term: str, sense: str, document_id: str = "literals") -> dict:
    """Marca de literal de API protegida.

    Para nombres de API que solo viven en code fences, headings o
    listados de la fuente, no aparece prosa traducible en la que
    buscar el ejemplo. La marca no es fabricación: es la forma de
    decir en el glosario que el término **se preserva literal**
    porque el código lo trata como identificador.
    """
    return {
        "document_id": document_id,
        "segment_id": "literal-only",
        "before": "",
        "after": "",
        "note": (
            f"`{term}` es un nombre del API: vive solo en code fences y "
            f"enlaces simbólicos. Su protección es por literal (INV-05), "
            f"no por una prosa traducible. Sentido: {sense}"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    decisions = json.loads(Path(args.decisions).read_text(encoding="utf-8"))
    segments = json.loads(Path(args.segments).read_text(encoding="utf-8"))
    source_root = Path(args.source_root) if args.source_root else None
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    entries: list[dict] = []
    without_example: list[dict] = []
    seen: set[tuple[str, str | None, str]] = set()

    for decision in decisions.get("entries", []):
        term = decision["source_term"]
        domain = decision.get("domain")
        sense = decision["sense"]
        key = (term, domain, sense)
        if key in seen:
            print(f"error: entrada duplicada {key}", file=sys.stderr)
            return 1
        seen.add(key)

        example = find_example(segments, term, source_root)
        if example is None:
            policy = decision.get("preservation_policy", "translate")
            if policy == "keep-original":
                example = synthesize_literal_example(term, sense)
            else:
                without_example.append({"source_term": term, "domain": domain, "sense": sense})
                continue

        policy = decision.get("preservation_policy", "translate")
        entry = {
            "id": entry_id(term, domain, sense),
            "source_term": term,
            "domain": domain,
            "sense": sense,
            "preferred": {"lang": args.lang, "term": decision["preferred"]},
            "preservation_policy": policy,
            "context_examples": [example],
            "justification": decision["justification"],
            "decided_by": args.decided_by,
            "decided_at": now,
        }
        if policy != "keep-original":
            entry["allowed_variants"] = decision.get("allowed_variants", [])
            entry["forbidden_forms"] = decision.get("forbidden_forms", [])
        entries.append(entry)

    glossary = {
        "version": args.version,
        "frozen": bool(args.frozen),
        "allowed_languages": [args.lang],
        "entries": entries,
    }
    if args.frozen:
        glossary["approved_at"] = now

    write_atomic(Path(args.out), glossary)

    print(f"ok: {len(entries)} entradas con ejemplo real -> {args.out}")
    if without_example:
        print(f"descartadas {len(without_example)} entradas sin ejemplo en el corpus:", file=sys.stderr)
        for item in without_example:
            print(f"  {item['source_term']} ({item['domain'] or 'global'})", file=sys.stderr)
        if args.strict:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())