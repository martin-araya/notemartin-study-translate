"""Pruebas de la adaptación local opt-in (fase 134).

Cubre:

- Sin reglas activas la copia es byte a byte idéntica al canónico.
- El árbol canónico nunca se escribe.
- Las reglas solo cambian rutas y nombres, nunca la prosa.
- Las referencias dentro de código protegido no se reescriben.
- Una regla sin justificación, sin implementación o con pérdida de
  contenido se rechaza.
- Destino y canónico disjuntos; las colisiones abortan.
"""

from __future__ import annotations

import tempfile
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "adapt_delivery.py"
SCHEMA = ROOT / "schemas" / "delivery_profile.schema.json"
PROFILE = ROOT / "references" / "delivery-profiles" / "plain-markdown-local.json"
CANONICAL = ROOT / "tests" / "fixtures" / "delivery" / "canonical"
TMP = Path(tempfile.gettempdir()) / "nst-tests"


def run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, check=False)


def hashes(root: Path) -> dict[str, str]:
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def make_canonical(name: str, *, with_awkward_resource: bool = False) -> Path:
    """Copia del fixture canónico, opcionalmente con un recurso problemático."""
    target = TMP / name
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(CANONICAL, target)
    if with_awkward_resource:
        awkward = target / "imagenes" / "Diagrama de Flujo.png"
        awkward.write_bytes((CANONICAL / "imagenes" / "diagrama.png").read_bytes())
        doc = target / "index.md"
        text = doc.read_text(encoding="utf-8")
        text += "\n![Diagrama avanzado](imagenes/Diagrama%20de%20Flujo.png)\n"
        text += "\n![Ruta absoluta](/imagenes/diagrama.png)\n"
        text += "\n![Ruta del sitio](/es/docs/Web/CSS/Values/var)\n"
        text += "\n![Separador heredado](imagenes\\diagrama.png)\n"
        text += "\n```text\nReferencia protegida: imagenes/Diagrama%20de%20Flujo.png\n```\n"
        doc.write_text(text, encoding="utf-8")
    return target


def adapt(canonical: Path, out_name: str, *rules: str, expect: int = 0):
    destination = TMP / out_name
    report = TMP / f"{out_name}_report.json"
    args = [
        str(SCRIPT),
        "--canonical", str(canonical),
        "--profile", str(PROFILE),
        "--destination-out", str(destination),
        "--out", str(report),
    ]
    for rule in rules:
        args += ["--enable", rule]
    proc = run(args)
    assert proc.returncode == expect, proc.stderr
    payload = json.loads(report.read_text(encoding="utf-8"))
    return proc, payload, destination


def test_perfil_cumple_el_esquema() -> None:
    import jsonschema

    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.validate(profile, schema)
    assert profile["activation"] == "explicit"
    assert profile["real_app_evidence"] is False
    assert profile["limitations"], "un adaptador debe declarar limitaciones"
    assert all(r["rationale"] for r in profile["rules"])


def test_sin_reglas_la_copia_es_identica() -> None:
    canonical = make_canonical("adapt_canonico_base")
    before = hashes(canonical)
    _proc, payload, destination = adapt(canonical, "adapt_identico")
    assert payload["rules_enabled"] == []
    assert payload["byte_identical"] is True
    assert hashes(destination) == before


def test_el_arbol_canonico_no_se_escribe() -> None:
    canonical = make_canonical("adapt_canonico_intacto", with_awkward_resource=True)
    before = hashes(canonical)
    _proc, payload, _destination = adapt(canonical, "adapt_intacto", "ascii-resource-names")
    assert payload["canonical_untouched"] is True
    assert payload["canonical_hashes_before"] == payload["canonical_hashes_after"] == before
    assert hashes(canonical) == before


def test_regla_de_rutas_normaliza_destinos() -> None:
    canonical = make_canonical("adapt_rutas", with_awkward_resource=True)
    _proc, payload, destination = adapt(canonical, "adapt_rutas_out", "relative-resource-paths")
    assert payload["rules_enabled"] == ["relative-resource-paths"]
    text = (destination / "index.md").read_text(encoding="utf-8")
    assert "![Separador heredado](imagenes/diagrama.png)" in text
    assert "![Ruta del sitio](/es/docs/Web/CSS/Values/var)" in text, "las rutas del sitio no se tocan"
    assert "imagenes/Diagrama%20de%20Flujo.png" in text, "la codificación porcentual se conserva"
    assert "imagenes/Diagrama de Flujo.png" not in text, "un espacio literal rompería el enlace"
    changes = {c["new"] for c in payload["changes"]}
    assert "imagenes/diagrama.png" in changes


def test_regla_de_nombres_renombra_y_conserva_bytes() -> None:
    canonical = make_canonical("adapt_nombres", with_awkward_resource=True)
    original = (canonical / "imagenes" / "Diagrama de Flujo.png").read_bytes()
    _proc, payload, destination = adapt(canonical, "adapt_nombres_out", "ascii-resource-names")
    renamed = destination / "imagenes" / "diagrama-de-flujo.png"
    assert renamed.exists()
    assert renamed.read_bytes() == original
    assert not (destination / "imagenes" / "Diagrama de Flujo.png").exists()
    text = (destination / "index.md").read_text(encoding="utf-8")
    assert "imagenes/diagrama-de-flujo.png" in text


def test_la_prosa_no_cambia() -> None:
    canonical = make_canonical("adapt_prosa", with_awkward_resource=True)
    before = (canonical / "guias" / "instalacion.md").read_text(encoding="utf-8")
    _proc, _payload, destination = adapt(
        canonical, "adapt_prosa_out", "relative-resource-paths", "ascii-resource-names"
    )
    assert (destination / "guias" / "instalacion.md").read_text(encoding="utf-8") == before


def test_no_reescribe_referencias_en_codigo_protegido() -> None:
    canonical = make_canonical("adapt_codigo", with_awkward_resource=True)
    _proc, _payload, destination = adapt(
        canonical, "adapt_codigo_out", "relative-resource-paths", "ascii-resource-names"
    )
    text = (destination / "index.md").read_text(encoding="utf-8")
    blocks = text.split("```")
    protected = next(b for b in blocks if "Referencia protegida" in b)
    assert "imagenes/Diagrama%20de%20Flujo.png" in protected
    assert "diagrama-de-flujo.png" not in protected
    outside = "".join(b for i, b in enumerate(blocks) if "Referencia protegida" not in b)
    assert "imagenes/diagrama-de-flujo.png" in outside


def test_regla_desconocida_se_rechaza() -> None:
    canonical = make_canonical("adapt_desconocida")
    proc, _payload, _destination = adapt(
        canonical, "adapt_desconocida_out", "regla-inventada", expect=3
    )
    assert "no declarada" in proc.stderr or "sin implementación" in proc.stderr


def test_regla_con_perdida_de_contenido_se_rechaza() -> None:
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    profile["rules"][0]["lossiness"] = "content_loss"
    lossy = TMP / "delivery_profile_lossy.json"
    lossy.write_text(json.dumps(profile, indent=2), encoding="utf-8")

    canonical = make_canonical("adapt_lossy")
    destination = TMP / "adapt_lossy_out"
    report = TMP / "adapt_lossy_report.json"
    proc = run([
        str(SCRIPT), "--canonical", str(canonical), "--profile", str(lossy),
        "--destination-out", str(destination), "--out", str(report),
        "--enable", "relative-resource-paths",
    ])
    assert proc.returncode == 2
    assert "content_loss" in proc.stderr


def test_destino_dentro_del_canonico_se_rechaza() -> None:
    canonical = make_canonical("adapt_dentro")
    destination = canonical / "entregado"
    report = TMP / "adapt_dentro_report.json"
    proc = run([
        str(SCRIPT), "--canonical", str(canonical), "--profile", str(PROFILE),
        "--destination-out", str(destination), "--out", str(report),
    ])
    assert proc.returncode == 2
    assert "disjunto" in proc.stderr


def test_colision_de_nombres_aborta() -> None:
    canonical = make_canonical("adapt_colision")
    images = canonical / "imagenes"
    (images / "Diagrama de flujo.png").write_bytes(b"uno")
    (images / "Diagrama  de  flujo.png").write_bytes(b"otro")
    _proc, _payload, _destination = adapt(
        canonical, "adapt_colision_out", "ascii-resource-names", expect=4
    )
