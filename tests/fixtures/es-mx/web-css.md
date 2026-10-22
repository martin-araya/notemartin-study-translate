# Estilos en CSS (México)

> Documento derivado CC0, variante es-MX. Uso constante de
> **usted**, sin voseo, sin vosotros. Vocabulario regional
> mexicano en las notas informales.
>
> SPDX-License-Identifier: CC0-1.0

```yaml
---
title: Estilos en CSS (MX)
locale: es-MX
---
```

Las hojas de estilo en cascada (CSS) le permiten a usted
controlar la presentación de documentos HTML. Mediante reglas
de selectores y propiedades, puede definir colores, fuentes y
diseños responsivos.

## Selectores básicos

| Selector | Uso | Compatibilidad |
|---|---|---|
| `h1` | Aplica a todos los `<h1>` del documento. | Universal. |
| `.clase` | Aplica a cualquier elemento con `class="clase"`. | Universal. |
| `#id` | Aplica a un único elemento con ese `id`. | Úselo con prudencia. |
| `[attr]` | Aplica a cualquier elemento con `atributo` definido. | Universal. |

## Caja y diseño

```css
.caja {
  width: 80%;
  margin: 0 auto;
  padding: 1rem;
  background-color: #f4f4f4;
}
```

> Los valores anteriores son ejemplos literales; ajústelos a
> las necesidades de su proyecto.

## Comentarios regionales

> [!TIP]
> En México, la palabra **«chido»** solo aparece en
> contextos muy informales. Para documentación técnica se
> recomienda evitarla; use «útil» o «práctico» en su lugar.
