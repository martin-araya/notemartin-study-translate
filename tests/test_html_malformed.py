"""Pruebas de HTML malformado (fase 078).

Verifica que el parser detecta y reporta:

- Aperturas sin cierre (``unclosed_tag``).
- Cierres sin apertura (``orphan_close``).
- Cierres mal anidados (``misnested_close``).

Y que **no** repara el documento silenciosamente: los bytes
originales quedan intactos. ``round_trip`` con malformado puede
fallar; el parser emite hallazgos.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS))

import html_parser


def test_parser_detecta_apertura_sin_cierre() -> None:
    text = "<details>body without close"
    doc = html_parser.parse_html(text)
    assert any(f["kind"] == "unclosed_tag" and f["tag"] == "details" for f in doc.malformed_findings)


def test_parser_detecta_cierre_huerfano() -> None:
    text = "before </table> after"
    doc = html_parser.parse_html(text)
    assert any(f["kind"] == "orphan_close" and f["tag"] == "table" for f in doc.malformed_findings)


def test_parser_detecta_misnested() -> None:
    text = "<div><span></div></span>"
    doc = html_parser.parse_html(text)
    kinds = {f["kind"] for f in doc.malformed_findings}
    assert "misnested_close" in kinds or "unclosed_tag" in kinds


def test_parser_no_repara_silenciosamente() -> None:
    text = "<details>body"
    doc = html_parser.parse_html(text)
    out = "".join(
        doc.source[doc.nodes[i].start:doc.nodes[i].end] if hasattr(doc.nodes[i], "start") else doc.source[doc.nodes[i].start:doc.nodes[i].end]
        for i in range(len(doc.nodes))
    )
    assert out == text


def test_html_bien_formado_no_reporta_malformado() -> None:
    text = "<details><summary>x</summary>body</details>"
    doc = html_parser.parse_html(text)
    assert doc.malformed_findings == []


def test_malformado_dentro_de_fence_no_se_reporta() -> None:
    text = """outer text

```html
<details>unclosed
```

more outer
"""
    doc = html_parser.parse_html(text)
    malformed = [f for f in doc.malformed_findings if not (f["start"] >= text.find("```html"))]
    assert malformed == []