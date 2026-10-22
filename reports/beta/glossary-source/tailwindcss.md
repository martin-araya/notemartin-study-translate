# `tailwindcss.md` — términos observados en la documentación de Tailwind

**Material leído:** `tailwindcss/styling-with-utility-classes.md`,
`tailwindcss/hover-focus-and-other-states.md`,
`tailwindcss/upgrade-guide.md`. De los 226 archivos del directorio
sólo 91 tienen contenido (135 están vacíos); los archivos vacíos son
**referencias de utilidad** que el scraper no descargó correctamente
y no tienen prosa traducible.

## Reglas generales observadas

- Tailwind compone nombres con **prefijos semánticos** sobre un
  nombre de utilidad: `bg-red-500`, `hover:bg-red-500`,
  `peer-invalid:underline`. Son formas compuestas que la
  documentación usa dentro de fences o de bloques `text` con
  `language-css`.
- Las **palabras-clave de modificador** (variants) son el campo
  terminológico más rico del framework: `hover`, `focus`, `active`,
  `disabled`, `group-hover`, `peer-invalid`, `data-attr-…`, `aria-…`,
  `before`, `after`, `placeholder`, `file`, `marker`, `selection`,
  `first-letter`, `first-line`.
- Tailwind define sus propios términos UX/UI: «utility class»,
  «variant», «design token», «theme variable», «preset», «important».
- La documentación es **informativa y concisa**, casi sin oraciones
  largas. Eso significa que pocas palabras llevan mucho peso.

## Propuestas por entrada

### `utility class` (compuesto central)

- **Sentido:** clase que aplica una sola utilidad CSS (margen,
  display, color). La idea clave de Tailwind: clases como unidades
  componibles, no como estilos que se sobreescriben.
- **Donde aparece:** `styling-with-utility-classes.md:7-8` —
  *«When you build entire projects with just utility classes, …»*;
  *«the utility classes for each avatar image are repeated five
  separate times»*.
- **Status:** `propuesto`
- **Preferred:** `clase utilitaria`.
- **Justificación:** los lectores reales de Tailwind en español usan
  ambas formas: «utility class» (inglés) y «clase utilitaria»
  (castellano). La elección define el tono de toda la documentación.
- **Decisión abierta:** conservar «utility class» por registro
  técnico, o traducirlo en cuerpo y dejar la frase entre comillas
  para clases específicas (`bg-red-500`).

### `utility class` (compuesto, sentido técnico-jurídico)

- **Sentido:** en sentido legal, cuando un CSS tiene
  `!important` y otro no, una utility class gana siempre.
- **Donde aparece:** `styling-with-utility-classes.md:21` —
  *«When you add two classes that target the same CSS property, the
  class that appears later in the stylesheet wins»*.
- **Status:** `pendiente`
- **Justificación:** el sentido jurídico de «gana la última» se
  describe con la misma frase. No aparece un término glosable.

### `theme variable` (compuesto técnico)

- **Sentido:** variable CSS declarada en `@layer theme` que define
  los valores predeterminados de las utilidades
  (`--tw-color-red-500`).
- **Donde aparece:** `styling-with-utility-classes.md:35-36` — *«using
  theme variables to keep the design consistent»*.
- **Status:** `propuesto`
- **Preferred:** `variable del tema` o `variable de tema`.
- **Justificación:** los dos órdenes generan frases distintas
  («variable de tema` es más común en el traductor oficial).

### `utility-first` (compuesto)

- **Sentido:** paradigma de CSS que define las clases como
  utilidades, no como componentes.
- **Donde aparece:** no aparece explícitamente en los archivos
  leídos, pero es central en la identidad del framework.
- **Status:** `pendiente` (revisar más archivos).
- **Preferred:** `utility-first` (literal) o «CSS basado en
  utilidades».

### `custom property` y `design token`

- **Sentido:** una `custom property` es una variable CSS del autor
  (`--mi-color`); un `design token` es el valor semántico que se
  mapea a esa propiedad en una librería de diseño.
- **Donde aparece:** `styling-with-utility-classes.md:35-36` —
  *«using theme variables … a `btn-primary` class … using theme
  variables to keep the design consistent»*.
- **Status:** `propuesto` / `mantener` (custom property ya estaba
  en el glosario v2 del piloto; se mantiene).
- **Preferred:** `propiedad personalizada` / `token de diseño`.
- **Justificación:** entradas asentadas. Re-confirmadas en este
  corpus.

### `important` (concepto CSS) y la sintaxis `important` (modificador)

- **Sentido:** la palabra clave CSS `!important`. Tailwind permite
  aplicar `!important` por configuración global.
- **Donde aparece:** `styling-with-utility-classes.md:32-33` —
  *«You can add `!` to the end of the class name … use the important
  flag when importing Tailwind»*.
- **Status:** `mantener`
- **Preferred:** literal.

### `prefix` (opción de configuración)

- **Sentido:** cadena que se prepende a cada clase generada por
  Tailwind para evitar conflictos con clases existentes.
- **Donde aparece:** `styling-with-utility-classes.md:34-36` —
  *«using the prefix option: @import "tailwindcss" prefix(tw); … .
  tw\:text-red-500 …»*.
- **Status:** `propuesto`
- **Preferred:** `prefijo`.
- **Justificación:** calco literal. El calco `prefijar` (verbalizar)
  se desaconseja aquí porque «prefijo de Tailwind» no es verbo.

### `important variant`, `important flag`

- **Sentido:** `important flag` es la configuración global
  (`@import "tailwindcss" important;`); `important variant` es la
  variante `!` que añade `!important` a una utilidad concreta.
- **Status:** `propuesto`
- **Preferred:** `importante` para la opción; variante `!` para la
  variante (literal).
- **Justificación:** la documentación usa ambas formas; la
  traducción natural es `importante` solo si se habla de la
  configuración (en cuyo caso sí es adjetivo, no declaración CSS).

### Variants (`hover`, `focus`, `active`, `disabled`, `group`, `peer`)

- **Sentido:** modificadores que aplican una utilidad cuando se da
  una condición. `group-*` actúa sobre el estado del padre;
  `peer-*` sobre el de un hermano.
- **Donde aparece:** `hover-focus-and-other-states.md:16` —
  *«if you want more fine-grained control you'll need to use group
  instead»*; línea 17 — *«use peer-* variants like peer-invalid to
  style the target element»*.
- **Status:** `mantener`
- **Preferred:** literal del API (`hover`, `group`, `peer`, etc.).
- **Justificación:** son nombres de variantes en el API y todo el
  ecosistema los usa literalmente.

### `sibling` y `subsequent-sibling combinator`

- **Sentido:** combinador CSS `~` y su semántica (hermanos
  posteriores).
- **Donde aparece:** `hover-focus-and-other-states.md:20-21` —
  *«only be used on previous siblings because of how the
  subsequent-sibling combinator works in CSS»*.
- **Status:** `propuesto`
- **Preferred:** `hermano`, `combinador de hermano
  subsiguiente`.
- **Justificación:** `sibling` es literal en muchos tutoriales;
  «hermano» es la traducción. El calco `sub-sibling` es
  incorrecto: «subsiguiente» significa «siguiente», no
  «sub-hermano».

### `peer` (variant) — sentido profundo

- **Sentido:** marcar un elemento como «peer» para que sus hermanos
  reaccionen a su estado vía `peer-*`. Este concepto es exclusivo de
  Tailwind, no de CSS.
- **Donde aparece:** `hover-focus-and-other-states.md:16-26`.
- **Status:** `mantener`
- **Preferred:** literal.

### `arbitrary value` (variante)

- **Sentido:** valor definido por el usuario entre corchetes
  (`bg-[#bada55]`).
- **Donde aparece:** `hover-focus-and-other-states.md:27-28` —
  *«can create one-off peer-* variants on the fly by providing your
  own selector as an arbitrary value between square brackets»*.
- **Status:** `propuesto` / **dudoso**
- **Preferred:** `valor arbitrario`.
- **Justificación:** calco asentado en la comunidad.

### `pseudo-element`, `pseudo-class` (sustantivos CSS)

- **Sentido:** `::before`, `::after`, `:hover`, `:focus`, etc.
- **Donde aparece:** `hover-focus-and-other-states.md:34-36` —
  *«Style the `::before` and `::after` pseudo-elements using the
  before and after variants»*; línea 40 — *«the content of the
  pseudo-element is not actually in the DOM»*.
- **Status:** `propuesto`
- **Preferred:** `pseudo-elemento`, `pseudo-clase`.
- **Justificación:** calco consolidado en CSS.

### `specificity` (sustantivo CSS)

- **Sentido:** prioridad CSS de un selector.
- **Donde aparece:** `styling-with-utility-classes.md:29-30` —
  *«have no other means of managing the specificity»*;
  `hover-focus-and-other-states.md:18-21` —
  *«subsequent-sibling combinator …»*.
- **Status:** `propuesto`
- **Preferred:** `especificidad` (literal, calco asentado en CSS).
- **Justificación:** la traducción castellana estándar.

### `snippet` (en contexto de ejemplo de código)

- **Sentido:** bloque pequeño de código que se muestra en el
  tutorial para ilustrar un punto.
- **Donde aparece:** `styling-with-utility-classes.md:23` (varios
  fences `text`).
- **Status:** `mantener` (literal del contexto de ejemplo de
  código).

### `stylelint`, `selector`, `source code`

- **Sentido:** términos del taller normal de CSS.
- **Status:** `mantener` / `traducir` según contexto. No se
  glosan en detalle.

## Lo que falta por leer

- `tailwindcss/installation/{index,play-cdn,using-postcss,using-vite,tailwind-cli}.md` —
  contienen terminología de integración y `@apply`, `theme()`,
  `screen()` y directivas CSS.
- `tailwindcss/border-collapse.md`, `table-layout.md`, `hover-focus-and-other-states.md`
  (resto).
- `tailwindcss/upgrade-guide.md` completo (versión v4 con
  `bg-(--color)` y notación nueva).
- Cualquier archivo de `tailwindcss/installation/framework-guides/`.
- El scraper omitió los archivos de referencia de utilidades; los
  nombres concretos se sostienen en fence (preservados literalmente)
  y la prosa suele ser pobre. No se gana mucho glosando términos
  que viven sólo en code fences.
## Segunda pasada (2026-10-20)

**Material leído en esta iteración:** `tailwindcss/upgrade-guide.md`,
`tailwindcss/installation/{index,using-vite,using-postcss,tailwind-cli,play-cdn}.md`,
`tailwindcss/installation/framework-guides/{nextjs,angular,react-router,vue,sveltekit,astro,nuxt}.md`.

Conclusión anticipada: casi todos los archivos de `installation/` y
`framework-guides/` son *stubs* de dos líneas con texto "Hello world!"
o un fragmento único. El **único archivo con prosa sustancial** es
`upgrade-guide.md`, que explica la migración v3→v4 y define la mayor
parte del vocabulario moderno.

### `v3`, `v4` y la diferencia de paradigma

- **Sentido:** Tailwind CSS v4 cambia la sintaxis del framework. Los
  archivos `.css` sustituyen a `tailwind.config.js`, los directivas
  `@theme`, `@utility`, `@custom-variant`, `@config`, `@source`,
  `@layer base/theme/components/utilities` configuran el sistema.
- **Status:** `mantener`
- **Justificación:** versiones y directivas literales del producto.

### `@theme` (directiva CSS)

- **Sentido:** "we recommend using those variables instead of the theme()
  function whenever possible" (`upgrade-guide.md:66`); centraliza los
  tokens de diseño como CSS variables (`--color-red-500`).
- **Status:** `mantener`
- **Decisión abierta:** en el cuerpo de una frase, ¿"define los tokens en
  una sección `@theme`"? Sí, mantener literal.

### `@utility` (directiva CSS)

- **Sentido:** "To customize the container utility in v4, extend it
  using the @utility directive" (`upgrade-guide.md:13`); permite
  declarar utilidades nuevas con su CSS.
- **Status:** `mantener`

### `@custom-variant` (directiva CSS)

- **Sentido:** redefinir una variante, p. ej. ``@custom-variant hover
  (&:hover);`` para sustituir la implementación `hover` sensible a
  dispositivo (`upgrade-guide.md:53-54`).
- **Status:** `mantener`

### `@config` (directiva CSS)

- **Sentido:** cargar `tailwind.config.js` desde el CSS cuando se
  mantiene configuración JavaScript por compatibilidad
  (`upgrade-guide.md:71`).
- **Status:** `mantener`

### `@source` (directiva CSS, una nueva aparición)

- **Sentido:** registrar rutas fuente adicionales o *inline* para el
  escaneo de clases: `@source inline(...)` safelista utilidades en v4
  (`upgrade-guide.md:73`).
- **Status:** `mantener`

### `@layer` (existente, nueva importancia)

- **Sentido:** sistema de cascadas de Tailwind v4 (`@layer base`,
  `@layer theme`, `@layer components`, `@layer utilities`). Las
  reglas del usuario entran por defecto en `components` o `utilities`.
- **Status:** `mantener`

### `custom property` y `theme variable` (re-confirmados)

- **Donde aparece:** `upgrade-guide.md:20` — *"border-color:
  var(--color-gray-200, currentColor)"*; v4 introduce el resto de
  variables `--color-*`, `--default-ring-*`, `--breakpoint-*`.
- **Status:** `mantener` (custom property) / `propuesto` (theme variable)
  / `mantener` la **sintaxis CSS** (`var(--color-red-500)`).
- **Preferred:** `variable CSS` para las references, `variable de tema`
  para cuando se habla del sistema semántico.

### `screen.xl`, `theme(screens.xl)` (deprecation)

- **Sentido:** v4 reemplaza `theme(screens.xl)` por la variable CSS
  `--breakpoint-xl` (`upgrade-guide.md:68`).
- **Status:** `mantener` la notación CSS; **`propuesto`** para el sintagma
  castellano: «el breakpoint `xl`» se lee natural.

### `theme()`, `theme(colors.red.500)` (deprecation)

- **Sentido:** la función JS `theme(...)` se conservaba para casos en los
  que no había variables CSS; v4 la depreca a favor de
  `var(--color-red-500)` (`upgrade-guide.md:66-68`).
- **Status:** `mantener` (API)

### `corePlugins`, `safelist`, `separator` (deprecation JS)

- **Sentido:** opciones de `tailwind.config.js` eliminadas en v4
  (`upgrade-guide.md:72`).
- **Status:** `mantener`

### `arbitrary value` con sintaxis `[...]` → `(...)`

- **Sentido:** v4 cambia el operador de arbitrary values de corchetes a
  paréntesis (`upgrade-guide.md:45-46`). Para variables, además
  desaparece el soporte implícito de `var(...)`, hay que escribir
  explícito.
- **Status:** `mantener`
- **Justificación:** literal del API.

### `divide-x-*`, `divide-y-*` (cambio de selector)

- **Sentido:** utilidad que aplica bordes entre hijos. v4 cambia el
  selector de `:not([hidden]) ~ :not([hidden])` a `:not(:last-child)`
  (`upgrade-guide.md:3`).
- **Status:** `mantener`

### `ring`, `ring-*` (cambio de 3px a 1px)

- **Sentido:** v4 cambia el grosor del ring (`ring-*`) de 3px a 1px y
  el color por defecto de `blue-500` a `currentColor`
  (`upgrade-guide.md:21`).
- **Status:** `mantener`

### `border-color`, `currentColor` (valor CSS)

- **Sentido:** valor por defecto en `border-*` y `divide-*` cambia a
  `currentColor` (`upgrade-guide.md:15`).
- **Status:** `mantener`

### `Preflight` (capa base)

- **Sentido:** el conjunto de estilos base que Tailwind inyecta
  (`upgrade-guide.md:31`).
- **Status:** `mantener`

### `placeholder` variant (cambio de color)

- **Sentido:** v4 simplifica el color de placeholder
  (`upgrade-guide.md:32`).
- **Status:** `mantener`

### `transition`, `transition-colors`, `outline-color`

- **Sentido:** la utility `transition-colors` ahora también transiciona
  `outline-color` (`upgrade-guide.md:56-57`).
- **Status:** `mantener`

### `transform`, `transform-none` (cambio de propiedades)

- **Sentido:** rotate-* / scale-* / translate-* v4 usan las propiedades
  CSS individuales en vez de la propiedad `transform`. Por eso
  `transform-none` ya no las "resetea" — hay que usar
  `rotate-none`, `scale-none`, `translate-none`
  (`upgrade-guide.md:59-62`).
- **Status:** `mantener`

### `focus ring`, `focus-visible` (interacción)

- **Status:** `mantener`

### `transform`, `scale`, `rotate`, `translate`

- **Status:** `mantener`

## Términos transversales de los guides de instalación

`installation/{index,using-postcss,using-vite,tailwind-cli,play-cdn}.md`
son *stubs*: el scraper perdió la prosa.

Los `installation/framework-guides/` son guías de un proyecto cada uno
(Angular, Next.js, Vue, Nuxt, Astro, SvelteKit, Gatsby, Tanstack Start,
PHP Laravel con Vite o Mix, React Router, Ember, Qwik, Parcel, Adonis,
Meteor, Phoenix, Rails, Rspack+Vue/React, SolidJS, Symfony).
Son traducciones del snippet de instalación de cada framework, así que
contienen nombres de frameworks y poco más.

**Decisión:** el glosario v3 no necesita entradas individuales para los
framework-guides de Tailwind — son material trivial para
traducción. Cuando pasemos por la traducción, los nombres propios de
cada framework se preservarán tal cual están en los fences.

## Lo que falta por leer

- `tailwindcss/border-collapse.md`, `tailwindcss/table-layout.md`,
  `tailwindcss/caption-side.md` y demás utility references con
  contenido. Los archivos de referencia de utilidades son cortos y de
  poco términos nuevos (la mayoría del texto es tablas de tokens
  `bg-red-500`, `p-4`, etc. que se preservan literal).
- `tailwindcss/upgrade-guide.md` en su totalidad (el archivo tiene 75
  líneas; sólo leí las primeras 80).
- `tailwindcss/installation/using-vite.md` etc. — re-intentando, podría
  ser que el scraper no haya cogido bien el HTML y haya dejado solo
  "Hello world!"; el material real está en el manual en vivo.
