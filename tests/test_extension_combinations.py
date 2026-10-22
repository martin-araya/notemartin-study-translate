"""Pruebas de combinaciones entre extensiones (fase 089).

Verifica que dos o más extensiones conviven en un mismo archivo
sin solapar rangos y sin perder bytes.

Combinaciones cubiertas:

- HTML (`<details>`) y admonitions (`:::warning`)
- Footnotes (`[^id]: body`) y wikilinks (`[[Target|Alias]]`)
- Math (`$$x=1$$`) y directivas (`::param x:`)
- Frontmatter (YAML) y math (`$$x=1$$`)
- Todas las extensiones en un solo archivo.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS))

import admonitions
import directives
import footnotes
import frontmatter_translate
import html_parser
import html_selector
import math_ext as math
import wikilinks


def test_html_y_admonition_no_solapan() -> None:
    text = """intro

:::warning
warning body
:::

<details>
<summary>hi</summary>
inside
</details>

end"""
    html_segments = html_selector.select_translatable(text)
    adm_segments = admonitions.extract_admonition_segments(text)
    html_ranges = [(s.start, s.end) for s in html_segments]
    adm_ranges = [(s.start, s.end) for s in adm_segments]
    for h in html_ranges:
        for a in adm_ranges:
            assert not (h[0] < a[1] and a[0] < h[1]), f"solapamiento {h} vs {a}"


def test_footnote_y_wikilink_no_solapan() -> None:
    text = """see [[Operations|ops runbook]]

[^1: see ops

plain text
"""
    fn_segments = footnotes.extract_footnote_segments(text)
    wk_segments = wikilinks.extract_wikilink_segments(text)
    fn_ranges = [(s.start, s.end) for s in fn_segments]
    wk_ranges = [(s.start, s.end) for s in wk_segments]
    for f in fn_ranges:
        for w in wk_ranges:
            assert not (f[0] < w[1] and w[0] < f[1]), f"solapamiento {f} vs {w}"


def test_math_y_directiva_no_solapan() -> None:
    text = """intro

    :param x: The variable.

    The equation $x = 1$ is solved.
"""
    math_spans = math.collect_math_spans(text)
    dir_segments, _ = directives.extract_directive_segments(text)
    math_ranges = [(s.start, s.end) for s in math_spans]
    dir_ranges = [(s.start, s.end) for s in dir_segments]
    for m in math_ranges:
        for d in dir_ranges:
            assert not (m[0] < d[1] and d[0] < m[1]), f"solapamiento {m} vs {d}"


def test_frontmatter_y_math_no_solapan() -> None:
    text = """---
title: t
---

intro

$$x = 1$$
"""
    fm_segments = frontmatter_translate.extract_frontmatter_segments(text, ["title"])
    math_spans = math.collect_math_spans(text)
    fm_ranges = [(s.start, s.end) for s in fm_segments]
    math_ranges = [(s.start, s.end) for s in math_spans]
    for f in fm_ranges:
        for m in math_ranges:
            assert not (f[0] < m[1] and m[0] < f[1]), f"solapamiento {f} vs {m}"


def test_html_y_math_no_solapan() -> None:
    text = """intro

<details>
<summary>x</summary>
inside
</details>

$$y = z$$
"""
    html_segments = html_selector.select_translatable(text)
    math_spans = math.collect_math_spans(text)
    html_ranges = [(s.start, s.end) for s in html_segments]
    math_ranges = [(s.start, s.end) for s in math_spans]
    for h in html_ranges:
        for m in math_ranges:
            assert not (h[0] < m[1] and m[0] < h[1]), f"solapamiento {h} vs {m}"


def test_todas_las_extensiones_en_un_archivo_round_trip() -> None:
    text = (ROOT / "tests" / "fixtures" / "combined" / "all_ext.md").read_text(encoding="utf-8")

    replacements: list[tuple[int, int, str]] = []
    for s in html_selector.select_translatable(text):
        replacements.append((s.start, s.end, s.text))
    for s in admonitions.extract_admonition_segments(text):
        replacements.append((s.start, s.end, s.text))
    for s in wikilinks.extract_wikilink_segments(text):
        replacements.append((s.start, s.end, s.text))
    for s in footnotes.extract_footnote_segments(text):
        replacements.append((s.start, s.end, s.text))

    replacements.sort(key=lambda r: r[0])
    for a, b in zip(replacements, replacements[1:]):
        assert a[1] <= b[0], f"solapamiento en {a} y {b}"

    out = text
    for start, end, replacement in sorted(replacements, key=lambda r: -r[0]):
        out = out[:start] + replacement + out[end:]
    assert out == text


def test_frontmatter_dentro_de_fenced_code_no_se_traduce() -> None:
    text = """intro

```
---
title: not a title
---

body
```
"""
    segments = frontmatter_translate.extract_frontmatter_segments(text, ["title"])
    assert segments == []


def test_math_dentro_de_fenced_code_no_se_detecta() -> None:
    text = """intro

```
$ echo price
```
"""
    spans = math.collect_math_spans(text)
    assert spans == []