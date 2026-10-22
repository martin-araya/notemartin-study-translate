# Informe beta (fase 050) — avance 2026-10-21

> **Cifras desfasadas.** Este documento se escribió el 2026-10-21 y sus
> §5, §9 y §11 quedaron desfasados tras los lotes 0001 y 0002. El estado
> vigente, medido sobre los mismos artefactos, está en
> [`reports/core/ESTADO-G-CORE.md`](../core/ESTADO-G-CORE.md). Este
> documento se conserva porque su §1, §7 y §8 documentan los defectos ya
> corregidos y su procedimiento sigue siendo válido.

**Run:** `run-7fbd5e24` (antes `run-beta-001`) · **Estado: NO APROBADO**

Este informe dice qué se corrigió y qué se verificó desde el cierre del
2026-10-20. **Ninguna casilla de `G-BETA` se marca.** La traducción del
corpus está en 43 de 44 293 segmentos.

## 1. Defectos reales encontrados y corregidos

Los cuatro los destapó el intento de ejecutar la fase. Los tres primeros
afectaban a la procedencia de la corrida; el cuarto, al contrato de
literales.

| # | Defecto | Dónde | Invariante | Prueba |
|---|---|---|---|---|
| 1 | `build_manifest.py` escribía `current_state: translated` y fabricaba la transición en `state_history`. Con 0 segmentos traducidos, el manifiesto anunciaba 2 682 archivos traducidos | `scripts/build_manifest.py` | INV-12 | `tests/test_build_manifest.py::test_no_declara_traducido_antes_de_traducir` |
| 2 | `--run-id` sin validación: `run-beta-001` se escribía a disco y solo después el esquema lo rechazaba | `scripts/build_manifest.py` | C-RUN | `tests/test_build_manifest.py::test_un_run_id_invalido_aborta_sin_escribir` |
| 3 | `advance_state --from prepared` movió los 2 682 archivos a `translated` sin comprobar que exista traducción alguna | `scripts/advance_state.py` | INV-12 | `tests/test_advance_state.py::test_no_avanza_sin_evidencia_de_traduccion` |
| 4 | `receive_translations` conservaba los marcadores `§§…§§` en `translated_text`, y `validate.py` rechazaba el documento entero por ello | `scripts/receive_translations.py` | INV-05 | `tests/test_receive_translations.py::test_los_marcadores_se_retiran_de_la_respuesta_persistente` |

El defecto 3 se detectó **usando la herramienta durante esta corrida**:
la llamada avanzó 2 682 archivos y se revirtió de inmediato. La
reparación añade `--translations`, que exige traducción persistida para
avanzar a un estado de trabajo. Descartar un documento (`blocked`,
`failed`, `excluded`) no la exige, porque no afirma trabajo hecho.

El defecto 4 también lo encontró `validate.py`, no el agente: el
documento ensamblado falló el control de protección con el mensaje
`marcador '§§' presente en translated_text`. Los marcadores son
instrumental del paquete, no carga útil de la entrega.

## 2. Manifiesto reparado

`work/run-beta-001/manifest.json` declaraba los 2 682 archivos en
`translated`. Ahora:

```
prepared: 2681 · translated: 1 · bloqueados: 0 · excluidos: 0
integrity_ok: false
```

El `run_id` era `run-beta-001`, que no cumple `^run-[0-9a-f]{8}$`.
Normalizado a `run-7fbd5e24` (ocho hex derivados del SHA-256 del
nombre original, para que sea auditable). El manifiesto valida contra
`schemas/manifest.schema.json`.

Cada reparación quedó registrada en `migrations[]` con su motivo, y cada
archivo lleva la nota correspondiente en `notes[]`.

## 3. Disposiciones resueltas con evidencia

`reports/beta/summary.md` (2026-10-20) decía que `unknown` (2 929) y
`mixed_or_code` (2 270) necesitaban una decisión del usuario. Las dos
categorías no eran una decisión terminológica: eran falta de decisión del
clasificador. `scripts/resolve_dispositions.py` las resuelve midiendo
prosa real tras enmascarar los literales protegidos.

| Entrada | Antes | Después |
|---|---|---|
| `unknown` 2 929 | — | `code_skip` 2 260 · `translatable` 562 · `too_short` 107 |
| `mixed_or_code` 2 270 | — | `code_skip` 2 166 · `translatable` 90 · `too_short` 14 |
| `too_short` 2 813 | — | `code_skip` 2 649 · `too_short` 164 |

La medición corrigió la hipótesis del informe anterior. `mixed_or_code`
no era «párrafos con mucha referencia inline»: de sus 2 270 segmentos,
**2 226 son tipos genéricos de TypeScript entre acentos graves**
(`InputSignal<boolean>`, `` MetadataReducer<boolean, boolean> ``), que
son literales protegidos, no prosa. Solo 90 tienen prosa traducible.
Lo mismo con `unknown`: 2 260 son rutas de módulo, rutas de archivo o
etiquetas de enlace.

Disposición final de los 70 972 segmentos:

| Disposición | Segmentos |
|---|---|
| `translatable` | 44 293 |
| `code_skip` | 19 443 |
| `no_text` | 5 654 |
| `already_target` | 1 297 |
| `too_short` | 285 |

Ningún segmento queda `unknown`. Ninguna categoría se descartó para
mejorar una métrica: las 5 202 que no son traducibles tienen disposición
explícita con su motivo en `disposition_reason`, y siguen contando en
el denominador.

## 4. Traducción entregada y verificada

Un documento completo del corpus real, no un fixture:

`nextjs/messages/blocking-prerender-client-hook.md` (`doc-f0342fb5`) —
7 paquetes, 43 segmentos, 51 líneas de prosa.

| Comprobación | Resultado |
|---|---|
| `receive_translations.py` | 7/7 paquetes aceptados, 0 hallazgos |
| Literal perdido | 0 (marcadores restaurados tras un hallazgo real) |
| Marcadores en la entrega | 0 |
| `assemble.py` | 15 354 bytes, parche por rangos |
| `validate.py` protección | 0 errores |
| `validate.py` destinos | 32 segmentos, 20 fragmentos, 0 errores |
| `copy_resources.py` | 66 recursos, 0 desajustes, 0 ausentes |

El texto traducido conserva los 32 literales protegidos (`usePathname`,
`<Suspense>`, `has-data-active:font-bold`, ` next build --debug-prerender `,
`Math.random()`, los `<a id>`) y las URL externas byte a byte.

## 5. Lo que sigue sin hacerse

> El detalle completo, con volumen medido por directorio, tamaño de lote
> y los once pasos pendientes, está en
> [`PLAN_PENDIENTE.md`](PLAN_PENDIENTE.md).

| Paso | Estado |
|---|---|
| Traducir 44 741 segmentos restantes | pendiente |
| Revisión semántica | no ejecutada: depende de traducción |
| Aprobación por estado | 1 de 2 682 documentos |
| Exportación | `export.py` rechaza el gate: revalida y encuentra el corpus incompleto |

`export.py` se ejecutó y **no promovió nada a `output/`**. Su mensaje
fue `validate.py falló`, y no dejó carpeta parcial. Es el comportamiento
correcto: una traducción del 0,1 % del corpus no se presenta como corpus
completo (INV-12).

Los dos bloqueos que impedían empezar a traducir están resueltos: las
colisiones de `document_id` y de `packet_id` (§7) y el recuento de
3 110 colisiones de anclas (§8, que no eran bloqueantes). Quedó una
decisión del usuario sobre los segmentos `already_target` (§9): **se
quedan fuera** del corpus traducible. Está registrada como
`dec-20261021` en `manifest.json`'s `decisions[]`, con motivo y rutas.
215 segmentos en 188 archivos permanecen como `already_target`:
107 etiquetas en inglés de la referencia de Angular + 20 frases en
inglés + 88 etiquetas que replican el fragmento (su idioma lo decide
la reescritura de anclas).

### Volumen real que falta

| Métrica | Valor |
|---|---|
| Segmentos traducibles (`segments_v2.json`) | 44 784 |
| Traducidos | 43 |
| Caracteres pendientes (medido sobre los paquetes) | 7 584 411 |
| Caracteres traducidos | 5 476 |
| Porcentaje | 0,10 % |

La cifra de 44 293 del informe anterior venía de `segments_resolved.json`.
`segments_v2.json` tiene 491 segmentos traducibles más: al trocear los
191 segmentos sobredimensionados en 682 trozos, cada trozo es un segmento
traducible propio. Los 191 originales quedan `superseded_by_split`.

Los 7,6 millones de caracteres son ≈2,4 millones de tokens de salida.
No caben en una sesión, y `AGENTS.md` §11 prohíbe responder en versión
abreviada para hacerlos caber. El trabajo continúa por lotes con
checkpoint, en sesiones sucesivas.

## 6. Procedimiento verificado para continuar

```bash
W=/Users/martin/Desktop/projects/notemartin-beta/work/run-beta-001
SK=/Users/martin/Desktop/projects/Skills/notemartin-study-translate

# 0. Ver el plan: qué falta, por directorio, en orden de riesgo
python3 $SK/scripts/select_lote.py --packets $W/packets_v3.json \
  --segments $W/segments_v2.json --translations $W/translations --order

# 1. Preparar el sobre del siguiente lote
python3 $SK/scripts/select_lote.py --packets $W/packets_v3.json \
  --segments $W/segments_v2.json --translations $W/translations \
  --size 6000 --lote-id <N> --out $W/lotes/lote-<N>-sobre.json

# 2. Escribir las respuestas y validarlas
python3 $SK/scripts/receive_translations.py \
  --packets $W/packets_v3.json --segments $W/segments_v2.json \
  --responses $W/lotes/lote-<N>.json --translations $W/translations \
  --report $W/lotes/lote-<N>-reporte.json --apply

# 3. Ensamblar y validar
python3 $SK/scripts/assemble.py --source <FUENTE>/<RUTA.md> \
  --segments $W/segments_v2.json --out $W/staged/<RUTA.md> \
  --translations $W/translations

python3 $SK/scripts/validate.py --source <FUENTE> --output-dir $W/staged \
  --packets $W/packets_v3.json --segments $W/segments_v2.json \
  --translations $W/translations --snapshots $W/snapshots.json \
  --anchors $W/anchors.json --manifest $W/manifest.json \
  --out $W/validate.json --require-assembled

# 4. Avanzar el estado solo de lo traducido, con evidencia
python3 $SK/scripts/advance_state.py --manifest $W/manifest.json \
  --to translated --from prepared --translations $W/translations \
  --reason 'traduccion real entregada y validada' --apply
```

`assemble.py` resuelve solo la clave de traducción. Si un paquete y su
documento tienen `document_id` ambiguo, la ruta desambigua; no hace
falta pasar nada a mano. El argumento `--translation-id` existe para
cuando la ruta no basta, y no se ha necesitado en el corpus real.

## 6bis. Subdivisión de los 191 paquetes con desborde (2026-10-21)

Los 191 paquetes con `overflow: true` contenían **un solo segmento**
cada uno. Partir «por segmento», como proponía el plan, no los divide:
no hay más segmentos que repartir. La unidad de corte correcta resultó
ser la **línea** dentro del segmento.

`scripts/rebuild_overflow_packets.py` trocea el `byte_range` del segmento
en tramos consecutivos que caben en `context_budget` (1 500), sin cortar
un literal protegido, sin partir una fila de tabla y sin cortar por medio
de un carácter multibyte. Los tramos se reempaquetan con
`packetize.pack_file`, así que heredan el mismo contrato que el resto del
corpus.

| Medida | Antes | Después |
|---|---|---|
| Paquetes con `overflow` | 191 | **0** |
| Paquetes totales | 6 604 | 6 927 |
| Paquete más largo | 61 454 chars | 1 500 chars |
| Mediana por paquete | 1 244 chars | 1 267 chars |
| Errores de validación de paquete | — | 0 |
| Documentos con identidad byte a byte | — | **98 / 98** |
| Trozos generados | — | 682 |

Artefactos: `packets_v2.json`, `segments_v2.json`,
`reports/rebuild_overflow.json`. El original queda en
`packets.original.json`. La fuente no se tocó (INV-01).

La mediana sube de 1 244 a 1 267: al partir los segmentos sobredimensionados
los paquetes quedan más uniformes. El criterio «mediana ≤ 1 244» que
figuraba en el plan era una línea base descriptiva, no un umbral de
calidad; el umbral real es `context_budget`, y se cumple.

### 6.1 Tres defectos encontrados al implementar la subdivisión

| # | Defecto | Invariante | Prueba |
|---|---|---|---|
| 6 | La asignación de literalesprotected buscaba por valor con `str.find`, que siempre devuelve la primera aparición. Un literal repetido se declaraba dos veces en el primer tramo y ninguna en el segundo: marcadores duplicados y `validate_packet` rechazaba el paquete | INV-05 | `test_literal_repetido_no_se_declara_dos_veces_en_el_mismo_trozo` |
| 7 | Al reempaquetar un documento se retiraban solo sus paquetes `overflow`. Los segmentos que no cambiaban quedaban en dos paquetes con dos propietarios, sin que ningún validador por paquete lo notara | INV-03 | `test_reempaquetar_no_deja_ningun_segmento_sin_propietario_unico` |
| 8 | Los primeros cortes comparaban un offset de byte con un índice de carácter; con acentos, el literal se asignaba al tramo equivocado | INV-05 | `test_los_cortes_caen_en_limites_utf8_validos` |

El defecto 7 es el relevante: 329 identificadores de paquete duplicados y
3 365 segmentos con doble propietario, introducidos por la propia
remediación. Lo detecta `_assert_single_owner`, que vigila **solo** lo que
el script genera. Sin ese control el error habría llegado al corpus.

Los defectos 6, 7 y 8 se corrigieron con pruebas de regresión. El defecto
**9** que sigue se encontró al verificar la remediación de §7: `packet_id`
también colisionaba, por la misma raíz, y afectaba a 53 paquetes.

| 9 | `packet_id` se derivaba de `document_id` + `segment_id`, ambos derivados de bytes. Ocho ids quedaron duplicados entre 53 paquetes; una respuesta se resolvía al último del grupo sin emitir hallazgo | INV-03 | `test_inyectar_renombra_los_packet_id_duplicados` |

## 7. Defecto de entrada de `document_id`: **CORREGIDO**

La subdivisión reveló una deuda **preexistente**, medida sobre
`packets.original.json` y no introducida aquí:

| Métrica | Valor |
|---|---|
| `document_id` reutilizados entre rutas distintas | **15** |
| Rutas afectadas | **214** |
| `segment_id` repetidos | **14** (hasta 20 repeticiones) |
| Segmentos en más de un paquete | 8 |

`prepare.py` deriva `document_id` de los **bytes** del archivo:

```python
document_id = "doc-" + sha256_hex(source_bytes)[:8]
```

Dos rutas con contenido byte a byte idéntico lo comparten. Comprobado
sobre el corpus: las cuatro páginas stub de
`tailwindcss/installation/` pesan 15 bytes cada una, contienen
`\n# Hello world!` y las cuatro son `doc-085fb377`.

**Por qué bloqueaba:** `receive_translations.py` persistía en
`translations/<document_id>.json`. Con un identificador compartido, la
traducción de un archivo se escribía junto a la de otro y el parche de
`assemble.py` se aplicaba sobre el documento equivocado.

### 7.1 Y un segundo defecto, de la misma raíz

`packet_id` se derivaba de `document_id` + `segment_id`, y **ambos**
derivan de los bytes. El resultado era el mismo a un nivel más alto:
**8 `packet_id` duplicados que afectaban a 53 paquetes**, uno de ellos
compartido por 20 rutas (`pack-13a84a72`).

Este es más grave que el anterior. `receive_translations.py` indexa los
paquetes en un dict por id, así que una respuesta que nombraba
`pack-efe1b073` se resolvía al último de los doce paquetes del grupo y
el trabajo de los otros once se perdía **sin emitir ningún hallazgo**.
Ningún validador por paquete lo detectaba.

### 7.2 Remediación aplicada: la clave de persistencia lleva la ruta

Se introduce `translation_id`, que es `document_id` más la ruta:

```python
translation_id = "trl-" + sha256(f"{document_id}|{ruta}")[:12]
```

`document_id` **no se regenera**. Conserva su significado real —la
clase de equivalencia de contenido, que es valuable para agrupar y para
la trazabilidad— y la colisión se resuelve solo en el lado de la
persistencia. Ver `scripts/translation_key.py`.

**Por qué no se renombran los 2 682 archivos.** Solo colisionan los
documentos ambiguos. Renombrar todos invalidaría el manifiesto, los
hashes de procedencia y la traducción ya entregada de `doc-f0342fb5`
(43 segmentos) sin ganar nada: el 92 % de las claves no ambigüas ya
era correcta. La clave de contenido se conserva cuando no hay
ambigüedad y la clave con ruta se usa cuando la hay. Un archivo tocado
por la remediación conserva su nombre; los demás no se mueven.

`scripts/inject_translation_ids.py` aplica la cambio a los paquetes ya
construidos **sin reempaquetar**: los 6 927 paquetes ya declaraban
`path`, así que la clave se calcula sin releer la fuente ni regenerar un
único `segment_id`. Los `packet_id` duplicados sí se renombraron, y
`packet_id_renames` registra el mapa viejo → nuevo por si alguna
respuesta anterior los nombra.

### 7.3 Evidencia medida

| Medida | Antes | Después |
|---|---|---|
| `document_id` ambiguos | 15 | 15 (se conservan: son la clase de equivalencia) |
| Rutas que comparten archivo de traducción | 214 | **0** |
| Paquetes con clave nueva | — | 61 |
| Paquetes que conservan `document_id` | — | 6 866 |
| `packet_id` duplicados | 8 (53 paquetes) | **0** |
| Paquetes renombrados | — | 61 |
| Doble propietario por `(ruta, segment_id)` | — | **0** |

Prueba de extremo a extremo sobre el corpus real: se entregaron 61
paquetes de las rutas colisionadas, cada uno con un marcador que
contiene **su** ruta.

| | Archivos escritos | Rutas cuyo contenido corresponde a otra |
|---|---|---|
| Antes | **8** | 53 perdidas sin aviso |
| Después | **61** | **0** |

Y la traducción ya entregada se conserva byte a byte: `assemble.py`
sobre `nextjs/messages/blocking-prerender-client-hook.md` produce los
mismos 15 354 bytes que antes de la remediación.

`validate.py` da los mismos 5 errores con `packets_v2.json` y con
`packets_v3.json` —4 documentos de `tailwindcss` sin ensamblar y la
cobertura incompleta—, que es el estado honesto de un corpus al 0,1 %.

La fuente no se tocó (INV-01). Los 98 documentos comprobados por
`rebuild_overflow_packets.py` siguen siendo idénticos byte a byte.

---

## 8. Colisiones de anclas: el recuento que no era un bloqueo

`PLAN_PENDIENTE.md` §4 listaba «3 110 colisiones de anclas» entre los
riesgos del trabajo. Medido con `scripts/dump_anchor_collisions.py`:

| Clase | Valor | ¿Bloquea? |
|---|---|---|
| Colisiones **dentro** de un documento | **0** | — |
| Anclas compartidas **entre** documentos | 3 110 | No |

Un fragmento solo se resuelve dentro del documento que lo contiene.
Reutilizar un slug entre rutas distintas no rompe la navegación:
`api-api` aparece en 1 113 rutas porque cada página de la referencia de
Angular tiene su propio encabezado `## API`.

**Cero colisiones intra-documento en los 2 483 documentos con mapa de
anclas.** El riesgo que `PLAN_PENDIENTE.md` declaraba no existe, y la
reescritura de fragmentos del paso 8 deja de estar condicionada por él.

---

## 9. Verificación de `already_target`: 127 de 1 297 no la sostienen

Los 1 297 segmentos con disposición `already_target` no se reescriben:
se comprueban (`scripts/verify_already_target.py`).

| Veredicto | Segmentos | Qué significa |
|---|---|---|
| `spanish_prose` | 1 037 | prosa en español; la disposición se sostiene |
| `english_label` | 107 | etiqueta de interfaz generada por Angular, en inglés |
| `link_label_pending` | 88 | la etiqueta replica el fragmento; la resuelve la reescritura de anclas |
| `spanish_label` | 45 | etiqueta sin residuo detectable |
| `english_prose` | 20 | frase entera en inglés |

| Directorio | `english_label` | `english_prose` |
|---|---|---|
| `angular` | 98 | 7 |
| `nextjs` | 8 | 2 |
| `oracle` | 1 | 11 |

El hallazgo es real pero acotado: **215 segmentos en 188 archivos no
sostienen la disposición**. 127 (9,8 %) son `english_label` o
`english_prose` — casi todos etiquetas de la referencia generada por
Angular (`Type Alias`, `function`, `stable`), que nunca entrarían en la
traducción. Los 88 restantes son `link_label_pending`, etiquetas que
replican el fragmento y cuyo idioma lo decide la reescritura de
anclas, no este paso.

Reetiquetar las 127 cambiaría el denominador de cobertura y por
tanto el resultado del gate, así que **la decisión es del usuario**.
El script no reescribe nada. Decisión tomada: **se quedan fuera**,
registrada como `dec-20261021` (`kind: defer`, role `owner`) en
`manifest.json`'s `decisions[]`, con motivo, hashes de los informes
revisados y las 188 rutas en `scope`.

### 9.1 Tres iteraciones del detector, con el número medido

El detector de residuo inglés es la parte donde este trabajo más se
equivocó. Tres versiones, sobre los mismos 1 297 segmentos:

| Versión | Falsos positivos | Causa |
|---|---|---|
| 1 | **884** | Acusaba token a token: cualquier palabra con guion («sub-sección») o con mayúscula interna («TypeScript») salía como inglesa. Es exactamente el error que el docstring de `detect_residual_language._looks_english` describe. |
| 2 | **386** | Filtraba por run, pero no distinguía la cita del PDF, el nombre de producto y la frase sin traducir. |
| 3 | **147** | Tres filtros añadidos, cada uno por un caso medido: se retiran las citas textuales, un run de solo nombres propios es un término, y **la frase que contiene el run debe carecer de evidencia española**. |

La última columna no es un ajuste de umbral: el filtro de frase usa
`_english_runs` y `_looks_english` del detector ya existente, para que
no haya dos detectores de residuo que den números distintos sobre el
mismo corpus. Las 20 entradas restantes se pueden leer una a una en
`reports/beta/already_target.md`.

---

## 10. Plan de traducción medido

`scripts/select_lote.py --order`, sobre `packets_v3.json`:

| Directorio | Paquetes | Pendientes | Caracteres | Documentos |
|---|---|---|---|---|
| `tailwindcss` | 99 | 99 | 33 119 | 76 |
| `oracle` | 477 | 477 | 622 790 | 17 |
| `angular` | 3 088 | 3 088 | 3 115 055 | 1 492 |
| `nextjs` | 3 263 | 3 257 | 3 813 447 | 908 |
| **total** | **6 927** | **6 921** | **7 584 411** | 2 493 |

Segmentos traducibles: **44 784**. La cifra del informe anterior (44 293)
era de `segments_resolved.json`; `segments_v2.json` tiene 491 más porque
al trocear los 191 segmentos sobredimensionados en 682 trozos, cada trozo
es un segmento traducible propio. Los 191 originales quedan marcados
`superseded_by_split`.

Lote `0001` preparado: `tailwindcss`, 80 paquetes, 87 segmentos,
11 497 caracteres. Los 61 paquetes de rutas colisionadas van en él, que
es justo donde la remediación tiene que aguantar.

---

## 11. Límites aceptados

- **No** se afirma equivalencia semántica: la revisión es asistida por
  agente y aún no se ha ejecutado.
- **No** se afirma verificación en Notion: `remote_status: no_verificado`.
- **No** se afirma cobertura del sitio remoto: solo de los Markdown
  recibidos (INV-16).
- Los 66 recursos de `oracle/resumenes/assets/` se copiaron con
  integridad verificada. Las rutas rotas del scraper
  (`resúmenes/assets/…` desde dentro de `resúmenes/`) siguen siendo
  `source_debt_missing_target`: no se reparan.
- Las 3 110 colisiones de anclas están registradas en
  `anchors.json/_collisions.json` y volcadas en
  `reports/beta/anchor-collisions.md`. **Son todas entre documentos y
  ninguna bloquea** (§8): 0 colisiones intra-documento.
- `packet_id_renames` de `packets_v3.json` es el mapa que permite
  reescribir una respuesta emitida antes de la reparación. Ninguna se
  emitió: los 43 segmentos entregados son de `nextjs/messages/`, fuera
  del grupo colisionado y con `packet_id` intacto.
- La subdivisión de los desbordes y la remediación de las colisiones
  están hechas y verificadas. **La traducción del corpus sigue en 43 de
  44 784 segmentos**, y ese sigue siendo el trabajo que bloquea
  G-BETA.
- Los 215 segmentos que no sostenían `already_target` (§9) están
  registrados como **fuera del corpus traducible** por la decisión
  `dec-20261021` en `manifest.json`. Permanecen `already_target`;
  ninguna los reconsiderará sin una nueva decisión.
- `G-BETA` sigue sin marcar. Marcarlo antes de traducir el corpus sería
  declarar un gate cumplido sin la cobertura que el gate mide.