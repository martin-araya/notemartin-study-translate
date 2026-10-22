<!-- version: 1.0.0 -->

# Política de revisores humanos (fase 109)

Esta política fija **quién firma qué** en una ejecución de la
skill `notemartin-study-translate`, y **qué distingue** esa firma
de una revisión asistida o de una autocertificación. Convive con
`references/operation.md` (privacidad), con
`references/locale-policy.md` (variante del español) y con
`references/source-language-policy-fr.md` (par fr→es), más las que
se deriven para otros pares.

> La fase 109 no se cierra con `✅` hasta que un nativo firme al
> menos un par distinto del `en → es` del núcleo 0.1.0. Mientras
> no haya firma, la fila 109 lleva `✅ ⚠` y los `human_reviewer`
> del manifiesto se quedan en `null`.

## 1. Tabla de firmantes esperados

Cada par documentado en el plan o en
`reports/language_matrix.json` debería tener un firmante o un
`null` explícito.

| Par | Variante | Firmante nativo | Estado |
|---|---|---|---|
| `en → es` (núcleo) | `es` | **(núcleo 0.1.0 ya cubierto)** | ✅ |
| `fr → es` | `es` | **(pendiente, fase 103 ⚠)** | ⚠ |
| `en → es-ES` | `es-ES` | **(pendiente)** | ⚠ |
| `en → es-MX` | `es-MX` | **(pendiente)** | ⚠ |
| `en → es-AR` | `es-AR` | **(pendiente)** | ⚠ |
| `ar → es` | `es` | **(pendiente)** | ⚠ |
| otros pares planificados | varias | pendiente del lote 110 | — |

> Mientras la columna « Firmante nativo » esté vacía, el par
> correspondiente aparece con `evaluation_kind: assisted` y
> `reviewer_status: assisted_only_pending_human`. Sustituir
> el marcador por un nombre real es lo único que promueve un par
> a `human_approved`.

## 2. Cómo se firma

La firma humana se materializa rellenando entradas en el campo
`reviewers` del `manifest.json` (extensión de la fase 109). Cada
entrada lleva:

- `pair`: pares exactos cubiertos (p. ej. `en → es-AR`).
- `name`: identificador del firmante (alias, handle, o nombre
  declarado por el usuario). Se prefiere un alias a un nombre
  completo para minimizar datos personales.
- `kind`: `human` (firmado) o `assisted` (registrado pero no
  firmado).
- `signed_at`: timestamp ISO 8601 de la firma.
- `scope`: `global` o lista de rutas firmadas explícitamente.
- `notes`: notas del firmante, opcionales.

El par pasa a `evaluation_kind: human_approved` cuando al menos
un firmante `kind: human` cubre el par en `scope: global` o
sobre todo el alcance de la ejecución.

## 3. Qué distingue una firma humana real

- **No** basta con un campo `name` en el manifiesto. La rúbrica
  exige:
  - Revisión manual sobre múltiples segmentos del par.
  - Coherencia con el glosario congelado.
  - Aprobación explícita: las notas del firmante declaran la
    conformidad.
- La firma se entrega como un documento firmado (en persona, o
  adjuntando un correo verificado) cuyo hash se incorpora al
  `manifest.json` con `signature_hash`. Mientras la skill no
  automatice esa operación, **cada firma es un proceso manual
  fuera del script**.
- Un firmante humano puede rechazar el corpus. En ese caso la
  fila del manifiesto queda `rejected_by_human`, y el par no se
  publica hasta una nueva auditoría.

## 4. Qué **NO** es firma humana

- **Revisión asistida** (`evaluation_kind: assisted`): la ejecuta
  el modelo aplicando la rúbrica `evals/rubric.md`. No demuestra
  conformidad humana.
- **Autorevisión del traductor**: el propio agente emite y firma
  su traducción. Sin valor como revisión humana.
- **Validación determinista**: los checks
  `scripts/validate.py`, `scripts/check_distribution.py` y
  `scripts/check_cache_isolation.py` son correctos sobre la
  forma, **no** sobre el significado.
- **Retrotraducción, similitud de embeddings, longitud**: señales
  auxiliares que **no** se usan como firma.

## 5. Procedimiento de rectificación

Cuando un firmante observa un fallo:

1. Abre una entrada en `reports/issues.json` con
   `severity ∈ {error, warning, info}` y el `segment_id` afectado.
2. Lo etiqueta con `rejection_source: human_reviewer`.
3. El siguiente lote corrige el segmento y vuelve a ejecutar la
   comprobación.
4. La entrada queda en `manifest.json.reviewers[].notes` y se
   publica en `reports/fr-es-pilot/summary.md` o equivalente.

## 6. Lo que esta política **NO** hace

- No sustituye la verificación humana: solo registra que ocurrió.
- No publica el nombre del firmante fuera del manifiesto; el
  pipeline nunca escribe el `name` en outputs que vayan al
  importador (Notion, navegador, etc.).
- No impide que un mismo segmento sea revisado por dos firmantes
  distintos; en ese caso gana el de `kind: human` con
  `signed_at` más reciente, salvo que se declare
  `conflicting_reviewers: true`.
- No firma equivalencia semántica absoluta; firma conformidad
  con la rúbrica definida para el par.
