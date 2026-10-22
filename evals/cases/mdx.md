# Caso MDX (fases 061-070)

Estado: **material autorizado y ejecutado**. La evidencia de ejecución está en
`reports/optional/mdx.json` y en la suite (`tests/test_mdx_*.py`, 10 ficheros).

Este caso existe para el criterio 1 de G-EXT: un módulo opcional solo se
enciende si un corpus concreto justifica por qué ese módulo debe estar
encendido en este proyecto. MDX se enciende porque el corpus piloto **real**
contiene componentes MDX dentro de `.md`.

## 1. Corpus que justifica la activación

| Campo | Valor |
|---|---|
| Ruta | `tests/fixtures/pilot/` |
| Naturaleza | material real autorizado, recortado a 4096 B por archivo |
| Archivos | 9 |
| Bytes | 36 864 |
| Árbol (SHA-256 de rutas y hashes por archivo, prefijo) | `ff6bfd76bc296061` |
| Caso de origen | `evals/cases/pilot.md` |

Construcciones observadas en ese corpus:

| Construcción | Dónde | Qué obliga |
|---|---|---|
| `<Info title="…">` | `APIs/OpenRouter/04 - Capacidades Avanzadas Reasoning, Tool Calling.md` | componente del contrato §2 |
| `<CodeGroup>` | mismo archivo | componente añadido al contrato §2 por este caso |
| `<div>` y `<img>` | `APIs/OpenRouter/01 - …` | motivates el módulo de HTML embebido, no este |

Comprobación ejecutada sobre el corpus con `mdx.enabled: true`:
9 archivos clasificados, 0 bloqueantes
(`python3 scripts/prepare.py --inventory … --profile … --out …`).

## 2. Corpus sintético de contrato

| Campo | Valor |
|---|---|
| Ruta | `tests/fixtures/mdx/` |
| Naturaleza | **sintético**, escrito para las pruebas del módulo |
| Archivos | 4 |
| Bytes | 2 158 |
| Árbol | `c93eef7878393c49` |

Cubre `Info`, `Note`, `Warning`, `Tabs`/`TabItem` y `Card`/`CardGroup`. No
cubre `CodeGroup` ni `TabPanel`: esos dos componentes están justificados por
el corpus real del §1, no por este.

## 3. Qué no justifica este caso

- **No** afirma que el soporte MDX sea general: el contrato §4 enumera lo que
  bloquea y ese enumerado es el límite real.
- **No** hay ningún archivo `.mdx` real en el repositorio. El corpus usa
  componentes MDX dentro de `.md`, que es exactamente el caso que `prepare.py`
  trata con `flag_mdx: false`.
- **No** se ha ejecutado una traducción del corpus piloto con el módulo MDX
  activo; la evidencia es de clasificación y de contrato, no de salida
  traducida.

## 4. Regresión y desactivación

- Regresión del núcleo: `python3 -m pytest tests -q`.
- Desactivación byte a byte:
  `tests/test_optional_deactivation.py::test_desactivacion_mdx`.
- Caso negativo de activación:
  `tests/test_optional_activation.py::test_mdx_no_acepta_activacion_sin_corpus`.