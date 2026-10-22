<!-- Acta del release ampliado 0.2.0 · generado por scripts/build_release_candidate.py -->

# Release ampliado 0.2.0 — mantenimiento y activación de módulos

Este documento es el acta de la fase 150. Enumera, módulo por módulo y
comprobación por comprobación, qué se verificó y qué no. Lo que aquí no
aparece como verificado, no está verificado.

## 1. Versión, contratos y esquemas

| Elemento | Valor | Fuente de verdad |
|---|---|---|
| Skill | 0.2.0 | `release_contract.json`, `CHANGELOG.md`, `RELEASE.md` |
| Contratos | `translate/v1` (C-IN, C-PROFILE, C-GLOSSARY, C-SEGMENT, C-RUN, C-ANCHORS, C-OUT) | `release_contract.json` |
| Manifiesto | `translate/v1`, ahora **obligatorio** | `schemas/manifest.schema.json` (x-schema-version 1.1.0) |
| Parser | `markdown-it-py` 3.0.0 | `references/markdown-contract.md` §2 |
| Prompt | 1.0.0 | `release_contract.json` |
| Cambio incompatible | `manifest-version-required` | migración `scripts/migrate_manifest.py` |

Es un **minor**: añade capacidades de mantenimiento y activa módulos que
antes no formaban parte de la entrega. No cambia ningún valor por defecto
del núcleo.

## 2. Módulos activos y resultado real de su gate

| Módulo | Fases | Gate | Código | Estado |
|---|---|---|---|---|
| `core` | 001–060 | `python3 -m pytest tests/ -q` (sin las pruebas del propio release) | 0 | activo |
| `mdx` | 061–070 | `tests/test_mdx_gate.py` | 0 | activo |
| `html` | 071–080 | `tests/test_html_gate.py`, `tests/test_html_release_gate.py` | 0 | activo |
| `markdown-extensions` | 081–090 | `tests/test_extension_combinations.py` | 0 | activo |
| `terminology` | 091–100 | perfiles, precedencia y procedencia de términos | 0 | activo |
| `language` | 101–110 | matriz de idioma y evaluación fr→es | 0 | activo |
| `scale` | 111–120 | gate de escala y reserva en serie | 0 | activo |
| `review` | 121–130 | gate de revisión | 0 | activo |
| `delivery` | 131–140 | gate de entrega | 0 | activo |
| `maintenance` | 141–150 | pruebas de las ocho fases de mantenimiento | 0 | activo |

Gate extendido (`scripts/gate_extended.py`): **código 0**, las nueve
comprobaciones internas en verde. Informe: `reports/maintenance/gate_extended.json`.

## 3. Evidencia

| Comprobación | Resultado | Informe |
|---|---|---|
| Suite completa en macOS (Python 3.9.6) | 934 pruebas pasan, 2 omitidas | salida de `python3 -m pytest tests/ -q` |
| Suite completa en Linux (Python 3.12.15) | 936 pasan, 0 fallan | `reports/maintenance/external/linux-cpython-3.12.json` |
| Regresión permanente | 22 fallos conocidos, 22 casos, 0 huecos, reproducidos con pytest | `reports/maintenance/regression.json` |
| Versionado | coherente: 12 esquemas, 58 referencias | `reports/maintenance/versioning.json` |
| Comparación de parser | 9 documentos, rangos, slugs y recuentos idénticos | `reports/maintenance/parser_comparison.json` |
| Variación entre modelos | 1 ejecución real registrada; falta la segunda | `reports/maintenance/model_runs/run-0000d3mo.json` |
| Auditoría documental | limpia: 71 documentos, 58 referencias, 5 reglas | `reports/maintenance/docs_audit.json` |
| Portabilidad | macOS y Linux `verified`, Windows `design_only` | `reports/maintenance/portability_matrix.json` |
| Retención | política y script presentes, pruebas en verde | `tests/test_purge_workdir.py` |

Huellas de los artefactos del candidato (SHA-256, 12 primeros caracteres):

```text
release_contract.json                        7395c0d8814a
evals/regression/registry.json               d075dc900691
reports/maintenance/regression.json          779938e2bbe6
reports/maintenance/versioning.json          a711366e4573
reports/maintenance/parser_comparison.json   66cb70a8b21a
reports/maintenance/model_runs/run-0000d3mo.json a3ed22c4fe09
reports/maintenance/docs_audit.json          6688b516cb2b
reports/maintenance/platform_probe.json      07899676eb9d
reports/maintenance/portability_matrix.json  ff8462591394
```

Lista completa y actualizada: `reports/maintenance/release_candidate.json`.

Las dos sumas no coinciden porque las 2 pruebas omitidas en macOS sí se
ejecutan en Linux: requieren un sistema de archivos sensible a mayúsculas o
que normalice Unicode, y en macOS el caso se salta. El total de pruebas es
el mismo.

## 4. Límites aceptados

| Límite | Qué significa |
|---|---|
| Módulos opcionales desactivados por defecto | ningún módulo se activa solo; activar es una decisión de perfil |
| Escala medida sobre una muestra | 30 documentos en CI, no el corpus de 4832 archivos |
| Retención declarada, no automática | 30 días de workdir, pero la purga la decide una persona |
| Registro de regresión sintético | los casos son escritos a propósito; el corpus real se revisa en ejecución |
| Comparación de parser sobre 9 documentos | corpus piloto, no el corpus completo |

## 5. Huecos externos abiertos

Ninguno de estos bloquea el release local. Todos bloquean afirmaciones.

| Hueco | Fases | Responsable | Procedimiento | Bloquea |
|---|---|---|---|---|
| `notion_import_evidence` | 131–133 | usuario | importar una muestra con el checklist y registrar la evidencia | afirmación remota |
| `second_delivery_destination` | 139 | usuario | ejecutar una entrega real en un destino elegido | afirmación remota |
| `native_reviewer_signature` | 103, 109, 110 | revisor humano | revisar la muestra bilingüe y registrar la decisión | firma humana |
| `live_back_translation` | 127 | usuario | ejecutar la retrotraducción en modo live | firma humana |
| `second_model_run` | 145 | usuario | traducir el piloto con otro modelo y registrar la ejecución | firma humana |
| `windows_execution` | 147 | mantenimiento | ejecutar la suite en Windows y adjuntar la sonda | firma humana |

## 6. Lo que este release NO afirma

- No afirma equivalencia semántica de la traducción.
- No afirma que nada se haya importado en Notion ni en ningún destino.
- No afirma que la salida del modelo sea reproducible entre ejecuciones.
- No afirma portabilidad en Windows: esa fila está en `design_only`.
- No afirma cobertura del corpus remoto: la fidelidad se evalúa sobre los
  Markdown recibidos.
- No afirma que el corpus completo de 4832 archivos se haya procesado.

## 7. Política de mantenimiento

| Cambio | Qué hay que hacer antes |
|---|---|
| Versión del parser | `scripts/compare_parser.py` sobre el corpus piloto; promoción solo si rangos, slugs y recuentos son idénticos (144) |
| Glosario | `invalidate_cache.py`; las aprobaciones existentes pierden vigencia (119, 124) |
| Esquema | actualizar `release_contract.json` y `CHANGELOG.md`; `check_versioning.py` lo bloquea si no (142) |
| Contrato de manifiesto | migración con `scripts/migrate_manifest.py`; nunca convierte revisiones antiguas en aprobaciones (143) |
| Modelo o prompt | nueva versión en `release_contract.json`; las ejecuciones dejan de ser comparables entre sí (145) |
| Referencia documental | marca de versión + auditoría documental en verde (146) |
| Sistema operativo nuevo | sonda y ejecución de la suite; sin evidencia, la fila queda `design_only` (147) |

## 8. Retención y limpieza

`source_root` y `output_root` no se borran nunca. `reports/` tampoco. Los
`work_root` se purgan a 30 días con autorización explícita y con log
(`references/workdir-retention.md`). El texto traducido no se versiona: solo
los metadatos.

## 9. Procedimiento de aviso de regresión

Cuando alguien reporte un fallo:

1. Reproducirlo en el corpus piloto.
2. Añadir el caso al registro: fixture con par positivo y negativo,
   detector, procedencia y nodeids.
3. Ejecutar `python3 scripts/regression_gate.py --reproduce`.
4. Si el fallo toca un contrato, actualizar el `release_contract.json` y el
   `CHANGELOG.md` antes de tocar código.

Un fallo sin caso en el registro es un fallo que puede volver.

## 10. Firma

**Release local aprobado.** No es un release production-ready: seis huecos
externos siguen abiertos y todos están listados arriba con su responsable.
Este acta no sustituye la aprobación de una persona, solo registra qué se
ejecutó y qué salió.

Fecha de generación: 2026-10-20 · candidato `0.2.0` · skill `0.2.0`