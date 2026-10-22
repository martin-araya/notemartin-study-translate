# Referencia HTML (Argentina)

> Documento derivado CC0, variante es-AR. Voseo, sin
> vosotros.
>
> SPDX-License-Identifier: CC0-1.0

```yaml
---
title: Referencia HTML (AR)
locale: es-AR
---
```

HTML define la estructura semántica de tu página web. Cada
elemento tiene un propósito concreto: encabezados, párrafos,
listas, enlaces, imágenes, formularios.

## Elementos esenciales

| Elemento | Descripción | Notas |
|---|---|---|
| `<h1>` ... `<h6>` | Encabezados con jerarquía. | No los uses para tamaño. |
| `<p>` | Párrafo de texto. | Siempre cerrá la etiqueta. |
| `<a href>` | Enlace a otra URL. | Usá `rel` cuando abras en pestaña nueva. |
| `<ul>` / `<ol>` | Listas no ordenadas / ordenadas. | Cada `<li>` debe ir dentro. |

> No abuses de los elementos `<div>` y `<span>` cuando exista
> un elemento semántico: `<article>`, `<section>`, `<aside>`,
> `<nav>`.

## Formularios

```html
<form action="/login" method="post">
  <label for="user">Usuario</label>
  <input id="user" name="user" type="text" required />
  <label for="pass">Contraseña</label>
  <input id="pass" name="pass" type="password" required />
  <button type="submit">Iniciar sesión</button>
</form>
```

Los nombres de los campos (`user`, `pass`) son literales
técnicos; **no los traduzcas**.

## Comentario regional

> [!NOTE]
> En el español rioplatense, «computadora» es el término
> estándar en contextos formales. **«Computador»** se evita.
> El término «ordenador» se asocia con España y no se usa
> aquí.
