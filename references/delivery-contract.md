<!-- version: 1.0.0 -->

# Contrato de adaptación local (fase 134)

Este documento define qué puede hacer un adaptador de destino y qué no.
La adaptación es una extensión opcional, desactivada por defecto, que
opera **sobre una copia** del árbol canónico. El árbol canónico
entregado por `scripts/export.py` no se modifica nunca.

## 1. Principio

> La traducción canónica es el resultado auditado. Un adaptador solo
> puede cambiar cómo se ven las rutas y los nombres. No puede cambiar
> lo que dice el documento.

Si una entrega necesita cambiar el contenido, el problema no es el
adaptador: es una decisión de traducción que corresponde al gate del
núcleo, con su revisión semántica y su aprobación.

## 2. Qué puede hacer un adaptador

| Permitido | Ejemplo | `lossiness` |
|---|---|---|
| Normalizar rutas de recursos | `imagenes\diagrama.png` → `imagenes/diagrama.png` | `none` |
| Quitar prefijos absolutos | `/imagenes/diagrama.png` → `imagenes/diagrama.png` | `none` |
| Renombrar recursos conservando bytes | `Diagrama de Flujo.png` → `diagrama-de-flujo.png` | `none` |
| Cambiar convenciones de archivo declaradas por el destino | separador de nombres, extensión | `none` |

## 3. Qué no puede hacer

| Prohibido | Motivo |
|---|---|
| Traducir, resumir, reordenar o ampliar prosa | Viola INV-04 y el contrato del núcleo. |
| Tocar literales protegidos, comandos, identificadores o números | Viola INV-05. |
| Reescribir referencias dentro de bloques de código o de código inline | Una referencia en código es contenido, no navegación. |
| Reescribir URLs externas | Un destino externo no se puede corregir desde aquí. |
| Eliminar documentos, advertencias, tablas o ejemplos | Pérdida de contenido: es un `content_loss` y se rechaza. |
| Degradar una advertencia a una nota | Cambia la fuerza normativa del texto. |
| Sobrescribir un recurso por colisión de nombre | Aborta con código 4 en vez de perder datos. |

## 4. Declaraciones obligatorias de cada regla

`schemas/delivery_profile.schema.json` exige, por regla:

| Campo | Significado |
|---|---|
| `rule_id` | Identificador estable de la regla. |
| `description` | Qué cambia, en una frase. |
| `rationale` | Por qué el destino lo exige. Sin esto, la regla se rechaza. |
| `lossiness` | `none`, `degraded_documented` o `content_loss`. El último está prohibido. |
| `reversible` | Si la transformación puede deshacerse. |
| `scope` | Superficie tocada: rutas, nombres, convenciones o nada. |

El esquema rechaza `lossiness: content_loss`. El script vuelve a
comprobarlo en tiempo de ejecución y también rechaza reglas sin
implementación conocida.

## 5. Activación

La adaptación requiere las tres cosas a la vez:

1. `profile.json` con `delivery.enabled: true`, `destination_id` y
   `profile_ref`.
2. Un perfil en `references/delivery-profiles/` con `activation:
   explicit` y `justification` de al menos diez caracteres.
3. Selección explícita de reglas: `--enable <rule_id>` o
   `default_rules` no vacío.

Sin reglas activas, la copia es byte a byte idéntica al canónico y el
informe declara `byte_identical: true`.

## 6. Qué garantiza el motor

`scripts/adapt_delivery.py`:

- Rechaza escribir dentro del árbol canónico o sobre él (rutas no
  disjuntas), con código 2.
- Comprueba los hashes del canónico antes y después y los publica en el
  informe como `canonical_hashes_before` y `canonical_hashes_after`.
- Devuelve código 3 si el canónico cambió o si se pidió una regla
  inválida.
- Devuelve código 4 ante una colisión de nombres de recurso.
- Calcula los destinos de enlace sobre una copia del texto con las
  regiones de código en blanco. Como el enmascarado conserva la
  longitud, las posiciones siguen valiendo sobre el original.
- Sustituye únicamente el destino del enlace. La etiqueta, la prosa y
  el resto de la línea quedan intactos.
- No decodifica `%20` a un espacio literal: un espacio sin escapar
  rompe el enlace Markdown.

## 7. Verificación posterior

La adaptación no es un comprobador. Para saber qué cambió de verdad hay
que ejecutar la fase 138:

```bash
python scripts/compare_delivery.py \
    --canonical output_root/<run_id> \
    --adapted work_root/<run_id>/delivery/<destino> \
    --out reports/delivery_degradations.json
```

El informe clasifica cada diferencia en `format_only`,
`degraded_documented` o `content_loss`. Cualquier `content_loss`
bloquea el gate de entrega de la fase 140.

## 8. Destinos disponibles

| Destino | Perfil | Tipo | Evidencia real |
|---|---|---|---|
| `notion-manual` | implícito | canónico | No verificada: depende del usuario. |
| `plain-markdown-local` | `references/delivery-profiles/plain-markdown-local.json` | adaptador interno | `real_app_evidence: false`. |

El segundo destino es un adaptador interno de la propia skill, no una
aplicación de escritorio. Ver `references/delivery-matrix.md` para las
limitaciones que eso implica.

## 9. Estado real sobre el corpus piloto

Ejecutado sobre `tests/fixtures/pilot/` (9 documentos reales) con las
dos reglas activadas:

```text
ok: reglas=2 cambios=0 byte_identical=True
ok: documentos=9 format_only=0 degraded_documented=0 content_loss=0
```

**Las reglas no se disparan sobre ese corpus.** Sus enlaces a recursos
son rutas relativas a la raíz del sitio de origen, que la regla deja
intactas a propósito. La justificación del perfil —recursos con espacios
y mayúsculas— está probada sobre `tests/fixtures/delivery/canonical/`,
no sobre el piloto.

Activar el adaptador en el piloto sería activarlo sin motivo. G-EXT pide
justificación por un corpus concreto: aquí el corpus concreto es el
fixture, y por eso el perfil se documenta como ejemplo declarado, no
como adaptación recomendada para ese corpus. Cuando aparezca un corpus
con recursos problemáticos, se añade su caso a `cases` y se vuelve a
ejecutar esta comprobación.