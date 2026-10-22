<!-- version: 1.0.0 -->

# Política de terminología y resolución de sentidos

Este documento registra las decisiones terminológicas que rigen la traducción del corpus. Define la política bilingüe, las decisiones de sentido por dominio y la precedencia cuando dos sentidos del mismo término coexisten. Su propósito es que cualquier ejecución pueda auditar las traducciones frente a una base explícita, no inferida.

## 1. Política bilingüe

La política bilingüe determina si el término original se mantiene junto a la traducción. Tres valores posibles, declarados en el perfil:

| Valor | Comportamiento | Uso recomendado |
|---|---|---|
| `none` | Solo se emite la traducción al español. | Documentación cuyo lector asume el término técnico estándar. |
| `first-mention-per-document` | La primera mención en cada documento lleva ambos: `término (original)`. Las siguientes, solo la traducción. | Documentación mixta con secciones extensas. |
| `first-mention-per-corpus` | La primera mención en el corpus lleva ambos; el resto, solo la traducción. | Documentación referenciada en varios archivos donde se evita repetir el original. |

Por defecto se aplica `first-mention-per-document`. El perfil puede sobrescribir este valor.

## 2. Decisiones de sentido por dominio

Las decisiones siguientes se derivan del glosario borrador generado por `scripts/extract_terms.py` y revisadas manualmente. Cada entrada declara el sentido observado, el equivalente preferido y la justificación de la elección.

| Término | Dominio | Sentido observado | Equivalente preferido | Política | Justificación |
|---|---|---|---|---|---|
| `state` | `ui` | estado visible de un componente de interfaz | `estado` | translate | En UI se distingue de `status`; preserva la noción de dato mutable del componente. |
| `state` | `database` | información persistente de una fila o tupla | `estado` | translate | En bases de datos se mantiene el equivalente `estado`; la diferencia con UI se anota en `sense`. |
| `request` | `api` | petición HTTP entrante | `solicitud` | translate | Coincide con la documentación oficial del producto. |
| `response` | `api` | respuesta HTTP saliente | `respuesta` | translate | Coincide con la documentación oficial del producto. |
| `endpoint` | `api` | URL que acepta peticiones | `endpoint` | keep-original | Identificador técnico ampliamente reconocido; la traducción `punto de conexión` introduce ambigüedad. |
| `streaming` | `api` | envío incremental de respuesta | `streaming` | keep-original | Anglicismo admitido en español técnico. No se sustituye por `flujo`. |
| `tool calling` | `api` | invocación de herramientas desde el modelo | `tool calling` | keep-original | Término del producto; conserva la marca. |
| `reasoning` | `ai` | proceso de razonamiento del modelo | `razonamiento` | translate | Equivalente asentado en la documentación en español. |
| `embedding` | `ai` | representación vectorial | `embedding` | keep-original | Identificador técnico; la traducción `incrustación` no se usa fuera de contextos pedagógicos. |
| `custom property` | `css` | variable CSS definida por autor | `propiedad personalizada` | translate | Traducción adoptada por MDN. La forma `variable CSS` se conserva como variante. |
| `anchor` | `markdown` | marcador de navegación | `ancla` | translate | Coincide con la documentación del selector; en HTML se mantiene `anchor` por la sintaxis `<a id>`. |

## 3. Precedencia entre sentidos

Cuando dos sentidos del mismo término coexisten en el mismo documento, la precedencia se decide así:

1. Si el documento lleva `domain` declarado, gana el sentido cuyo dominio coincide.
2. En su defecto, gana el sentido cuya entrada tiene `decided_by: user` sobre `decided_by: script`.
3. Si persiste la ambigüedad, se consulta al usuario antes de aprobar.

Para términos sin entrada en el glosario, el traductor aplica la regla de "sentido único por dominio": elige el sentido más frecuente dentro del dominio del documento y registra la decisión en el archivo `manifest.json` del paquete.

## 4. Procedimiento de revisión

| Acción | Procedimiento |
|---|---|
| Añadir un término | Crear entrada en el glosario borrador con `decided_by: user`, `frozen: false`. Confirmar el equivalente preferido y la política de conservación. |
| Cambiar el sentido de un término existente | Marcar la entrada anterior como `superseded_by: <nuevo-id>`. La nueva entrada hereda el dominio. |
| Retirar un término | Marcar la entrada con `superseded_by` apuntando a la entrada que la sustituye. No se borra el historial. |
| Aprobar un lote | El piloto genera el `manifest.json` con la versión y hash del glosario congelado. Cambios posteriores invalidan los segmentos afectados. |

Cada cambio incrementa `version` en el glosario y registra `decided_at` en la entrada. El campo `justification` es obligatorio y se redacta a partir del contexto, no se copia de la entrada anterior.

## 5. Limitaciones

- El glosario se congela tras la aprobación del piloto (fase 030). Una entrada `frozen: true` no se modifica sin invalidar los segmentos aprobados.
- El borrador generado por `scripts/extract_terms.py` solo propone candidatos por frecuencia y co-ocurrencia. La decisión final corresponde al usuario o al revisor humano.
- No se afirma que la terminología cubre todo el corpus. Las entradas `unknown` se registran como pendientes.
- El glosario es por ejecución. Una nueva ejecución con la misma fuente puede generar entradas distintas si los umbrales cambian. La versión y el hash se conservan en `manifest.json` para auditoría.