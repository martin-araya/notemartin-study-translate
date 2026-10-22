# Release — `notemartin-study-translate`

Esta es una **release candidata del núcleo estable** de la skill
`notemartin-study-translate`. No es un lanzamiento 1.0.0 ni una
declaración de producción. La numeración semver queda pendiente
hasta que el usuario la solicite.

## 1. Dialecto soportado

La skill está validada sobre el corpus piloto en
`tests/fixtures/pilot/`, que incluye:

- **CommonMark** base: encabezados, párrafos, listas, citas,
  bloques de código indentados y fenced, enlaces inline, imágenes
  inline y HTML anclado.
- **GitHub Flavored Markdown**: tablas con separadores y fila de
  alineación, listas de tareas, autolinks, tachado.
- **Frontmatter YAML** preservado íntegro por defecto.
- **Bloques Mermaid** preservados como literales (no se traducen
  sus etiquetas salvo activación explícita de la extensión opcional
  fase 085).

Las construcciones fuera de este dialecto se bloquean y se
registran en `reports/issues.json`. El parser utilizado es
`markdown-it-py` versión fijada en `manifest.json`.

## 2. Lo que NO se garantiza

Esta sección enumera las afirmaciones que esta release **no**
sostiene. El usuario y los revisores deben tenerlo presente antes
de presentar la skill como producto terminado.

- **Fidelidad semántica absoluta.** La validación determinista
  verifica integridad estructural y literal, no equivalencia de
  significado. La revisión asistida por modelo no es revisión
  humana ni certificación profesional.
- **Paridad de render en Notion.** El paquete es válido para
  CommonMark + GFM, pero la importación la realiza el usuario y la
  navegación, tablas, anclas y código pueden comportarse distinto en
  Notion. Ver `references/notion-handoff.md`.
- **Inferencia local.** El procesamiento sigue al proveedor del
  agente activo. No se asume ni se promete inferencia local.
- **Cobertura de MDX, HTML embebido, directivas o componentes
  personalizados.** Estas extensiones son módulos opcionales
  (fases 061–080) y quedan desactivadas por defecto.
- **Retrotraducción como prueba.** La retrotraducción, la similitud
  de embeddings y la proporción de longitud pueden ayudar a
  priorizar revisión, pero no demuestran equivalencia semántica por
  sí solas.
- **Reproducibilidad exacta de las respuestas del modelo.** El
  manifiesto registra las claves de procedencia, pero la salida
  textual del modelo puede variar entre ejecuciones.

## 3. Evidencia

- **Changelog completo:** ver `CHANGELOG.md`.
- **Corpus piloto:** 9 archivos en `tests/fixtures/pilot/`.
- **Pruebas:** `pytest` corre 165+ tests (incluyendo los de las
  fases 051–060). Ver el último `RELEASE_NOTES.md` para el conteo
  exacto.
- **Reporte de release:** generado por `scripts/test_release.py`
  con secciones explícitas de pruebas automáticas, revisión
  asistida, revisión humana y Notion no verificado.
- **Distribución:** `scripts/check_distribution.py` verifica el
  paquete antes de cualquier instalación.
- **Procedimiento de operación:** `references/operation.md` cubre
  permisos, secretos, conflictos, recuperación y límite de
  contexto.

## 4. Limitaciones aceptadas

Las limitaciones que no bloquean el gate global se listan en
`reports/issues.json` y se vuelcan en la sección `## Limitaciones
aceptadas` de `RELEASE_NOTES.md`. Cada una declara categoría,
severidad, mensaje, ruta y `segment_id` cuando aplica.

## 5. Lo que sigue

Las fases 061–150 están descritas en el roadmap como catálogo
planificado. **No** son requisitos de esta release 0.1.0. Construir
alguna de ellas requiere un corpus real que justifique la
activación del módulo correspondiente.

### 5.1 Subrelease 0.1.1 — par experimental fr→es (lote 101–105)

Esta subrelease es **experimental** y no forma parte del núcleo
0.1.0. Su alcance:

- Cierra las fases 101, 102, 104 y 105 con artefactos
  verificables.
- Cierra la fase 103 en modalidad **asistida**. La fila 103 del
  roadmap lleva `✅ ⚠` y no se considera estable hasta que un
  nativo en francés firme `manifest.json` con
  `reviewer_status: human_approved`.

Lo que **no** afirma esta subrelease:

- Que la traducción fr→es sea correcta sin auditor humano.
- Que el corpus piloto CC0 sustituya al corpus Nextcloud real
  (la sustitución se levantará cuando se activen las fases
  071–080 con un conversor HTML→MD auditado).
- Que el par esté listo para producción, publicación o
  importación remota.

Para activar el par en una ejecución real, el `profile.json`
debe llevar `mixed_profile.enabled: true` con
`allowed_source_languages: ["en", "fr"]`,
`source_language_policy: references/source-language-policy-fr.md`,
`citations_policy: references/citations-policy.md`, y
`reviewer_status: assisted_only_pending_human`. Sin esos campos,
el lote fr queda inactivo y el núcleo en→es sigue siendo el único
« production-ready ».

### 5.2 Subrelease 0.1.2 — variantes regionales, RTL y matriz (fases 106–110)

Esta subrelease añade tres variantes regionales del español y el
soporte RTL del par `ar → es`. Su alcance:

- Cierra las fases 106, 107 y 108 con artefactos verificables.
- Cierra las fases 109 y 110 con su disclaimer correspondiente:
  los slots de firmantes quedan vacíos (`null` en el manifest) y
  la matriz `reports/language_matrix.json` aún no supera el umbral
  de 3 pares `human_approved`.

Pares disponibles:

| Par | Variante | Firmante humano | Estado |
|---|---|---|---|
| `en → es` | núcleo | núcleo 0.1.0 | `human_approved` |
| `fr → es` | `es` | — | `assisted_only_pending_human` |
| `en → es-ES` | `es-ES` | — | `assisted_only_pending_human` |
| `en → es-MX` | `es-MX` | — | `assisted_only_pending_human` |
| `en → es-AR` | `es-AR` | — | `assisted_only_pending_human` |
| `ar → es` | `es` | — | `assisted_only_pending_human` |

Lo que esta subrelease **no** afirma:

- Que las variantes regionales reflejen el uso nativo real.
- Que el par `ar → es` conserve la dirección del texto fuera del
  importador en cuestión (Notion / navegador).
- Que los coloquialismos cerrados sean exhaustivos; son una
  lista inicial ampliable solo por revisión humana.

Para activar una variante, el `profile.json` debe llevar
`locale.variant` ∈ `{es-ES, es-MX, es-AR}`. Para activar el par
RTL, `rtl.enabled: true` y `rtl.source_text_direction ∈ {ltr, rtl,
mixed}`. El plan documenta los requisitos por variante en
`references/locale-policy.md` y `references/rtl-policy.md`.

### 5.3 Subrelease 0.1.3 — escala y separación autor/revisor (fases 111–115)

Esta subrelease añade la **infraestructura de escala** sobre el corpus
real (`/Users/martin/Desktop/documentacion`, 4832 archivos) y
formaliza la separación autor/revisor.

Pieza | Función
|---|---|
| `scripts/measure_execution.py` | Mide tiempos reales con `time.monotonic()`. Sin inventar tokens ni costos. |
| `scripts/schedule_packets.py` | Orden topológico por dependencias de glosario y anclas. Rechaza ciclos. |
| `scripts/worker.py` | Esqueleto ejecutable para workers con particiones disjuntas. Glosario no se modifica. |
| `scripts/coordinator.py` | Lock sobre el manifiesto; rechazo de conflictos sobre `segment_id`. |
| `scripts/reviewer_role.py` | Bitácora JSONL; rechaza inputs con `author_notes` o `tokens_estimated`. |
| `references/scheduler-policy.md` | Política del planificador de paquetes. |
| `references/worker-protocol.md` | Protocolo de aislamiento de workers. |
| `references/reviewer-protocol.md` | Política de separación autor/revisor. |
| `evals/rubric-distributed.md` | Rúbrica para revisores en modo distribuido. |
| `schemas/execution_profile.schema.json` | Contrato del perfil de ejecución. |
| `schemas/packet_schedule.schema.json` | Contrato del plan. |
| `evals/cases/corpus-full.md` | Caso del corpus grande con muestreo de 30 archivos para CI. |

Lo que esta subrelease **no** afirma:

- Que la ejecución paralela real esté operativa. Los workers y el
  coordinador están listos como infraestructura; el orquestador
  arranca por instrucción del usuario.
- Que el corpus grande se ejecute en cada CI: el muestreo de 30
  archivos mantiene los tiempos acotados.
- Que `fcntl.flock` esté disponible en todos los sistemas; el
  fallback `threading.Lock` se aplica en máquinas no POSIX y se
  documenta en `coordination.json`.
- Que las fases 116–120 estén cubiertas. Concurrencia real,
  fallback en serie, caché contextual, invalidez transitiva y
  gate de escala quedan fuera.

Activación por defecto: ninguna. Cada pieza se invoca con su CLI
propia. El muestreador de CI corre con `--sample 30 --seed 42`
sobre `tests/fixtures/scale/`. La ejecución sobre el corpus grande
se lanza manualmente con
`scripts/measure_execution.py --corpus /Users/martin/Desktop/documentacion`.

### 5.4 Subrelease 0.1.4 — concurrencia, caché contextual y gate (fases 116–120)

Esta subrelease **cierra la sección L** del roadmap (escalas
111-120 ya cerrada por 0.1.3). Las cinco fases formalizan el
protocolo y ofrecen scripts verificables.

Pieza | Función
|---|---|
| `scripts/run_concurrent.py` | Lanza workers en `ThreadPoolExecutor` con backoff y pausa segura. |
| `scripts/run_serial.py` | Recorre el orden topológico con un solo worker `--id serial`. |
| `scripts/diff_ledgers.py` | Compara dos manifiestos (serial vs. concurrent). |
| `scripts/translation_cache.py` | Caché por segmento con clave compuesta. |
| `scripts/invalidate_cache.py` | Invalida entradas por cambio de glosario o de anclas. |
| `scripts/gate_scale.py` | Cinco checks: cobertura, ledger, regresión de enlaces, bloqueos, tiempo. |
| `references/concurrency-policy.md` | Backoff, `max_workers`, `allow-single-cpu`. |
| `references/serial-fallback.md` | Equivalencia de ledgers entre modos. |
| `references/translation-cache.md` | Clave compuesta y persistencia. |
| `schemas/cache_entry.schema.json` | Contrato de cada entrada de caché. |

Lo que esta subrelease **no** afirma:

- Que el modo concurrente sea más rápido en todos los sistemas.
  La elección de `threading` sigue la I/O dominante del núcleo.
- Que la memoria caché reduzca el tiempo de traducción: el
  objetivo es **seguridad** (no reutilizar sentido incompatible),
  no rendimiento.
- Que la ejecución sobre el corpus grande esté validada: se
  documenta como decisión fuera del CI. `tests/fixtures/scale/`
  cubre los protocolos.
- Que la sección L vuelva a abrirse. Cualquier activación futura
  (multipart, memoria distribuida, predicciones de capacidad)
  requiere nuevas filas del roadmap.

Activación por defecto: ninguna. El modo serie (`scripts/run_serial.py`)
sigue siendo la elección predeterminada. El concurrente solo se
activa con `scripts/run_concurrent.py --packets <P> --workdir <W>
--max-workers N --allow-single-cpu` (CI) o sin la última opción
(producción).

### 5.5 Subrelease 0.1.5 — entrega local, paquete ZIP y destinos (fases 131–140)

Esta subrelease añade un **módulo de entrega opt-in**. Sin activarlo, el
núcleo se comporta exactamente igual: `scripts/export.py` sigue
entregando un árbol limpio y la traducción canónica sigue siendo la
referencia auditada.

| Pieza | Función |
|---|---|
| `scripts/record_import_evidence.py` | Checklist de importación de muestra, resolución local de enlaces y matriz de importación. |
| `schemas/import_evidence.schema.json` | Contrato de la evidencia, con `verified` condicionado a revisor humano. |
| `references/delivery-notion-checklist.md` | Procedimiento y evidencia que debe aportar el usuario. |
| `scripts/adapt_delivery.py` | Adaptación local opt-in sobre una copia del árbol canónico. |
| `schemas/delivery_profile.schema.json` | Contrato del perfil de entrega y de sus reglas. |
| `references/delivery-contract.md` | Qué puede y qué no puede hacer un adaptador. |
| `references/delivery-profiles/plain-markdown-local.json` | Perfil de ejemplo con dos reglas `lossiness: none`. |
| `scripts/export_zip.py` | Paquete ZIP autocontenido y determinista. |
| `scripts/validate_zip_package.py` | Auditoría del paquete contra el manifiesto aprobado. |
| `schemas/delivery_package.schema.json` | Contrato del manifiesto de paquete. |
| `scripts/render_delivery_guide.py` | Guía de entrega fuera del árbol importable. |
| `scripts/compare_delivery.py` | Clasificación de diferencias entre adaptado y canónico. |
| `scripts/delivery_matrix.py` | Matriz de destinos con su estado de evidencia real. |
| `references/delivery-matrix.md` | Destinos, limitaciones y cómo activar uno nuevo. |
| `scripts/gate_delivery.py` | Siete comprobaciones con códigos de salida 1 a 7. |
| `references/delivery-gate.md` | Detalle de cada comprobación del gate. |

Lo que esta subrelease **no** afirma:

- **Que la importación a Notion esté verificada.** No lo está. Ninguna
  ejecución de esta skill ha importado nada en Notion. El registro
  `import_evidence.json` nace con `remote_status: no_verificado` y solo
  cambia si el usuario aporta evidencia con revisor humano declarado.
  Las fases 131, 132 y 133 llevan `✅ ⚠` por eso.
- **Que exista un segundo destino probado en una aplicación real.**
  `plain-markdown-local` es un adaptador interno con
  `real_app_evidence: false`. La fase 139 lleva `✅ ⚠`.
- **Que el ZIP sea una entrega certificada.** Es un contenedor
  determinista con una lista de miembros auditable. No valida el
  contenido contra el destino.
- **Que una adaptación pueda cambiar la traducción.** El contrato de la
  fase 134 lo prohíbe: solo rutas y nombres, y `compare_delivery.py`
  bloquea cualquier pérdida de contenido.
- **Que la similitud de texto sea evidencia de fidelidad.** El informe
  de degradaciones la registra solo para priorizar.

Activación por defecto: ninguna. Requiere `delivery.enabled: true` en
`profile.json` con `destination_id` y `profile_ref`. El recorrido
completo es `adapt_delivery.py` → `export_zip.py` →
`validate_zip_package.py` → `render_delivery_guide.py` →
`compare_delivery.py` → `delivery_matrix.py` → `gate_delivery.py`.

### 5.6 Subrelease 0.2.0 — mantenimiento y release ampliado (fases 141–150)

**Qué cambia.** Entra el bloque de mantenimiento (141–148) y, por
primera vez, el candidato de release declara sus módulos **activos**, cada
uno con su gate propio. El candidato lo valida
`schemas/release_candidate.schema.json` y lo construye
`scripts/build_release_candidate.py`.

**Módulos activos:** `core`, `mdx`, `html`, `markdown-extensions`,
`terminology`, `language`, `scale`, `review`, `delivery`, `maintenance`.
Los diez con su gate en verde en el candidato del 2026-10-20.

**Qué NO se activa por defecto:** `delivery.enabled`, `html.enabled`,
`mixed_profile.enabled`, `rtl.enabled`, etiquetas Mermaid y frontmatter
traducible. Declarar un módulo activo no lo enciende: encenderlo sigue
siendo una decisión de `profile.json`.

**Herramientas nuevas:**

| Fase | Herramienta | Qué hace |
|---|---|---|
| 141 | `scripts/regression_gate.py` | 22 fallos conocidos con caso positivo y negativo, reproducibles |
| 142 | `scripts/check_versioning.py` | seis familias de versión y migraciones obligatorias |
| 143 | `scripts/migrate_manifest.py` | `translate/v0` → `v1` sin fabricar aprobaciones vigentes |
| 144 | `scripts/compare_parser.py` | no promueve si cambian rangos o slugs |
| 145 | `scripts/compare_model_runs.py` | solo compara ejecuciones reales comparables |
| 146 | `scripts/audit_docs.py` | rutas, flags, reglas contradictorias y afirmaciones remotas |
| 147 | `scripts/probe_platform.py`, `check_portability.py` | `verified` exige evidencia |
| 148 | `scripts/purge_workdir.py` | el trabajo es lo único desechable, y con rastro |
| 149 | `scripts/build_release_candidate.py`, `gate_extended.py` | nueve comprobaciones internas y huecos externos declarados |

**Qué encontró esta subrelease.** La primera ejecución de la suite en
Linux (contenedor `python:3.12-slim`) falló 108 de 891 pruebas. Ninguna era
un fallo de traducción: eran dependencias no declaradas (`langdetect`),
78 rutas temporales fijas a macOS, bytecode dentro del paquete, una prueba de
colisión Unicode que nunca comprobaba nada porque el `skip` la ocultaba, y
una comprobación de validador que se saltaba los documentos sin literales
protegidos. Todo corregido y registrado en
`references/portability.md`.

**Lo que esta subrelease NO afirma:**

- Que la variación entre modelos esté medida: hay **una** ejecución real
  registrada, no dos. La fase 145 queda `✅ ⚠`.
- Que Windows funcione: esa fila de la matriz está en `design_only`.
- Que exista una versión de parser más nueva que la fijada: se comprobó
  que no la hay; la comparación registrada es entre la fijada (3.0.0) y la
  anterior (2.2.0) y sirve como prueba del mecanismo, no como promoción.
- Nada de lo que la 0.1.5 ya declaran sin evidencia: Notion, firmas
  nativas, segundo destino, retrotraducción en vivo.

Acta completa con huellas, códigos de salida y huecos externos:
`evals/release/RELEASE_NOTES_0.2.0.md`.

### 5.7 Subrelease 0.4.0 — G-EXT verificado en los nueve módulos (fases 061–150)

**Qué cambia.** Ninguna capacidad nueva de traducción. Lo que cambia es que
el checklist `G-EXT, cada módulo opcional` del roadmap, que llevaba seis
módulos sin bloque aplicado y cuatro casillas sin comprobar, pasa a estar
comprobado por un gate ejecutable.

**Qué no estaba bien.** El candidato de release declaraba `activation:
"active"` como literal para los diez módulos, ejecutaba entre uno y tres de
los diez ficheros de prueba de cada módulo, y ponía `limitations: []` a
módulos sin corpus real. Eso convertía «las pruebas pasan» en «el módulo está
sostenido»: el mismo argumento que G-CORE ya había detectado en el lado del
núcleo, repetido en el lado de los módulos.

**Herramientas nuevas:**

| Qué | Herramienta | Qué hace |
|---|---|---|
| Contrato | `schemas/module_declaration.schema.json`, `modules.json` | Declara por módulo activación, corpus, justificación, contratos, todas sus pruebas y su política de fallo |
| Gate | `scripts/gate_optional.py` | Un código de salida por casilla (1–7). Lo no medido no es verde |
| Inventario | `scripts/optional_modules.py` | Qué script es núcleo y de qué módulo es, y en qué dirección importan |
| Migración | `scripts/migrate_profile.py` | Lleva un perfil antiguo al requisito de corpus declarado |

**Defectos corregidos:** el núcleo importaba del módulo de revisión; cuatro
opciones de perfil aceptadas por el esquema no hacían nada; encender MDX o
HTML era permitir cualquier JSX o cualquier HTML; dos esquemas prohibían
campos que el código leía o escribía; `--mode expanded` de revisión era más
débil que `basic`; el modo concurrente declaraba cobertura sin traducciones;
la invalidación de caché por anclas no podía dispararse; el detector de
idioma residual no honraba la política de preservación; y dos contratos
prometían un backoff y un comparador que no existen. Detalle con archivo y
línea en `CHANGELOG.md` 0.4.0.

**Cambio incompatible:** `profile.schema.json` 1.1.0 exige `corpus_ref` y
`justification` para activar cualquier módulo. Los perfiles de `reports/pilot/`
y `reports/beta/` no se corrigen porque su hash está anclado en el manifiesto:
su activación sin corpus queda registrada como **activación inmotivada**.

**Lo que esta subrelease NO afirma:**

- Que los módulos sirvan para un corpus cualquiera: cada informe de
  `reports/optional/` declara sobre qué corpus se midió.
- Que MDX, HTML, las extensiones, terminología o revisión estén activados
  sobre material real: cuatro de ellos no tienen corpus que los justifique y
  lo dicen en su informe.
- Nada de lo que ya se declaraba sin evidencia: equivalencia semántica,
  Notion, firmas nativas, segundo destino, retrotraducción en vivo, Windows,
  variación entre modelos y ejecución sobre los 4 832 archivos del corpus.

## 6. Firma

**Release candidata del núcleo estable, no production-ready, sin
garantía semántica absoluta.** Esta release se entrega al usuario
como una herramienta documentada y reproducible; la certificación de
idoneidad para cualquier uso específico la realiza el usuario.