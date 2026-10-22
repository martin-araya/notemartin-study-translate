# Qué falta para cerrar G-BETA (fase 050)

> **Cifras desfasadas.** Las de §1 quedaron desfasadas tras los lotes
> 0001 y 0002: el denominador de 44 784 sigue en pie, pero lo traducido
> ya no es 43 segmentos y 1 documento. El estado vigente está en
> [`reports/core/ESTADO-G-CORE.md`](../core/ESTADO-G-CORE.md). El
> procedimiento de §3 (pasos 1 a 11) sigue siendo válido y es el que se
> está ejecutando.

**Run:** `run-7fbd5e24` · **Estado:** NO APROBADO · **Medido:** 2026-10-21

Este documento dice exactamente qué está hecho, qué falta, en qué orden
y con qué evidencia se cierra cada paso. Las cifras son medidas sobre los
artefactos reales, no estimaciones.

> **Actualizado el 2026-10-21 (segunda ronda).** Los dos bloqueos que
> este documento declaraba ya están resueltos y medidos en
> [`summary.md`](summary.md) §7 y §8:
>
> - La colisión de `document_id` (15 ids, 214 rutas) tiene remediación
>   aplicada y verificada. Sale `packets_v3.json`.
> - La colisión de `packet_id` (8 ids, 53 paquetes), de la misma raíz,
>   también. No estaba en la primera redacción de este documento.
> - Las 3 110 colisiones de anclas **no eran un bloqueo**: son todas
>   entre documentos. Hay **0 intra-documento** en 2 483 documentos.
> - Los 1 297 segmentos `already_target` están verificados. 127 no
>   sostienen la disposición y esperan decisión del usuario.
>
> Usa `packets_v3.json` y `segments_v2.json` en los pasos 1 a 10. Los
> comandos de abajo ya están actualizados.

Las cuatro casillas de `roadmap.md` §8 G-BETA siguen sin marcar. Marcar
`G-BETA` antes de traducir el corpus sería declarar un gate cumplido sin
la cobertura que el gate mide.

---

## 1. Estado en una línea

| Métrica | Valor | Gate que mide |
|---|---|---|
| Segmentos traducibles | 44 293 | — |
| Segmentos traducidos | **43** (0,07 %) | Traducción completa |
| Documentos en `translated` | **1** de 2 682 | Traducción completa |
| Documentos aprobados | 0 | Cobertura |
| Documentos exportados | 0 | Cobertura |
| Recursos copiados | 66 de 66, 0 desajustes | Recursos |
| Bloqueos | 0 | Cero bloqueos |
| Regresiones nuevas de enlaces | 0 | Cero regresiones |
| Revisión semántica | no ejecutada | Cobertura |

Las tres últimas filas ya están verdes sobre el material disponible. Las
cuatro primeras no.

---

## 2. Lo que ya está hecho y verificado

### 2.1 Preparación (completa)

| Artefacto | Estado |
|---|---|
| Inventario | 2 682 Markdown + 66 recursos, 2 748 archivos |
| Segmentos | 70 972, con rango de bytes verificable |
| Clasificación de idioma | 70 972 clasificados |
| Paquetes | 6 604 construidos, 191 con desborde de presupuesto |
| Perfil | activo, con módulos opt-ins justificados |
| Glosario v3 | congelado, 146 entradas, hash `be1502643c0aa6c8…` |
| Mapa de anclas | 2 682 documentos, 3 110 colisiones registradas |

El hash del glosario en el manifiesto coincide con el hash del archivo en
disco. `frozen: true`. Verificado.

### 2.2 Disposiciones resueltas (completo)

Ninguno de los 70 972 segmentos queda sin decidir. Se resolvió con
`scripts/resolve_dispositions.py`, que mide la prosa que queda tras
enmascarar los literales protegidos:

| Disposición | Segmentos | Qué exige |
|---|---|---|
| `translatable` | 44 293 | traducción real + revisión |
| `code_skip` | 19 443 | presencia e integridad, no traducción |
| `no_text` | 5 654 | nada |
| `already_target` | 1 297 | verificar que está en español, no reescribir |
| `too_short` | 285 | nada |

Las 5 202 categorías que el informe anterior dejó sin decidir
(`unknown`, `mixed_or_code`, `too_short`) tienen disposición con motivo
en `disposition_reason`. Ninguna se descartó para mejorar una métrica:
siguen contando en el denominador.

### 2.3 Traducción entregada (1 documento)

`nextjs/messages/blocking-prerender-client-hook.md` (`doc-f0342fb5`),
7 paquetes, 43 segmentos traducidos a español.

| Comprobación | Resultado |
|---|---|
| `receive_translations.py` | 7/7 paquetes, 0 hallazgos |
| Literales protegidos perdidos | 0 |
| Marcadores `§§` en la entrega | 0 |
| `assemble.py` | 15 354 bytes por parche de rangos |
| `validate.py` protección | 0 errores |
| `validate.py` destinos | 32 segmentos, 20 fragmentos, 0 errores |
| `copy_resources.py` | 66 copiados, 0 desajustes, 0 ausentes |

### 2.4 Defectos corregidos en el intento (4)

Cada uno con prueba que falla antes del arreglo:

| # | Defecto | Invariante |
|---|---|---|
| 1 | `build_manifest.py` escribía `current_state: translated` con 0 segmentos traducidos | INV-12 |
| 2 | `--run-id` sin validar: escribía un manifiesto inválido a disco | C-RUN |
| 3 | `advance_state --from prepared` movió 2 682 archivos sin comprobar traducción | INV-12 |
| 4 | `receive_translations` dejaba los marcadores `§§…§§` en la entrega | INV-05 |
| 5 | `gate_scale.py` reventaba al pedir `--help` por un `%` sin escapar | usabilidad |

El defecto 3 se detectó usando la herramienta durante la corrida: la
llamada empujó los 2 682 archivos y se revirtió en el acto. La reparación
añade `--translations`, que exige traducción persistida para avanzar a un
estado de trabajo. Descartar (`blocked`, `failed`, `excluded`) no la
exige, porque no afirma trabajo hecho.

Suite: **1 077 pruebas verdes, 2 omitidas** (línea base 1 037).

### 2.5 Fuente inmutable (INV-01, verificado)

Hash de árbol `283c5a073dc8fe01127abb6e884d59546284827a879d66585c12492c338f8214`,
idéntico al registrado en `evals/cases/beta.md`. Los cuatro hashes por
directorio también coinciden. La fuente no se modificó.

---

## 3. Lo que falta, en orden

### Paso 1 · Traducir 44 741 segmentos

Es el 99,9 % del trabajo que falta. Volumen medido:

| Directorio | Paquetes | Caracteres pendientes | Documentos | Tokens de salida aprox. |
|---|---|---|---|---|
| `tailwindcss/` | 99 | 33 119 | 76 | 10 800 |
| `oracle/` | 477 | 622 790 | 17 | 202 400 |
| `angular/` | 3 088 | 3 115 055 | 1 492 | 1 012 400 |
| `nextjs/` | 3 257 | 3 813 447 | 908 | 1 239 300 |
| **total** | **6 921** | **7 584 411** | **2 493** | **≈2 465 000** |

Medido con `scripts/select_lote.py --order` sobre `packets_v3.json`.
Los 44 784 segmentos traducibles son el número de `segments_v2.json`; el
44 293 de la tabla anterior venía de `segments_v2.json` y no incluía
los 682 trozos en que se dividieron los segmentos sobredimensionados.

**Los 7,5 millones de caracteres no caben en una sesión.**
`AGENTS.md` §11 prohíbe responder en versión abreviada para hacerlos
caber. El trabajo se hace por lotes con checkpoint, en sesiones
sucesivas, y el estado vive en el manifiesto.

Procedimiento por lote:

```bash
W=/Users/martin/Desktop/projects/notemartin-beta/work/run-beta-001
SK=/Users/martin/Desktop/projects/Skills/notemartin-study-translate

# 1. Ver qué falta, por directorio, en orden de riesgo
python3 $SK/scripts/select_lote.py --packets $W/packets_v3.json \
  --segments $W/segments_v2.json --translations $W/translations --order

# 2. Preparar el sobre del lote. El sobre lleva `translation_id` ya
#    resuelto, así que las rutas colisionadas no se pisan entre sí.
python3 $SK/scripts/select_lote.py --packets $W/packets_v3.json \
  --segments $W/segments_v2.json --translations $W/translations \
  --size 6000 --lote-id <N> --out $W/lotes/lote-<N>-sobre.json

# 3. Escribir las respuestas y validarlas
python3 $SK/scripts/receive_translations.py \
  --packets $W/packets_v3.json --segments $W/segments_v2.json \
  --responses $W/lotes/lote-<N>.json --translations $W/translations \
  --report $W/lotes/lote-<N>-reporte.json --apply

# 4. Ensamblar cada documento del lote. La clave se resuelve sola de
#    document_id + ruta; no hace falta pasar --translation-id.
python3 $SK/scripts/assemble.py --source <FUENTE>/<RUTA.md> \
  --segments $W/segments_v2.json --out $W/staged/<RUTA.md> \
  --translations $W/translations

# 5. Validar el conjunto
python3 $SK/scripts/validate.py --source <FUENTE> --output-dir $W/staged \
  --packets $W/packets_v3.json --segments $W/segments_v2.json \
  --translations $W/translations --snapshots $W/snapshots.json \
  --anchors $W/anchors.json --manifest $W/manifest.json \
  --out $W/validate.json --require-assembled

# 6. Avanzar el estado SOLO de lo traducido
python3 $SK/scripts/advance_state.py --manifest $W/manifest.json \
  --to translated --from prepared --translations $W/translations \
  --reason 'traduccion real entregada y validada' --apply
```

Un lote no cruza directorio a propósito: cada directorio tiene su propia
terminología, y mezclar `angular/api/` con `nextjs/messages/` haría que
un fallo en las tablas de parámetros no se pudiera atribuir.

Orden recomendado, de menor a mayor riesgo:

1. `tailwindcss/` (99 paquetes, 33 k) — tablas densas, corpus pequeño.
   Concentra además las 61 rutas con clave colisionada: es donde la
   remediación se prueba con trabajo real.
2. `oracle/resúmenes/` (477 paquetes, 623 k, 17 docs) — ya en español:
   son `already_target`, se **verifican**, no se reescriben.
3. `angular/` (3 088) — tablas de parámetros, donde se concentran las
   regresiones de cifras y valores por defecto.
4. `nextjs/` (3 257) — encabezados que se autolinkean, rutas escapadas.

Tamaño de lote: ~6 000 caracteres por paquete conjunto. A mediana de
1 267 caracteres por paquete, eso da **≈1 265 lotes**.

El lote `0001` ya está preparado en `$W/lotes/lote-0001-sobre.json`:
`tailwindcss`, 80 paquetes, 87 segmentos, 11 497 caracteres.

### Paso 2 · Los 191 paquetes con desborde de presupuesto — **RESUELTO 2026-10-21**

191 paquetes tienen `overflow: true`. Ninguno se podía traducir de una
sentada: el mayor tiene **61 454 caracteres en un solo segmento**
(`oracle/resúmenes/13_…`).

| Paquete | Caracteres | Segmentos | Documento |
|---|---|---|---|
| `pack-30b0505b` | 61 454 | 1 | `oracle/resúmenes/13_…` |
| `pack-f7417a74` | 21 186 | 1 | `oracle/resúmenes/13_…` |
| `pack-fe2ee43f` | 21 045 | 1 | `oracle/resúmenes/13_…` |
| `pack-57f9c7c8` | 18 210 | 1 | `oracle/resúmenes/09_…` |

45 paquetes superan 5 000 caracteres.

**Medición que cambió el método:** los 191 paquetes contienen **un solo
segmento** cada uno. Partir «por segmento» no los divide. La unidad de
corte es la **línea** dentro del segmento.

Hecho con `scripts/rebuild_overflow_packets.py`. Resultado medido:

| Métrica | Antes | Después |
|---|---|---|
| Paquetes `overflow` | 191 | **0** |
| Paquete más largo | 61 454 | 1 500 (el presupuesto) |
| Identidad byte a byte | — | 98 / 98 documentos |

Uso a partir de ahora: sustituir `packets.json` → `packets_v3.json` y
`segments_v2.json` → `segments_v2.json` en los pasos 1 a 10.

`packets_v3.json` lo produce `scripts/inject_translation_ids.py` sobre
`packets_v2.json`: añade `translation_id` a los 61 paquetes de rutas
colisionadas, rehashea los 61 paquetes con `packet_id` duplicado y no
reempaqueta nada. Detalle y evidencia en [`summary.md`](summary.md) §7.

> ~~**Antes de traducir por lotes:** hay una deuda de entrada que lo
> bloquea.~~ **RESUELTO.** La colisión de `document_id` y de `packet_id`
> tiene remediación aplicada y verificada. Ver `summary.md` §7.

### Paso 2 bis · Decisión sobre los segmentos `already_target`

**DECIDIDO** (`dec-20261021`, registrada en `manifest.json`).

| Verdict | Segmentos | Resolución |
|---|---|---|
| `spanish_prose` | 1 037 | Sostienen la disposición; quedan como están |
| `english_label` | 107 | Fuera del corpus traducible |
| `english_prose` | 20 | Fuera del corpus traducible |
| `link_label_pending` | 88 | Fuera del corpus traducible; los decide la reescritura de anclas |
| `spanish_label` | 45 | Sostienen la disposición; quedan como están |

**215 segmentos en 188 archivos permanecen `already_target`.**
Cero reetiquetados. No entran en el denominador del gate; los 1 082
sostenidos tampoco. El run traducible queda intacto en sus 44 784
segmentos.

```bash
python3 $SK/scripts/verify_already_target.py --segments $W/segments_v2.json \
  --glossary $W/glossary.json --out $W/reports/already_target.json \
  --report reports/beta/already_target.md
```

El script no reescribe nada. Quien quiera reetiquetar más adelante
tiene que hacerlo pasando por una nueva decisión (`manifest.decisions`)
con su `kind` y motivo; la decisión vigente está pinada con
`decided_at` y `reviewed_hashes[]`.

### Paso 3 · Verificar los 1 297 segmentos `already_target`

**HECHO.** 1 037 `spanish_prose` + 45 `spanish_label` sostienen la
disposición. 88 quedan `link_label_pending`: son etiquetas que replican
el fragmento, y su idioma lo decide el encabezado de destino, así que las
resuelve la reescritura de anclas (INV-09), no este paso. Informe en
`reports/beta/already_target.md`.

### Paso 4 · Revisión semántica (fase 042)

Nunca se ha ejecutado. La revisión es un pase **separado** contra la
fuente, no una lectura de la propia traducción:

```bash
python3 $SK/scripts/reviewer_role.py --reviewer-id <ID> \
  --input <paquete.json> --rubric evals/rubric-distributed.md \
  --source-path <FUENTE> --out $W/review/<LOTE>.jsonl
```

La herramienta escribe la plantilla de veredictos y rechaza el input si
contamina las autojustificaciones del traductor (`author_notes`,
`tokens_estimated`, `cost_estimated_usd`, `metadata.author`). Los
veredictos se rellenan después.

Qué revisar en cada segmento: negación, `MUST`/`SHOULD`/`MAY`, sujeto de
la acción, condiciones, excepciones, cuantificadores, unidades, cifras,
versiones y causalidad.

### Paso 5 · Corrección de lo rechazado (fase 043)

Cada corrección invalida la revisión anterior y obliga a repetir las
comprobaciones afectadas del segmento:

```bash
python3 $SK/scripts/apply_corrections.py \
  --translations $W/translations --corrections <correcciones.json> \
  --out-translations $W/translations --manifest $W/manifest.json \
  --report $W/reports/corrections.json
```

Solo se corrigen los segmentos rechazados. No se reescribe el resto.

### Paso 6 · Consolidación terminológica (fase 045)

```bash
python3 $SK/scripts/audit_terminology.py \
  --translations $W/translations --glossary $W/glossary.json \
  --out $W/reports/terminology.json
```

Comprueba que el mismo sentido recibe el mismo equivalente en los 2 682
documentos, y que las excepciones justificadas del glosario se respetan.

### Paso 7 · Comprobación de cifras y unidades (fase 037)

```bash
python3 $SK/scripts/check_numbers.py \
  --translations $W/translations --segments $W/segments_v2.json \
  --out $W/reports/numbers.json
```

Señala cambios en números, unidades, versiones y operadores. No corrige:
señala. En `angular/api/` es donde más señales aparecen, porque son las
tablas de parámetros con valores por defecto.

### Paso 8 · Reescritura de fragmentos de enlace (fase 039)

```bash
python3 $SK/scripts/rewrite_references.py \
  --source <FUENTE> --output-dir $W/staged \
  --anchors $W/anchors.json --report $W/reports/rewrite.json
```

Solo reescribe fragmentos de enlaces locales resueltos hacia encabezados
traducidos. Reglas que no se saltan:

- Las anclas explícitas `<a id="…"></a>` **no** se reescriben. El scraper
  las emite en casi todos los encabezados de Next.js y Angular.
- Las rutas, queries y codificación se conservan intactas.
- Las URL externas no se tocan.
- Un fragmento ambiguo se bloquea, no se adivina.

Hay 3 110 anclas compartidas entre documentos y **0 intra-documento**.
Medido con `scripts/dump_anchor_collisions.py`; informe en
`reports/beta/anchor-collisions.md`. Un fragmento solo se resuelve dentro
del documento que lo contiene, así que las entre-documento no rompen la
navegación y **no bloquean** esta reescritura.

### Paso 9 · Aprobación por estado (fases 060)

Recorrer la secuencia C-RUN documento a documento, con evidencia:

```bash
python3 $SK/scripts/advance_state.py --manifest $W/manifest.json \
  --to deterministic_pass --translations $W/translations \
  --reason 'validate.py sin errores' --apply
python3 $SK/scripts/advance_state.py --manifest $W/manifest.json \
  --to semantic_pass --translations $W/translations \
  --reason 'revision contrastada con la fuente' --apply
python3 $SK/scripts/advance_state.py --manifest $W/manifest.json \
  --to approved --translations $W/translations \
  --reason 'sin dudas bloqueantes' --apply
```

### Paso 10 · Exportación (fase 047)

```bash
python3 $SK/scripts/export.py \
  --source-root <FUENTE> --translations $W/translations \
  --inventory $W/inventory.json --manifest $W/manifest.json \
  --segments $W/segments_v2.json --packets $W/packets_v3.json \
  --snapshots $W/snapshots.json --anchors $W/anchors.json \
  --glossary $W/glossary.json --output-root $W/output \
  --run-id run-7fbd5e24 --merge-strategy new-destination \
  --report $W/export.json
```

`export.py` revalida antes de promover. Ya se ejecutó una vez sobre el
estado parcial y **rechazó promover**: no creó `output/`. Ese es el
comportamiento correcto y se repetirá hasta que el corpus esté completo.

### Paso 11 · Gate final

```bash
python3 $SK/scripts/gate_review.py --mode expanded \
  --manifest $W/manifest.json --translations $W/translations \
  --glossary $W/glossary.json ...
```

Los cuatro checks de G-BETA deben dar 0 antes de marcar el roadmap:

| Casilla | Evidencia exigida |
|---|---|
| Traducción completa | `translated_segments == traducibles`, sin `unknown` |
| Cobertura completa | `validate.py` 0 errores; `integrity_ok: true` |
| Cero bloqueos y cero regresiones | 0 `blocked`; 0 enlaces nuevos rotos |
| Recursos íntegros | 66 copiados, 0 desajustes, 0 ausentes |

El denominador de la primera casilla **está fijado**: `traducibles == 44 784`.
La nota `dec-20261021` en `manifest.json` saca del gate los 215 segmentos
que no sostenían `already_target`: nunca formaron parte del
denominador, y así queda hasta una nueva decisión. Hoy son 43
traducidos y 44 741 pendientes.

---

## 4. Riesgos de este trabajo

| Riesgo | Por qué importa | Respuesta |
|---|---|---|
| 2,44 M tokens de salida | No cabe en una sesión | Lotes con checkpoint; estado en el manifiesto |
| Paquetes con desborde | No entran en el presupuesto de contexto | **Resuelto**: troceados por línea, 0 desbordes |
| Colisión de `document_id` | Una traducción pisaba a otra sin aviso | **Resuelto**: clave con ruta, 0 colisiones, evidencia medida |
| Colisión de `packet_id` | Una respuesta se perdía sin emitir hallazgo | **Resuelto**: id con ruta, 0 duplicados |
| Colisiones de anclas | 3 110 colisiones de anclas | **No eran bloqueo**: 0 intra-documento |
| Fabricar progreso | Ya ocurrió dos veces (defectos 1 y 3) | `--translations` como evidencia obligatoria |
| Regresión de cifras | `angular/api/` concentra tablas de parámetros | `check_numbers.py` + revisión semántica |
| Revisión complaciente | La traducción se revisa a sí misma | Pase separado con `reviewer_role.py` |
| Deriva del glosario | Un término nuevo rompe coherencia | `audit_terminology.py` + invalidez selectiva |
| Cifras del documento de alcance | `beta.md` decía 61 075 709 B; real 61 055 709 B | Corregido; hashes por directorio coinciden |

---

## 5. Lo que este documento no afirma

- **No** afirma equivalencia semántica. La revisión es asistida por
  agente y aún no se ha ejecutado. Un validador determinista en verde no
  autoriza `semantic_pass`.
- **No** afirma verificación en Notion. `remote_status: no_verificado`.
- **No** afirma cobertura del sitio remoto. Solo de los Markdown
  recibidos (INV-16).
- **No** afirma que las rutas rotas del scraper se hayan reparado. Se
  registran como `source_debt_missing_target` y `source_debt_external`.
- **No** afirma que el corpus de 4 832 archivos esté cubierto. El alcance
  autorizado son 2 748 archivos.

---

## 6. Cómo reanudar

El estado de la corrida vive en el manifiesto, no en la conversación:

```
work/run-beta-001/manifest.json     ← prepared 2681 · translated 1
work/run-beta-001/translations/     ← doc-f0342fb5.json (43 segmentos)
work/run-beta-001/lotes/            ← sobres, respuestas y reportes por lote
work/run-beta-001/validate.json     ← estado de la última validación
work/run-beta-001/reports/          ← inyección de claves, already_target, números
```

Para retomar: leer el manifiesto, correr `select_lote.py --order` para ver
qué falta, y dejar que elija el siguiente sobre. No hace falta
reconstruir ninguna decisión desde la memoria.

```
work/run-beta-001/packets_v3.json       ← usar este (0 overflow, 0 colisión)
work/run-beta-001/segments_v2.json      ← usar este
work/run-beta-001/packets_v2.json       ← anterior, sin claves; conservado
work/run-beta-001/packets.original.json ← original, sin tocar
work/run-beta-001/lotes/lote-0001-sobre.json ← primer lote, listo
```

Regla práctica: si `packets_v3.json` no está, se regenera con

```bash
python3 $SK/scripts/inject_translation_ids.py --packets $W/packets_v2.json \
  --segments $W/segments_v2.json --out $W/packets_v3.json \
  --report $W/reports/inject_translation_ids.json
```

y solo debe devolver `integrity_ok: true`. Si devuelve `false`, no se
traduce nada: un lote de trabajo cuyo destino no se puede nombrar no es
un lote de trabajo.