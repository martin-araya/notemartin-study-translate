<!-- version: 1.0.0 -->

# Entrega local e importación a Notion

Este documento separa lo que se entrega al usuario para subir a Notion de lo que queda fuera, y declara qué no se garantiza sobre la importación remota.

## 1. Árbol entregado al usuario

Único lo siguiente se entrega para importación:

```
output_root/<run_id>/
  <mismas rutas relativas que source_root, archivo a archivo>
```

El árbol refleja la estructura del corpus original. Cada archivo está aprobado y vigente según el manifiesto de la ejecución. El usuario importa esta carpeta en Notion con el procedimiento de la sección 4.

## 2. Árbol excluido del paquete importable

El siguiente contenido **no se mezcla** con los documentos traducidos porque contaminaría la importación y haría pasar artefactos operativos como documentación del producto:

| Recurso | Ubicación | Por qué se excluye |
|---|---|---|
| Manifiesto de ejecución | `work_root/<run_id>/manifest.json` | Contiene metadatos operativos no publicables |
| Glosario | `work_root/<run_id>/glossary.json` | Contiene decisiones terminológicas internas |
| Inventario | `work_root/<run_id>/inventory.json` | Contiene hashes y métricas |
| Segmentos extraídos | `work_root/<run_id>/segments/` | Texto intermedio sin valor documental |
| Traducciones candidatas | `work_root/<run_id>/translations/` | Texto sin ensamblar |
| Staging de ensamblado | `work_root/<run_id>/staged/` | Versiones intermedias antes del gate |
| Mapa de anclas | `work_root/<run_id>/anchors.json` | Datos de reescritura local |
| Reportes | `work_root/<run_id>/reports/` | Hallazgos, métricas y decisiones internas |

Estos archivos se conservan en `work_root` para auditoría y reanudación. No se incluyen en `output_root`.

## 3. Lo que Notion no garantiza

**No se garantiza paridad visual** entre el Markdown entregado y la representación renderizada por Notion. Las siguientes limitaciones son conocidas y deben verificarse manualmente tras la importación:

| Construcción | Comportamiento esperado en Notion |
|---|---|
| Bloques personalizados tipo `<Info>`, `<CodeGroup>`, `<Note>` | Se renderizan como texto plano, como HTML sin procesar o se pierden |
| Mermaid dentro de fences | Se conserva como bloque de código etiquetado `mermaid`, sin renderizar |
| Anclas HTML `<a id="…"></a>` | Pueden no sobrevivir al importador |
| Tablas con alineación compleja | La alineación de columnas puede perderse |
| Bloques de código con resaltado | El lenguaje declarado puede ignorarse |
| Enlaces internos con fragmento | La navegación por anclas puede romperse |
| Imágenes referenciadas por ruta absoluta del scraper | Pueden no cargarse en Notion; revisar manualmente |
| Listas de tareas | El estado `[ ]` y `[x]` puede no convertirse en casillas interactivas |

Estas son limitaciones del importador de Notion, no errores de la skill. La traducción cumple su contrato: producir Markdown fiel, preservando literales y estructura. La representación remota es responsabilidad del importador y del usuario que verifica.

## 4. Procedimiento de verificación manual recomendado

El procedimiento detallado, con la evidencia que hay que aportar en
cada paso, está en `references/delivery-notion-checklist.md`. El
procedimiento resumido es:

1. Importar una muestra de 3 a 5 archivos representativos.
2. Verificar que las tablas se visualizan con la estructura esperada.
3. Verificar que los bloques de código conservan su contenido byte a byte.
4. Hacer clic en al menos un enlace interno y comprobar que navega al destino esperado.
5. Verificar al menos una imagen con su descripción alternativa.
6. Verificar una advertencia o callout si existe en la muestra.
7. Confirmar que no aparecen en la página importada artefactos del árbol excluido (manifiesto, glosario, reportes).

El registro de esas comprobaciones lo genera
`scripts/record_import_evidence.py`. Distingue dos cosas que no deben
confundirse: la **resolución local** del enlace, que la skill calcula
sobre el Markdown entregado, y la **navegación remota**, que solo puede
constar si el usuario aporta la evidencia.

Si la muestra presenta desviaciones, el usuario decide si:

- Continúa con la importación y acepta las desviaciones como limitación del destino.
- Solicita ajustes de formato que la skill pueda aplicar sin cambiar la traducción.
- Conserva la documentación original en `output_root` y no importa a Notion.

## 5. Re-importación

Nunca se sobreescriben páginas Notion ya existentes sin confirmación explícita del usuario. Si se desea reimportar:

- Se crea un árbol `output_root/<nuevo_run_id>/` con la nueva ejecución.
- Se eliminan manualmente las páginas Notion anteriores si se desea reemplazar.
- O se importa el árbol nuevo en una ubicación distinta.

Una reimportación no es una sobrescritura silenciosa. El usuario decide en cada caso.

## 6. Límite de la promesa

Este documento **separa validez Markdown local de verificación remota**. La skill garantiza que el Markdown entregado es válido en el dialecto declarado, conserva literales y refleja la estructura de la fuente. **No afirma** que Notion lo represente con paridad visual, que conserve la navegación ni que renderice correctamente todas las construcciones.

La afirmación de éxito de la importación corresponde al usuario, basada en la verificación manual de la sección 4. La skill no certifica publicación remota.

**Estado actual de la verificación remota: `no verificado`.** Ninguna ejecución de esta skill ha importado nada en Notion ni ha recibido evidencia de una persona que lo hiciera. El registro `import_evidence.json` mantiene esa distinción por construcción: nace con `remote_status: no_verificado` y solo cambia cuando el usuario aporta evidencia con revisor humano declarado. La matriz de destinos de `references/delivery-matrix.md` conserva el mismo estado.

## 7. Construcciones preservadas con límites

Notion importa Markdown con su propio dialecto. Esta tabla enumera qué construcciones conserva esta skill en el Markdown entregado y qué comportamiento cabe esperar al importar. La paridad visual no se garantiza; el usuario debe verificar la muestra del paso 4.

| Construcción | Comportamiento esperado en Notion | Limitaciones conocidas |
|---|---|---|
| Encabezados ATX (`#`, `##`, …) | Preservados como títulos jerárquicos. | Sin límite documentado. |
| Encabezados Setext (`===`, `---`) | Preservados como títulos. | El importador puede normalizar a ATX en algunas versiones. |
| Tablas GFM con alineación | Preservadas con la misma estructura. | La alineación `:---`, `:---:`, `---:` puede perderse en la representación. |
| Listas ordenadas y no ordenadas | Preservadas con jerarquía. | Anidamiento profundo (> 3 niveles) puede aplanarse o numerarse de nuevo. |
| Citas en bloque (`> …`) | Preservadas. | Sin límite conocido. |
| Código inline (`` `…` ``) | Preservado. | El resaltado de sintaxis depende del lenguaje declarado. |
| Bloques de código fenced (` ``` `) | Preservados con su contenido. | El resaltado puede perderse si el lenguaje declarado no es estándar. |
| Imágenes (`![alt](src)`) | Preservadas con su descripción y destino. | El anclaje relativo puede romperse en Notion si el destino es una ruta del scraper. |
| Tablas con separador `\|` literal en celdas (texto traducido) | El separador se escapa como `\\|` en la celda antes de aplicar el parche; la tabla sigue siendo parseable. | El escape solo se aplica cuando la traducción introduce el `\|`. |
| Mermaid dentro de fences | Conservado como bloque de código etiquetado `mermaid`. | Notion no renderiza Mermaid por defecto; requiere integración externa. |
| Componentes MDX/JSX (`<Info>`, `<CodeGroup>`) | Conservados como texto literal o se pierden en el importador. | Sin render en Notion. |
| HTML embebido fuera de CommonMark | Bloqueado por el validador; no entra en la salida. | El archivo queda marcado como `blocked`. |
| Anchor HTML inline `<a id="…"></a>` | Conservado. | El anclaje interno puede no sobrevivir al importador. |
| Listas de tareas (`- [ ]`, `- [x]`) | Preservadas. | Las casillas interactivas requieren la API de Notion. |
| Anclas en enlaces `[texto](#slug)` | Reescritas si el slug cambia. Las externas se mantienen intactas. | Sin verificación remota del destino reescrito. |
| Negrita, cursiva, tachado, código | Preservados. | Sin límite. |

## 8. Recomendaciones para el usuario

1. Importar una muestra de 3 a 5 archivos antes del corpus completo.
2. Verificar manualmente la tabla de la sección 7 para cada tipo presente.
3. Si Notion no renderiza una construcción (por ejemplo, Mermaid), considerar agregar la página manualmente o usar una integración externa.
4. Conservar `output_root/<run_id>/` como respaldo local mientras dure el experimento.
5. Si una reimportación es necesaria, seguir la sección 5: árbol nuevo, no sobrescritura silenciosa.