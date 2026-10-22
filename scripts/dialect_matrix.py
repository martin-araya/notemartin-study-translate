"""Emisor de la matriz de dialectos versionada (fase 090).

Genera ``dialect_matrix.json`` con la lista de perfiles soportados
y sus versiones, basándose en ``references/dialect-profiles.md``.

Uso::

    python scripts/dialect_matrix.py --out dialect_matrix.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PROFILES = [
    {
        "profile_id": "core-v1",
        "version": "1.0.0",
        "extensions_enabled": [],
        "supports": ["CommonMark + GFM básico", "Mermaid preservado"],
        "does_not_support": [
            "footnotes", "admonitions", "definitions", "directives",
            "MDX", "HTML embebido", "wikilinks", "frontmatter translate",
            "math", "mermaid.labels",
        ],
    },
    {
        "profile_id": "mild-extensions-v1",
        "version": "1.0.0",
        "extensions_enabled": ["footnotes", "admonitions", "definitions", "directives"],
        "supports": [
            "core-v1",
            "footnotes",
            "admonitions",
            "definition lists",
            "directivas Sphinx/Numpydoc",
        ],
        "does_not_support": [
            "MDX", "HTML embebido", "wikilinks", "frontmatter translate",
            "math", "mermaid.labels",
        ],
    },
    {
        "profile_id": "extended-mdx-v1",
        "version": "1.0.0",
        "extensions_enabled": ["mild-extensions-v1", "mdx"],
        "supports": ["mild-extensions-v1", "MDX con gate opt-in"],
        "does_not_support": [
            "HTML embebido", "wikilinks", "frontmatter translate",
            "math", "mermaid.labels",
        ],
    },
    {
        "profile_id": "extended-html-v1",
        "version": "1.0.0",
        "extensions_enabled": ["mild-extensions-v1", "html"],
        "supports": ["mild-extensions-v1", "HTML embebido con gate opt-in"],
        "does_not_support": [
            "MDX", "wikilinks", "frontmatter translate",
            "math", "mermaid.labels",
        ],
    },
    {
        "profile_id": "experimental-v1",
        "version": "1.0.0",
        "extensions_enabled": [
            "mild-extensions-v1", "mdx", "html", "mermaid", "wikilinks",
        ],
        "supports": [
            "extended-mdx-v1",
            "extended-html-v1",
            "wikilinks",
            "mermaid.labels con labels=allow",
        ],
        "does_not_support": ["frontmatter translate", "math"],
    },
    {
        "profile_id": "fr-es-experimental-v1",
        "version": "0.1.0",
        "extensions_enabled": [],
        "supports": ["CommonMark + GFM básico en francés", "par fr→es sin revisión humana"],
        "does_not_support": [
            "MDX", "HTML embebido", "wikilinks", "frontmatter translate",
            "math", "mermaid.labels",
            "revisión humana nativa en fr (fase 103)",
        ],
        "language_pair": "fr-es",
        "reviewer_status": "assisted_only_pending_human",
    },
    {
        "profile_id": "en-es-es-v1",
        "version": "0.1.0",
        "extensions_enabled": [],
        "supports": ["CommonMark + GFM básico", "locale es-ES con vosotros"],
        "does_not_support": [
            "MDX", "HTML embebido", "wikilinks", "frontmatter translate",
            "math", "mermaid.labels",
            "firma nativa en es-ES (fase 109)",
        ],
        "language_pair": "en-es",
        "locale": "es-ES",
        "reviewer_status": "assisted_only_pending_human",
    },
    {
        "profile_id": "en-es-mx-v1",
        "version": "0.1.0",
        "extensions_enabled": [],
        "supports": ["CommonMark + GFM básico", "locale es-MX con usted"],
        "does_not_support": [
            "MDX", "HTML embebido", "wikilinks", "frontmatter translate",
            "math", "mermaid.labels",
            "firma nativa en es-MX (fase 109)",
        ],
        "language_pair": "en-es",
        "locale": "es-MX",
        "reviewer_status": "assisted_only_pending_human",
    },
    {
        "profile_id": "en-es-ar-v1",
        "version": "0.1.0",
        "extensions_enabled": [],
        "supports": ["CommonMark + GFM básico", "locale es-AR con voseo"],
        "does_not_support": [
            "MDX", "HTML embebido", "wikilinks", "frontmatter translate",
            "math", "mermaid.labels",
            "firma nativa en es-AR (fase 109)",
        ],
        "language_pair": "en-es",
        "locale": "es-AR",
        "reviewer_status": "assisted_only_pending_human",
    },
]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="dialect_matrix.py")
    p.add_argument("--out", required=True)
    return p.parse_args(argv)


def write_atomic(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = {
        "generated_at": "",
        "skill": "notemartin-study-translate",
        "schema_version": "1",
        "profiles": PROFILES,
    }
    write_atomic(Path(args.out), payload)
    print(f"ok: {len(PROFILES)} perfiles -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())