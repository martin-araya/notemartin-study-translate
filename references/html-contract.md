<!-- version: 1.1.0 -->

# Contrato de la extensión HTML embebido (`notemartin-study-translate`)

Este contrato delimita el subconjunto de HTML embebido que la skill
soporta cuando el gate del perfil (`profile.html.enabled`) está
activo. **No es una promesa de soporte universal**: cualquier
etiqueta, atributo o patrón no listado aquí se reporta como
`unsupported_html` con severidad `critical` y bloquea el archivo.

## 1. Estado del módulo

- **Activación:** opt-in. Por defecto desactivado en `prepare.py`.
- **Gating:** el perfil declara `html.enabled`. Si es `false`, el
  HTML fuera del conjunto CommonMark se mantiene como bloqueante
  (comportamiento histórico).
- **Corpus de referencia:** `tests/fixtures/html/`. Es un corpus
  sintético. La skill no promete paridad con el HTML5 completo.

## 2. Etiquetas soportadas

| Etiqueta | Texto traducible | Atributos visibles permitidos | Notas |
|---|---|---|---|
| `details` | contenedor (no se traduce directamente) | `open` (literal) | Hijos `<summary>` y resto traducibles individualmente. |
| `summary` | sí | `title` | Conserva el encabezado plegable. |
| `a` | sí | `title`, `aria-label` | `href` literal. |
| `img` | contenedor (no traduce) | `alt`, `title`, `aria-label` | `src` literal. |
| `table` | contenedor | ninguno | Celdas y cabeceras traducibles individualmente. |
| `thead`, `tbody`, `tfoot` | contenedor | ninguno | No introducen texto. |
| `tr` | contenedor | ninguno | Filas. |
| `th`, `td` | sí | `title`, `aria-label` | Celdas traducibles. |
| `code` | sí | ninguno | Solo dentro del contrato; preserva contenido técnico. |
| `kbd` | sí | `title` | Entrada de teclado. |
| `br` | contenedor (vacío) | ninguno | Auto-cerrada. |
| `span` | sí | `title`, `aria-label` | Genérico con clase prohibida. |

Cualquier otra etiqueta se reporta como `unsupported_html`.

## 3. Lo que NO se ejecuta ni se traduce

- `<script>` y `<style>` siempre se preservan literales. Su
  aparición se reporta como `unsafe_html` con severidad `critical`.
- `<iframe>`, `<object>`, `<embed>`: se preservan literales; el
  parser no carga URLs externas.
- Atributos de evento (`on*`): se preservan literales; se marcan
  como `unsafe_event_handler`.

## 4. Reglas de conserv

- Atributos `id`, `class`, `style`, `data-*`, `href`, `src`,
  `target`, `rel`, `type`, `lang`, `dir`, `tabindex`, `role` son
  siempre literales.
- Etiquetas con `unsafe_html` se reportan pero no se eliminan: la
  traducción no toca su contenido.
- Las entidades HTML (`&amp;`, `&lt;`, etc.) se preservan en su
  forma codificada.

## 5. Activación y desactivación

- `profile.html.enabled: false` → HTML fuera de CommonMark se
  bloquea.
- `profile.html.enabled: true` → el parser HTML aplica el contrato;
  lo que no esté listado se reporta como `unsupported_html` con
  severidad `critical`.
- El gate es independiente del gate MDX. Si ambos están activos
  en el mismo corpus, MDX tiene precedencia.