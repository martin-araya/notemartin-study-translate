# Caso mantenimiento (fases 141-150)

Estado: **corpus permanente de regresión ejecutado**. La evidencia está en
`reports/maintenance/` y en la suite (`tests/test_regression_registry.py`,
`test_regression_cases.py`, `test_versioning_policy.py`,
`test_manifest_migration.py`, `test_compare_parser.py`,
`test_model_variation.py`, `test_audit_docs.py`, `test_portability.py`,
`test_purge_workdir.py`, `test_release_candidate.py`).

Este módulo no es opcional en el sentido del resto: sus herramientas comprueban
el release. Figura en `modules.json` porque su gate también tiene que cumplir
las cuatro casillas de G-EXT.

## 1. Corpus

| Campo | Valor |
|---|---|
| Ruta | `evals/regression/` |
| Archivos | 2 (`registry.json`, `PROVENANCE.md`) |
| Bytes | 30 904 |
| Árbol (prefijo) | `14145847f69f3ab3` |
| Casos registrados | 22 fallos conocidos, 22 pares positivo/negativo, 0 huecos |
| Procedencia | **sintética**: los hashes de los fixtures no corresponden a ningún artefacto real (`evals/regression/PROVENANCE.md`) |

Comando de reproducción:
`python3 scripts/regression_gate.py --out reports/maintenance/regression.json --reproduce`.

## 2. Estado de la activación

Siempre activo: `regression_gate.py`, `check_versioning.py`, `audit_docs.py`,
`build_release_candidate.py` y `gate_extended.py` son las herramientas que
comprueban el release. No se pueden apagar.

Lo que sí es opcional son sus **delegaciones**: `regression_detectors.py`
delega en detectores de otros módulos (`compare_delivery`,
`translation_cache`, `validate_zip_package`) para no reimplementarlos. Esa
delegación está declarada en `modules.json` (`core_delegations`) y solo ocurre
al correr el gate de release, nunca durante una traducción.

## 3. Qué no afirma este caso

- **No** afirma que Windows funcione: esa fila está en `design_only`
  (`reports/maintenance/portability_matrix.json`).
- **No** afirma variación entre modelos: hay una sola ejecución registrada
  (`reports/maintenance/model_runs/run-0000d3mo.json`) y comparar exige dos.
- **No** afirma que la regresión sea de Translation Quality: es de
  comportamiento determinista de las herramientas.