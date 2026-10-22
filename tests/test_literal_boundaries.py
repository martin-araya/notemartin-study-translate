"""Pruebas de los cortes por byte de los literales protegidos (cierre G-BETA).

El corpus beta destapó tres defectos en `prepare.py` que solo aparecen
con literales no ASCII o con varios tramos de código inline en la misma
línea:

1. `safe_byte_slice` comprobaba el byte equivocado al ajustar un corte, y
   recortaba el final de un literal multibyte: `ƒ` (0xC6 0x92) quedaba
   en un solo byte y se decodificaba como U+FFFD. El literal se
   guardaba corrupto y la protección de código dejaba de proteger
   (INV-05).
2. La rama de `code_inline` de primer nivel calculaba el inicio del
   literal restando `m.start(0)`, que no corresponde al índice del grupo
   interno.
3. La búsqueda del tramo de código tomaba la primera coincidencia de la
   línea, así que dos tramos inline en la misma línea producían un solo
   literal, con el valor del primero aplicado al segundo.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INVENTORY = ROOT / "scripts" / "inventory.py"
PREPARE = ROOT / "scripts" / "prepare.py"
TMP = Path(tempfile.gettempdir()) / "nst-tests"

DOC = (
    "# Cache Components\n\n"
    "Para un componente, `ƒ` significa que la compilacion acepto el prerender. "
    "Luego `generateStaticParams` devuelve las rutas.\n\n"
    "El valor `áéíóú` y el emoji `→` se conservan literalmente.\n\n"
    "El destino `resúmenes/assets/figura.png` no debe cambiar.\n\n"
    "![Ilustración del PDF original](resúmenes/assets/figura.png)\n"
)


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def segments_for(name: str, body: str = DOC) -> list[dict]:
    root = TMP / name
    source = root / "source"
    if source.exists():
        import shutil

        shutil.rmtree(source)
    source.mkdir(parents=True)
    (source / "doc.md").write_text(body, encoding="utf-8")

    inv = root / "inventory.json"
    seg = root / "segments.json"
    assert run([str(INVENTORY), "--source", str(source), "--out", str(inv)]).returncode == 0
    assert run([str(PREPARE), "--inventory", str(inv), "--segments", str(seg)]).returncode == 0
    payload = json.loads(seg.read_text(encoding="utf-8"))
    return [s for f in payload["files"] for s in f["segments"]]


def literals_of(segments: list[dict]) -> list[str]:
    return [
        lit["value"]
        for seg in segments
        for lit in (seg.get("protected_literals") or [])
        if lit.get("type") == "code_inline"
    ]


def all_literals_of(segments: list[dict]) -> list[str]:
    return [
        lit["value"]
        for seg in segments
        for lit in (seg.get("protected_literals") or [])
    ]


def test_literal_multibyte_no_se_trunca() -> None:
    values = literals_of(segments_for("lit-multibyte"))
    assert "ƒ" in values, f"el literal multibyte no se conservo: {values}"
    assert "�" not in values, "aparece un caracter de reemplazo"


def test_rango_del_literal_cai_en_la_fuente() -> None:
    """El rango declarado tiene que cubrir exactamente los bytes del literal."""
    source = TMP / "lit-multibyte" / "source" / "doc.md"
    raw = source.read_bytes()
    for seg in segments_for("lit-multibyte"):
        for lit in seg.get("protected_literals") or []:
            if lit.get("type") != "code_inline":
                continue
            br = lit["byte_range"]
            sliced = raw[br["start"]:br["end"]].decode("utf-8")
            assert sliced == lit["value"], f"rango {br} no corresponde a {lit['value']!r}"


def test_dos_tramos_inline_en_una_linea_dos_literales() -> None:
    segments = segments_for("lit-dos")
    primero = next(
        s for s in segments
        if "generateStaticParams" in (s.get("translatable_text") or "")
    )
    values = [
        lit["value"]
        for lit in primero.get("protected_literals") or []
        if lit.get("type") == "code_inline"
    ]
    assert values == ["ƒ", "generateStaticParams"], values


def test_acentos_y_emoji_en_codigo_inline() -> None:
    values = literals_of(segments_for("lit-acentos"))
    assert "áéíóú" in values, values
    assert "→" in values, values


def test_destino_con_acentos_se_conserva_sin_escapar() -> None:
    """markdown-it normaliza el href a percent-encoding; el literal tiene que
    ser la forma cruda de la fuente, o al ensamblar se cambiarían los bytes."""
    segments = segments_for("lit-destino")
    values = all_literals_of(segments)
    destinos = [
        lit["value"]
        for seg in segments
        for lit in (seg.get("protected_literals") or [])
        if lit.get("type") == "image_destination"
    ]
    assert "resúmenes/assets/figura.png" in destinos, destinos
    assert not any("%C3" in v for v in values), f"literal percent-encoded: {values}"