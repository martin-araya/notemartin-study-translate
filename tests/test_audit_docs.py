"""Pruebas de la auditoría documental (fase 146).

La auditoría no se prueba contra el repositorio solamente: cada código de
salida se provoca en un árbol temporal en ``tmp_path`` con un documento que
falla exactamente esa regla.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from audit_docs import audit, exit_code_for  # noqa: E402

HELPER_SCRIPT = '''#!/usr/bin/env python3
"""Guion de prueba para audit_docs."""

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(prog="helper.py")
    parser.add_argument("--out", required=True)
    parser.add_argument("--root", default=".")
    parser.parse_args()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def _tree(root: Path, *, references: dict[str, str] | None = None,
          extra_docs: dict[str, str] | None = None) -> Path:
    (root / "references").mkdir(parents=True, exist_ok=True)
    (root / "scripts").mkdir(parents=True, exist_ok=True)
    (root / "scripts" / "helper.py").write_text(HELPER_SCRIPT, encoding="utf-8")
    shutil.copy(ROOT / "references" / "rule-registry.json", root / "references" / "rule-registry.json")
    (root / "SKILL.md").write_text(
        "<!--\nname: notemartin-study-translate\ndescription: prueba\n-->\n\n"
        "# Prueba\n\n## §6 · Archivos\n\n"
        "No hay archivos de referencia.\n",
        encoding="utf-8",
    )
    for name, body in (references or {}).items():
        (root / "references" / name).write_text(body, encoding="utf-8")
    for name, body in (extra_docs or {}).items():
        (root / name).write_text(body, encoding="utf-8")
    return root


def _audit(root: Path) -> dict:
    return audit(root, root / "references" / "rule-registry.json")


# --------------------------------------------------------------------------
# repositorio real
# --------------------------------------------------------------------------

def test_el_repositorio_real_pasa_la_auditoria() -> None:
    report = _audit(ROOT)
    assert report["failures"] == {}, report["failures"]
    assert exit_code_for(report) == 0


# --------------------------------------------------------------------------
# 1 · rutas
# --------------------------------------------------------------------------

def test_una_ruta_inexistente_falla(tmp_path: Path) -> None:
    root = _tree(tmp_path, extra_docs={
        "RELEASE.md": "Usa `scripts/no_existe.py` para comprobar.\n",
    })
    report = _audit(root)
    assert report["failures"]["1"], report["failures"]
    assert exit_code_for(report) == 1


# --------------------------------------------------------------------------
# 2 · comandos
# --------------------------------------------------------------------------

def test_un_flag_inexistente_falla(tmp_path: Path) -> None:
    root = _tree(tmp_path, extra_docs={
        "RELEASE.md": "```bash\npython3 scripts/helper.py --no-existe\n```\n",
    })
    report = _audit(root)
    assert report["failures"]["2"], report["failures"]
    assert any("no-existe" in f for f in report["failures"]["2"])


def test_un_flag_que_existe_no_falla(tmp_path: Path) -> None:
    root = _tree(tmp_path, extra_docs={
        "RELEASE.md": "```bash\npython3 scripts/helper.py --out informe.json --root .\n```\n",
    })
    assert "2" not in _audit(root)["failures"]


def test_un_script_inexistente_en_un_comando_falla(tmp_path: Path) -> None:
    root = _tree(tmp_path, extra_docs={
        "RELEASE.md": "```bash\npython3 scripts/inventado.py --out x.json\n```\n",
    })
    report = _audit(root)
    assert report["failures"]["2"], report["failures"]


# --------------------------------------------------------------------------
# 3 · reglas contradictorias
# --------------------------------------------------------------------------

def test_una_version_de_parser_contradictoria_falla(tmp_path: Path) -> None:
    root = _tree(tmp_path, references={
        "contrato.md": "<!-- version: 1.0.0 -->\n\n# Contrato\n\nUsamos markdown-it-py 9.9.9 para parsear.\n",
    })
    report = _audit(root)
    assert report["failures"]["3"], report["failures"]
    assert any("9.9.9" in f for f in report["failures"]["3"])


def test_la_version_de_parser_correcta_no_falla(tmp_path: Path) -> None:
    root = _tree(tmp_path, references={
        "contrato.md": "<!-- version: 1.0.0 -->\n\n# Contrato\n\nUsamos markdown-it-py 3.0.0.\n",
    })
    assert "3" not in _audit(root)["failures"]


def test_el_algoritmo_de_anchas_contradictorio_falla(tmp_path: Path) -> None:
    root = _tree(tmp_path, references={
        "anchors.md": "<!-- version: 1.0.0 -->\n\n# Anclas\n\nUsamos github-slug-v7.\n",
    })
    report = _audit(root)
    assert report["failures"]["3"], report["failures"]


def test_otra_skill_no_es_una_contradiccion(tmp_path: Path) -> None:
    root = _tree(tmp_path, references={
        "notas.md": "<!-- version: 1.0.0 -->\n\n# Notas\n\n"
                    "Este proyecto no es notemartin-study-notes.\n",
    })
    assert "3" not in _audit(root)["failures"]


# --------------------------------------------------------------------------
# 4 · afirmaciones remotas
# --------------------------------------------------------------------------

def test_una_afirmacion_remota_sin_evidencia_falla(tmp_path: Path) -> None:
    root = _tree(tmp_path, extra_docs={
        "RELEASE.md": "La entrega está soportado en Notion desde la 0.1.0.\n",
    })
    report = _audit(root)
    assert report["failures"]["4"], report["failures"]


def test_una_prohibicion_no_es_una_afirmacion(tmp_path: Path) -> None:
    root = _tree(tmp_path, extra_docs={
        "RELEASE.md": "Markdown listo para importar no significa verificado en Notion.\n",
    })
    assert "4" not in _audit(root)["failures"]


# --------------------------------------------------------------------------
# 5 y 6 · versión y alcanzabilidad
# --------------------------------------------------------------------------

def test_una_referencia_sin_marca_de_version_falla(tmp_path: Path) -> None:
    root = _tree(tmp_path, references={"sinnumero.md": "# Sin número\n"})
    report = _audit(root)
    assert report["failures"]["5"], report["failures"]
    assert exit_code_for(report) == 5


def test_una_referencia_huerfana_falla(tmp_path: Path) -> None:
    root = _tree(tmp_path, references={
        "usada.md": "<!-- version: 1.0.0 -->\n\n# Usada\n",
    }, extra_docs={"RELEASE.md": "Se usa `references/usada.md`.\n"})
    assert "6" not in _audit(root)["failures"]
    root2 = _tree(tmp_path / "otro", references={
        "suelta.md": "<!-- version: 1.0.0 -->\n\n# Suelta\n",
    })
    report = _audit(root2)
    assert report["failures"]["6"], report["failures"]
    assert exit_code_for(report) == 6


def test_el_registro_de_reglas_es_legible() -> None:
    registry = json.loads((ROOT / "references" / "rule-registry.json").read_text(encoding="utf-8"))
    keys = {rule["key"] for rule in registry["rules"]}
    assert {"parser_version", "anchor_algorithm", "remote_status"} <= keys