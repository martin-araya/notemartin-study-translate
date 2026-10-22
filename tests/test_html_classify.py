"""Pruebas de clasificación código vs contenido (fase 077).

Verifica:

- HTML dentro de fences se preserva como código y no produce
  segmentos traducibles.
- El inventario cuenta etiquetas dentro de fences sin marcarlas
  como activas.
- Round-trip byte-exacto para fences con HTML.
- Con ``html.enabled: true``, un archivo con HTML solo en fences
  no se bloquea.
"""

from __future__ import annotations

import tempfile
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "html"
TMP = Path(tempfile.gettempdir()) / "nst-tests"

sys.path.insert(0, str(SCRIPTS))

import html_parser
import html_selector


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def test_html_dentro_de_fence_no_produce_segmentos() -> None:
    text = (FIXTURES / "code_with_html.md").read_text(encoding="utf-8")
    segments = html_selector.select_translatable(text)
    fence_with_html = text.find("```html")
    fence_end = text.find("```", fence_with_html + 3)
    assert fence_with_html != -1 and fence_end != -1
    for seg in segments:
        assert not (fence_with_html <= seg.start < fence_end), (
            f"segmento traducible dentro de fence: {seg}"
        )


def test_inventory_cuenta_etiquetas_en_fences() -> None:
    out = TMP / "code_html_inv.json"
    proc = run([str(SCRIPTS / "html_inventory.py"), "--root", str(FIXTURES), "--out", str(out)])
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["summary"]["files"] >= 5
    counts = payload["attribute_counts"]
    assert counts.get("colspan", 0) >= 1


def test_round_trip_fence_con_html() -> None:
    text = """# Title

```html
<details>
  <summary>x</summary>
  body
</details>
```

End.
"""
    assert html_parser.round_trip(text) == text


def test_parser_trata_fence_como_span_literal() -> None:
    text = (FIXTURES / "code_with_html.md").read_text(encoding="utf-8")
    doc = html_parser.parse_html(text)
    fence_spans = [n for n in doc.nodes if isinstance(n, html_parser.Span) and n.kind == "code_fenced"]
    assert fence_spans
    assert fence_spans[0].value.startswith("```html")


def test_no_segmentos_en_fence_round_trip() -> None:
    text = """inline <a href="x" title="t">link</a> text
```html
<a href="x" title="inside">inside</a>
```
"""
    segments = html_selector.select_translatable(text)
    fence_start = text.find("```html")
    fence_end = text.find("```", fence_start + 3)
    inside_segments = [s for s in segments if fence_start < s.start < fence_end]
    assert inside_segments == []


def test_fence_no_re_clasifica_como_bloqueante() -> None:
    corpus = TMP / "fence_only"
    if corpus.exists():
        shutil.rmtree(corpus)
    corpus.mkdir()
    (corpus / "doc.md").write_text((FIXTURES / "code_with_html.md").read_text(encoding="utf-8"), encoding="utf-8")
    inv = TMP / "inv_fence.json"
    profile = TMP / "profile_fence.json"
    profile.write_text(json.dumps({
        "target_language": "es",
        "source_language": "auto",
        "markdown_dialect": "commonmark+gfm",
        "slug_algorithm": {"name": "github", "version": "v1"},
        "code_preservation": "strict",
        "frontmatter_policy": "preserve",
        "bilingual_policy": "first-mention-per-document",
        "punctuation_preference": "es-comma-period",
        "review_mode": "assisted",
        "paths": {"source_root": str(corpus), "work_root": "/tmp", "output_root": "/tmp"},
        "exclusions": [],
        "context_budget": 1500,
        "model_metadata": {"provider": "unknown", "model": "unknown", "prompt_version": "v0"},
        "html": {"enabled": True},
    }), encoding="utf-8")
    assert run([str(SCRIPTS / "inventory.py"), "--source", str(corpus), "--out", str(inv)]).returncode == 0
    out = TMP / "out_fence.json"
    proc = run([
        str(SCRIPTS / "prepare.py"),
        "--inventory", str(inv),
        "--out", str(out),
        "--profile", str(profile),
    ])
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(out.read_text(encoding="utf-8"))
    blocked = [f for f in payload["files"] if f["verdict"] == "blocked"]
    assert blocked == []
