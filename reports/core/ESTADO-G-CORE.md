RUN=run-7fbd5e24 · ESTADO: NO APROBADO · MEDIDO: 2026-10-22

Este documento sustituye las cifras de `summary.md` §5 y de
`PLAN_PENDIENTE.md` §1, que quedaron desfasadas tras el lote 0001. Todas
las cifras están medidas sobre los artefactos reales de
`/Users/martin/Desktop/projects/notemartin-beta/work/run-beta-001`.

## 1. Estado del gate

| Gate | Casillas | Estado |
|---|---|---|
| G-PILOT (030) | 4/4 | ✅ |
| G-BETA (050) | 0/4 | ❌ sin marcar |
| G-CORE (060) | 0/5 | ❌ sin marcar |

`roadmap.md` §8 no se ha modificado.

## 2. Cifras medidas hoy

| Métrica | Valor |
|---|---|
| Documentos en el alcance autorizado | 2 682 Markdown + 66 recursos |
| Segmentos traducibles (denominador del gate) | **44 784** |
| Entradas de traducción en disco | **167** |
| Documentos en `prepared` | 2 606 |
| Documentos en `deterministic_pass` | **76** |
| Documentos aprobados / exportados | 0 / 0 |
| `integrity_ok` | `false` (`pending: 2 682`) |
| Registros con `state` contradictorio | **0** (eran 2 608) |
| Hash de árbol de la fuente | `283c5a07…` — coincide con `evals/cases/beta.md` |

Pendiente real: **44 617 segmentos traducibles** (44 784 − 167), en
6 825 paquetes y ≈7,5 M caracteres. Medido con
`select_lote.py --order`:

| Directorio | Paquetes pendientes | Caracteres | Documentos |
|---|---|---|---|
| `tailwindcss` | 3 | 1 941 | 74 |
| `oracle` | 477 | 622 790 | 17 |
| `angular` | 3 088 | 3 115 055 | 1 492 |
| `nextjs` | 3 257 | 3 813 447 | 908 |

`tailwindcss` está prácticamente cerrado: el lote 0002 lo dejó en 3
paquetes pendientes frente a los 19 de ayer.

## 3. Lo que cambió en las herramientas

Cinco defectos de instrumentación, todos con prueba que falla antes del
arranque. Detalle en `CHANGELOG.md` 0.3.0.

1. **`advance_state.py` afirmaba revisión y aprobación sin ninguna.**
   `semantic_pass` y `approved` solo exigían traducción en disco. Ahora
   exigen `--review` con cobertura medida contra `--segments`, y `approved`
   exige además firma humana con `scope` real.
2. **`repair_state_field.py` solo reparaba una divergencia.** Dejó pasar
   2 608 registros con `state: translated` y `current_state: prepared`.
   Ahora degrada en el sentido inverso, y `check_integrity.py` no da
   `integrity_ok` con registros contradictorios.
3. **`export.py` nunca comparó la estructura de lo que entregaba.**
   Validaba el padre del directorio del run. Ahora valida el árbol final
   con `--require-assembled` y no promueve si difiere.
4. **`check_structure` se saltaba los documentos que la traducción
   toca.** De 2 682 documentos comparaba **4**. Ahora alcanza 2 427.
5. **El agregado por archivo contradecía a sus segmentos.** Lo recalcula
   `resolve_dispositions.py` después de aplicar.

## 4. Evidencia de esta sesión

| Artefacto | Qué prueba |
|---|---|
| `reports/core/estructura-antes-despues.json` | Cobertura del chequeo de estructura: 4 → 2 427 documentos |
| `reports/core/puertas-estado.json` | Códigos de salida reales de las puertas nuevas sobre la corrida |
| `reports/core/lote-0002.json` | Lote 0002: 16/16 paquetes, 37/37 segmentos, 0 hallazgos |
| `reports/core/pytest.txt` | 1 183 pruebas verdes, 2 omitidas, 0 fallos |
| `reports/core/versioning.json`, `distribution.json` | Paquete coherente con la 0.3.0 |
| `work/.../manifest.json.bak-pre-h4` | Manifiesto antes de la reparación de estados |
| `work/.../validate-lote-0002.json` | 46 documentos comparados firma a firma, 0 diferencias |

## 5. Lo que este documento no afirma

- **No** afirma que G-CORE ni G-BETA estén cerca. 167 de 44 784
  segmentos es el 0,37 %.
- **No** afirma equivalencia semántica. La revisión asistida no se ha
  ejecutado sobre este lote, y la casilla 4 de G-CORE exige además una
  firma humana que no existe.
- **No** afirma verificación en Notion: `remote_status: no_verificado`.
- **No** afirma cobertura del sitio remoto: solo de los 2 682 Markdown
  recibidos (INV-16).
- **No** repara las rutas rotas del scraper: se registran como deuda de
  entrada.

## 6. Lo que queda para cerrar G-CORE

1. Traducir los 44 617 segmentos pendientes, por lotes, sin cruzar
   directorio.
2. Pase de revisión separado por directorio, con `reviewer_role.py`.
3. Correcciones de lo rechazado, repitiendo las comprobaciones de los
   segmentos afectados.
4. **Firma humana** de la revisión, registrada en `manifest.reviewers[]`
   y `manifest.decisions[]`. Sin ella la casilla 4 no se marca.
5. Exportación y gate G-BETA con `validate.py --require-assembled` sobre
   el árbol entregado.
6. Evidencia de recuperación e invalidez incremental, y de protección del
   destino editado.
7. Solo entonces actualizar `roadmap.md` §8.

Ver `reports/beta/PLAN_PENDIENTE.md` para el procedimiento por lote y
`reports/core/PREGUNTAS-PENDIENTES.md` para las decisiones de terminología
que necesitan respuesta del usuario.