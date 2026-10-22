"""Pruebas de la política de purga de workdirs (fase 148).

Todas las pruebas trabajan en ``tmp_path``. Ninguna toca un ``work_root``,
``source_root`` ni ``output_root`` reales: esa restricción también la
comprueba el propio script.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from purge_workdir import check_roots, collect_candidates, purge  # noqa: E402


def _run_dir(root: Path, run_id: str = "run-0000beef", *, state: str | None = None) -> Path:
    workdir = root / run_id
    (workdir / "segments").mkdir(parents=True, exist_ok=True)
    (workdir / "manifest.json").write_text(json.dumps({
        "run_id": run_id,
        "manifest_version": "translate/v1",
        "files": [{"path": "docs/a.md", "current_state": state or "translated"}] if state else [],
    }), encoding="utf-8")
    (workdir / "segments" / "seg-1.json").write_text("{}", encoding="utf-8")
    (workdir / "notes.txt").write_text("notas\n", encoding="utf-8")
    return workdir


def _log(tmp_path: Path) -> dict:
    return json.loads((tmp_path / "purge.json").read_text(encoding="utf-8"))


def test_el_simulado_no_borra_nada(tmp_path: Path) -> None:
    workdir = _run_dir(tmp_path / "work")
    before = sorted(p.name for p in workdir.rglob("*"))
    code = purge([
        "--work-root", str(tmp_path / "work"),
        "--run-id", "run-0000beef",
        "--dry-run",
        "--out", str(tmp_path / "purge.json"),
    ])
    assert code == 0
    assert sorted(p.name for p in workdir.rglob("*")) == before
    log = _log(tmp_path)
    assert log["dry_run"] is True
    assert log["deleted"] == []
    assert log["candidates"], "el simulado debe listar los candidatos"


def test_aplicar_exige_autorizacion(tmp_path: Path) -> None:
    _run_dir(tmp_path / "work")
    code = purge([
        "--work-root", str(tmp_path / "work"),
        "--run-id", "run-0000beef",
        "--apply",
        "--out", str(tmp_path / "purge.json"),
    ])
    assert code == 3
    assert (tmp_path / "work" / "run-0000beef" / "notes.txt").exists()


def test_aplicar_con_autorizacion_borra_y_deja_log(tmp_path: Path) -> None:
    workdir = _run_dir(tmp_path / "work")
    code = purge([
        "--work-root", str(tmp_path / "work"),
        "--run-id", "run-0000beef",
        "--apply",
        "--authorized-by", "tester",
        "--reason", "cierre de prueba",
        "--out", str(tmp_path / "purge.json"),
    ])
    assert code == 0
    assert not (workdir / "notes.txt").exists()
    log = _log(tmp_path)
    assert log["dry_run"] is False
    assert log["authorized_by"] == "tester"
    assert "notes.txt" in log["deleted"]
    assert log["bytes_reclaimed"] > 0
    assert log["manifest_sha256"]


def test_un_workdir_dentro_del_source_root_se_rechaza(tmp_path: Path) -> None:
    source = tmp_path / "corpus"
    (source / "run-0000beef").mkdir(parents=True)
    code = purge([
        "--work-root", str(source),
        "--source-root", str(source),
        "--run-id", "run-0000beef",
        "--dry-run",
        "--out", str(tmp_path / "purge.json"),
    ])
    assert code == 2


def test_un_workdir_dentro_del_output_root_se_rechaza(tmp_path: Path) -> None:
    out = tmp_path / "out"
    (out / "run-0000beef").mkdir(parents=True)
    code = purge([
        "--work-root", str(out),
        "--output-root", str(out),
        "--run-id", "run-0000beef",
        "--dry-run",
        "--out", str(tmp_path / "purge.json"),
    ])
    assert code == 2


def test_un_workdir_inexistente_falla(tmp_path: Path) -> None:
    code = purge([
        "--work-root", str(tmp_path / "no"),
        "--run-id", "run-0000beef",
        "--dry-run",
        "--out", str(tmp_path / "purge.json"),
    ])
    assert code == 6


def test_un_symlink_no_se_sigue(tmp_path: Path) -> None:
    workdir = _run_dir(tmp_path / "work")
    destino = tmp_path / "outside"
    destino.mkdir()
    (destino / "precioso.txt").write_text("no tocar\n", encoding="utf-8")
    try:
        (workdir / "enlace").symlink_to(destino)
    except (OSError, NotImplementedError):
        return
    code = purge([
        "--work-root", str(tmp_path / "work"),
        "--run-id", "run-0000beef",
        "--apply",
        "--authorized-by", "tester",
        "--out", str(tmp_path / "purge.json"),
    ])
    assert code == 0
    assert (destino / "precioso.txt").exists(), "el destino del symlink no puede tocarse"
    assert (workdir / "enlace").exists() or not (workdir / "enlace").is_symlink()
    log = _log(tmp_path)
    assert any(s["path"] == "enlace" for s in log["skipped"])


def test_una_ejecucion_exportada_exige_autorizacion(tmp_path: Path) -> None:
    _run_dir(tmp_path / "work", state="exported")
    code = purge([
        "--work-root", str(tmp_path / "work"),
        "--run-id", "run-0000beef",
        "--apply",
        "--out", str(tmp_path / "purge.json"),
    ])
    assert code == 3  # sin --authorized-by ni siquiera llega a mirar el estado


def test_una_ejecucion_exportada_con_autorizacion_si_puede_purgarse(tmp_path: Path) -> None:
    _run_dir(tmp_path / "work", state="exported")
    code = purge([
        "--work-root", str(tmp_path / "work"),
        "--run-id", "run-0000beef",
        "--apply",
        "--authorized-by", "tester",
        "--reason", "ejecución ya entregada",
        "--out", str(tmp_path / "purge.json"),
    ])
    assert code == 0
    assert _log(tmp_path)["run_state"] == "exported"


def test_la_comprobacion_de_solapamiento_acepta_raices_distintas(tmp_path: Path) -> None:
    work = (tmp_path / "work").resolve()
    source = (tmp_path / "corpus").resolve()
    assert check_roots(work, source, None) is None


def test_los_candidatos_no_incluyen_directorios(tmp_path: Path) -> None:
    workdir = _run_dir(tmp_path / "work")
    removable, skipped = collect_candidates(workdir)
    assert all(path.is_file() for path in removable)
    assert "notes.txt" in {path.name for path in removable}
    assert skipped == []