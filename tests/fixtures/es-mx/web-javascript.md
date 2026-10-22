# JavaScript básico (México)

> Documento derivado CC0, variante es-MX. Tratamiento formal
> de **usted**, sin voseo.
>
> SPDX-License-Identifier: CC0-1.0

```yaml
---
title: JavaScript básico (MX)
locale: es-MX
---
```

JavaScript le permite a usted ejecutar lógica compleja dentro
del navegador. Mediante variables, funciones y eventos, puede
manipular el DOM y responder a las acciones del usuario.

## Tipos y variables

| Sintaxis | Notas |
|---|---|
| `let` | Ámbito de bloque. |
| `const` | Constante de referencia. |
| `var` | Evítelo; compatibilidad histórica. |

```js
const saludo = "Hola";
console.log(`${saludo}, mundo`);
```

## Funciones y `this`

Las funciones flecha **no** enlazan su propio `this`. Use
funciones tradicionales cuando necesite el contexto.

> [!WARNING]
> Modificar el DOM sin sanitizar puede introducir
> vulnerabilidades XSS. Sanitice siempre el contenido
> que provenga del usuario.

## Comentario regional

> [!TIP]
> En México, «cuate» se usa coloquialmente; evite esa
> palabra en la documentación técnica. Use «colega» o
> «compañero» en su lugar.
