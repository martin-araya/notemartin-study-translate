"""Pruebas del adaptador Mermaid opt-in (fase 085)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures" / "mermaid"
REF = ROOT / "references" / "mermaid-labels.md"

sys.path.insert(0, str(SCRIPTS))

import mermaid_adapter


def test_referencia_existe_y_declara_estado_opt_in() -> None:
    assert REF.exists()
    text = REF.read_text(encoding="utf-8")
    assert "opt-in" in text.lower()


def test_mermaid_en_modo_nucleo_no_segmentos() -> None:
    """Si el adaptador está desactivado, ninguna extensión debe
    ejecutarlo. Aquí verificamos que el módulo no se importa solo."""
    text = (FIXTURES / "basic.mmd").read_text(encoding="utf-8")
    segments = mermaid_adapter.extract_mermaid_label_segments(text)
    assert segments
    assert mermaid_adapter.is_valid_mermaid(text)


def test_mermaid_con_etiqueta_traducible() -> None:
    text = """flowchart TD
    A["Start"] --> B["Process"]
"""
    segments = mermaid_adapter.extract_mermaid_label_segments(text)
    texts = [s.text for s in segments]
    assert "Start" in texts
    assert "Process" in texts


def test_mermaid_id_literal() -> None:
    text = """flowchart TD
    A["Start"] --> B["Process"]
"""
    segments = mermaid_adapter.extract_mermaid_label_segments(text)
    node_segs = [s for s in segments if s.kind == "mermaid_node_label"]
    ids = [s.parent for s in node_segs]
    assert "A" in ids
    assert "B" in ids


def test_mermaid_sintaxis_invalida_no_se_traduce() -> None:
    text = (FIXTURES / "invalid.mmd").read_text(encoding="utf-8")
    findings = mermaid_adapter.mermaid_findings(text)
    assert findings
    assert any(f["severity"] == "critical" for f in findings)


def test_mermaid_edge_label_traducible() -> None:
    text = """flowchart TD
    A -->|Yes| B
"""
    segments = mermaid_adapter.extract_mermaid_label_segments(text)
    edge = [s for s in segments if s.kind == "mermaid_edge_label"]
    assert any("Yes" in s.text for s in edge)


def test_mermaid_no_ejecuta_javascript() -> None:
    src = (SCRIPTS / "mermaid_adapter.py").read_text(encoding="utf-8")
    forbidden = ("eval(", "exec(", "subprocess.run", "subprocess.Popen", "os.system", "urllib.request")
    for token in forbidden:
        assert token not in src, f"mermaid_adapter.py no debe usar {token!r}"


def test_mermaid_no_modifica_en_modo_nucleo() -> None:
    text = (FIXTURES / "basic.mmd").read_text(encoding="utf-8")
    bytes_text = text.encode("utf-8")
    segments = mermaid_adapter.extract_mermaid_label_segments(text)
    out = bytearray(bytes_text)
    for s in sorted(segments, key=lambda x: -x.start):
        out[s.start:s.end] = s.text.encode("utf-8")
    assert bytes(out) == bytes_text


def test_mermaid_adaptador_no_importa_browsers() -> None:
    src = (SCRIPTS / "mermaid_adapter.py").read_text(encoding="utf-8")
    forbidden = ("playwright", "selenium", "puppeteer", "headless")
    for token in forbidden:
        assert token not in src, f"mermaid_adapter.py no debe usar {token!r}"