# JavaScript básico (Argentina)

> Documento derivado CC0, variante es-AR. Voseo rioplatense.
>
> SPDX-License-Identifier: CC0-1.0

```yaml
---
title: JavaScript básico (AR)
locale: es-AR
---
```

JavaScript te permite ejecutar lógica compleja dentro del
navegador. Mediante variables, funciones y eventos, podés
manipular el DOM y responder a las acciones del usuario.

## Tipos y variables

| Sintaxis | Notas |
|---|---|
| `let` | Ámbito de bloque. |
| `const` | Constante de referencia. |
| `var` | Evitalo; compatibilidad histórica. |

```js
const saludo = "Hola";
console.log(`${saludo}, mundo`);
```

## Funciones y `this`

Las funciones flecha **no** enlazan su propio `this`. Usá
funciones tradicionales cuando necesites el contexto.

> [!WARNING]
> Modificar el DOM sin sanitizar puede introducir
> vulnerabilidades XSS. Sanitizá siempre el contenido
> que provenga del usuario.

## Comentario regional

> [!TIP]
> En Argentina, «pibe» y «piba» son coloquiales; evitá su uso
> en documentación técnica. Usá «colega», «compañero» o, si
> el contexto lo permite, «desarrollador».
