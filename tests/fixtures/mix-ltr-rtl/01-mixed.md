# Mixed LTR/RTL corpus

> Documento derivado CC0. Combina párrafos en español con un bloque
> en árabe dentro del mismo archivo. Sirve para validar la
> clasificación `mixed` de la dirección de texto.
>
> SPDX-License-Identifier: CC0-1.0

```yaml
---
title: Mixed LTR/RTL corpus
locale: mixed
---
```

## Sección en español

Esta sección está enteramente en español. El sistema la clasifica
como LTR. Los acentos, las cifras ASCII y los caracteres latinos
dominantes confirman la dirección.

## Sección mixta

This paragraph is in English but mentions an Arabic phrase
inline: «مرحبا بكم». We expect the segment to be classified as
`mixed` because it contains both LTR and RTL characters.

El siguiente bloque es por completo en árabe:

> أهلاً بالعالم. هذا فقرة قصيرة تهدف لإثبات أن اتجاه النص
> يُحسب صحيحاً.

Cuando mezclas LTR y RTL en el mismo párrafo, el algoritmo decide
`mixed`. El resto del documento sigue siendo mayoritario en
español.

## Cierre

> Última advertencia: este fixture no debe traducirse porque su
> objetivo es probar la **detección**, no la traducción.
