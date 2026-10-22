"""Pruebas de la matriz de portabilidad (fase 147).

La aceptación pide distinguir «diseño portable» de «ejecución
efectivamente comprobada». Estas pruebas comprueban que la distinción la
toma el **informe de ejecución**, no el texto del documento.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from check_portability import build_matrix, main  # noqa: E402
from probe_platform import main as probe_main  # noqa: E402
from probe_platform import probe  # noqa: E402

LINUX_PROBE = {
    "generated_at": "2026-10-20T16:30:00Z",
    "python_version": "3.12.3",
    "os_name": "posix",
    "platform": "linux",
    "fcntl": {"available": True},
    "atomic_replace": {"available": True},
    "case_insensitive_fs": {"sensitive": True},
}


def _write(path: Path, payload: dict) -> str:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return str(path)


# --------------------------------------------------------------------------
# sonda
# --------------------------------------------------------------------------

def test_la_sonda_devuelve_todas_las_claves() -> None:
    report = probe()
    for key in ("python_version", "os_name", "platform", "filesystem_encoding",
                "fcntl", "atomic_replace", "case_insensitive_fs",
                "unicode_names", "long_names", "zoneinfo"):
        assert key in report, key


def test_la_sonda_es_repetible_en_estructura() -> None:
    first, second = probe(), probe()
    assert set(first) == set(second)
    assert first["os_name"] == second["os_name"]
    assert first["filesystem_encoding"] == second["filesystem_encoding"]


def test_la_sonda_prueba_de_verdad_el_lock() -> None:
    report = probe()
    assert isinstance(report["fcntl"]["available"], bool)
    if report["fcntl"]["available"]:
        assert "detail" in report["fcntl"]


def test_la_sonda_crea_y_borra_sus_ficheros() -> None:
    probe()
    leftovers = [
        path for path in Path(tempfile.gettempdir()).iterdir()
        if path.name.startswith("nst-probe-") and path.is_dir()
    ]
    assert leftovers == [], leftovers


def test_la_cli_escribe_el_informe(tmp_path: Path) -> None:
    out = tmp_path / "probe.json"
    assert probe_main(["--out", str(out)]) == 0
    assert json.loads(out.read_text(encoding="utf-8"))["os_name"]


# --------------------------------------------------------------------------
# matriz
# --------------------------------------------------------------------------

def test_sin_evidencia_externa_linux_queda_de_diseno() -> None:
    matrix = build_matrix(probe(), [])
    linux = next(r for r in matrix["rows"] if r["system_id"] == "linux-cpython")
    if probe()["os_name"] == "posix" and not str(probe()["platform"]).startswith("darwin"):
        # Aquí la sonda local ES la de Linux: hay evidencia, y por tanto
        # la fila queda verificada sin informe externo.
        assert linux["status"] == "verified"
        assert linux["source"] == "local"
    else:
        assert linux["status"] == "design_only"
        assert linux["evidence"] is None
    if linux["status"] == "design_only":
        assert "linux-cpython" in matrix["design_only_systems"]


def test_con_informe_externo_linux_pasa_a_verificado() -> None:
    matrix = build_matrix(probe(), [LINUX_PROBE])
    linux = next(r for r in matrix["rows"] if r["system_id"] == "linux-cpython")
    assert linux["status"] == "verified"
    assert linux["evidence"]["python_version"] == "3.12.3"
    assert "linux-cpython" in matrix["verified_systems"]


def test_un_inventario_sin_evidencia_nunca_dice_verificado() -> None:
    matrix = build_matrix(None, [])
    assert matrix["verified_systems"] == []
    assert set(matrix["design_only_systems"]) == {
        "macos-darwin", "linux-cpython", "windows-cpython"
    }


def test_la_matriz_declara_que_significa_cada_estado() -> None:
    matrix = build_matrix(probe(), [])
    assert "verified significa" in matrix["claim"]
    assert "design_only significa" in matrix["claim"]
    for row in matrix["rows"]:
        assert row["status"] in ("verified", "design_only")
        assert row["requirement"]


def test_la_cli_sin_sonda_falla(tmp_path: Path) -> None:
    assert main(["--probe", str(tmp_path / "no.json"), "--out", str(tmp_path / "m.json")]) == 2


def test_la_cli_construye_la_matriz(tmp_path: Path) -> None:
    probe_path = tmp_path / "probe.json"
    probe_path.write_text(json.dumps(LINUX_PROBE), encoding="utf-8")
    out = tmp_path / "matrix.json"
    assert main(["--probe", str(probe_path), "--out", str(out)]) == 0
    matrix = json.loads(out.read_text(encoding="utf-8"))
    assert "linux-cpython" in matrix["verified_systems"]


def test_el_sistema_local_queda_verificado() -> None:
    matrix = build_matrix(probe(), [])
    local = [row for row in matrix["rows"] if row["status"] == "verified"]
    assert len(local) == 1
    assert local[0]["source"] == "local"


def test_la_sonda_no_necesita_red() -> None:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "probe_platform.py"),
         "--out", str(Path(tempfile.gettempdir()) / "nst-probe-cli.json")],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 0, proc.stderr