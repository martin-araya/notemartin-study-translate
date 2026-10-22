<!-- version: 1.0.0 -->

# Atributos visibles y reglas de accesibilidad (fase 074)

Este documento completa `references/html-contract.md` con reglas
específicas sobre qué atributos HTML pueden traducirse. La regla
por defecto es **prohibido**: solo los atributos listados aquí se
traducen. Cualquier otro atributo se preserva literal.

## 1. Atributos visibles permitidos

| Atributo | Etiquetas donde aplica | Tipo | Notas |
|---|---|---|---|
| `title` | todas las soportadas | cadena | Tooltip o título visible. |
| `aria-label` | todas las soportadas | cadena | Accesibilidad. |
| `alt` | `img` | cadena | Texto alternativo. |
| `placeholder` | (reservado para futuro) | cadena | No se observa en el corpus sintético. |

## 2. Atributos prohibidos (literales siempre)

- Funcionales: `href`, `src`, `id`, `class`, `style`, `target`,
  `rel`, `type`, `lang`, `dir`, `tabindex`, `role`, `data-*`,
  `aria-*` (excepto `aria-label`), `datetime`.
- Eventos: `onclick`, `onerror`, `onload`, `onfocus`, `onblur`,
  `onchange`, `onsubmit`, `onmouseover`, `onmouseout` y cualquier
  otro atributo que comience por `on`.
- Inline style y posicionamiento visual: `width`, `height`,
  `align`, `valign`, `color`, `bgcolor`.

## 3. Reglas por contexto

### 3.1 `<img>`

- `alt` es obligatorio por accesibilidad. Si está ausente, el
  validador emite issue `accessibility_missing_alt` con severidad
  `warning`.
- `title` y `aria-label` son opcionales; si están presentes, se
  traducen.

### 3.2 `<a>`

- El texto visible del enlace es traducible.
- `aria-label` se traduce si está presente.
- `title` se traduce si está presente (tooltip).
- `href` permanece literal: es la ruta funcional.

### 3.3 `<details>` y `<summary>`

- `<summary>` siempre traduce su texto.
- `<details>` es contenedor: no produce segmento propio.
- `open` permanece literal (estado plegable).

### 3.4 `<table>` y celdas

- Cada `<th>` y `<td>` traduce su contenido.
- `scope`, `colspan`, `rowspan` permanecen literales.

## 4. Procedimiento para añadir un atributo

1. Identificar el uso del atributo en `tests/fixtures/html/`.
2. Justificar el cambio en una issue con el corpus citado.
3. Actualizar la tabla de la sección 1.
4. Registrar la decisión en `manifest.json` bajo
   `policy_decisions` con `kind: html_attribute`, `tag`,
   `attribute`, `motivo`, `corpus_path`.
5. Añadir prueba positiva en `tests/test_html_attributes.py`.

## 5. Validación

`scripts/html_selector.py` recibe `translatable_attributes` desde el
contrato. Cualquier atributo traducible fuera de la lista genera un
segmento con `kind: attribute` cuyo `attribute` no está en la lista
permitida. El validador debe reportarlo como
`unsupported_attribute` con severidad `critical` y bloquear el
archivo.