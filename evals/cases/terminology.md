# Caso terminología (fases 091-100)

Estado: **material sintético declarado**. La evidencia está en
`reports/optional/terminology.json` y en la suite (`tests/test_glossary_*.py`,
`test_term_profiles.py`, `test_term_precedence.py`, `test_term_provenance.py`,
`test_term_drift.py`, `test_term_report.py`: 55 pruebas en 10 ficheros).

## 1. Qué hay hoy en los glosarios reales

| Glosario | Ruta | Dominios presentes | Perfiles de dominio activados |
|---|---|---|---|
| Piloto v2 | `reports/pilot/glossary.json` | `api`, `network`, `database`, `ai`, `ui` | ninguno de los cinco perfiles de 091-095 |
| Beta | `reports/beta/glossary.json` | `angular` (dominio propio) | ninguno |

Los perfiles `database`, `network`, `frontend`, `systems` y `ml_ai` de
`references/term-profiles.md` **no están activos en ningún glosario real**:
los términos que contienen (`schema`, `instance`, `transaction`, `socket`,
`thread`, `training`, …) solo existen en los fixtures.

Hay dos hechos que este caso deja escritos porque son la diferencia entre un
perfil y una copia:

1. El corpus Beta sí tiene material de frontend (`angular/`, 1 492
   documentos), pero su glosario usa el dominio `angular`, no `frontend`. El
   perfil existe y el corpus existe: no están unidos.
2. El único material de ML del corpus (`oracle/resúmenes/`) ya está en
   español y sale como `already_target`: no se traduce ni se glosa.

## 2. Corpus sintético que activa el módulo

| Campo | Valor |
|---|---|
| Ruta | `tests/fixtures/glossaries/` |
| Naturaleza | **sintético**; las decisiones están firmadas por `example-agent`, no por una persona |
| Archivos | 9 |
| Bytes | 30 352 |
| Árbol (prefijo) | `c0b8a140c5f6164b` |

| Fichero | SHA-256 (prefijo) | Para qué |
|---|---|---|
| `databases.json` | `7c48c9394fc75452` | perfil 091 |
| `networks.json` | `cb46bb1c0884f835` | perfil 092 |
| `frontend.json` | `67de55336b8b9de0` | perfil 093 |
| `systems.json` | `891b8d32fe5ff6d5` | perfil 094 |
| `ml_ai.json` | `d7dc5131d28da1c3` | perfil 095 |
| `with_conflict.json` | `89578dc129670490` | fase 097, conflictos entre dominios |
| `with_provenance.json` | `c7a9ebee4ec7db42` | fase 096, procedencia |
| `drift_old.json` / `drift_new.json` | `fe53ee5ea9c043cb` / `8e63870bc5a24b5b` | fase 098, deriva entre versiones |

## 3. Estado de la activación

La activación de un perfil de dominio se declara en
`schemas/term_profile.schema.json` y en el bloque `terminology` del perfil, que
exige `corpus_ref` y `justification`. Con los datos de §1, la justificación
honesta de cualquier perfil hoy sería «no hay corpus real»: por eso los cinco
perfiles quedan **dormantes** y este caso se registra con
`corpus_real: false`.

## 4. Qué no afirma este caso

- **No** afirma que los cinco dominios estén soportados para traducir
  documentación real. Afirma que el machinery de decisión, precedencia,
  procedencia y deriva está probado sobre fixtures declarados.
- **No** afirma equivalencia terminológica: las decisiones las firma una
  persona y el decision log real sigue en
  `reports/core/PREGUNTAS-PENDIENTES.md` §1 con 11 términos sin cerrar.