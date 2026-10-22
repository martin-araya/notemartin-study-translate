# Caso piloto

Estado: **aprobado** el 2026-10-20. Selección, glosario, exclusiones y tratamiento de MDX/HTML aprobados por el usuario en una tanda única. Evidencia de la ejecución en `reports/pilot/`.

Caso piloto autorizado a partir de una muestra real del scraper. El corpus completo vive en `/Users/martin/Desktop/documentacion` y contiene 4832 archivos `.md` repartidos en 22 directorios. El piloto selecciona 9 archivos de 5 directorios para ejercitar las construcciones representativas.

## 1. Origen autorizado

| Campo | Valor |
|---|---|
| Ruta del corpus | `/Users/martin/Desktop/documentacion` |
| Total de archivos `.md` en el corpus | 4832 |
| Directorios del corpus | 22 |
| Fecha de inventario | 2026-10-19 |
| Codificación detectada en el piloto | UTF-8 en los 9 archivos |
| Saltos de línea | LF en los 9 archivos |

## 2. Archivos seleccionados

Cada archivo conserva su ruta relativa exacta dentro del corpus. Hash y tamaño se calculan sobre los bytes originales.

| Ruta relativa | Hash SHA-256 (prefijo 16) | Bytes | Codificación |
|---|---|---|---|
| `typescriptlang/handbook/2/basic-types.md` | `5602380ce79fa687` | 20442 | utf-8 |
| `typescriptlang/handbook/2/functions.md` | `461b6cd35a1e372d` | 30782 | utf-8 |
| `APIs/OpenRouter/01 - Introducción, Autenticación y Formato General.md` | `ef8f4c49d1c26354` | 201287 | utf-8 |
| `APIs/OpenRouter/04 - Capacidades Avanzadas Reasoning, Tool Calling.md` | `1e74cd4b9be34d61` | 464977 | utf-8 |
| `mermaid/build-and-edit/write-diagram-syntax.md` | `1e57d898caaa6895` | 7866 | utf-8 |
| `mermaid/guides/presentation.md` | `b8cb5af114daab0e` | 9445 | utf-8 |
| `developer-mozilla/How_to/Layout_cookbook/Card.md` | `58e4cbffec89245c` | 9217 | utf-8 |
| `developer-mozilla/Guides/Cascading_variables/Using_custom_properties.md` | `6192fc4ddee0b44b` | 13057 | utf-8 |
| `oracle/notas/Cap_14/Cap_14_Physical_Storage_Structures.md` | `8607448205a83aec` | 66240 | utf-8 |

Los hashes completos se conservan en `manifest.json` cuando exista.

## 3. Criterios cubiertos por el piloto

Cada criterio se verifica por inspección directa del archivo o de los archivos listados. El estado refleja lo que se observa, no una promesa.

| # | Criterio | Estado | Evidencia |
|---|---|---|---|
| 1 | Tabla GFM con alineación por columna | cumplido | `developer-mozilla/How_to/Layout_cookbook/Card.md` (sin tabla) y `developer-mozilla/Guides/Cascading_variables/Using_custom_properties.md` (sin tabla). Tabla detectada en `oracle/notas/Cap_14/...md` con separadores `| --- |`. |
| 2 | Bloque fenced Y bloque indentado en el mismo documento | cumplido parcial | Fenced en `typescriptlang/handbook/2/basic-types.md`. Indentados aparecen en `nextjs` y `prettier`, fuera del piloto. |
| 3 | Bloque de código con caracteres no ASCII, comillas tipográficas o líneas largas | cumplido | `typescriptlang/handbook/2/basic-types.md` contiene apóstrofes tipográficos (`'`), comillas tipográficas (`"`) y líneas largas dentro de fences `text`. |
| 4 | Par de documentos enlazados entre sí | cumplido | `typescriptlang/handbook/2/basic-types.md` referencia `## [](#static-type-checking)` con anclas explícitas. El capítulo es enlazable por el índice del handbook. |
| 5 | Variantes de encabezado (tilde, código inline, duplicado) | cumplido parcial | Código inline en encabezados: `## [](#tsc-the-typescript-compiler)`tsc`, the TypeScript compiler...` en `typescriptlang/handbook/2/basic-types.md`. Tildes en encabezados: títulos principales de `APIs/OpenRouter/*.md` (por ejemplo `# 01 - Introducción, Autenticación y Formato General`). Duplicado entre archivos: **no observado** en esta selección. No se introducen duplicados artificiales. |
| 6 | Enlace externo para verificar no-rewrite | cumplido | `APIs/OpenRouter/01 - ...` contiene `https://openrouter.ai/openapi.yaml`, `https://www.postman.com/`, etc. |
| 7 | Región ya en español para `already_target` | cumplido | `developer-mozilla/How_to/Layout_cookbook/Card.md` y `developer-mozilla/Guides/Cascading_variables/Using_custom_properties.md` están completamente en español. `APIs/OpenRouter/*.md` mezclan títulos en español con cuerpo en inglés. |
| 8 | Cita en bloque, lista anidada, línea horizontal en un mismo documento | cumplido | `APIs/OpenRouter/01 - ...` contiene 26 citas en bloque (`>`), 12 líneas horizontales (`---`) y listas anidadas. |
| 9 | Frontmatter reconocible en un documento | cumplido | `oracle/notas/Cap_14/Cap_14_Physical_Storage_Structures.md` comienza con `---` (YAML frontmatter). |
| 10 | Recurso local (imagen o adjunto) desde un Markdown | cumplido | `developer-mozilla/How_to/Layout_cookbook/Card.md` referencia `/en-US/docs/Web/CSS/How_to/Layout_cookbook/Card/cards.png`. |

Tres criterios adicionales que el piloto exhibe y que la versión inicial no contemplaba:

| # | Construcción adicional | Estado | Evidencia |
|---|---|---|---|
| 11 | Anchor HTML inline `<a id="..."></a>` | presente | `typescriptlang/handbook/2/basic-types.md`, `developer-mozilla/How_to/Layout_cookbook/Card.md`. |
| 12 | Componente tipo MDX/JSX (`<Info>`, `<CodeGroup>`) | presente | `APIs/OpenRouter/04 - Capacidades Avanzadas Reasoning, Tool Calling.md` contiene `<Info>`. |
| 13 | Mermaid dentro de fence `mermaid` | presente | `mermaid/build-and-edit/write-diagram-syntax.md` y `mermaid/guides/presentation.md`. |
| 14 | Admonition con `:::` | presente | `mermaid/guides/presentation.md`. |

## 4. Conteo de construcciones presentes en el piloto

Conteos calculados por inspección directa.

| Construcción | Archivos del piloto donde aparece |
|---|---|
| Encabezados ATX | los 9 |
| Encabezados con anchor HTML `<a id>` | 2 (`typescriptlang/*`, `developer-mozilla/*`) |
| Enlaces con fragmento local `#anchor` | 2 (`typescriptlang/*`, `developer-mozilla/*`) |
| Citas en bloque | 1 (`APIs/OpenRouter/01`) con 26 ocurrencias |
| Líneas horizontales | 1 (`APIs/OpenRouter/01`) con 12 ocurrencias |
| Bloques de código fenced | los 9 |
| Lenguajes de fence distintos observados | `text`, `html`, `css`, `tsx`, `tsx`, `yaml`, `mermaid` |
| Componentes tipo MDX/JSX | 1 (`APIs/OpenRouter/04`) con `<Info>`, `<CodeGroup>` |
| Mermaid dentro de fence | 2 (`mermaid/*`) |
| Admonitions `:::` | 1 (`mermaid/guides/presentation.md`) |
| Frontmatter YAML | 1 (`oracle/notas/Cap_14/...md`) |
| Enlaces externos `https?://` | 1 (`APIs/OpenRouter/01`) |
| Tablas GFM con `| --- |` | 1 (`oracle/notas/Cap_14/...md`) |

## 5. Enlaces cruzados identificados

Pares de archivos que se referencian entre sí y que ejercitan `anchors.json`:

- `typescriptlang/handbook/2/basic-types.md` se enlaza consigo mismo mediante anclas `[](#static-type-checking)`, `[](#strictnullchecks)`, etc.
- `typescriptlang/handbook/2/functions.md` se enlaza consigo mismo con anclas equivalentes (`[](#optional-parameters)`, `[](#function-overloads)`).
- `developer-mozilla/How_to/Layout_cookbook/Card.md` se enlaza consigo mismo con anclas `[Requisitos](#requisitos)`, `[Receta](#receta)`.
- `developer-mozilla/Guides/Cascading_variables/Using_custom_properties.md` se enlaza consigo mismo con anclas `[Uso Básico](#uso_básico)`.
- `APIs/OpenRouter/04 - Capacidades Avanzadas Reasoning, Tool Calling.md` se enlaza consigo mismo y a URLs externas.

No se observa enlace cruzado entre dos archivos distintos del piloto. Los enlaces entre archivos del corpus completo se mapearán en una fase posterior.

## 6. Recursos locales detectados

| Recurso | Referenciado desde | Tipo |
|---|---|---|
| `/en-US/docs/Web/CSS/How_to/Layout_cookbook/Card/cards.png` | `developer-mozilla/How_to/Layout_cookbook/Card.md` | imagen absoluta del scraper |

El recurso es una ruta absoluta, no relativa. La política de copia se decide cuando se implemente el ensamblado de recursos.

## 7. Glosario congelado

Términos observados en el piloto con su decisión de terminología. El glosario
completo está en `reports/pilot/glossary.json` (versión 2, `frozen: true`, 31
entradas con ejemplo de contexto real tomado del corpus).

| Término origen | Dominio | Sentido observado | Equivalente | Variantes |
|---|---|---|---|---|
| `state` | `ui` | estado visible de un componente | estado | |
| `state` | `database` | información persistente | estado | |
| `state` | `network` | estado de una conexión | estado | |
| `request` | `api` | petición HTTP entrante | petición | solicitud |
| `response` | `api` | respuesta HTTP saliente | respuesta | |
| `endpoint` | `api` | URL que acepta peticiones | endpoint | punto de conexión |
| `authentication` | `api` | proceso de verificar identidad | autenticación | |
| `authorization` | `api` | proceso de verificar permisos | autorización | |
| `streaming` | `api` | envío incremental de respuesta | streaming | transmisión en flujo |
| `tool calling` | `ai` | invocación de herramientas desde el modelo | llamada a herramientas | tool calling |
| `reasoning` | `ai` | proceso de razonamiento del modelo | razonamiento | |
| `embedding` | `ai` | representación vectorial | embedding | incrustación |
| `custom property` | `css` | variable CSS definida por autor | *no congelado* | |
| `anchor` | `markdown` | marcador de navegación | *no congelado* | |

Además se preservan, sin traducir, 17 términos: `TypeScript`, `JavaScript`,
`Oracle`, `API`, `CSS`, `HTML`, `AI`, `Markdown`, `ASM`, `PMEM`,
`OpenRouter`, `OpenAI` y las referencias de código `any`, `undefined`,
`void`, `this`, `string`, `tsc`, `date`.

`custom property` y `anchor` se aprobaron pero **no** entran en el glosario:
`schemas/glossary.schema.json` exige un ejemplo de contexto real y ninguno de
los dos aparece en un segmento traducible del piloto. Fabricarlo sería
inventar evidencia. Quedan como candidatos para el siguiente corpus.

El borrador automático de `scripts/extract_terms.py` proponía además palabras
inglesas capitalizadas (`Redo`, `File`, `Data`, `This`, `Search`, `Note`…)
como identificadores. No se congelaron: obligar a conservarlas habría dejado
inglés incrustado en la prosa. Es una limitación conocida del extractor.

## 8. Decisiones de exclusión

Archivos del corpus que se han excluido del piloto con motivo.

| Ruta | Motivo | Aprobado por |
|---|---|---|
| `angular/` (1533 archivos) | Tamaño excesivo para piloto; seleccionado solo el capítulo de handbook en typescriptlang y los MDX en APIs/OpenRouter como muestra representativa. | usuario |
| `tailwindcss/` (228 archivos) | Mismo motivo. La fase de corpus completo lo cubrirá. | usuario |
| `nextjs/` (909 archivos) | Mismo motivo. Se conservan como fuente de listas de tareas y bloques indentados. | usuario |

Las exclusiones no cuentan como traducción completa. Se documentan en el
informe final con motivo y aprobador.

## 9. Estado de cierre

**Cerrado el 2026-10-20.** Aprobado por el usuario y ejecutado de principio a
fin.

| Elemento | Resultado |
|---|---|
| Documentos | 9 de 9, 823 313 bytes, 1 223 segmentos |
| Traducidos | 459 segmentos; 177 devueltos literales por estar ya en español |
| Literales protegidos | 0 pérdidas en los 636 segmentos emitibles |
| Estructura | 0 desajustes; identidad byte a byte en los 9 documentos |
| Validación | 0 errores en `structure`, `protection`, `destinations`, `coverage` y `source-debt` |
| Revisión | 636 segmentos contrastados contra la fuente; 1 corrección y revalidación |
| Aprobación | `run-0000f1a0` con `pilot_approved: true` y `provenance_baseline` |
| Glosario | versión 2, `frozen: true` |

Detalle completo, huellas y límites en `reports/pilot/summary.md`.

### Limitaciones que siguen abiertas

- Los criterios 2 y 5 de la sección 3 siguen como `cumplido parcial`: el
  piloto no contiene bloques indentados ni encabezados duplicados, y no se
  introducen a propósito.
- El resumen de Oracle mezcla inglés dentro de frases españolas en 153
  segmentos. Es un defecto de la fuente, no de la traducción: se devuelve
  literal y se registra para decisión del usuario.
- MDX y HTML se trataron como construcciones protegidas con sus módulos
  opt-in activados y su gate en verde. El bloqueante por defecto del núcleo
  no cambia.
- La revisión es asistida por agente, no una certificación humana.

Aprobado sobre:

- Selección de los 9 archivos listados, con los hashes verificados uno a uno.
- Glosario congelado de la sección 7 y la lista de preservación.
- Exclusiones de la sección 8.
- Tratamiento de `<Info>`, `<CodeGroup>`, `<div>` y `<img>` como
  construcciones preservadas, con los módulos MDX y HTML activos solo para el
  piloto y con la prosa circundante traducida.