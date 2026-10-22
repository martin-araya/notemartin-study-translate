# Referencia HTML (México)

> Documento derivado CC0, variante es-MX. Tratamiento
> formal de **usted**. Sin voseo ni vosotros.
>
> SPDX-License-Identifier: CC0-1.0

```yaml
---
title: Referencia HTML (MX)
locale: es-MX
---
```

HTML define la estructura semántica de su página web. Cada
elemento tiene un propósito concreto: encabezados, párrafos,
listas, enlaces, imágenes, formularios.

## Elementos esenciales

| Elemento | Descripción | Notas |
|---|---|---|
| `<h1>` ... `<h6>` | Encabezados con jerarquía. | No los use para tamaño. |
| `<p>` | Párrafo de texto. | Siempre cierra la etiqueta. |
| `<a href>` | Enlace a otra URL. | Use `rel` cuando abra en pestaña nueva. |
| `<ul>` / `<ol>` | Listas no ordenadas / ordenadas. | Cada `<li>` debe ir dentro. |

> No abuse de los elementos `<div>` y `<span>` cuando exista
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
técnicos; **no los traduzca**.

## Comentario regional

> [!NOTE]
> En español de México, «computadora» es el término
> estándar en contextos formales. **«Ordenador»** se asocia
> con España y se evita en esta variante.
