RUN=run-7fbd5e24 · MEDIDO: 2026-10-22

Decisiones que no puede tomar el agente sin cambiar el resultado, y
observaciones de la fuente que se registran en vez de repararse
(`AGENTS.md` §5.3). Ninguna bloquea la traducción: bloquean el
`semantic_pass` del directorio correspondiente.

## 1. Terminología que necesita decisión

El glosario v3 está congelado (146 entradas, hash `be150264…`). Al traducir
el lote 0002 de Tailwind aparecieron términos que **no** están en él y que
se repitirán en los 3 257 paquetes de `nextjs`. Los equivalentes de abajo
son los que usé, y son una propuesta, no una política:

| Término de origen | Equivalente usado | Conflicto o duda |
|---|---|---|
| `variant` | variante | No está en el glosario. Es la palabra más frecuente del lote. |
| `arbitrary value` | valor arbitrario | No está en el glosario. |
| `arbitrary variant` | variante arbitraria | No está en el glosario. |
| `pseudo-class` / `pseudo-element` | pseudo-clase / pseudo-elemento | No está en el glosario. |
| `breakpoint` | punto de ruptura | No está en el glosario. |
| `template partial` | parcial de plantilla | No está en el glosario. |
| `specificity` | especificidad | No está en el glosario. |
| `placeholder` | marcador de posición | Ojo: `placeholder` también es el valor del atributo HTML. Aquí se traduce solo cuando es prosa. |
| `forced color adjust` | *(se conserva literal)* | Es el nombre de una familia de utilidades de Tailwind, no prosa. |
| `importance flag` / `important flag` | *(se conserva literal)* | El glosario tiene `important flag` marcado como traducible; mantuve el término inglés porque es el argumento real de `@import`. **Contradicción sin resolver.** |

Los nombres de clase (`hover`, `focus`, `peer-*`, `group-aria-*`,
`@custom-variant`, `@supports`, …) se conservan literales en todos los
casos: son identificadores, no prosa.

## 2. Observaciones de la fuente

Ninguna se reparó. Todas están en el corpus Beta autorizado.

| Ubicación | Qué ocurre | Decisión tomada |
|---|---|---|
| `hover-focus-and-other-states.md`, `seg-50808be6` | El texto dice `While pointeronly targets…`: el token `pointer` perdió el espacio y quedó pegado a la palabra siguiente. | Traducido literalmente como `pointeronly`. Repararlo sería corregir el producto en origen. |
| `styling-with-utility-classes.md`, `seg-51fe5d08` | «…but using a␤ instead of the ::before pseudo-element»: falta el nombre del elemento; el scraper se lo comió. | Traducido manteniendo el hueco. No inventé `<span>`. |
| `hover-focus-and-other-states.md`, `seg-1eab7334` y `seg-02d91966` | «when a␤ or␤ element is in an open state»: faltan dos nombres de elemento (`<details>`/`<dialog>`). | Igual que arriba: hueco conservado. |
| `hover-focus-and-other-states.md`, `seg-061aa662` | «Use the not-forced-colors variant to apply styles based when…»: sobra una palabra en el original. | Traducido al español sin la palabra sobrante; el significado no cambia. |
| `hover-focus-and-other-states.md`, `seg-303f4397` | «Tailwind also includes a forced color adjust utilities…»: el artículo está en singular. | Traducido correctamente en español. No afecta contenido técnico. |
| 37 segmentos del lote 0002 | Ninguno tiene `protected_literals`, pese a contener mucho código inline, CSS y JSX. | La protección de literales no se está extrayendo en este corpus. **No es un defecto del lote**: es un hueco del extractor que conviene medir antes de traducir 44 000 segmentos. |

## 3. Lo que hace falta del usuario

1. ¿Apruebas los equivalentes de la tabla de §1, o los cambias? Si se
   aprueban, entran en el glosario v4 con hash nuevo, y eso invalida los
   segmentos ya traducidos que los usen.
2. ¿Cómo se llama el destino de la revisión? La casilla 4 de G-CORE
   exige `manifest.reviewers[].kind == "human"` con alias y
   `signed_at`. Sin ese nombre, `advance_state --to approved` seguirá
   devolviendo 1, y esa es la respuesta correcta.
3. ¿Revisas el alcance completo o por partes? Si la firma declara
   `scope` distinto de `global`, G-CORE no se puede marcar y hay que
   decirlo en el informe.