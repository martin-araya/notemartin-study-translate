"""Verifica los segmentos con disposición `already_target` (paso 3 del cierre).

Un segmento `already_target` está en el idioma de destino: no se
reescribe. Lo que se **comprueba** es que de verdad lo esté. Declarar
`already_target` sin verificar es reducir el denominador para mejorar una
métrica, que es justo lo que INV-04 prohíbe y lo que §9 de `AGENTS.md`
prohíbe explícitamente.

La medición sobre el corpus beta encontró que la clasificación no es
homogénea:

- `oracle/resúmenes/`: prosa española redactada. Correcto.
- `angular/api/`: etiquetas de la referencia generada por Angular
  (`Type Alias`, `function`, `stable`, `[destroy](#destroy)`). Son
  inglés y quedan fuera de la traducción.

Este script **no reescribe nada**. Clasifica cada segmento y deja el
resultado en un informe, para que la decisión de qué hacer con ellos
sea del usuario y quede registrada.

    python3 scripts/verify_already_target.py \\
        --segments segments_v2.json --out reports/already_target.json \\
        --report reports/already_target.md

Requiereglossary opcional para respetar los términos con
`preserve: true` del glosario congelado.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# Las heurísticas de idioma viven en el núcleo (`text_signals`) porque este
# script pertenece al flujo básico y no puede depender de la fase 126.
from text_signals import (  # noqa: E402
    SPANISH_STOPWORDS,
    english_runs as _english_runs,
    looks_english as _looks_english,
    severity_for as _severity_for,
)

ACCENTS = set("áéíóúüñÁÉÍÓÚÜÑ")
TOKEN_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ][\w./'-]*")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?;:])\s+|\n+")
MIN_SPANISH_SHARE_IN_SENTENCE = 0.15

# Una etiqueta muy corta ("function", "stable") no es prosa: es una
# etiqueta de interfaz. Tampoco es traducible sin decisión editorial.
LABEL_RE = re.compile(r"^\s*(?:[*_`\[]+[A-Za-z][^*_`\[\]]{0,48}[*_`\]]+|[a-z]+:)\s*$")
MARKDOWN_LINK_ONLY_RE = re.compile(r"^\s*\[[^\]]*\]\([^)]*\)\s*$")

# Etiquetas de la referencia generada por Angular. Solo se listan
# palabras que no existen también en español: «alias», «type», «class»,
# «input», «output», «value» y «code» tienen peso ambiguo (el español
# dice «alias», y «code» es préstamo de «código»), y listarlos acusaba
# «Tipo alias» de estar en inglés.
ENGLISH_LABEL_HINTS = {
    "function", "stable", "experimental", "deprecated",
    "read-only", "readonly", "protected",
}

# Parejas de palabras que solo aparecen juntas en la etiqueta inglesa.
# «alias» y «type» son ambiguos por separado; «type alias» no.
ENGLISH_LABEL_PHRASES = {
    "type alias", "type annotation", "enum member", "class member",
}

# Citas textuales: comillas rectas, tipográficas y bloques en cursiva.
QUOTED_RE = re.compile(r"\"[^\"]{12,}\"|“[^”]{12,}”|\*[^*\n]{20,}\*")


def segment_kind(text: str) -> str:
    """Clase de forma del segmento, no de idioma."""
    stripped = (text or "").strip()
    if not stripped:
        return "empty"
    if MARKDOWN_LINK_ONLY_RE.match(stripped):
        return "link_only"
    if LABEL_RE.match(stripped):
        return "label"
    return "prose"


def strip_quoted_spans(text: str) -> str:
    """Retira las citas textuales, que se traducen solo si la política lo dice.

    `AGENTS.md` §5.2 deja la prosa entrecomillada bajo la categoría de
    cita, y el capítulo 05 del corpus Oracle incluye párrafos citados
    literalmente del PDF en inglés: *"The following sections include new
    AI Vector Search features…"*. Contar eso como prosa sin traducir
    señalaría un hueco que la política no considera.
    """
    out = QUOTED_RE.sub(" ", text or "")
    out = re.sub(r"\*[^*]*\b(?:the|and|with|are|for|that|this|from|which)\b[^*]*\*",
                 " ", out, flags=re.IGNORECASE)
    return out


def looks_like_proper_noun_run(tokens: list[str]) -> bool:
    """¿El run es un nombre propio o un término de producto?

    «Oracle AI Vector Search», «Hybrid Vector Indexes» y «Release
    Update» son nombres que el glosario puede mandar conservar. No son
    prosa sin traducir, y acusarlos produciría cientos de hallazgos
    sobre un documento que ya está en español.
    """
    if not tokens:
        return False
    if any(t[:1].islower() for t in tokens):
        return False
    # Un nombre propio no empieza por un funcional inglés.
    return not any(t.lower() in ENGLISH_LABEL_HINTS for t in tokens)


def english_evidence(text: str, preserve: set[str]) -> list[dict]:
    """Runs de inglés con evidencia positiva, no tokens sueltos.

    La primera versión de esta función acusaba token a token y produjo
    884 falsos positivos sobre 1 297 segmentos: cualquier palabra con
    guion («sub-sección») o con mayúscula interna («TypeScript») salía
    como inglesa. Es el error que `text_signals.looks_english` documenta en
    su docstring: sin filtrar palabras funcionales españolas, el detector
    informa de prosa española corriente.

    Se reutiliza `_english_runs`, que segmenta en runs contiguas
    descartando stopwords españolas y términos con `preserve: true`. A
    eso se añaden tres filtros medidos sobre este corpus:

    - las citas textuales se retiran antes de medir;
    - un run que es todo nombre propio es un término, no prosa;
    - **la frase que contiene el run debe carecer de evidencia
      española**. Esta última es la que separa los casos reales: el
      capítulo 05 de Oracle está redactado en español e incrusta
      «release update», «online rebuild» y «scalar quantization», que
      son nombres de producto y no huecos de traducción. Una frase
      inglesa sin traducir no tiene por qué contener ninguna palabra
      funcional española; una frase española con un término inglés, sí.
    """
    scannable = strip_quoted_spans(text)
    sentences = [s for s in SENTENCE_SPLIT_RE.split(scannable) if s.strip()]
    starts: list[int] = []
    cursor = 0
    for s in sentences:
        idx = scannable.find(s, cursor)
        if idx < 0:
            idx = cursor
        starts.append(idx)
        cursor = idx + len(s)

    def sentence_at(pos: int) -> str:
        chosen = scannable
        for start, s in zip(starts, sentences):
            if start <= pos:
                chosen = s
            else:
                break
        return chosen

    findings: list[dict] = []
    for start, end, tokens in _english_runs(scannable, preserve):
        if not _looks_english(tokens):
            continue
        if looks_like_proper_noun_run(tokens):
            continue
        sentence = sentence_at(start)
        if spanish_share(sentence) >= MIN_SPANISH_SHARE_IN_SENTENCE:
            continue
        findings.append({
            "words": list(tokens),
            "severity": _severity_for(tokens),
            "snippet": (scannable[start:end] or "").strip()[:80],
            "sentence": sentence.strip()[:140],
        })
    return findings


def label_evidence(text: str) -> list[str]:
    """Etiquetas de interfaz generadas que están en inglés."""
    plain = re.sub(r"[*_`\[\]()#]", " ", text or "").lower()
    words = plain.split()
    hits = {t for t in words if t in ENGLISH_LABEL_HINTS}
    for a, b in zip(words, words[1:]):
        phrase = f"{a} {b}"
        if phrase in ENGLISH_LABEL_PHRASES:
            hits.add(phrase)
    return sorted(hits)


def classify(text: str, preserve: set[str] | None = None) -> tuple[str, list]:
    """Devuelve (veredicto, evidencia).

    Verdicts:

    - ``spanish_prose``: hay prosa y no aparece residuo inglés.
    - ``spanish_label``: forma de etiqueta, sin residuo detectable.
    - ``english_label``: etiqueta de interfaz generada, en inglés.
    - ``link_label_pending``: la etiqueta replica el fragmento que
      apunta. Su idioma lo decide el encabezado de destino, no este
      segmento, así que no puede juzgarse aquí: hay que resolverlo con
      la reescritura de anclas (INV-09).
    - ``english_prose``: hay una frase entera en inglés: debería
      traducirse.
    - ``no_text``: nada que verificar.
    """
    preserve = preserve or set()
    kind = segment_kind(text)
    if kind == "empty":
        return "no_text", []

    label_hits = label_evidence(text)
    if label_hits:
        return "english_label", label_hits
    if kind == "link_only":
        return "link_label_pending", [re.sub(r"[*_`\[\]()#]", " ", text).strip()[:60]]

    runs = english_evidence(text, preserve)
    solid = [r for r in runs if r["severity"] == "warning"]
    if solid:
        return "english_prose", [r["snippet"] for r in solid[:3]]
    if kind == "label":
        return "spanish_label", []
    return "spanish_prose", []


MARKER_RE = re.compile(r"§+")


def spanish_share(text: str) -> float:
    """Proporción de tokens con evidencia española en un fragmento.

    Evidencia española: stopword española o tilde. Decide si una frase
    está en español aunque contenga términos ingleses.
    """
    scannable = re.sub(r"[*_`\[\]()|#]", " ", text or "")
    tokens = TOKEN_RE.findall(scannable)
    if not tokens:
        return 0.0
    spanish = sum(
        1 for t in tokens
        if t.lower() in SPANISH_STOPWORDS or any(c in ACCENTS for c in t)
    )
    return spanish / len(tokens)


PRESERVE_POLICIES = {"preserve", "keep-original", "keep_original"}


def load_preserve_terms(glossary_path: str | None) -> set[str]:
    """Términos que el glosario manda conservar, en minúsculas.

    Un término con `preservation_policy: keep-original` no es residuo
    inglés: es una decisión del usuario. Sin cargarlo, `embedding`,
    `token` o `component` se reportarían como texto sin traducir en cada
    documento donde el glosario ya decidió mantenerlos.

    Se aceptan varias grafías del esquema (`preserve`, `preserve: true`,
    `preservation_policy`) porque el campo ha cambiado de forma entre
    versiones del glosario y un lector de政策的 que ignora una variante
    informaría en falso.
    """
    if not glossary_path:
        return set()
    path = Path(glossary_path)
    if not path.exists():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data.get("entries", []) if isinstance(data, dict) else data
    out: set[str] = set()
    for e in entries or []:
        if not isinstance(e, dict):
            continue
        policy = str(e.get("preservation_policy") or "").lower()
        keep = bool(e.get("preserve")) or policy in PRESERVE_POLICIES
        if not keep:
            continue
        term = e.get("source_term") or e.get("term") or ""
        if term:
            out.add(str(term).lower())
            # El equivalente en español también se acepta: la política
            # protege el término en ambos idiomas.
            preferred = e.get("preferred")
            if isinstance(preferred, dict) and preferred.get("term"):
                out.add(str(preferred["term"]).lower())
    return out


def scan(segments_doc: dict, only_disposition: str = "already_target",
         preserve: set[str] | None = None) -> dict:
    segments: list[dict] = []
    for f in segments_doc.get("files", []):
        for s in f.get("segments", []):
            if only_disposition and s.get("disposition") != only_disposition:
                continue
            text = s.get("translatable_text") or ""
            verdict, evidence = classify(text, preserve)
            segments.append({
                "path": f.get("path"),
                "document_id": f.get("document_id"),
                "segment_id": s.get("segment_id"),
                "verdict": verdict,
                "evidence": evidence,
                "text": text[:240],
            })

    verdicts = Counter(s["verdict"] for s in segments)
    by_dir: dict[str, Counter] = {}
    for s in segments:
        top = (s["path"] or "").split("/")[0]
        by_dir.setdefault(top, Counter())[s["verdict"]] += 1

    needs_translation = [
        s for s in segments if s["verdict"] in ("english_prose", "english_label")
    ]
    pending_anchor = [s for s in segments if s["verdict"] == "link_label_pending"]
    return {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "disposition_checked": only_disposition,
        "total": len(segments),
        "verdicts": dict(verdicts.most_common()),
        "by_directory": {k: dict(v.most_common()) for k, v in sorted(by_dir.items())},
        "needs_translation_count": len(needs_translation),
        "pending_anchor_count": len(pending_anchor),
        "needs_translation": needs_translation,
        "all_segments": segments,
        "note": (
            "Ningún segmento se reescribe. Los veredictos `english_*` indican "
            "que la disposición `already_target` no se sostiene para ellos y "
            "que deberían reetiquetarse como `translatable` para entrar en la "
            "traducción. `link_label_pending` no es un hueco de traducción: "
            "la etiqueta replica el fragmento y su idioma lo decide el "
            "encabezado de destino (INV-09). Cualquiera de las dos "
            "decisiones es del usuario: cambian el denominador de cobertura y "
            "por tanto el resultado del gate."
        ),
    }


def render_markdown(payload: dict) -> str:
    lines = [
        "# Verificación de `already_target`",
        "",
        f"**Medido:** {payload['generated_at']}",
        "",
        f"Segmentos con disposición `{payload['disposition_checked']}`: "
        f"**{payload['total']}**",
        "",
        "| Veredicto | Segmentos | Qué significa |",
        "|---|---|---|",
    ]
    meaning = {
        "spanish_prose": "prosa en español; la disposición se sostiene",
        "spanish_label": "etiqueta sin residuo inglés detectable",
        "english_label": "etiqueta de interfaz generada, en inglés",
        "link_label_pending": "la etiqueta replica el fragmento; la resuelve la reescritura de anclas",
        "english_prose": "frase entera en inglés; debería traducirse",
        "no_text": "sin texto que verificar",
    }
    for verdict, n in payload["verdicts"].items():
        lines.append(f"| `{verdict}` | {n} | {meaning.get(verdict, '')} |")

    lines += ["", "## Por directorio", "",
              "| Directorio | " + " | ".join(sorted(payload["verdicts"])) + " |",
              "|---|" + "---|" * len(payload["verdicts"])]
    for d, counts in payload["by_directory"].items():
        row = [str(counts.get(v, 0)) for v in payload["verdicts"]]
        lines.append(f"| `{d}` | " + " | ".join(row) + " |")

    needs = payload["needs_translation"]
    lines += ["", f"## Segmentos que no sostienen la disposición ({len(needs)})", ""]
    if not needs:
        lines.append("Ninguno.")
    else:
        lines += ["| Ruta | `segment_id` | Veredicto | Evidencia | Texto |",
                  "|---|---|---|---|---|"]
        for s in needs[:200]:
            ev = ", ".join(f"`{e}`" for e in s["evidence"][:4]) or "—"
            txt = s["text"].replace("|", "\\|")[:70]
            lines.append(f"| `{s['path']}` | `{s['segment_id']}` | `{s['verdict']}` | {ev} | {txt} |")
        if len(needs) > 200:
            lines.append(f"| … | | | | {len(needs) - 200} más en el JSON |")

    lines += ["", "## Lo que este informe no afirma", "",
              "- **No** reescribe ningún documento.",
              "- **No** demuestra que la prosa en español sea una traducción "
              "fiel: solo que no presenta residuo inglés detectable.",
              "- **No** autoriza `semantic_pass`.",
              "- **No** reduce el denominador por su cuenta: reetiquetar exige "
              "decisión humana registrada."]
    return "\n".join(lines) + "\n"


def write_atomic(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(target)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="verify_already_target.py")
    p.add_argument("--segments", required=True)
    p.add_argument("--out", required=True, help="Informe JSON.")
    p.add_argument("--report", help="Informe Markdown opcional.")
    p.add_argument("--disposition", default="already_target",
                   help="Disposición a verificar. Por defecto already_target.")
    p.add_argument("--glossary", help="Glosario congelado, para respetar `preserve: true`.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    segments_doc = json.loads(Path(args.segments).read_text(encoding="utf-8"))
    preserve = load_preserve_terms(args.glossary)
    payload = scan(segments_doc, args.disposition, preserve)
    payload["preserve_terms_loaded"] = len(preserve)
    write_atomic(Path(args.out), payload)
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(render_markdown(payload), encoding="utf-8")
    summary = {k: v for k, v in payload.items() if k not in ("all_segments", "needs_translation", "note")}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    # No es un gate: un residuo es una señal para la decisión humana.
    return 0


if __name__ == "__main__":
    sys.exit(main())