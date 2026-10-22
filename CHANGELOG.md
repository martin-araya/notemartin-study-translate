# Changelog de `notemartin-study-translate`

Todas las entradas siguen el formato "qué cambió, por qué y cómo se
verifica". Los números de fase corresponden al roadmap de este
proyecto.

## Núcleo estable (no publicado)

### 0.4.0 — G-EXT verificado en los nueve módulos opcionales

Ninguna casilla de gate de traducción se cierra aquí: G-PILOT sigue
aprobado, G-BETA y G-CORE siguen en 0. Lo que se cierra es el checklist
`G-EXT, cada módulo opcional` de `roadmap.md`, que llevaba seis módulos sin
bloque aplicado y cuatro casillas sin comprobar.

El problema de fondo no era que faltara evidencia: era que la evidencia
existía y no comprobaba lo que decía. `build_release_candidate.py` escribía
`activation: "active"` como literal para los diez módulos, cada gate de
módulo ejecutaba entre uno y tres de sus diez ficheros de prueba, y
`limitations: []` declaraba que MDX, HTML, extensiones y terminología no
tenían nada que declarar. Con eso, un módulo dormiente con fixtures
sintéticos pasaba por módulo activo con pruebas en verde.

#### Contrato ejecutable

- `schemas/module_declaration.schema.json` (nuevo) y `modules.json`: cada
  módulo declara activación, corpus, justificación, contratos, **todas** sus
  pruebas y su política de fallo.
- `references/optional-modules.md`: qué significa cada casilla y cómo se
  comprueba.
- `scripts/gate_optional.py`: un código de salida por casilla, 1 a 7. Lo no
  medido no es verde: sin la evidencia del núcleo el gate falla con 4.
- `scripts/optional_modules.py`: inventario explícito de qué script es
  núcleo y qué script es de qué módulo, y comprobación de la **dirección de
  las dependencias**. Un script sin clasificar hace fallar el gate.
- Informes por módulo en `reports/optional/`, escritos por el propio gate.

#### Defectos corregidos

1. **El núcleo dependía de un módulo opcional.** `verify_already_target.py`
   importaba `detect_residual_language` (fase 126) y `regression_detectors.py`
   importaba `check_approval_freshness` (fase 124): apagar el módulo de
   revisión rompía la verificación de `already_target` y la promoción de
   aprobaciones. Las primitivas se movieron a `scripts/text_signals.py` y
   `scripts/approval_freshness.py`, que son núcleo. Ahora solo quedan dos
   delegaciones, declaradas con su motivo: los detectores puros que
   `prepare.py` necesita para bloquear, y los detectores de regresión que
   solo corren al pasar el gate de release.

2. **Cuatro gates de perfil no hacían nada.** `classify_file` recibía
   `definitions_enabled`, `directives_enabled`, `mermaid_enabled` y
   `mermaid_labels` y nunca los leía, mientras `profile.schema.json` los
   validaba. `admonitions.types` también se ignoraba. Ahora cada opción del
   esquema tiene lector, efecto y prueba.

3. **Encender un módulo era permitir cualquier cosa.** El gate MDX quitaba el
   hallazgo entero sin mirar el contrato, y el HTML igual. Ahora
   `mdx_selector.contract_findings()` y `html_parser.contract_findings()`
   emiten un hallazgo bloqueante por cada componente, atributo o patrón fuera
   del contrato. El contrato de MDX crece con `<CodeGroup>` porque el corpus
   piloto real lo usa.

4. **El esquema prohibía lo que el código escribía.** `manifest.schema.json`
   rechazaba con `additionalProperties: false` los `target_glossary_hash`,
   `target_anchor_hash` y `target_profile_hash` que la fase 124 documenta,
   usa y prueba (ahora 1.4.0). `glossary.schema.json` rechazaba el bloque
   `provenance` que `term_provenance.py` escribe (ahora 1.2.0). El segundo
   además aparecía como `term_exceptions` en `references/term-profiles.md`,
   campo que el esquema nunca tuvo.

5. **`--mode expanded` de revisión era más débil que `basic`.** No ejecutaba
   `basic_check`, exigía los códigos 6 y 7 sincubrirlos, y las fases 122 y
   125 se leían «si existen». Ahora compone, tiene código propio para cada
   requisito y exige `--justification`: activar sin corpus sale con 7.

6. **El modo concurrente declaraba cobertura que no tenía.** No propagaba
   `--content-dir` y contaba la partición entera como aprobada: una ejecución
   sin traducciones producía un manifiesto con todos los segmentos aprobados,
   y el gate 120 comparaba ese número con el del serie y daba por buena una
   cobertura inexistente. Ahora solo se aprueba lo entregado.

7. **La invalidación de caché por anclas no podía ocurrir.** Se leía un campo
   `anchors` que el esquema prohibía y que `translation_cache.store()` nunca
   escribía; la prueba lo tapaba fabricando la entrada a mano.

8. **El detector de idioma residual no honraba la política de preservación.**
   Buscaba `preserve`, que no está en el enum `preservation_policy` del
   esquema, así que la exención nunca se activaba sobre un glosario válido.

9. **Dos contratos afirmaban capacidades inexistentes.** El modo concurrente
   «pausaba por saturación con backoff exponencial» y `diff_ledgers` «reportaba
   `conflicts_state`»; ninguna de las dos cosas existe en el código. Los
   documentos dicen ahora lo que el código hace, y lo que no hace está
   declarado como deuda.

#### Cambio incompatible

`profile.schema.json` 1.1.0 exige `corpus_ref` y `justification` para activar
cualquier módulo. Un perfil que hoy los activa sin declararlos no valida.
Migración: `scripts/migrate_profile.py`, que los rellena desde el caso de
`evals/cases/` del módulo y no toca ningún otro valor.

Los perfiles de `reports/pilot/` y `reports/beta/` **no** se corrigen: su hash
está anclado en el manifiesto y tocarlo invalidaría la aprobación de G-PILOT
(INV-13). Sus activaciones sin corpus quedan registradas como activación
inmotivada en `evals/cases/html.md` y `reports/optional/html.json`.

#### Lo que este gate no dice

Ninguna casilla G-EXT afirma equivalencia semántica, ejecución sobre el corpus
completo de 4 832 archivos, importación real en Notion, firma nativa de
revisor, portabilidad en Windows ni variación entre modelos. Cada hueco tiene
dueño y procedimiento en `modules.json` → `known_external_gaps`.

### 0.3.0 — cinco defectos de instrumentación encontrados al medir G-CORE

Ninguna casilla de gate se cierra en esta entrada. Lo que se corrige son
cinco herramientas que, tal y como estaban, habrían permitido declarar
G-BETA y G-CORE completos sin que lo fueran. Todos con prueba que falla
antes del arreglo y evidencia medida sobre la corrida `run-7fbd5e24`.

#### 1 · `advance_state.py` afirmaba revisión y aprobación sin ninguna

`--translations` impedía escribir `translated` sin traducción en disco,
pero `semantic_pass` y `approved` solo exigían eso: bastaba un archivo de
traducción con una entrada para escribir que el corpus estaba revisado y
aprobado. Es la tercera vez que la misma familia de defecto aparece en
esta corrida (INV-12).

- `--review <ledger>` y `--segments <segments.json>` son **exigidos** para
  `semantic_pass` y `approved`. Sin ellos, código de salida 1.
- El denominador de la cobertura sale del archivo de segmentos, nunca del
  propio ledger: un ledger que declarara su total se declararía completo
  a sí mismo.
- `approved` exige además las dos mitades de
  `references/reviewer-policy.md` §2: una decisión `approve` con
  `reviewed_hashes` no vacío y un firmante `reviewers[].kind == human`,
  ambos con `scope` que cubra la ruta. `kind: assisted` no firma.
- `deterministic_pass`, `translated` y `prepared` no cambian: la
  validación determinista es previa y no se le inventa una exigencia.

Verificado sobre la corrida real: `semantic_pass` sin ledger → 1;
`approved` sin firma → 1; ledger inexistente → 1; `deterministic_pass` con
traducción → 76 archivos elegibles.

#### 2 · `repair_state_field.py` solo reparaba una de las dos divergencias

2 608 de 2 682 registros del manifiesto beta declaraban
`state: "translated"` con `current_state: "prepared"`, sin transición que
lo sostuviera en `state_history`. Todos los gates leen `current_state`,
así que la divergencia pasaba desapercibida mientras cualquier lector de
`state` —un informe, una herramienta externa, una persona— leía 2 608
documentos traducidos que no lo están.

- La reparación es bidireccional y basada en historial en los dos
  sentidos: si el historial sostiene `state`, se adopta; si sostiene
  `current_state` y no `state`, se **degrada**. Sin historial que sostenga
  ninguno, no se toca y se reporta.
- `check_integrity.py` cuenta los registros divergentes y **no** da
  `integrity_ok` mientras haya alguno: un manifiesto que se contradice a
  sí mismo describe dos corpus a la vez.
- Aplicado a `run-7fbd5e24`: 2 608 degradados, 0 adoptados, 0 sin
  evidencia. El único campo modificado fue `state`; `current_state` no se
  tocó. Copia previa en `manifest.json.bak-pre-h4`.

#### 3 · `export.py` nunca comparó la estructura del árbol que entregaba

Su `validate.py` interno recibía `--output-dir` del **padre** del
directorio del run, mientras ensamblaba en `output_root/<run_id>/`, y sin
`--require-assembled`. El chequeo `structure` no encontraba ningún
documento y pasaba en vacío.

- Después del ensamblado y del `rename` atómico, `export.py` ejecuta
  `validate.py --checks structure --require-assembled` contra el árbol
  final. Si falla, borra el árbol y no promueve nada.
- El informe de exportación incluye `structure_check`.

#### 4 · `check_structure` se saltaba los documentos que la traducción toca

El atajo que evita el aviso «sin headings ni enlaces» para los documentos
de prosa a los que el scraper les perdió las cabeceras se aplicaba
**antes** de comparar fuente contra ensamblado, así que saltaba el
documento entero. Medido sobre el corpus beta: **4 de 2 682 documentos**
se comparaban. Los 2 462 restantes se saltaban por tener segmentos
traducibles, es decir, por ser exactamente los que un ensamblado puede
dañar (INV-06).

- Los atajos se limitan a su propósito: evitan el aviso de parser roto,
  no la comparación. Un documento traducible **tampoco** se salta.
- `check_structure` devuelve ahora `compared`, `skipped_stubs` y
  `unassembled_count`: sin un contador positivo el informe no distingue
  «comparado e idéntico» de «nunca alcanzado», que es la ambigüedad que
  dejó pasar todo esto.

Medido sobre el corpus beta tras el arreglo: **2 427 documentos
alcanzados** por la comparación, 211 stubs omitidos, 46 comparados firma a
firma contra la fuente con 0 diferencias.

#### 5 · El agregado por archivo contradecía a sus propios segmentos

`detect_language.py` escribe `file_disposition` y
`file_disposition_counts` al clasificar. `resolve_dispositions.py` cambia
después disposiciones de segmento y el agregado se quedaba con el valor
anterior: `oracle/resúmenes/09_…` declaraba 189 segmentos traducibles y
tenía 255. Era el número que se leía al informar y no era cierto.

- `resolve_dispositions.py` recalcula el agregado con la misma regla de
  `detect_language.py` después de aplicar, y lo añade si no existía.

#### Lo que no cambia

- El denominador del gate sigue siendo **44 784 segmentos traducibles**.
- `G-BETA` y `G-CORE` siguen sin marcar. Translated: 76 de 2 682
  documentos, 167 entradas de traducción, 2 606 en `prepared`.
- La firma humana de la revisión sigue pendiente: es lo que exige la
  casilla 4 de G-CORE.

### 0.2.3 — decisión `dec-20261021` (fase 050, G-BETA abierta)

No cierra ningún gate. Es una decisión editorial registrada que cierra
la decisión pendiente sobre los segmentos `already_target` que no
sostenían el español: el usuario los deja fuera.

#### Cambios

- `scripts/verify_already_target.py` ya estaba en 0.2.2; en 0.2.3 se
  corrigen dos fallos de la primera versión (acusaba token a token
  en vez de por run; mezclaba enlace-queda-pendiente con
  necesita-traducción). Tres iteraciones medidas, documentadas en
  `reports/beta/summary.md` §9.
- Decisión `dec-20261021` (`kind: defer`, `role: owner`):
  215 segmentos en 188 archivos **permanecen** `already_target`.
  - 107 `english_label`: etiquetas de Angular en inglés.
  - 20 `english_prose`: frases enteras en inglés.
  - 88 `link_label_pending`: etiquetas que replican el fragmento; las
    decide la reescritura de anclas (INV-09).
- `manifest.json.decisions[]` registra la decisión con motivo, hashes
  del informe y las 188 rutas en `scope`.
- `manifest.json.migrations[]` añade una entrada de auditoría con el
  conteo.
- `reports/beta/summary.md` §5, §9 y §11 y `PLAN_PENDIENTE.md` §2 bis
  reflejan la decisión: «quedan fuera».

#### Lo que no cambia

- El denominador del gate sigue siendo **44 784 segmentos traducibles**
  (los 215 nunca fueron `translatable`, no se restan). Cero suma, cero
  resta.
- `G-BETA` sigue sin marcar: 43 de 44 784 segmentos. La barrera es la
  traducción por lotes, no la decisión editorial.
- `_collisions.json` con las 3 110 entradas entre documentos se
  conserva por trazabilidad.

### 0.2.2 — identidad de documentos y paquetes (fase 050, G-BETA abierta)

Ninguna casilla de gate se cierra en esta entrada. Lo que se corrige son
dos colisiones de identificadores que hacían que la traducción por lotes
entregara contenido en el archivo equivocado **sin emitir ningún
hallazgo**, y que dejaban escrito en disco un trabajo perdido.

#### Colisión de `document_id` (INV-03, C-RUN)

`prepare.py` deriva `document_id` de los **bytes** del archivo:
`"doc-" + sha256(source_bytes)[:8]`. Dos rutas byte a byte idénticas lo
comparten. Medido sobre el corpus beta: **15 identificadores ambiguos,
214 rutas**, y 14 `segment_id` repetidos hasta 20 veces. Las cuatro
páginas stub de `tailwindcss/installation/` pesan 15 bytes, contienen
`\n# Hello world!` y las cuatro son `doc-085fb377`.

`receive_translations.py` persistía en `translations/<document_id>.json`:
la traducción de un archivo se escribía junto a la de otro y el parche de
`assemble.py` se aplicaba sobre el documento equivocado.

**Solución:** `scripts/translation_key.py` introduce `translation_id`,
que suma la ruta al hash. `document_id` **no se regenera** — conserva su
significado real, la clase de equivalencia de contenido — y la colisión se
resuelve solo en la clave de persistencia. Un documento no ambiguo sigue
usando `document_id` como nombre de archivo, de modo que **las 2 682
traducciones ya escritas no se mueven** y el manifiesto, los hashes de
procedencia y la traducción entregada de `doc-f0342fb5` siguen siendo
válidos. Renombrar todo habría invalidado el trabajo hecho sin ganar
nada: solo colisionan 214 de 2 682 archivos.

#### Colisión de `packet_id` (INV-03)

Misma raíz, un nivel más arriba. `packet_id` se derivaba de
`document_id` + `segment_id`, y ambos derivan de los bytes: **8 ids
duplicados entre 53 paquetes**, uno compartido por 20 rutas.

Este es el más grave de los dos. `receive_translations.py` indexa los
paquetes en un dict por id, así que una respuesta que nombraba
`pack-efe1b073` se resolvía al último de los doce paquetes del grupo y el
trabajo de los otros once se perdía sin aviso. `packetize.py` ahora
incluye la ruta en el hash; `scripts/inject_translation_ids.py` repara
los paquetes ya construidos y deja el mapa `packet_id_renames`.

#### Evidencia

Prueba de extremo a extremo sobre el corpus real: 61 paquetes de rutas
colisionadas, cada uno devolviendo un marcador con **su** ruta.

| | Archivos escritos | Rutas perdidas sin aviso |
|---|---|---|
| Antes | 8 | 53 |
| Después | **61** | **0** |

`validate.py` devuelve los mismos 5 errores con `packets_v2.json` y con
`packets_v3.json`, y `assemble.py` sobre el documento ya traducido
produce los mismos 15 354 bytes. Verificación:
`tests/test_document_id_collision.py` (26 casos, con la colisión real de
Tailwind como fixture).

#### Dos cálculos que no eran bloqueos

- **Colisiones de anclas.** `_collisions.json` contaba 3 110 anclas
  compartidas, todas **entre documentos**. Un fragmento solo se resuelve
  dentro del documento que lo contiene, así que reutilizar un slug entre
  rutas no rompe la navegación. `scripts/dump_anchor_collisions.py` separa
  los dos casos y mide **0 colisiones intra-documento** en 2 483
  documentos. El riesgo que `PLAN_PENDIENTE.md` listaba no existía.
- **Disposición `already_target`.** `scripts/verify_already_target.py`
  verifica en vez de asumir. **127 de 1 297** no sostienen la
  disposición, casi todos etiquetas de la referencia generada por Angular.
  El script no reescribe nada: reetiquetar cambia el denominador del
  gate, y esa decisión es del usuario.

#### Utilidades nuevas

- `scripts/translation_key.py` — clave de persistencia con ruta.
- `scripts/inject_translation_ids.py` — inyecta `translation_id` y repara
  `packet_id` duplicados **sin reempaquetar** (los paquetes ya declaraban
  `path`), con `integrity_ok` como gate.
- `scripts/select_lote.py` — mide qué falta por directorio y arma el
  sobre del siguiente lote. No cruza directorios: mezclar `angular/api/`
  con `nextjs/messages/` haría indiagnosticable un fallo.
- `scripts/verify_already_target.py` — verificación de `already_target`.
- `scripts/dump_anchor_collisions.py` — informe legible de colisiones.

#### Lo que este changelog no dice

No se afirma que el corpus esté traducido. `G-BETA` sigue sin marcar: 43
de 44 784 segmentos, 0,1 %. La remediación **permite** traducir por
lotes; no es traducción.

#### Decisión `dec-20261021` — exclusión editorial de 215 segmentos

Los 215 segmentos que no sostenían `already_target` (107 `english_label`
+ 20 `english_prose` + 88 `link_label_pending`) **se quedan fuera** del
corpus traducible. Casi todos son etiquetas de la referencia generada
por Angular (`Type Alias`, `function`, `stable`); reetiquetarlos sería
una decisión editorial pendiente por escrito de quien tendría que
tomarla, y el corpus no la exige. La decisión está registrada en
`manifest.json.decisions[]` con `kind: defer`, `role: owner`,
`decided_at` 2026-10-21, `reviewed_hashes` apuntando al informe
verificador, y `scope` con las 188 rutas afectadas. Los 1 082
segmentos que sí sostienen la disposición permanecen `already_target`
sin intervención.

El efecto sobre el gate es **cero**: esos 215 nunca fueron `translatable`,
así que sumarlos o no no cambia el denominador. Sumarlos equivaldría
a una puerta editorial pendiente que esta decisión opta por no abrir.

### 0.2.1 — correcciones que el corpus beta destapó (fase 050, G-BETA abierta)

Ninguna casilla de gate se cierra en esta entrada. Lo que cambia es que
varias comprobaciones que parecían estar en verde **no miraban nada**, y
que la protección de literales se rompía con contenido no ASCII.

#### Protección de literales (INV-05)

Cuatro defectos en `scripts/prepare.py`, todos reproducibles solo con
contenido que el piloto no tenía:

- `safe_byte_slice` comprobaba el byte anterior al corte en vez del byte
  del corte, y recortaba el final hacia atrás. Un literal multibyte
  quedaba en un byte: `ƒ` (0xC6 0x92) se guardaba como U+FFFD.
- La rama de `code_inline` de primer nivel calculaba el inicio del
  literal restando `m.start(0)`, índice que no corresponde al grupo
  interno del patrón.
- La búsqueda del tramo de código inline tomaba la primera coincidencia
  de la línea: dos tramos en la misma línea producían un solo literal,
  con el valor del primero aplicado al segundo.
- Los destinos de enlace e imagen se guardaban percent-encoded
  (`res%C3%BAmenes/…`) mientras la fuente contiene `resúmenes/…`. El
  literal no aparecía nunca en el texto y 23 paquetes no se podían
  construir.

`packetize.build_packet_markers` envolvía por valor en vez de por
posición, de modo que un literal repetido en un segmento se marcaba dos
veces sobre la misma aparición y la validación lo daba por perdido.

Verificación: `tests/test_literal_boundaries.py`. Con el corpus beta,
`build_packets.py` pasa de 23 paquetes con errores a 0.

#### Comprobaciones que no inspeccionaban el corpus

- `validate.check_structure` recorría `source_dir.glob("*.md")`, que no
  es recursivo, y buscaba el snapshot por nombre de archivo en vez de
  ruta relativa. Sobre un corpus anidado devolvía `structure: 0 errores`
  sin mirar un solo archivo. Ahora recorre las rutas del inventario y
  compara la firma estructural de la fuente con la del ensamblado
  (`heading_levels`, anclas explícitas, tablas, fences, listas), con
  `--require-assembled` para el gate posterior al ensamblado.
- `validate.check_destinations` solo comprobaba que sobrevivieran las
  URL `http(s)`. Ahora compara por `segment_id` las clases `external`,
  `site_absolute` y `relative` por valor exacto, y los fragmentos `#`
  por cantidad: cambiar el valor de un fragmento es la excepción
  autorizada de INV-09, pero que aparezcan o desaparezcan enlaces es un
  defecto.
- `validate.check_source_debt` tenía el mismo defecto no recursivo y
  resolvía las anclas contra el propio documento. Ahora es recursivo,
  resuelve rutas relativas al documento, distingue anclas rotas,
  destinos inexistentes, escapes de la raíz y rutas absolutas del sitio,
  y usa el mismo algoritmo de slugs que `build_anchors.py`.

#### Estados y procedencia

- `approve_pilot.py` escribía `entry["state"]` y nunca
  `current_state`, que es el campo que exige el esquema y leen todos los
  gates. El manifiesto del piloto quedó aprobado pero describía un
  corpus que ningún gate daba por aprobado.
- `check_integrity.py` contaba `translated` como integrado, así que
  `integrity_ok` podía ser cierto sobre un corpus sin revisar. Ahora
  solo cuentan `approved`, `exported` y `already_target`; lo demás es
  pendiente, incluidos los estados desconocidos, que se declaran.
- `scripts/advance_state.py` (nuevo) recorre la secuencia C-RUN
  `inventoried → prepared → translated → deterministic_pass →
  semantic_pass → approved → exported` y rechaza los saltos. Antes esa
  secuencia no la completaba ninguna herramienta y `exported` era
  inalcanzable.
- `export.py` promueve a `exported` los archivos que estaban aprobados
  y tienen bytes entregados, y escribe su `output_sha256`. El esquema
  de manifiesto sube a 1.3.0 con ese campo opcional.
- `run_end_to_end.py` fabricaba procedencia: `run_id` fijo, `"hash":
  "x"` y fechas escritas a mano. Ahora deriva de los archivos reales y
  su informe declara que la traducción identidad no es una traducción.
- `worker.py` escribía candidatos con `content: null` y proponía la
  transición a `deterministic_pass`; `run_serial.py` declaraba
  `approved_segment_ids` = todos los paquetes. Un recorrido de escala
  producía así un informe verde sin haber traducido nada. Ahora un
  candidato sin contenido queda `pending_translation` y no propone
  transición.

#### Herramientas

- `scripts/build_manifest.py` y `scripts/build_glossary.py` (nuevos):
  las herramientas del piloto vivían en el workdir de aquella corrida y
  no formaban parte de la skill. El glosario aplica decisiones ya
  aprobadas y las evidencia con un ejemplo real del corpus; una entrada
  sin ejemplo no entra.
- `scripts/repair_state_field.py` (nuevo): adopta `state` como
  `current_state` solo cuando el historial del archivo contiene esa
  transición. No aprueba nada.
- `detect_residual_language.py` exigía evidencia a favor para informar
  de una run; antes bastaba con que no hubiera evidencia en contra, y
  sobre el piloto produjo 273 avisos que eran prosa española corriente.
  Su salida quedó registrada como no utilizable en
  `reports/pilot/summary.md`.

### 0.1.0 — release candidata del núcleo estable (fase 060)

Núcleo traducible de prosa técnica Markdown al español, con
preservación de literales, estructura y enlaces internos, y entrega
local limpia para importación manual a Notion.

#### Fases 001–010 — contratos y paquete

- 001: flujo de trabajo fiel, sin resumen ni publicación.
- 002: corpus piloto representativo en `evals/cases/pilot.md`.
- 003: contrato Markdown en `references/markdown-contract.md`.
- 004: perfil declarativo en `schemas/profile.schema.json`.
- 005: glosario por dominio y sentido en `schemas/glossary.schema.json`.
- 006: manifiesto con estados y procedencia en
  `schemas/manifest.schema.json`.
- 007: política de operación, confianza y permisos en
  `references/operation.md`.
- 008: rúbrica de fidelidad y criticidad en `evals/rubric.md`.
- 009: entrega y límites de Notion en `references/notion-handoff.md`.
- 010: punto de entrada de la skill en `SKILL.md`.

#### Fases 011–020 — preparación estructural

- 011–020: inventario, detección de extensiones no soportadas,
  extracción de segmentos con rangos verificables, mapa de literales
  protegidos, ensamblado byte-a-byte sin reescritura libre.

#### Fases 021–030 — terminología y piloto

- 021–030: detección de idioma por región, protecciones, borrador de
  glosario, paquetes con presupuesto acotado, plantilla de
  traducción, traducción del piloto y aprobación humana antes de
  escalar.

#### Fases 031–040 — corpus y navegación

- 031–040: traducción del corpus en orden controlado, checkpoints
  atómicos, validador de respuestas, ensamblado por parches,
  preservación de tablas y marcas inline, detección de cambios
  numéricos, mapa de anclas con algoritmo fijado, reescritura de
  fragmentos y cierre del ledger del corpus solicitado.

#### Fases 041–050 — calidad y beta

- 041–050: validación determinista, auditoría semántica, ronda de
  correcciones, registro de issues, consolidación de terminología,
  copia de recursos, exportación local limpia, documentación de
  límites de Notion, recorrido end-to-end y paquete beta.

#### Fases 051–055 — robustez y núcleo estable

- 051: contenido adversarial tratado como dato; sin ejecución ni
  llamadas externas.
- 052: detección de errores de fidelidad conocidos (omisión,
  alteración, negación invertida, tabla recortada).
- 053: recuperación ante permisos denegados, disco lleno y cierre
  abrupto, sin exportación parcial.
- 054: endurecimiento de anclas y rutas (colisiones cross-doc,
  truncado de slugs, enlaces ambiguos bloqueados).
- 055: invalidador selectivo que distingue cambios de fuente,
  whitespace_only y no afectados.

#### Fases 056–060 — liberación

- 056: protección de ediciones manuales del destino, con estrategias
  `new-destination`, `preserve` y `patch`, y catálogo
  `output_hashes.json`.
- 057: procedimiento §9 de `references/operation.md` para límite de
  contexto y parada segura, con reanudación por `last_segment_id` e
  idempotencia de `translate_pilot.py`.
- 058: `scripts/check_distribution.py` verifica SKILL.md,
  referencias, scripts, dependencias pinneadas y artefactos
  prohibidos; nunca se autoinstala.
- 059: `scripts/test_release.py` emite `RELEASE_NOTES.md` con
  secciones explícitas de pruebas automáticas, revisión asistida,
  revisión humana y Notion no verificado.
- 060: este `CHANGELOG.md` y `RELEASE.md` declaran el núcleo estable
  para el dialecto probado, sin afirmar garantía semántica absoluta.

### 0.1.1 — par experimental fr→es (fases 101, 102, 104, 105 + 103 asistida)

Subrelease que añade soporte **experimental** para el par `fr → es`,
sin afectar el núcleo estable.

- 101 ✅: corpus piloto derivado CC0 en
  `tests/fixtures/pilot-fr/`, documentado en `evals/cases/pilot-fr.md`,
  perfil `fr-es-experimental-v1` añadido a `references/dialect-profiles.md`
  y `scripts/dialect_matrix.py`.
- 102 ✅: política lingüística del origen francés en
  `references/source-language-policy-fr.md` (modalidad, puntuación,
  acentos, falsos amigos ≥ 6, sin localizar números ni unidades).
- 103 ✅ ⚠: `scripts/eval_pair.py` ejecuta la cadena determinista
  sobre el piloto fr y emite
  `reports/fr-es-pilot/{eval.json,summary.md,citations.json,packets.json,...}`.
  **Revisión asistida registrada; pendiente de firma humana nativa
  en fr.** El manifiesto lleva `evaluation_kind: assisted` y
  `reviewer_status: assisted_only_pending_human`. No se afirma
  equivalencia semántica.
- 104 ✅: `schemas/profile.schema.json` (campos `mixed_profile`,
  `source_language_policy`, `citations_policy`, `reviewer_status`),
  `schemas/segment.schema.json` (campos `citation_type`,
  `detected_language`, `declared_language`), `scripts/detect_language.py
  --recognized`, `scripts/packetize.py --mixed-profile`. Fixture en
  `tests/fixtures/mixed_lang/` y prueba `tests/test_mixed_profile.py`.
  Los paquetes de traducción ya no mezclan segmentos de idiomas
  distintos.
- 105 ✅: política de citas en `references/citations-policy.md`,
  clasificador en `scripts/citations.py`, fixture en
  `tests/fixtures/citations/`, prueba
  `tests/test_citations_policy.py`. Tres categorías explícitas:
  `contractual`, `technical_literal`, `translatable_prose`.

Cobertura de pruebas añadida: 35 tests nuevos
(`tests/test_pilot_fr.py`, `tests/test_source_language_policy_fr.py`,
`tests/test_citations_policy.py`, `tests/test_mixed_profile.py`,
`tests/test_eval_fr.py`). Regresión del núcleo: 483 tests pasan,
2 skipped.

### 0.1.2 — variantes regionales, RTL ar→es, matriz lingüística (fases 106-108 ✅, 109-110 ✅ ⚠)

Subrelease que añade tres variantes regionales del español
(`es-ES`, `es-MX`, `es-AR`), soporte para el par `ar → es`, política
de citas por revisor y matriz lingüística.

- 106 ✅: `references/locale-policy.md` enumera tres variantes; lista
  cerrada de coloquialismos (vosotros / coche / ordenador / vale /
  chido / carnal / che / boludo / pibe / guay / chaval); API, números
  y unidades fuera del alcance regional. `schemas/profile.schema.json`
  con campo `locale`. Tres perfiles `en-es-{es,mx,ar}-v1` en
  `references/dialect-profiles.md` y `scripts/dialect_matrix.py`.
  Fixture es-ES usa MDN traducido real; es-MX y es-AR son derivados
  CC0.
- 107 ✅: `scripts/eval_regional.py` ejecuta la cadena determinista
  por variante y `scripts/check_cache_isolation.py` recorre varias
  ejecuciones y verifica que ningún `packet_id` se reutilice entre
  variantes, y que cada ejecución declare `locale.variant`.
- 108 ✅: `references/rtl-policy.md`, `scripts/detect_text_direction.py`,
  `scripts/eval_rtl.py`. `schemas/segment.schema.json` con
  `text_direction ∈ {ltr, rtl, mixed}` y `digits ∈ {ascii,
  arabic_indic, arabic_eastern, other}`. Fixtures en `tests/fixtures/rtl/`
  (árabe) y `tests/fixtures/mix-ltr-rtl/`.
- 109 ✅ ⚠: `references/reviewer-policy.md` distingue
  explícitamente firma humana real de revisión asistida. El esquema
  `manifest.schema.json` admite `reviewers[]` con `kind: human|assisted`
  y slots `null` mientras no haya firmante. **No hay firmantes
  humanos designados todavía** para los pares nuevos (`en→es-ES/MX/AR`,
  `ar→es`); los slots quedan `null` con `evaluation_kind: assisted`.
- 110 ✅ ⚠: `scripts/language_matrix.py` y `reports/language_matrix.json`
  con 6 pares activos (`en-es` con `human_approved`, los demás con
  `assisted`). El umbral `stable` exige 3 pares con `evaluation_kind:
  human_approved`; el estado actual es `stable: false` hasta que dos
  pares adicionales consigan firma humana.

Cobertura de pruebas añadida: 41 tests nuevos
(`tests/test_locale_policy.py`, `tests/test_regional_eval.py`,
`tests/test_rtl_policy.py`, `tests/test_reviewer_policy.py`,
`tests/test_language_matrix.py`). Regresión del núcleo: 524 tests
pasan, 2 skipped.

### 0.1.3 — escala y separación autor/revisor (fases 111–115)

Subrelease que añade la **infraestructura de escala** sobre el corpus
real (`/Users/martin/Desktop/documentacion`, 4832 archivos `.md`)
y formaliza la separación autor/revisor.

- 111 ✅: `scripts/measure_execution.py` mide `inventory → prepare →
  detect_language → packetize` con `time.monotonic()`. El JSON
  resultante lleva `provider_known: false`, `cost_unknown: true`,
  `tokens_estimated: null` y `cost_estimated_usd: null` por
  política (AGENTS.md §1). El muestreo `--sample N` permite CI
  sin ejecutar el corpus completo. `schemas/execution_profile.schema.json`
  documenta el contrato. Muestreo de 30 archivos en
  `tests/fixtures/scale/` documentado en `evals/cases/corpus-full.md`.
- 112 ✅: `scripts/schedule_packets.py` ordena paquetes
  topológicamente. Dependencias de glosario (palabra completa,
  plural simple) y de anclas entre documentos. Ciclos
  rechazados con código no cero. `glossary_hash` se valida
  contra el `glossary.json` congelado.
  `schemas/packet_schedule.schema.json` y
  `references/scheduler-policy.md`.
- 113 ✅: `scripts/worker.py` toma una partición (`packet_ids`)
  y escribe candidatos vacíos en
  `work_root/workers/<worker_id>/translations/<packet_id>.json`.
  Verifica el hash del glosario antes y después de la ejecución;
  cualquier cambio se registra en `errors.jsonl`.
  `references/worker-protocol.md` formaliza la mensajería
  (`dispatch`, `candidate`, `progress`, `failure`).
- 114 ✅: `scripts/coordinator.py` centraliza la escritura del
  manifiesto. `fcntl.flock` con fallback a `threading.Lock`
  cuando el sistema no soporta `fcntl`. Conflicto sobre
  `segment_id` rechazado con código 9 (`409 Conflict`). Log
  persistente por evento (`coordination.log`).
- 115 ✅: `scripts/reviewer_role.py` toma un
  `candidate.json`, valida la ausencia de campos prohibidos
  (`author_notes`, `tokens_estimated`, `cost_estimated_usd`,
  `metadata.author`) y emite un JSONL de veredictos vacíos.
  Inputs contaminados se abortan con código 3.
  `references/reviewer-protocol.md` y
  `evals/rubric-distributed.md` formalizan la separación autor/
  revisor.

Cobertura de pruebas añadida: 37 tests nuevos (8+8+6+8+7). Regresión
del núcleo: 561 tests pasan, 2 skipped.

> Las fases 116–120 (concurrencia, fallback en serie, caché
> contextual, invalidez, gate de escala) **NO** entran en esta
> subrelease. Quedan condicionadas a que el usuario autorice la
> ejecución real sobre el corpus grande fuera de CI.

### 0.1.4 — concurrencia, caché contextual y gate de escala (fases 116–120)

Subrelease que cierra la sección L del roadmap. Protocolos y
scripts verificables; ejecución real sobre el corpus grande
queda a discreción del usuario.

- 116 ✅: `scripts/run_concurrent.py` lanza workers en
  `ThreadPoolExecutor` con particiones disjuntas y `--max-workers N`.
  Backoff exponencial (0.5s × 2 con techo en 8s, 3 reintentos).
  Captura `SIGINT`/`SIGTERM`, vuelca
  `reports/concurrency_log.json` con `graceful_shutdown`.
  `references/concurrency-policy.md`.
- 117 ✅: `scripts/run_serial.py` recorre el orden topológico con
  un solo worker `--id serial`. `scripts/diff_ledgers.py` compara
  dos manifiestos y reporta `only_in_a`, `only_in_b`,
  `conflicts_state`. `references/serial-fallback.md`.
- 118 ✅: `scripts/translation_cache.py` con clave compuesta
  `(segment_id, source_hash, glossary_hash, locale_variant)`.
  `store` y `lookup` por archivo; `reset` borra toda la raíz o
  por variante. `schemas/cache_entry.schema.json` y
  `references/translation-cache.md`.
- 119 ✅: `scripts/invalidate_cache.py` recorre el caché y
  detecta cambios de glosario (`--glossary-old/--glossary-new`)
  o de anclas (`--anchors-old/--anchors-new`). Idempotente.
  Extiende `references/translation-cache.md` con §7.
- 120 ✅: `scripts/gate_scale.py` ejecuta cinco checks:
  cobertura, ledger, regresión de enlaces, nuevos bloqueos,
  tolerancia de tiempo (default 10 %). Sin scope, el chequeo de
  cobertura queda como warning; con manifests sintéticos sobre
  `tests/fixtures/scale` los cinco checks pasan.

Cobertura de pruebas añadida: 34 tests nuevos (10+6+5+6+7). Regresión
del núcleo: 595 tests pasan, 2 skipped.

> Esta subrelease **no** ejecuta el corpus grande en CI. El
> muestreo de 30 archivos en `tests/fixtures/scale/` y los
> manifests sintéticos son la base de los tests. La activación
> del modo concurrente sobre los 4832 archivos del corpus real
> (`/Users/martin/Desktop/documentacion`) es decisión del
> usuario.

### 0.1.5 — entrega local, paquete ZIP y destinos (fases 131–140)

Subrelease que cierra la sección N del roadmap con un módulo de
entrega **opt-in**. No cambia los valores por defecto del núcleo:
`scripts/export.py` sigue entregando un árbol limpio y la traducción
canónica sigue siendo la referencia auditada.

- 131 ✅ ⚠: `schemas/import_evidence.schema.json`,
  `scripts/record_import_evidence.py` y
  `references/delivery-notion-checklist.md`. El checklist de muestra
  nace con `verified: false`, `remote_status: no_verificado` y todos los
  `remote_result` en `unknown`. Promover exige revisor humano con
  nombre, al menos un documento marcado como importado y evidencia por
  cada comprobación superada; si falta algo, el registro se degrada y
  el script sale con código 3. **No hay ninguna importación real en
  Notion**: la evidencia remota sigue pendiente.
- 132 ✅ ⚠: `--check-links` calcula la resolución local de enlaces sobre
  el árbol entregado usando los slugs `github-slug-v1`, y la reporta
  separada de `remote_result`, que sigue en `unknown`.
- 133 ✅ ⚠: `--matrix-out` emite `reports/import_matrix.json` con nueve
  construcciones por destino. Todas las celdas nacen `unverified`.
- 134 ✅: `schemas/delivery_profile.schema.json`,
  `scripts/adapt_delivery.py`, `references/delivery-contract.md` y el
  perfil `references/delivery-profiles/plain-markdown-local.json` con dos
  reglas `lossiness: none`. Sin reglas la copia es byte a byte idéntica;
  el canónico no se escribe y el informe publica sus hashes antes y
  después. El bloque `delivery` de `schemas/profile.schema.json` exige
  destino y perfil si se activa, y queda desactivado por defecto.
- 135 ✅: `scripts/export_zip.py` y
  `schemas/delivery_package.schema.json`. Un solo directorio raíz,
  orden estable y fecha fija: el mismo árbol produce el mismo ZIP byte a
  byte. Excluye `manifest.json`, `glossary.json`, `reports/`, caches y
  temporales, declarando cada exclusión con motivo.
- 136 ✅: `scripts/validate_zip_package.py` comprueba conjunto de
  miembros, unicidad, SHA-256 por miembro, rutas relativas POSIX sin
  `..`, ausencia de symlinks y pertenencia al alcance aprobado del
  manifiesto.
- 137 ✅: `scripts/render_delivery_guide.py` escribe `DELIVERY.md` y
  `delivery_manifest.json` en `reports/delivery/<run_id>/`, fuera del
  árbol importable y del paquete, con las diez secciones obligatorias y
  el estado remoto real.
- 138 ✅: `scripts/compare_delivery.py` clasifica cada diferencia entre
  adaptado y canónico en `format_only`, `degraded_documented` o
  `content_loss`. Compara encabezados, bloques y código inline, tablas,
  listas y prosa normalizada. Cualquier pérdida de contenido devuelve
  código 3.
- 139 ✅ ⚠: `scripts/delivery_matrix.py` y
  `references/delivery-matrix.md` con los destinos `notion-manual` y
  `plain-markdown-local`. El segundo es un **adaptador interno**, no una
  aplicación de escritorio: declara `real_app_evidence: false` y su
  evidencia es `local_fixture_only`, porque no hay ningún importador
  local instalado en el entorno. El artefacto generado queda en
  `reports/delivery_matrix.json`.
- 140 ✅: `scripts/gate_delivery.py` y `references/delivery-gate.md`
  con siete comprobaciones y códigos de salida 1 a 7. Revalida el
  paquete en vivo en lugar de confiar solo en el informe de la fase 136.

Cobertura de pruebas añadida: 71 tests nuevos
(`tests/test_import_evidence.py` 11,
`tests/test_adapt_delivery.py` 11,
`tests/test_export_zip.py` 10,
`tests/test_delivery_guide.py` 7,
`tests/test_compare_delivery.py` 8,
`tests/test_delivery_matrix.py` 5,
`tests/test_gate_delivery.py` 10,
`tests/test_delivery_docs.py` 9). Regresión del núcleo: **723 tests
pasan, 2 skipped**, los mismos dos skips que antes del lote.

Recorrido verificado sobre `tests/fixtures/pilot/` (9 documentos
reales): 28 enlaces con resolución local correcta, 18 rutas relativas
al sitio registradas como deuda de entrada, 0 enlaces rotos, 0
pérdidas de contenido, paquete de 9 miembros validado y gate de
entrega en verde con sus siete comprobaciones. Ese recorrido detectó
dos defectos que quedaron corregidos: el resolvedor ignoraba las anclas
`<a id="…"></a>` del corpus real y la regla de rutas rompía los enlaces
con raíz del sitio.

### 0.2.0 — mantenimiento y release ampliado (fases 141–150)

Subrelease que añade el bloque de mantenimiento y activa en el
candidato **todos los módulos ya construidos**. No cambia ningún valor
por defecto del núcleo: sin perfil de entrega, sin perfil mixto, sin
RTL y sin revisión ampliada el comportamiento es el de 0.1.5.

Esta entrada se completa fase a fase conforme se ejecuta el lote; el
acta de la fase 150 recoge el resultado final con los conteos reales.

#### Fases 141–150 — mantenimiento

- 141: corpus permanente de regresión en `evals/regression/registry.json`
  con 22 fallos conocidos, cada uno con caso positivo y negativo
  reproducibles, `scripts/regression_detectors.py`, su gate
  `scripts/regression_gate.py` y la procedencia en
  `evals/regression/PROVENANCE.md`.
- 142: `release_contract.json` + `schemas/release_contract.schema.json` +
  `references/versioning-policy.md` + `scripts/check_versioning.py`.
  Todas las referencias llevan marca de versión y todos los esquemas
  declaran `x-schema-version`.
- 143: `manifest.schema.json` sube a `x-schema-version` 1.1.0 con
  `manifest_version`, `migrations[]`, `approval.stale` y
  `file_record.requires_revalidation`. `scripts/migrate_manifest.py`
  migra `translate/v0` → `v1` y nunca fabrica una aprobación vigente.
- 144: `scripts/compare_parser.py` + `references/parser-upgrade.md`.
  Comparación real ejecutada: 3.0.0 frente a 2.2.0 en una venv aislada
  sobre los 9 documentos del piloto, con rangos, slugs y recuentos
  idénticos. Comprobado que no existe versión publicada posterior.
- 145: `scripts/record_model_run.py` y `scripts/compare_model_runs.py` +
  `references/model-variation.md`. Una ejecución real registrada
  (`run-0000d3mo`, 10 segmentos del piloto, modelo activo de la sesión).
  Falta la segunda ejecución: la fila queda con aviso.
- 146: `scripts/audit_docs.py` + `references/rule-registry.json` +
  `references/content-audit.md`. La primera ejecución encontró cuatro
  rutas rotas en la documentación y las corrigió.
- 147: `scripts/probe_platform.py` + `scripts/check_portability.py` +
  `references/portability.md`. macOS y Linux verificados con ejecución
  real; Windows en `design_only`.
- 148: `references/workdir-retention.md` + `scripts/purge_workdir.py`.
  `references/log-redaction.md` deja de remitir a una fase inexistente.
- 149: `schemas/release_candidate.schema.json` +
  `scripts/build_release_candidate.py` + `scripts/gate_extended.py` +
  `references/release-gate.md`. El candidato activa los nueve módulos
  más el de mantenimiento, cada uno con su gate, y declara seis huecos
  externos con responsable y procedimiento.
- 150: acta en `evals/release/RELEASE_NOTES_0.2.0.md`.

#### Cambios fuera del número de fase

- `requirements.txt` pasa de estar vacío a declarar `markdown-it-py`,
  `jsonschema`, `pytest` y `langdetect` con versión fijada. `langdetect`
  ya lo importaba `scripts/detect_language.py` y no estaba declarado: en
  un entorno limpio el clasificador no arrancaba.
- 78 pruebas fijaban el directorio temporal de macOS en su código. Ahora
  usan `tempfile.gettempdir()` mediante `tests/conftest.py`.
- `scripts/validate.py` ya no se salta la comprobación de marcadores en
  documentos sin literales protegidos.
- `tests/test_inventory.py::test_rechaza_colision_por_unicode` creaba dos
  veces la misma forma normalizada y nunca comprobaba nada en macOS.
- `tests/test_export.py::test_export_aborta_si_destino_existe_sin_force`
  depended de un directorio vacío, que no choca con nadie.
- Cuatro referencias apuntaban a rutas inexistentes y se corrigieron.

#### Evidencia de esta subrelease

| Sistema | Resultado |
|---|---|
| macOS, Python 3.9.6 | 934 pruebas pasan, 2 omitidas |
| Linux, Python 3.12.15 (`python:3.12-slim`) | 936 pruebas pasan, 0 fallan |

Detalle y huellas en `evals/release/RELEASE_NOTES_0.2.0.md`.