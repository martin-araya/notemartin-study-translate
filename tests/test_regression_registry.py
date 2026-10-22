"""Pruebas del registro permanente y de su gate (fase 141).

``scripts/regression_gate.py`` comprueba que cada fallo conocido tiene un
caso positivo y un caso negativo **reproducibles**: fixture presente,
variante presente, procedencia autorizada y nodeid de pytest existente que
referencia a ese fixture.

Las pruebas negativas construyen registros temporales en ``tmp_path`` para
provocar cada código de salida sin tocar el registro real.
"""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path
from typing import Callable

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from regression_gate import check_registry, exit_code_for, load_registry  # noqa: E402

REGISTRY_PATH = ROOT / "evals" / "regression" / "registry.json"


def _registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def _all_nodeids_exist(nodeid: str) -> bool:
    return True


def _declared_only() -> Callable[[str], bool]:
    """Solo acepta los nodeids que el registro real declara."""
    payload = _registry()
    declared = {
        entry["tests"][side]
        for entry in payload["cases"]
        for side in ("positive", "negative")
    }
    return lambda nodeid: nodeid in declared


def test_el_registro_real_no_tiene_huecos() -> None:
    report = check_registry(REGISTRY_PATH, root=ROOT, nodeid_exists=_all_nodeids_exist)
    assert report["gaps"] == [], report["gaps"]
    assert report["failures"] == {}, report["failures"]
    assert report["counts"]["cases"] == len(_registry()["cases"])
    assert exit_code_for(report) == 0


def test_cada_fallo_conocido_tiene_caso_mas_y_menos() -> None:
    report = check_registry(REGISTRY_PATH, root=ROOT, nodeid_exists=_all_nodeids_exist)
    covered = report["counts"]["by_known_failure"]
    for failure in _registry()["known_failures"]:
        entry = covered.get(failure)
        assert entry == {"positive": 1, "negative": 1}, failure


def test_hueco_cuando_un_fallo_conocido_no_tiene_entrada(tmp_path: Path) -> None:
    payload = _registry()
    payload["known_failures"].append("fallo_inventado")
    target = tmp_path / "registry.json"
    target.write_text(json.dumps(payload), encoding="utf-8")
    report = check_registry(target, root=ROOT, nodeid_exists=_all_nodeids_exist)
    assert "fallo_inventado" in report["gaps"]
    assert exit_code_for(report) == 7


def test_nodeid_inventado_falla(tmp_path: Path) -> None:
    payload = _registry()
    payload["cases"][0]["tests"]["negative"] = "tests/test_no_existe.py::test_nada"
    target = tmp_path / "registry.json"
    target.write_text(json.dumps(payload), encoding="utf-8")
    report = check_registry(target, root=ROOT, nodeid_exists=_declared_only())
    assert report["failures"]["5"], report["failures"]
    assert exit_code_for(report) == 5


def test_nodeid_inventado_en_el_lado_positivo_falla(tmp_path: Path) -> None:
    payload = _registry()
    payload["cases"][0]["tests"]["positive"] = "tests/test_no_existe.py::test_nada"
    target = tmp_path / "registry.json"
    target.write_text(json.dumps(payload), encoding="utf-8")
    report = check_registry(target, root=ROOT, nodeid_exists=_declared_only())
    assert report["failures"]["4"], report["failures"]
    assert exit_code_for(report) == 4


def test_procedencia_incompleta_falla(tmp_path: Path) -> None:
    payload = _registry()
    payload["cases"][0]["provenance"].pop("license_note")
    target = tmp_path / "registry.json"
    target.write_text(json.dumps(payload), encoding="utf-8")
    report = check_registry(target, root=ROOT, nodeid_exists=_all_nodeids_exist)
    assert report["failures"]["6"], report["failures"]
    assert exit_code_for(report) == 6


def test_fixture_inexistente_falla(tmp_path: Path) -> None:
    payload = _registry()
    payload["cases"][0]["positive"]["fixture"] = "tests/fixtures/regression/no_existe.json"
    target = tmp_path / "registry.json"
    target.write_text(json.dumps(payload), encoding="utf-8")
    report = check_registry(target, root=ROOT, nodeid_exists=_all_nodeids_exist)
    assert report["failures"]["2"], report["failures"]
    assert exit_code_for(report) == 2


def test_variante_inexistente_en_el_fixture_falla(tmp_path: Path) -> None:
    payload = _registry()
    payload["cases"][0]["negative"]["variant_key"] = "no_existe"
    target = tmp_path / "registry.json"
    target.write_text(json.dumps(payload), encoding="utf-8")
    report = check_registry(target, root=ROOT, nodeid_exists=_all_nodeids_exist)
    assert report["failures"]["8"], report["failures"]
    assert exit_code_for(report) == 8


def test_case_id_duplicado_falla(tmp_path: Path) -> None:
    payload = _registry()
    payload["cases"].append(copy.deepcopy(payload["cases"][0]))
    target = tmp_path / "registry.json"
    target.write_text(json.dumps(payload), encoding="utf-8")
    report = check_registry(target, root=ROOT, nodeid_exists=_all_nodeids_exist)
    assert report["failures"]["1"], report["failures"]
    assert exit_code_for(report) == 1


def test_el_registro_rechaza_un_esquema_invalido(tmp_path: Path) -> None:
    payload = _registry()
    payload["cases"][0]["severity"] = "catastrofico"
    target = tmp_path / "registry.json"
    target.write_text(json.dumps(payload), encoding="utf-8")
    report = check_registry(target, root=ROOT, nodeid_exists=_all_nodeids_exist)
    assert report["failures"]["1"], report["failures"]


def test_el_registro_no_declara_un_fixture_fuera_de_tests() -> None:
    for entry in _registry()["cases"]:
        for side in ("positive", "negative"):
            assert entry[side]["fixture"].startswith("tests/fixtures/regression/")


def test_los_nodeids_declarados_existen_de_verdad() -> None:
    """Reproducibilidad real: pytest coleta los nodeids del registro."""
    payload = _registry()
    nodeids = sorted({
        entry["tests"][side]
        for entry in payload["cases"]
        for side in ("positive", "negative")
    })
    assert nodeids, "el registro no declara nodeids"
    files = sorted({nodeid.split("::")[0] for nodeid in nodeids})
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", *files],
        cwd=str(ROOT), capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    collected = proc.stdout
    missing = [nodeid for nodeid in nodeids if nodeid not in collected]
    assert missing == [], missing


def test_load_registry_omite_un_registro_ilegible() -> None:
    assert load_registry(ROOT / "evals" / "regression" / "no_existe.json") is None