<!-- version: 1.0.0 -->

# Matriz de compatibilidad HTML local ↔ Notion

Esta matriz describe lo que la skill produce localmente y qué puede
esperar el lector al importar el resultado a Notion. **No es una
promesa de paridad**. Conservar HTML localmente no demuestra que el
importador de Notion lo renderice igual.

## 1. Etiquetas soportadas

| Etiqueta | Local | Notion | Notas |
|---|---|---|---|
| `details` / `summary` | preservado y traducible | preservado, renderiza como plegable | El usuario debe verificar el render en su espacio. |
| `a` (enlace) | traducible; `href` literal | preservado | Funciona como enlace Markdown estándar. |
| `img` | traducible; `src` literal | preservado | `alt` traducible para accesibilidad. |
| `table` / `thead` / `tbody` / `tfoot` / `tr` / `th` / `td` | traducible | preservado | `colspan` y `rowspan` se mantienen literales. |
| `code` | traducible | preservado | Igual que el código Markdown. |
| `kbd` | traducible | preservado | Rara vez se renderiza como `<kbd>` real. |
| `br` | preservado | preservado | Sin cambios. |
| `span` | traducible | preservado | Sin estilo aplicado. |

## 2. Etiquetas prohibidas

| Etiqueta | Local | Notion | Notas |
|---|---|---|---|
| `<script>`, `<style>` | preservado literal, marcado como unsafe | se preserva o se filtra | El usuario debe auditar antes de importar. |
| `<iframe>`, `<object>`, `<embed>` | preservado literal | se filtra típicamente | No se carga contenido. |
| `<script>onclick` y similares | preservado literal | se filtra | Atributos de evento siempre literales. |

## 3. Lo que NO se garantiza

- **Soporte universal.** El subconjunto cubierto está limitado a
  las etiquetas listadas arriba. Esta skill **no** promete paridad
  con HTML5 ni con el render específico de Notion.
- **Sin render real.** La skill no carga el resultado en Notion.
  La importación la realiza el usuario.
- **HTML malformado se bloquea.** No se repara silenciosamente
  (INV-03 del proyecto).
- **HTML dentro de fences.** Se trata como código, no se traduce.

## 4. Procedimiento para añadir una etiqueta

1. Identificar el uso en `tests/fixtures/html/`.
2. Justificar el cambio en una issue con el corpus citado.
3. Actualizar la tabla de la sección 1.
4. Registrar la decisión en `manifest.json` bajo
   `policy_decisions` con `kind: html_tag`, `tag`, `motivo`,
   `corpus_path`.
5. Añadir prueba positiva en `tests/test_html_matrix.py` o el test
   correspondiente.

## 5. Verificación

La presencia de esta matriz es **informativa**, no bloqueante.
Las pruebas que la cubren (`tests/test_html_matrix.py`) verifican
que el documento:

- Existe y es accesible.
- Cubre las etiquetas soportadas.
- Declara al menos una advertencia sobre Notion.
- No promete paridad universal.