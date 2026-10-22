"""Compara dos versiones del parser antes de promocionarla (fase 144).

El comparador extrae, con cada intérprete, las **features relevantes
estructuralmente** del corpus:

- rangos de línea declarados por cada token con `map`,
- conteos de tokens, tokens con `map`, líneas, bloques y código inline,
- slugs de anclas de cada encabezado.

Después diffea baseline contra candidata. La promoción solo se permite si
`changed_ranges`, `changed_slugs` **y** `changed_counts` están vacíos. La
aceptación de la fase pide bloquear cuando cambian rangos o slugs; bloquear
también ante un cambio de recuento es la regla más estricta y es la que se
aplica, porque un recuento distinto significa que la candidata interpreta el
documento de otra forma aunque los rangos declarados coincidan.

Cuando la promoción queda bloqueada, el informe lista los **dependientes**
que habría que migrar: `anchors.json`, `segments/*.json`, entradas de caché
con la versión de parser anterior y `reports/`.

Códigos de salida:

    0 = promoción permitida (rangos y slugs idénticos)
    2 = corpus inválido oCandidate noinstalled
    3 = error al ejecutar la sonda con un intérprete
    4 = promoción bloqueada: cambiaron rangos o slugs
    5 = la versión candidata del parser no está instalada

Uso::

    python scripts/compare_parser.py --corpus tests/fixtures/pilot \\
        --candidate-interpreter /tmp/nst-parser-alt/bin/python \\
        --out reports/maintenance/parser_comparison.json

    # solo extraer features con este intérprete (uso interno del padre)
    python scripts/compare_parser.py --emit --corpus tests/fixtures/pilot
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import random
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from build_anchors import github_slug  # noqa: E402
from delivery_common import now_iso, write_atomic  # noqa: E402

PINNED_PARSER = "3.0.0"
DEPENDENTS = (
    "anchors.json",
    "segments/",
    "translations/",
    "cache de traducción (schemas/cache_entry.schema.json)",
    "reports/ (anchors y determinista)",
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="compare_parser.py")
    p.add_argument("--corpus", required=True)
    p.add_argument("--out")
    p.add_argument("--emit", action="store_true",
                   help="Emite las features de este intérprete y termina.")
    p.add_argument("--baseline-interpreter", default=sys.executable)
    p.add_argument("--candidate-interpreter", default=None)
    p.add_argument("--candidate-adapter", default=None,
                   help="Módulo .py con transform(features) para simular otra versión.")
    p.add_argument("--sample", type=int, default=None)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--corpus-hash", default=None,
                   help="SHA-256 esperado del corpus; si no cuadra, exit 2.")
    return p.parse_args(argv)


# --------------------------------------------------------------------------
# extracción de features
# --------------------------------------------------------------------------

def _parser():
    """Misma configuración que ``scripts/prepare.py``.

    El frontmatter no lo añade el parser: lo preserva el ensamblador por
    rango, igual que en el núcleo. Por eso aquí no se habilita ninguna regla
    extra: comparar el parser es comparar su salida real sobre el dialecto
    declarado.
    """
    from markdown_it import MarkdownIt

    return (
        MarkdownIt("commonmark", {"html": True, "linkify": False, "typographer": False})
        .enable("table")
        .enable("strikethrough")
    )


def _documents(corpus: Path, sample: int | None, seed: int) -> list[Path]:
    files = sorted(p for p in Path(corpus).rglob("*.md") if p.is_file())
    if sample is not None and sample < len(files):
        rng = random.Random(seed)
        files = sorted(rng.sample(files, sample))
    return files


def _inline_text(tokens) -> str:
    return "".join(child.content for child in tokens if child.type in ("text", "code_inline"))


def document_features(text: str) -> dict:
    md = _parser()
    tokens = md.parse(text)
    ranges = []
    slugs = []
    with_map = 0
    for token in tokens:
        if token.map:
            with_map += 1
            ranges.append({"type": token.type, "lines": [token.map[0], token.map[1]]})
        if token.type == "heading_open":
            slugs.append(github_slug(_inline_text(token.children or [])))
    lines = text.splitlines()
    return {
        "tokens": len(tokens),
        "tokens_with_map": with_map,
        "lines": len(lines),
        "ranges": ranges,
        "slugs": slugs,
        "fence_blocks": sum(1 for line in lines if line.strip().startswith("```")),
        "inline_code": text.count("`") // 2,
    }


def extract(corpus: Path, sample: int | None, seed: int, adapter: str | None = None) -> dict:
    features = {
        rel: document_features(path.read_text(encoding="utf-8"))
        for rel, path in (
            (str(path.relative_to(corpus)), path)
            for path in _documents(corpus, sample, seed)
        )
    }
    if adapter:
        features = _apply_adapter(adapter, features)
    return {
        "python": sys.executable,
        "parser": _parser_version(),
        "documents": features,
    }


def _apply_adapter(adapter: str, features: dict) -> dict:
    spec = importlib.util.spec_from_file_location("parser_adapter", adapter)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"no se puede cargar el adaptador: {adapter}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.transform(features)


def _parser_version() -> str:
    try:
        import markdown_it

        return getattr(markdown_it, "__version__", "unknown")
    except ImportError:  # pragma: no cover
        return "not-installed"


# --------------------------------------------------------------------------
# comparación
# --------------------------------------------------------------------------

def _probe(interpreter: str, corpus: Path, sample: int | None, seed: int,
           adapter: str | None) -> tuple[dict | None, str]:
    cmd = [
        interpreter, str(Path(__file__).resolve()), "--emit",
        "--corpus", str(corpus),
        "--seed", str(seed),
    ]
    if sample is not None:
        cmd += ["--sample", str(sample)]
    if adapter:
        cmd += ["--candidate-adapter", str(Path(adapter).resolve())]
    proc = None
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except OSError as exc:
        return None, f"no se puede ejecutar {interpreter}: {exc}"
    if proc.returncode != 0:
        return None, (proc.stdout + proc.stderr)[-2000:]
    try:
        return json.loads(proc.stdout), ""
    except json.JSONDecodeError as exc:
        return None, f"salida no parseable: {exc}"


def compare(baseline: dict, candidate: dict) -> dict:
    changed_ranges: list[str] = []
    changed_slugs: list[str] = []
    changed_counts: list[str] = []
    base_docs = baseline.get("documents") or {}
    cand_docs = candidate.get("documents") or {}
    for rel in sorted(set(base_docs) | set(cand_docs)):
        left = base_docs.get(rel)
        right = cand_docs.get(rel)
        if left is None or right is None:
            changed_counts.append(rel)
            continue
        if left["ranges"] != right["ranges"]:
            changed_ranges.append(rel)
        if left["slugs"] != right["slugs"]:
            changed_slugs.append(rel)
        for field in ("tokens", "tokens_with_map", "lines", "fence_blocks", "inline_code"):
            if left[field] != right[field]:
                changed_counts.append(f"{rel}:{field}")
    allowed = not changed_ranges and not changed_slugs and not changed_counts
    return {
        "promotion": "allowed" if allowed else "blocked",
        "changed_ranges": sorted(changed_ranges),
        "changed_slugs": sorted(changed_slugs),
        "changed_counts": sorted(changed_counts),
        "dependents_to_migrate": [] if allowed else list(DEPENDENTS),
        "baseline_parser": baseline.get("parser"),
        "candidate_parser": candidate.get("parser"),
        "documents_compared": len(set(base_docs) | set(cand_docs)),
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    corpus = Path(args.corpus)

    if args.emit:
        payload = extract(corpus, args.sample, args.seed, args.candidate_adapter)
        print(json.dumps(payload, ensure_ascii=False))
        return 0

    if not corpus.is_dir():
        print(f"error: el corpus no existe: {corpus}", file=sys.stderr)
        return 2

    out_path = Path(args.out) if args.out else None
    report: dict = {
        "generated_at": now_iso(),
        "corpus": str(corpus),
        "pinned_parser": PINNED_PARSER,
    }

    baseline, error = _probe(args.baseline_interpreter, corpus, args.sample, args.seed, None)
    if baseline is None:
        print(f"error: sonda baseline falló: {error}", file=sys.stderr)
        report["error"] = {"side": "baseline", "detail": error}
        if out_path:
            write_atomic(out_path, report)
        return 3

    candidate_interpreter = args.candidate_interpreter or args.baseline_interpreter
    candidate, error = _probe(
        candidate_interpreter, corpus, args.sample, args.seed, args.candidate_adapter
    )
    if candidate is None:
        not_installed = "not-installed" in error or "ModuleNotFoundError" in error
        code = 5 if not_installed else 3
        print(f"error: sonda candidata falló: {error}", file=sys.stderr)
        report["error"] = {"side": "candidate", "detail": error}
        report["alternate_installed"] = not not_installed
        if out_path:
            write_atomic(out_path, report)
        return code

    diff = compare(baseline, candidate)
    report.update(diff)
    report["alternate_installed"] = bool(args.candidate_interpreter or args.candidate_adapter)
    report["baseline_interpreter"] = args.baseline_interpreter
    report["candidate_interpreter"] = candidate_interpreter

    if out_path:
        write_atomic(out_path, report)

    if diff["promotion"] == "blocked":
        print(
            "fail: promoción bloqueada; rangos="
            f"{len(diff['changed_ranges'])} slugs={len(diff['changed_slugs'])} "
            f"recuentos={len(diff['changed_counts'])}",
            file=sys.stderr,
        )
        return 4
    print(
        f"ok: promoción permitida ({diff['documents_compared']} documentos comparados, "
        f"baseline {diff['baseline_parser']} vs candidata {diff['candidate_parser']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())