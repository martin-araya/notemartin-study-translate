# Estilos en CSS (Argentina)

> Documento derivado CC0, variante es-AR. Voseo y marcadores
> rioplatenses. **Sin vosotros**.
>
> SPDX-License-Identifier: CC0-1.0

```yaml
---
title: Estilos en CSS (AR)
locale: es-AR
---
```

Las hojas de estilo en cascada (CSS) te permiten controlar la
presentación de tus documentos HTML. Mediante reglas de
selectores y propiedades, podés definir colores, fuentes y
diseños responsivos.

## Selectores básicos

| Selector | Uso | Compatibilidad |
|---|---|---|
| `h1` | Aplica a todos los `<h1>` del documento. | Universal. |
| `.clase` | Aplica a cualquier elemento con `class="clase"`. | Universal. |
| `#id` | Aplica a un único elemento con ese `id`. | Usalo con prudencia. |
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

> Los valores anteriores son ejemplos literales; ajustalos a
> las necesidades de tu proyecto.

## Comentarios regionales

> [!TIP]
> En Argentina, la palabra « **boludo** » es coloquial y se
> considera vulgar en registros formales. Evitala en
> documentación técnica; «útil», «práctico», « copado »
> funcionan en registros informales sin carga negativa.
