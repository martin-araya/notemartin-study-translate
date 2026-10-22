# Caso escala (fases 111-120)

Estado: **corpus real declarado, ejecución real pendiente de autorización**.
La evidencia de lo ejecutado está en `reports/optional/scale.json` y en la
suite (`tests/test_measure_execution.py`, `test_schedule_packets.py`,
`test_worker_protocol.py`, `test_coordinator.py`, `test_reviewer_protocol.py`,
`test_concurrency_policy.py`, `test_serial_fallback.py`,
`test_translation_cache.py`, `test_invalidate_cache.py`, `test_gate_scale.py`:
73 pruebas en 10 ficheros).

## 1. Corpus declarado

| Campo | Valor |
|---|---|
| Ruta | `/Users/martin/Desktop/documentacion` |
| Archivos `.md` | 4 832 |
| Directorios | 25 |
| Bytes | ≈291 MB |
| Fecha de inventario | 2026-10-20 |
| Naturaleza | **material real autorizado** (el mismo del piloto y del corpus Beta) |
| Muestreo de CI | `tests/fixtures/scale/`, 30 archivos, semilla 42, `tests/fixtures/scale/_sample.json` |

El detalle del inventario completo está en `evals/cases/corpus-full.md`.

## 2. Qué se ha ejecutado y qué no

| Comprobación | Estado |
|---|---|
| Medición de ejecución sobre un directorio temporal de 5 archivos | ejecutada, `reports/execution_profile.json` |
| Medición sobre el corpus completo | **no ejecutada**: `reports/execution_profile_full.json` no existe |
| Modo serie sobre `tests/fixtures/scale/` | ejecutada en la suite |
| Modo concurrente sobre material real | **no ejecutada** |
| `gate_scale.py` sobre ejecuciones reales | **no ejecutado**: la prueba fabrica manifiestos sintéticos |
| Caché e invalidación | ejecutadas sobre entradas reales producidas por `translation_cache.py` |

La última fila de la tabla de arriba se corrigió durante este trabajo: antes
`invalidate_cache.py` leía un campo `anchors` que el esquema prohibía y que el
almacén nunca escribía, así que la invalidación transitiva solo podía probarse
con entradas escritas a mano.

## 3. Estado de la activación

El modo serie es el valor por defecto; el concurrente solo se activa por
invocación explícita y con `--allow-single-cpu` cuando la máquina tiene un solo
procesador. El módulo es **dormiente**: `run_concurrent.py`, `worker.py`,
`coordinator.py` y `translation_cache.py` no se invocan desde
`run_end_to_end.py`.

## 4. Qué no afirma este caso

- **No** afirma que el modo concurrente sobre 4 832 archivos conserve la misma
  cobertura que el serie. Esa es la aceptación de la fase 120 y sigue sin
  ejecutarse sobre material real.
- **No** afirma ningún dato de costo ni de tokens: `provider_known: false`,
  `cost_unknown: true` (`schemas/execution_profile.schema.json`).