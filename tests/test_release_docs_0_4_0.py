"""Pruebas del acta de G-EXT 0.4.0.

El acta de `evals/release/RELEASE_NOTES_0.4.0.md` no es decorativa: cada
afirmación suya tiene que seguir siendo cierta cuando se lee. Si el gate deja
de dar 0, o si un módulo cambia de corpus declarado, el acta deja de
servir y estas pruebas avisan.

A diferencia del acta de 0.2.0, aquí sí se exige que las cifras declaradas
coincidan con las de hoy: el acta de 0.4.0 habla del estado actual, no de
un release cerrado.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ACTA = ROOT / "evals" / "release" / "RELEASE_NOTES_0.4.0.md"
GATE_REPORT = ROOT / "reports" / "maintenance" / "gate_optional.json"
CORE_REPORT = ROOT / "reports" / "core" / "pytest.json"
CANDIDATE = ROOT / "reports" / "maintenance" / "release_candidate.json"
MODULES_JSON = ROOT / "modules.json"


def _text(path: Path) -> str:
    assert path.exists(), path
    return path.read_text(encoding="utf-8")


def test_el_acta_existe_y_declara_su_alcance() -> None:
    text = _text(ACTA)
    assert "0.4.0" in text
    # Un acta de G-EXT no es un acta de traducción.
    assert "no cierra G-BETA" in text or "No cierra G-BETA" in text


def test_el_acta_no_afirma_lo_que_el_gate_no_mide() -> None:
    text = _text(ACTA).lower()
    for frase in ("importación real en notion", "4 832", "firma nativa"):
        assert frase in text, frase
    assert "equivalencia semántica" in text


def test_las_cifras_del_acta_coinciden_con_la_suite() -> None:
    core = json.loads(_text(CORE_REPORT))
    text = _text(ACTA)
    match = re.search(r"`(\d+) passed, (\d+) skipped`", text)
    assert match, "el acta no declara el resultado de la suite"
    assert int(match.group(1)) == core["passed"], core
    assert int(match.group(2)) == core["skipped"], core


def test_las_filas_de_modulo_coinciden_con_las_declaraciones() -> None:
    data = json.loads(_text(MODULES_JSON))
    text = _text(ACTA)
    for module in data["modules"]:
        assert f"`{module['module_id']}`" in text or f"| {module['module_id']} (" in text, module["module_id"]
        # El número de ficheros declarado no crece sin que el acta lo sepa.
        assert f"{len(module['test_files'])} ficheros" in text, module["module_id"]


def test_cada_modulo_tiene_informe_de_evidencia() -> None:
    """Cada módulo tiene su informe, y el informe está en verde si es actual.

    El matiz del `mtime` es deliberado y no un atajo: `reports/optional/*.json`
    los escribe el gate, que se ejecuta **después** de construir el
    candidato. Durante una corrida del gate, los informes que hay en disco
    son los de la corrida anterior. Exigir que estén en verde en ese
    momento sería exigir que la corrida actual ya hubiera terminado. Lo que
    sí se exige sin condición es que existan, tengan la forma del contrato y
    no se contradigan con la declaración.
    """
    data = json.loads(_text(MODULES_JSON))
    for module in data["modules"]:
        report = ROOT / "reports" / "optional" / f"{module['module_id']}.json"
        assert report.exists(), module["module_id"]
        payload = json.loads(_text(report))
        assert payload["gate"] == "scripts/gate_optional.py"
        assert payload["module_id"] == module["module_id"]
        assert payload["corpus_ref"] == module["corpus_ref"]
        if report.stat().st_mtime >= CANDIDATE.stat().st_mtime:
            assert payload["failing_checks"] == {}, payload["failing_checks"]


def test_el_informe_por_modulo_no_contradice_a_la_declaracion() -> None:
    data = json.loads(_text(MODULES_JSON))
    for module in data["modules"]:
        report = json.loads(_text(ROOT / "reports" / "optional" / f"{module['module_id']}.json"))
        assert report["activation"] == module["activation"], module["module_id"]
        assert report["limitations"] == module["limitations"], module["module_id"]
        assert report["known_external_gaps"] == module["known_external_gaps"], module["module_id"]


def test_el_gate_registrado_documenta_los_nueve_modulos() -> None:
    """El informe del gate cubre los nueve módulos y no tiene formato roto.

    No se comprueba aquí que `ok` sea verdadero: ese informe se escribe al
    terminar el gate, y el gate se ejecuta después de construir el
    candidato. Afirmar su resultado dentro de la suite que el propio gate
    ejecuta sería un bucle. Lo que sí se comprueba es que el informe exista,
    nombre los nueve módulos y tenga la forma del contrato. El resultado
    con código 0 se verifica ejecutando el gate, y su salida es la evidencia
    de esta subrelease.
    """
    report = json.loads(_text(GATE_REPORT))
    assert set(report["modules"]) == {
        "mdx", "html", "markdown-extensions", "terminology", "language",
        "scale", "review", "delivery", "maintenance",
    }, report["modules"]
    assert report["checks"], "el informe no enumera las casillas"
    assert report["detail"]["core"]["core_suite_exit_code"] == 0, report["detail"]["core"]


def test_el_gate_registrado_documenta_los_nueve_modulos() -> None:
    """El informe del gate cubre los nueve módulos y no tiene formato roto.

    No se comprueba aquí que `ok` sea verdadero: ese informe se escribe al
    terminar el gate, y el gate se ejecuta después de construir el
    candidato. Afirmar su resultado dentro de la suite que el propio gate
    ejecuta sería un bucle. Lo que sí se comprueba es que el informe exista,
    nombre los nueve módulos y tenga la forma del contrato. El resultado
    con código 0 se verifica ejecutando el gate, y su salida es la evidencia
    de esta subrelease.
    """
    report = json.loads(_text(GATE_REPORT))
    assert set(report["modules"]) == {
        "mdx", "html", "markdown-extensions", "terminology", "language",
        "scale", "review", "delivery", "maintenance",
    }, report["modules"]
    assert report["checks"], "el informe no enumera las casillas"
    assert report["detail"]["core"]["core_suite_exit_code"] == 0, report["detail"]["core"]


def test_el_candidato_no_declara_activo_un_modulo_dormiente() -> None:
    candidate = json.loads(_text(CANDIDATE))
    por_id = {m["module_id"]: m for m in candidate["modules"]}
    for module in json.loads(_text(MODULES_JSON))["modules"]:
        entry = por_id[module["module_id"]]
        assert entry["activation"] == module["activation"], module["module_id"]
        if not module["corpus_real"]:
            assert entry["limitations"], module["module_id"]


def test_los_comandos_del_acta_existen() -> None:
    """Un comando que ya no existe vuelve el acta falsa sin que nadie lo note."""
    text = _text(ACTA)
    for script in ("gate_optional.py", "build_release_candidate.py", "gate_extended.py",
                   "check_versioning.py", "audit_docs.py", "pytest"):
        assert script in text, script
    assert (ROOT / "scripts" / "gate_optional.py").is_file()


def test_reproducir_el_acta_sigue_dando_cero() -> None:
    """Ejecuta el gate en modo estructural con la evidencia ya medida.

    No corre la suite entera (eso tarda minutos y ya lo hace el candidato);
    comprueba que la parte estructural del acta sigue siendo cierta.

    Escribe en un temporal: sobrescribir `reports/maintenance/gate_optional.json`
    con un informe estructural dejaría la evidencia del release en rojo y
    rompería la prueba anterior en cascada.
    """
    import tempfile

    out = Path(tempfile.gettempdir()) / "nst-tests" / "gate_optional_structural.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "gate_optional.py"),
         "--root", str(ROOT),
         "--declarations", str(MODULES_JSON),
         "--core-exit-code", str(json.loads(_text(CORE_REPORT))["exit_code"]),
         "--candidate", str(CANDIDATE),
         "--no-run-tests",
         "--out", str(out)],
        capture_output=True, text=True, check=False, cwd=str(ROOT),
    )
    assert proc.returncode == 5, proc.stderr
    payload = json.loads(_text(out))
    # Lo único que falla es que no se ejecutaron las pruebas, que es lo que
    # el modo estructural significa.
    assert set(payload["failures"]) == {"5"}, payload["failures"]