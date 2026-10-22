# Caso revisión ampliada (fases 121-130)

Estado: **herramientas probadas sobre fixtures; ejecución real ausente**.
La evidencia está en `reports/optional/review.json` y en la suite
(`tests/test_render_bilingual.py`, `test_prioritize_findings.py`,
`test_decision_schema.py`, `test_approval_freshness.py`,
`test_group_inconsistencies.py`, `test_detect_residual_language.py`,
`test_eval_back_translation.py`, `test_report_accessibility.py`,
`test_log_redaction.py`, `test_gate_review.py`).

## 1. Qué se ha ejecutado sobre material real

Una sola vez, y con resultado negativo:

| Herramienta | Corrida | Resultado |
|---|---|---|
| `detect_residual_language.py` | `reports/pilot/` | 273 falsos positivos sobre prosa española; motivó reescribir la heurística (`CHANGELOG.md` 0.2.0) |
| `render_bilingual.py` | — | sin ejecución registrada |
| `prioritize_findings.py` | — | sin ejecución registrada |
| `group_inconsistencies.py` | — | sin ejecución registrada |
| `eval_back_translation.py` | — | solo modo `dry-run`, con 6 casos de `tests/fixtures/back_translation/` |
| `gate_review.py --mode expanded` | — | sin ejecución registrada |

Ningún informe de este módulo existe en `reports/` con nombre propio, y
ningún manifiesto real tiene `decisions[]` ni `approvals[]`:
`reports/pilot/manifest.json` y `reports/beta/manifest.json` no contienen esos
campos. Por eso `gate_review.py --mode expanded` habría fallado con los códigos
2 y 3 sobre cualquier manifiesto real del repositorio.

## 2. Corpus que activa el módulo

| Campo | Valor |
|---|---|
| Ruta sintética | `tests/fixtures/bilingual/` (1 documento, 2 segmentos, hashes fabricated) — `6ea4885337fef176` |
| Ruta sintética | `tests/fixtures/back_translation/` (6 casos) — `5ea7061dcb6da256` |
| Ruta sintética | `tests/fixtures/review/` (3 manifiestos) — `dc7b8bc2bb167790` |
| Corpus real que **no** activa el módulo | `tests/fixtures/pilot/`, 9 documentos — `ff6bfd76bc296061` |

`tests/fixtures/review/` lo consume `tests/test_reviewer_protocol.py`, que
pertenece a la fase 115 (módulo de escala), no a este. Se declara aquí para que
el inventario de fixtures no se lea como cobertura de la fase 121-130.

## 3. Estado de la activación

`gate_review.py` exige `--justification` en modo `expanded` y sale con código
7 sin ella. El módulo es **dormiente por defecto**: el modo `basic` es el que
usa el flujo normal, y no lee ningún artefacto de las fases 121-129.

## 4. Qué no afirma este caso

- **No** afirma que la revisión asistida equivalga a una revisión humana. El
  gate exige `decisions[]` con `kind: approve` y `scope: global`, y la
  casilla 4 de G-CORE sigue sin firma humana
  (`reports/core/PREGUNTAS-PENDIENTES.md` §3).
- **No** afirma nada sobre la retrotraducción en vivo: el modo `live` exige
  `NOTE_BACK_TRANSLATION_LIVE=1` y queda fuera del repositorio.