<!-- version: 1.1.0 -->

# Caché contextual de traducción (fase 118)

Este documento define la **memoria de traducción versionada** que la
skill `notemartin-study-translate` consulta antes de cada traducción.
El caché es contextual en tres dimensiones: el `source_hash` del
texto origen, el `glossary_hash` del glosario congelado, y la
`locale_variant` del español de destino. Cualquier cambio en una de
ellas invalida la entrada sin importar si el texto fuente coincide.

> La fase 118 **no** promete que el caché mejore el rendimiento. Su
> objetivo es **seguridad**: impedir la reutilización de un texto
> cuyo sentido ya no aplica. La mejora de rendimiento, si llega,
> es un efecto secundario.

## 1. Granularidad

**Por segmento**. Cada entrada corresponde a un `segment_id`
extraído por `scripts/prepare.py`. La disyunción por paquete es
demasiado gruesa: el mismo segmento puede aparecer en varios
paquetes cuando se reformula.

## 2. Clave compuesta

La entrada del caché combina:

| Campo | Tipo | Valor |
|---|---|---|
| `key` | 16 caracteres hex | SHA-256 corto de la concatenación de los demás campos. |
| `segment_id` | string | Identificador estable del segmento. |
| `source_hash` | 64 caracteres hex | SHA-256 del `translatable_text`. |
| `glossary_hash` | 64 caracteres hex | SHA-256 del `glossary.json` congelado. |
| `locale_variant` | string | BCP-47 del destino: `es`, `es-ES`, `es-MX`, `es-AR`. |

Un `lookup` exitoso requiere que los cuatro campos coincidan
exactamente. Si difiere **cualquiera**, el caché devuelve «miss».

## 3. Regla de incompatibilidad

Un texto cuyo `source_hash` coincide con el de la entrada NO se
reutiliza si:

- El `glossary_hash` cambió: el sentido de un término puede haber
  cambiado; la traducción anterior está obsoleta.
- La `locale_variant` cambió: el estilo regional ya no coincide
  (por ejemplo, pasar de `es-ES` a `es-AR` exige voseo).
- El `segment_id` desapareció del manifiesto actual: el caché
  queda obsoleto pero no se borra automáticamente; la fase 119
  lo invalida.

## 4. Persistencia

Cada entrada se guarda en:

```
reports/cache/<locale_variant>/<source_hash_short>__<glossary_hash_short>/<segment_id>.json
```

Los nombres de archivo son estables para inspección humana. La
estructura de directorios es **rápida de podar**: `reset()` borra
todo `reports/cache/<locale_variant>/` de una variante.

## 5. Caché congelado vs caché vivo

- **Vivo**: entradas de trabajo. Se sobrescriben cuando llega una
  nueva versión coherente. Se borran con `reset()`.
- **Congelado**: entradas archivadas para auditoría. No se
  modifican al traducir. Se mueven a `reports/cache/frozen/`.

La fase 118 implementa solo el modo vivo.

## 6. Procedimiento

1. Antes de traducir un segmento, el orquestador llama a
   `translation_cache.lookup(...)`.
2. Si recibe `content` distinto de `null`, usa ese texto como
   candidato sin volver a traducir.
3. Si recibe `null` (o `KeyError`), traduce y luego llama a
   `translation_cache.store(...)`.
4. Tras un cambio de glosario o encabezados, la fase 119
   (`scripts/invalidate_cache.py`) marca las entradas a borrar.

## 7. Invalidez transitiva (fase 119)

El orquestador invalida entradas del caché cuando ocurre **cualquiera**
de estos cambios:

### 7.1 Cambio de glosario

Si un término del `glossary.json` cambia de traducción o de
sentido, todas las entradas cuyo `glossary_hash` actual no
coincida con el congelado se marcan como inválidas.
El script `scripts/invalidate_cache.py --glossary-old <hash1>
--glossary-new <hash2>` las enumera y las elimina.

### 7.2 Cambio de encabezados

Si un encabezado traducido cambia (p. ej. `## Tipos básicos` →
`## Tipos elementales`), todas las entradas del caché que
corresponden a un ancla reescrita, y todas las entradas de
documentos que apuntaban a ese ancla, quedan inválidas.
El script `scripts/invalidate_cache.py --anchors-old
<archivo_anterior> --anchors-new <archivo_actual>` detecta la
diferencia.

### 7.3 Procedimiento

1. El orquestador detecta el cambio (commit, edit manual, o
   `scripts/invalidate_run.py` con `--mode transitive`).
2. Llama a `scripts/invalidate_cache.py` con los hashes anterior y
   nuevo.
3. El script vuelca un plan en `--out` con dos listas:
   `direct_invalidations` (entradas a borrar) y
   `transitive_invalidations` (dependientes).
4. El orquestador borra las entradas del plan. Para vaciar el caché entero
   se usa `scripts/translation_cache.py reset --root <raíz>`, que es una
   operación distinta y explícita.

Lo que **no** existe: la opción `--apply-empty`. Una versión anterior de este
documento la nombraba y ninguna herramienta la acepta. Aplicar el plan de
invalidación y vaciar el caché son decisiones distintas: la primera es
conservadora y la segunda borra reutilizaciones que siguen siendo válidas.

## 8. Lo que esta política **NO** hace

- No promete mejoras de rendimiento. La velocidad depende del
  número de segmentos ya traducidos bajo la misma clave
  compuesta.
- No replica el caché en otro proceso. El lock es interno al
  proceso que escribe.
- No compara texto en sí: si dos `translatable_text` distintos
  producen el mismo `source_hash` por colisión (teórica, no
  práctica), se tratan como idénticos. La probabilidad es
  despreciable.
- No asume invariantes de proveedor. Cualquier `metadata.author`
  o `tokens_estimated` queda fuera de la entrada.
