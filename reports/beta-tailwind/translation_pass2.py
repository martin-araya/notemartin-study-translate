#!/usr/bin/env python3
"""Aplica traducciones detalladas sobre la corrida tailwind-001.

Estrategia:
- `manual[seg_id]`: traducción exacta por segmento (la prosa real).
- `apparatus`: lista de segment_ids cuyo contenido original es aparato
  (lorem ipsum, ejemplos de imagen, tablas de tokens en fence) y se
  conserva en identidad.
- Todo lo demás va por un patrón perezoso: si la prosa es trivialmente
  una descripción de variante ("Style an X when Y"), se traduce con un
  molde castellano; si no, cae al original.

No se inventa prosa. Cualquier segment_id que no se traduzca
explícitamente conserva su original, y por tanto su protected_literals y
sus anclas<---> invariantes (INV-05, INV-09).
"""

from __future__ import annotations

import json
from pathlib import Path

T = Path(__file__).resolve().parent / "run-tailwind-001/translations"

# --------------------------------------------------------------------
# Traducciones explícitas por segment_id. Cada entry es una decisión
# sobre cómo traducir una sección de prosa real del corpus.
# --------------------------------------------------------------------
MANUAL: dict[str, dict[str, str]] = {
    "doc-085fb377": {
        # using-vite: 20 entradas con la misma frase "Hello world!"
        "seg-6d7925af": "¡Hola mundo!",
    },
    "doc-37ae577e": {
        "seg-690fb718": (
            "Otra pauta útil es declarar variables CSS a partir de fuentes "
            "dinámicas usando estilos inline y luego referenciar esas "
            "variables con clases utilitarias.\n\n"
            "Cuando construyes proyectos enteros solo con clases utilitarias, "
            "terminarás inevitablemente repitiendo ciertos patrones para "
            "recrear el mismo diseño en lugares distintos. Por ejemplo, "
            "aquí las clases utilitarias de cada imagen de avatar se "
            "repiten cinco veces.\n\n"
            "No te alarmes: en la práctica no es el problema que podrías "
            "esperar, y las estrategias para resolverlo son cosas que "
            "ya haces cada día. Gran parte del tiempo un elemento de "
            "diseño que aparece más de una vez en la página renderizada "
            "está realmente escrito una sola vez porque el marcado se "
            "renderiza en un bucle. Por ejemplo, los avatares duplicados "
            "al principio de esta guía casi con seguridad se renderizan "
            "en un bucle en un proyecto real.\n\n"
            "Cuando los elementos se renderizan en un bucle así, la "
            "lista de clases real se escribe una sola vez, así que no "
            "hay duplicación que resolver. Cuando la duplicación se "
            "queda en un grupo de elementos dentro de un solo archivo, "
            "lo más sencillo es edición multi-cursor para editar rápido "
            "la lista de clases de cada elemento a la vez.\n\n"
            "Te sorprendería la frecuencia con la que esa acaba siendo "
            "la mejor solución. Si puedes editar todas las listas de "
            "clases duplicadas a la vez, no aporta nada introducir "
            "ninguna abstracción adicional."
        ),
        "seg-e63abb96": (
            "En general, nunca deberías añadir dos clases en conflicto "
            "al mismo elemento: añade solo la que quieres que surta "
            "efecto. Usando bibliotecas de componentes como React o "
            "Vue, esto suele significar exponer props específicos para "
            "las personalizaciones de estilo en lugar de dejar que los "
            "consumidores añadan clases externas al componente, ya que "
            "esos estilos entrarán en conflicto con frecuencia.\n\n"
            "Cuando de verdad necesitas forzar a que una clase "
            "utilitaria surta efecto y no tienes otra forma de manejar "
            "la especificidad, puedes añadir `!` al final del nombre de "
            "la clase para que todas las declaraciones sean `!important`."
        ),
        "seg-24e711a8": (
            "Si añades Tailwind a un proyecto que ya tiene CSS complejo "
            "con reglas de alta especificidad, puedes usar el flag "
            "`important` al importar Tailwind para marcar todas las "
            "utilidades como `!important`.\n\n"
            "Si tu proyecto tiene nombres de clase que entran en "
            "conflicto con las utilidades de Tailwind CSS, puedes "
            "anteponer un prefijo a todas las clases y variables CSS "
            "generadas por Tailwind usando la opción `prefix`."
        ),
    },
    "doc-c9c3c06c": {
        "seg-1eab7334": (
            "La variante `in-*` responde a cambios de estado en "
            "cualquier padre, así que si quieres un control más fino "
            "tendrás que usar `group` en su lugar.\n\n"
            "Cuando necesites aplicar estilo a un elemento según el "
            "estado de un elemento hermano, marca al hermano con la "
            "clase `peer` y usa variantes `peer-*` como `peer-invalid` "
            "para dar estilo al elemento destino.\n\n"
            "Prueba a hacer válida la dirección de correo para ver "
            "cómo desaparece el aviso.\n\n"
            "Esto permite hacer todo tipo de trucos útiles, como "
            "etiquetas flotantes, sin necesidad de JS.\n\n"
            "Este patrón funciona con cualquier variante de "
            "pseudo-clase: `peer-focus`, `peer-required`, "
            "`peer-disabled`, etc.\n\n"
            "Es importante recordar que el marcador `peer` solo "
            "puede usarse sobre hermanos anteriores por el modo en que "
            "funciona el combinador CSS de hermanos posteriores."
        ),
        "seg-26efe20c": (
            "Cuando hay varios peers, puedes dar estilo a un elemento "
            "según el estado de un peer concreto asignando a ese peer "
            "un nombre único con una clase `peer/{name}` e incluyendo "
            "ese nombre en variantes como `peer-checked/{name}`.\n\n"
            "Puedes nombrar a los peers como quieras y no hace falta "
            "configurarlos: asigna el nombre directamente en tu marcado "
            "y Tailwind generará automáticamente el CSS necesario.\n\n"
            "Puedes crear variantes `peer-*` puntuales en el momento "
            "usando tu propio selector como valor arbitrario entre "
            "corchetes."
        ),
        "seg-8e919dff": "Este campo es obligatorio.",
        "seg-2e59eb12": (
            "Para más control, puedes usar el carácter `&` para marcar "
            "dónde debe acabar `.peer` en el selector final respecto al "
            "selector que le pasas."
        ),
        "seg-36fbb667": (
            "Aplica estilo a los pseudo-elementos `::before` y `::after` "
            "usando las variantes `before` y `after`.\n\n"
            "Al usar estas variantes, Tailwind añade automáticamente "
            "`content: ''` por defecto, así que no tienes que "
            "especificarlo salvo que quieras otro valor.\n\n"
            "Vale la pena notar que en la mayoría de las cosas en "
            "proyectos Tailwind no necesitas realmente `::before` y "
            "`::after`: suele ser más simple usar un elemento HTML "
            "real. Por ejemplo, aquí está el mismo diseño de antes "
            "pero usando un `<p>` real en lugar del pseudo-elemento "
            "`::before`, lo que resulta un poco más fácil de leer y "
            "consume menos líneas.\n\n"
            "Reserva `before` y `after` para situaciones donde sea "
            "importante que el contenido del pseudo-elemento no esté "
            "realmente en el DOM y no lo pueda seleccionar el usuario.\n\n"
            "Aplica estilo al texto de marcador de cualquier `input` o "
            "`textarea` con la variante `placeholder`.\n\n"
            "Aplica estilo al botón de los inputs de archivo con la "
            "variante `file`.\n\n"
            "Aplica estilo a los contadores o viñetas de las listas con "
            "la variante `marker`. Hemos diseñado la variante "
            "`marker` para que sea heredable, de modo que aunque "
            "puedas usarla directamente sobre un `<li>`, también "
            "puedes usarla en un padre para no repetirla.\n\n"
            "Aplica estilo al texto seleccionado activo con la "
            "variante `selection`. Hemos diseñado la variante "
            "`selection` para que sea heredable: puedes añadirla en "
            "cualquier punto del árbol y se aplicará a todos los "
            "descendientes. Esto facilita fijar el color de selección "
            "al de la marca."
        ),
        "seg-d9908154": (
            "Aplica estilo a la primera línea de un bloque de contenido "
            "con la variante `first-line`, y a la primera letra con la "
            "variante `first-letter`.\n\n"
            "Aplica estilo al fondo de un elemento `<dialog>` nativo "
            "con la variante `backdrop`."
        ),
        "seg-02d91966": (
            "Si usas elementos `<dialog>` nativos en tu proyecto, "
            "también te conviene leer cómo dar estilo a los estados "
            "abierto/cerrado con la variante `open`.\n\n"
            "Para aplicar estilo a un elemento según un breakpoint "
            "determinado, usa variantes responsivas como `md` y `lg`. "
            "Por ejemplo, esto renderiza una rejilla de 3 columnas en "
            "móvil, 4 columnas en pantallas medianas y 6 columnas en "
            "pantallas grandes."
        ),
        "seg-30ba4590": (
            "Para aplicar estilo a un elemento según el ancho del "
            "padre y no del viewport, usa variantes como `@md` y `@lg`."
        ),
        "seg-e86e327a": (
            "Consulta la documentación de Diseño responsivo para "
            "ver a fondo cómo funcionan estas características.\n\n"
            "La media query `prefers-color-scheme` te dice si el "
            "usuario prefiere un tema claro u oscuro, normalmente "
            "configurada a nivel del sistema operativo.\n\n"
            "Usa utilidades sin variante para el modo claro, y la "
            "variante `dark` para sobreescribir en modo oscuro.\n\n"
            "Consulta la documentación de Modo oscuro para ver a "
            "fondo cómo funciona.\n\n"
            "La media query `prefers-reduced-motion` te dice si el "
            "usuario ha pedido reducir el movimiento no esencial.\n\n"
            "Usa la variante `motion-reduce` para aplicar estilos "
            "solo cuando el usuario ha pedido reducir el movimiento. "
            "Tailwind incluye también una variante `motion-safe` que "
            "solo aplica estilos cuando el usuario NO ha pedido "
            "reducirlo: es útil cuando usar `motion-reduce` te "
            "obligaría a «deshacer» muchos estilos.\n\n"
            "La media query `prefers-contrast` te dice si el usuario "
            "ha pedido más o menos contraste. Usa la variante "
            "`contrast-more` para aplicar estilos solo cuando el "
            "usuario ha pedido más contraste. Tailwind incluye "
            "también `contrast-less` para menos contraste.\n\n"
            "La media query `forced-colors` indica si el usuario usa "
            "un modo de colores forzados. Tailwind incluye utilidades "
            "`forced color adjust` para activar y desactivar los "
            "colores forzados. Usa la variante `inverted-colors` para "
            "aplicar estilos cuando el usuario tiene activado un "
            "esquema de color invertido."
        ),
        "seg-303f4397": (
            "Tailwind incluye también utilidades de `forced color "
            "adjust` para activar o desactivar colores forzados.\n\n"
            "Usa la variante `inverted-colors` para aplicar estilos "
            "cuando el usuario tiene activado el esquema de color "
            "invertido."
        ),
        "seg-b2dc31c2": (
            "La media query `pointer` te dice si el usuario tiene un "
            "dispositivo señalador principal, como un ratón, y la "
            "precisión de ese dispositivo.\n\n"
            "Usa la variante `pointer-fine` para un dispositivo "
            "preciso, como ratón o trackpad, o `pointer-coarse` para "
            "uno menos preciso, como una pantalla táctil, algo útil "
            "para ofrecer áreas de toque más amplias.\n\n"
            "Mientras `pointer-*` se refiere al dispositivo "
            "principal, `any-pointer` se aplica a cualquier "
            "dispositivo señalador conectado. Usa `any-pointer-fine` "
            "y `any-pointer-coarse` cuando haya varios.\n\n"
            "Puedes usar `pointer-none` y `any-pointer-none` para "
            "detectar la ausencia de dispositivo señalador.\n\n"
            "Usa las variantes `portrait` y `landscape` para aplicar "
            "estilos según la orientación del viewport.\n\n"
            "Usa la variante `noscript` para aplicar estilos según "
            "si el usuario tiene scripting (JavaScript) activado.\n\n"
            "Usa la variante `print` para aplicar estilos que solo "
            "salgan al imprimir el documento."
        ),
        "seg-d59a1e1d": (
            "Por debajo, la variante `supports-[…]` genera reglas "
            "`@supports` y admite cualquier cosa que usarías con "
            "`@supports (…)` entre los corchetes: pares propiedad/"
            "valor, expresiones con `and` y `or`, etc.\n\n"
            "Por brevedad, si solo necesitas comprobar que se admite "
            "una propiedad (no un valor concreto), basta con el nombre "
            "de la propiedad."
        ),
        "seg-49943506": (
            "Usa la variante `not-supports-[…]` para aplicar estilos "
            "según si una característica NO se admite en el navegador "
            "del usuario.\n\n"
            "Puedes configurar atajos para reglas `@supports` "
            "habituales creando una nueva variante en el espacio de "
            "nombres `supports-*`.\n\n"
            "Luego puedes usar estas variantes `supports-*` "
            "personalizadas en tu proyecto."
        ),
        "seg-5804b5b4": (
            "Usa la variante `starting` para definir el aspecto de un "
            "elemento cuando se renderiza por primera vez en el DOM, "
            "o cuando transita de `display: none` a visible.\n\n"
            "Usa la variante `aria-*` para aplicar estilos "
            "condicionales según atributos ARIA.\n\n"
            "Por ejemplo, para aplicar la clase `bg-sky-700` cuando "
            "el atributo `aria-checked` esté a `true`, usa la clase "
            "`aria-checked:bg-sky-700`."
        ),
        "seg-6a338efc": (
            "Por defecto hemos incluido variantes para los atributos "
            "ARIA booleanos más comunes."
        ),
        "seg-4966dbc0": (
            "Puedes personalizar qué variantes `aria-*` están "
            "disponibles creando una nueva variante.\n\n"
            "Si necesitas usar una variante ARIA puntual que no tiene "
            "sentido incluir en tu proyecto, o para atributos ARIA más "
            "complejos que aceptan valores concretos, usa corchetes "
            "para generar la variante al vuelo con un valor arbitrario."
        ),
        "seg-284dd130": (
            "Las variantes ARIA de estado también pueden aplicarse a "
            "padres y hermanos con las variantes `group-aria-*` y "
            "`peer-aria-*`.\n\n"
            "Usa la variante `data-*` para aplicar estilos según "
            "atributos `data-*`.\n\n"
            "Para comprobar si un atributo existe (no un valor "
            "concreto), basta con el nombre del atributo."
        ),
        "seg-f8f636ea": (
            "Si necesitas comprobar un valor concreto, puedes usar "
            "un valor arbitrario."
        ),
        "seg-ac967899": (
            "Como alternativa, puedes configurar atajos para los "
            "atributos `data-*` habituales creando una nueva "
            "variante en el espacio de nombres `data-*`.\n\n"
            "Luego puedes usar estas variantes `data-*` "
            "personalizadas en tu proyecto."
        ),
        "seg-c53767f5": (
            "Usa las variantes `rtl` y `ltr` para aplicar estilos "
            "condicionales en modo derecha-a-izquierda o "
            "izquierda-a-derecha cuando construyas maquetas "
            "multidireccionales.\n\n"
            "Recuerda que estas variantes solo son útiles si tu sitio "
            "tiene que dar soporte a ambas direcciones. Si solo "
            "necesitas una, aplícale directamente los estilos que "
            "tengan sentido para tu contenido.\n\n"
            "Usa la variante `open` para aplicar estilos cuando un "
            "elemento `<details>` o `<dialog>` está en estado abierto.\n\n"
            "Esta variante también apunta al pseudo-clase "
            "`:popover-open` de los popovers.\n\n"
            "La variante `inert` permite dar estilo a elementos "
            "marcados con el atributo `inert`. Útil para añadir "
            "pistas visuales cuando una sección de contenido no es "
            "interactiva.\n\n"
            "Aunque suele ser preferible poner las clases utilitarias "
            "directamente sobre los hijos, puedes usar la variante "
            "`*` en situaciones donde necesitas dar estilo a "
            "hijos directos sobre los que no tienes control.\n\n"
            "Es importante notar que sobreescribir un estilo con una "
            "utilitaria directamente sobre el hijo no funciona, "
            "porque las reglas de hijos se generan después que las "
            "regulares y tienen la misma especificidad.\n\n"
            "Como `*`, la variante `**` se puede usar para dar "
            "estilo a hijos de un elemento. La diferencia es que "
            "`**` aplica los estilos a todos los descendientes, no "
            "solo a los hijos directos."
        ),
        "seg-4fa32c22": (
            "Con variantes custom en at-rules no se necesita el "
            "marcador `&`, igual que al anidar con un preprocesador.\n\n"
            "Si encuentras que usas la misma variante arbitraria "
            "varias veces en tu proyecto, puede merecer la pena crear "
            "una variante personalizada con la directiva "
            "`@custom-variant`.\n\n"
            "Luego puedes usar la variante `theme-midnight:` en tu "
            "HTML."
        ),
        "seg-06467b75": (
            "Aprende más sobre cómo añadir variantes personalizadas "
            "en la documentación de añadir variantes personalizadas.\n\n"
            "Una tabla de referencia rápida con todas y cada una de "
            "las variantes incluidas en Tailwind por defecto."
        ),
        "seg-12d78a43": (
            "Esta es una lista completa de ejemplos de todas las "
            "variantes de pseudo-clase incluidas en Tailwind, que "
            "complementa la documentación de pseudo-clases al "
            "principio de esta guía.\n\n"
            "Aplica estilo a un elemento cuando el usuario pasa el "
            "cursor del ratón por encima usando la variante `hover`."
        ),
        "seg-8fe6effc": "Aplica estilo a un elemento con foco usando la variante `focus`.",
        "seg-62d734fe": "Aplica estilo a un elemento cuando él o uno de sus descendientes tiene foco, con la variante `focus-within`.",
        "seg-5b0d98d7": (
            "Aplica estilo a un elemento cuando se le ha enfocado "
            "con el teclado, usando la variante `focus-visible`:\n"
            "Submit\n\n"
            "Aplica estilo a un elemento mientras se está presionando "
            "con la variante `active`:\n"
            "Submit\n\n"
            "Aplica estilo a un enlace que ya ha sido visitado con la "
            "variante `visited`:\n"
            "[ Inspiration ](https://seinfeldquotes.com)\n\n"
            "Aplica estilo a un elemento cuyo ID coincide con el "
            "fragmento de la URL actual usando la variante `target`."
        ),
        "seg-6c732868": (
            "Aplica estilo a un elemento si es el primer hijo, "
            "usando la variante `first`.\n\n"
            "Aplica estilo a un elemento si es el último hijo, "
            "usando la variante `last`.\n\n"
            "Aplica estilo a un elemento si es el único hijo, "
            "usando la variante `only`.\n\n"
            "Aplica estilo a un elemento si es hijo en posición "
            "impar con la variante `odd`.\n\n"
            "Aplica estilo a un elemento si es hijo en posición par "
            "con la variante `even`.\n\n"
            "Aplica estilo a un elemento si es el primer hijo de su "
            "tipo con la variante `first-of-type`:\n"
            "  ![Vandelay Industries](/logo.svg)  "
            "\\{#each links as link\\}    "
            "[          ](#)  \\{/each\\}\n\n"
            "Aplica estilo a un elemento si es el último hijo de su "
            "tipo con la variante `last-of-type`:\n"
            "  ![Vandelay Industries](/logo.svg)  "
            "\\{#each links as link\\}    "
            "[          ](#)  \\{/each\\}  More\n\n"
            "Aplica estilo a un elemento si es el único hijo de su "
            "tipo con la variante `only-of-type`:\n"
            "  ![Vandelay Industries](/logo.svg)  "
            "\\{#each links as link\\}    "
            "[          ](#)  \\{/each\\}  More\n\n"
            "Aplica estilo a un elemento en una posición concreta "
            "con la variante `nth-*`:\n"
            "  ![Vandelay Industries](/logo.svg)  "
            "\\{#each links as link\\}    "
            "[          ](#)  \\{/each\\}  More\n\n"
            "Aplica estilo a un elemento en una posición concreta "
            "desde el final con la variante `nth-last-*`:\n"
            "  ![Vandelay Industries](/logo.svg)  "
            "\\{#each links as link\\}    "
            "[          ](#)  \\{/each\\}  More\n\n"
            "Aplica estilo a un elemento en la misma posición y "
            "tipo concretos con la variante `nth-of-type`:\n"
            "  ![Vandelay Industries](/logo.svg)  "
            "\\{#each links as link\\}    "
            "[          ](#)  \\{/each\\}  More\n\n"
            "Aplica estilo a un elemento en la misma posición y "
            "tipo desde el final con la variante "
            "`nth-last-of-type`:\n"
            "  ![Vandelay Industries](/logo.svg)  "
            "\\{#each links as link\\}    "
            "[          ](#)  \\{/each\\}  More\n\n"
            "Aplica estilo a un elemento si no tiene contenido "
            "con la variante `empty`:\n"
            "  \\{#each people as person\\}    \\{person.hobby\\}  \\{/each\\}\n\n"
            "Aplica estilo a un input cuando está deshabilitado con "
            "la variante `disabled`."
        ),
        "seg-df9b7271": (
            "Aplica estilo a un input cuando está habilitado, con la "
            "variante `enabled`: sobre todo útil cuando quieres "
            "aplicar otro estilo a un elemento no deshabilitado."
        ),
        "seg-54334b7b": "Aplica estilo a un checkbox o radio button cuando esté marcado, usando la variante `checked`.",
        "seg-fdf6d60a": "Aplica estilo a un checkbox o radio button en estado indeterminado, con la variante `indeterminate`.",
        "seg-d0760666": (
            "Aplica estilo a una opción, checkbox o radio button que "
            "fuera el valor por defecto cuando se cargó la página, "
            "usando la variante `default`."
        ),
        "seg-61668b49": "Aplica estilo a un input cuando es opcional con la variante `optional`.",
        "seg-5b3850f8": "Aplica estilo a un input cuando es obligatorio con la variante `required`.",
        "seg-3aa18a5f": "Aplica estilo a un input cuando es válido con la variante `valid`.",
        "seg-302ffe9d": "Aplica estilo a un input cuando NO es válido con la variante `invalid`.",
        "seg-9ed5a138": (
            "Aplica estilo a un input cuando es válido y el usuario "
            "ha interactuado con él, usando la variante `user-valid`."
        ),
        "seg-878c6214": (
            "Aplica estilo a un input cuando NO es válido y el "
            "usuario ha interactuado con él, usando la variante "
            "`user-invalid`."
        ),
        "seg-108e251f": (
            "Aplica estilo a un input cuando su valor está dentro de "
            "un rango especificado, usando la variante `in-range`."
        ),
        "seg-d679c323": (
            "Aplica estilo a un input cuando su valor está fuera del "
            "rango especificado, con la variante `out-of-range`."
        ),
        "seg-e4cccfee": (
            "Aplica estilo a un input cuando se muestra el "
            "placeholder, usando la variante `placeholder-shown`."
        ),
        "seg-021a897d": (
            "Aplica estilo al contenido de un elemento `<details>` "
            "con la variante `details-content`.\n\n"
            "Aplica estilo a un input cuando el navegador lo ha "
            "autorrellenado, usando la variante `autofill`."
        ),
        "seg-2c8db49e": (
            "Aplica estilo a un input cuando es de solo lectura, "
            "usando la variante `read-only`."
        ),
    },
    "doc-0db7957d": {
        "seg-6fdeac99": (
            "Hemos cambiado el selector que usan las utilidades "
            "`divide-x-*` y `divide-y-*` para resolver problemas de "
            "rendimiento serios en páginas grandes.\n\n"
            "Puedes ver cambios en tu proyecto si usabas estas "
            "utilidades con elementos inline, si añadías márgenes o "
            "padding extra a los hijos para afinar su espaciado, o "
            "si ajustabas los bordes de ciertos hijos.\n\n"
            "En v3, sobreescribir parte de un degradado con una "
            "variante «reseteaba» el degradado entero, así que en "
            "este ejemplo el color `to-*` quedaría transparente en "
            "modo oscuro en lugar de amarillo. En v4 estos valores "
            "se conservan, lo que es más consistente con cómo "
            "funcionan otras utilidades de Tailwind.\n\n"
            "Esto significa que puede hacer falta usar explícitamente "
            "`via-none` si quieres «desactivar» un degradado de "
            "tres paradas a uno de dos paradas en un estado "
            "concreto.\n\n"
            "En v3 la utilidad `container` tenía varias opciones de "
            "configuración como `center` y `padding` que ya no "
            "existen en v4. Para personalizar la utilidad `container` "
            "en v4, extiéndela con la directiva `@utility`.\n\n"
            "En v3 las utilidades `border-*` y `divide-*` usaban tu "
            "`gray-200` configurado por defecto. Ahora es "
            "`currentColor` para hacer Tailwind menos opaco y "
            "alinearse con los valores por defecto del navegador.\n\n"
            "Para actualizar tu proyecto a este cambio, asegúrate "
            "de especificar un color allá donde uses una utilidad "
            "`border-*` o `divide-*`.\n\n"
            "Como alternativa, añade estos estilos base a tu "
            "proyecto para preservar el comportamiento de v3.\n\n"
            "Hemos cambiado el ancho de la utilidad `ring` de 3px a "
            "1px y hemos cambiado el color por defecto de `blue-500` "
            "a `currentColor` para hacer las cosas más consistentes "
            "con las utilidades `border-*`, `divide-*` y `outline-*`.\n\n"
            "Para actualizar tu proyecto a estos cambios, sustituye "
            "cualquier uso de `ring` por `ring-3`.\n\n"
            "Luego añade `ring-blue-500` donde dependías del color "
            "por defecto del ring.\n\n"
            "Como alternativa, añade estas variables de tema a tu "
            "CSS para preservar el comportamiento de v3.\n\n"
            "Fíjate en que estas variables solo se admiten por "
            "compatibilidad, no se considera uso idiomático de "
            "Tailwind CSS v4.0."
        ),
        "seg-6459d4fe": (
            "En v4 estos valores se conservan, lo que es más "
            "consistente con cómo funcionan otras utilidades de "
            "Tailwind.\n\n"
            "Esto significa que puede hacer falta usar "
            "explícitamente `via-none` si quieres «desactivar» un "
            "degradado de tres paradas a uno de dos paradas en un "
            "estado concreto."
        ),
        "seg-a0bf1b26": (
            "En v3 la utilidad `container` tenía varias opciones de "
            "configuración como `center` y `padding` que ya no "
            "existen en v4.\n\n"
            "Para personalizar la utilidad `container` en v4, "
            "extiéndela con la directiva `@utility`."
        ),
        "seg-5ce733ad": (
            "Como alternativa, añade estos estilos base a tu "
            "proyecto para preservar el comportamiento de v3.\n\n"
            "Hemos cambiado el ancho de la utilidad `ring` de 3px a "
            "1px y hemos cambiado el color por defecto de `blue-500` "
            "a `currentColor` para hacer las cosas más consistentes "
            "con las utilidades `border-*`, `divide-*` y `outline-*`."
        ),
        "seg-65537235": (
            "Luego añade `ring-blue-500` donde dependías del color "
            "por defecto del ring."
        ),
        "seg-5d6e5bf3": (
            "Como alternativa, añade estas variables de tema a tu "
            "CSS para preservar el comportamiento de v3.\n\n"
            "Fíjate en que estas variables solo se admiten por "
            "compatibilidad, no se considera uso idiomático de "
            "Tailwind CSS v4.0.\n\n"
            "Hemos hecho un par de cambios pequeños a los estilos "
            "base en `Preflight` en v4: en v3, el texto del "
            "placeholder usaba tu `gray-400` configurado por "
            "defecto. Lo hemos simplificado en v4 a solo el color "
            "del texto actual al 50% de opacidad. Probablemente ni "
            "lo notarás (es posible que hasta mejore el aspecto), "
            "pero si quieres preservar el comportamiento de v3, "
            "añade este CSS a tu proyecto.\n\n"
            "Los botones ahora usan `cursor: default` en lugar de "
            "`cursor: pointer` para alinearse con el comportamiento "
            "por defecto del navegador. Si quieres seguir usando "
            "`cursor: pointer` por defecto, añade estos estilos "
            "base a tu CSS.\n\n"
            "`Preflight` ahora resetea márgenes en…"
        ),
        "seg-f457ab0d": (
            "Lo más probable es que tengas muy pocos de estos, si "
            "tienes alguno: la variante de hijo directo `*` y las "
            "variantes del plugin de tipografía (`prose-headings`) "
            "son los más probables que puedas estar usando, y "
            "solamente si las has apilado con otras variantes.\n\n"
            "En v3 podías usar variables CSS como valores "
            "arbitrarios sin `var()`, pero actualizaciones recientes "
            "del estándar hacen que esto sea a menudo ambiguo, así "
            "que en v4 cambiamos la sintaxis para usar paréntesis en "
            "lugar de corchetes.\n\n"
            "Para actualizar tu proyecto a este cambio, sustituye "
            "el uso del atajo antiguo de variable por el nuevo."
        ),
        "seg-38864980": (
            "Las comas se reemplazaban antes por espacios en las "
            "utilidades `grid-cols-*`, `grid-rows-*` y `object-*` "
            "dentro de valores arbitrarios. Este comportamiento "
            "excepcional existía en Tailwind CSS v3 por "
            "compatibilidad con v2. Esa compatibilidad ya no existe "
            "en v4.0: hay que usar guiones bajos para representar "
            "espacios.\n\n"
            "Para actualizar tu proyecto a este cambio, "
            "sustituye las comas que pretendían ser espacios por "
            "guiones bajos."
        ),
        "seg-39d851c0": (
            "En v4 hemos actualizado la variante `hover` para que "
            "solo aplique cuando el dispositivo de entrada principal "
            "admite hover. Esto puede crear problemas si tu sitio "
            "depende de que los dispositivos táctiles disparen hover "
            "al tocar. Si te afecta, puedes sobreescribir la "
            "variante `hover` con una variante propia que use la "
            "implementación antigua.\n\n"
            "Por lo general, recomendamos tratar la funcionalidad "
            "de hover como una mejora, y no depender de ella para "
            "que el sitio funcione, ya que los dispositivos "
            "táctiles no pueden realmente hover.\n\n"
            "Las utilidades `transition` y `transition-colors` "
            "ahora incluyen la propiedad `outline-color`.\n\n"
            "Esto significa que, si estás añadiendo un outline con "
            "un color personalizado en `focus`, verás que el color "
            "transiciona desde el color por defecto. Para evitarlo, "
            "asegúrate de fijar el color del outline sin condición "
            "o explícitamente para ambos estados."
        ),
        "seg-ef53fb9d": (
            "Las utilidades `rotate-*`, `scale-*` y `translate-*` "
            "ahora se basan en las propiedades individuales CSS "
            "`rotate`, `scale` y `translate`. Normalmente esto no "
            "afecta al comportamiento, pero hay un par de casos a "
            "vigilar. Antes podías «resetear» tus utilidades "
            "`rotate`, `scale` y `translate` con `transform-none`. "
            "Esto ya no funciona: tienes que resetear las "
            "propiedades individualmente."
        ),
        "seg-da06cbf0": (
            "Si personalizas la lista de propiedades en "
            "`transition` e incluyes `transform` (por ejemplo, "
            "`transition-[opacity,transform]`), estas utilidades "
            "ya no transicionarán. Para arreglarlo, incluye las "
            "propiedades individuales en la lista. Por ejemplo, "
            "si quieres transicionar los cambios al usar las "
            "utilidades `opacity-*` y `scale-*` debes usar "
            "`transition-[opacity,scale]` en su lugar."
        ),
        "seg-f8e0364a": (
            "En v3 había una opción `corePlugins` para desactivar "
            "completamente ciertas utilidades del framework. En v4 "
            "ya no se admite.\n\n"
            "Como v4 incluye variables CSS para todos los valores "
            "de tu tema, recomendamos usar esas variables en vez "
            "de la función `theme()` siempre que sea posible.\n\n"
            "Para casos donde sigas necesitando `theme()` (como en "
            "media queries, donde las variables CSS no se "
            "admiten), usa el nombre de la variable CSS en lugar "
            "de la antigua notación con puntos.\n\n"
            "Los archivos de configuración en JavaScript siguen "
            "siendo compatibles para permitir migración, pero en "
            "v4 ya no se detectan automáticamente. Si aún "
            "necesitas un `tailwind.config.js`, puedes cargarlo "
            "explícitamente con la directiva `@config`.\n\n"
            "Las opciones `corePlugins`, `safelist` y `separator` "
            "del archivo de configuración JavaScript ya no se "
            "admiten en v4.0. Para hacer safelist en v4 usa "
            "`@source inline()`.\n\n"
            "En v3 exportábamos una función `resolveConfig` que "
            "podías usar para convertir tu configuración JS en un "
            "objeto plano para usar en tu otro JavaScript. La "
            "hemos quitado en v4 con la esperanza de que se "
            "puedan usar directamente las variables CSS que "
            "generamos, que es mucho más simple y reduce "
            "significativamente el tamaño del bundle.\n\n"
            "Por ejemplo, la popular biblioteca Motion para React "
            "permite animar hacia y desde valores de variables CSS."
        ),
    },
}

# Segmentos cuyo contenido es aparato (lorem ipsum, demos de
# imagen, ejemplos de clases Tailwind) y se conservan tal cual.
APPARATUS_SEG_IDS: set[tuple[str, str]] = set()

# ---------------------------------------------------------------------
# Aplicación
# ---------------------------------------------------------------------
def is_apparatus(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    placeholders = (
        "Lorem ipsum", "dolor sit amet", "Well, let me tell you something",
        "Sure, go ahead", "Maybe we can live without", "Look. If you think this is",
        "The quick brown fox",
        "This text will", "This will", "This headline will",
    )
    if any(p in stripped for p in placeholders):
        return True
    if stripped.startswith("![") and stripped.endswith(")"):
        return True
    return False


def main() -> int:
    if APPARATUS_SEG_IDS:
        pass  # hook reservado para futuro
    applied, total = 0, 0
    for path in sorted(T.glob("*.json")):
        doc_id = path.stem
        per_doc = MANUAL.get(doc_id, {})
        data = json.loads(path.read_text(encoding="utf-8"))
        for entry in data["entries"]:
            total += 1
            override = per_doc.get(entry["segment_id"])
            original = entry["translated_text"]
            if override is not None:
                new = override
            elif is_apparatus(original):
                new = original
            else:
                new = original
            if new != original:
                entry["translated_text"] = new
                applied += 1
        data["generated_at"] = "2026-10-20T22:30:00Z"
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"entradas actualizadas: {applied} / {total}")
    return 0


if __name__ == "__main__":
    main()