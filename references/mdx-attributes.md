<!-- version: 1.0.0 -->

# Atributos visibles permitidos en MDX (`notemartin-study-translate`)

Este documento fija qué atributos de los componentes MDX del
contrato (ver `references/mdx-contract.md`) pueden traducirse. La
regla por defecto es **prohibido**: solo los atributos listados aquí
se traducen. Cualquier otro atributo se reporta como
`unsupported_attribute` con severidad `critical`.

## 1. Atributos permitidos por defecto

| Atributo | Componentes donde aplica | Tipo | Notas |
|---|---|---|---|
| `title` | `Info`, `Note`, `Warning`, `Callout`, `Card` | cadena | Visible para el lector. |
| `label` | `TabItem` | cadena | Visible en la pestaña. |
| `altText` | (reservado para futuro) | cadena | Accesibilidad. |

## 2. Atributos prohibidos

- `value`, `icon`, `type`, `severity`, `cols`, `defaultValue`,
  `as`, `className`, `style`, `id`, `href`, `src`, `onClick` y
  cualquier atributo cuyo nombre no esté en la sección 1.
- Atributos cuyo valor sea una expresión JSX
  (`{...}`) **nunca** se traducen: el traductor no resuelve el valor
  y la sustitución rompería el render.

## 3. Procedimiento para añadir un atributo

1. Identificar un componente del corpus `tests/fixtures/mdx/` que
   use el atributo.
2. Justificar el uso en una issue con el corpus citado.
3. Actualizar la tabla de la sección 1 con el nuevo atributo.
4. Registrar la decisión en `manifest.json` bajo
   `policy_decisions` con `kind: mdx_attribute`,
   `component`, `attribute`, `motivo`, `corpus_path`.
5. Añadir prueba positiva en `tests/test_mdx_attributes.py`.

## 4. Validación

`scripts/mdx_selector.py` recibe `translatable_attributes` desde el
contrato. Cualquier atributo traducible fuera de la lista genera
un segmento con `kind: unsupported_attribute` y severidad `critical`
en `reports/issues.json`. El gate MDX bloquea el archivo.