<!-- version: 1.1.0 -->

# Contrato de Markdown soportado

Este documento declara el dialecto Markdown aceptado por la skill y las construcciones ajenas al núcleo. Define qué se traduce, qué se preserva y qué bloquea la aprobación de un archivo.

## 1. Núcleo sintáctico soportado

Base: CommonMark 0.30, sin variantes regionales.

Construcciones aceptadas sin política adicional:

- Encabezados ATX (`#`, `##`, …, `######`) y Setext (subrayado con `=` o `-`).
- Párrafos y saltos de línea explícitos con dos espacios o barra invertida al final.
- Listas ordenadas y no ordenadas, con anidamiento hasta tres niveles por defecto.
- Énfasis (`*…*` o `_…_`) y negrita (`**…**` o `__…__`).
- Tachado (`~~…~~`) como extensión GFM.
- Enlaces inline (`[texto](destino "título")`) y de referencia (`[texto][etiqueta]` con definiciones).
- Enlaces con fragmento local (`[texto](#anchor)`).
- Imágenes inline (`![alt](destino "título")`) y de referencia.
- Código inline entre comillas invertidas simples (`` `…` ``) con longitud de backticks variable.
- Bloques de código fenced con tres o más comillas invertidas, y bloques de código indentados con cuatro espacios o tabulador.
- Citas en bloque (`> …`).
- Líneas horizontales (`---`, `***`, `___`).
- Entidades HTML (`&amp;`, `&#1234;`, `&Nombre;`) y referencias de carácter solo cuando cumplen función sintáctica explícita.
- Escape con barra invertida (`\*`, `\\`, etc.).
- Anchor HTML inline `<a id="anchor"></a>` como complemento del enlace Markdown, observado en la fuente del piloto.

## 2. Construcciones GFM aceptadas

- Tablas con separadores `|` y fila de alineación (`| --- |`, `| :--- |`, `| ---: |`, `| :---: |`).
- Listas de tareas (`- [ ]`, `- [x]`).
- Autolinks (`<https://…>`, `<email@dominio>`).
- Tachado (`~~texto~~`).

## 3. Construcciones aceptadas con política explícita

### 3.1 Frontmatter

- Política por defecto: `preserve`. Se conserva íntegro, sin traducir claves ni valores.
- Política opcional: `translate-allowlist`. Requiere lista permitida no vacía de campos traducibles. Los campos no listados se preservan.
- El tipo YAML no se altera. Claves y valores funcionales permanecen literales.

### 3.2 Mermaid dentro de fences

- Estado: **no se traduce** dentro del núcleo.
- Estado: **no se valida sintácticamente** en el núcleo: `prepare.py`
  comprueba que el fence está cerrado, y nada más.
- Estado: se **preserva byte a byte** dentro del bloque.
- Un Mermaid sintácticamente inválido **no bloquea** en el núcleo: se copia
  literal y se registra un hallazgo `mermaid_unsupported` con severidad
  `info`. Bloquea solo si el perfil activa la traducción de etiquetas
  (`mermaid.enabled: true` y `mermaid.labels: allow`), que exige
  `mermaid.corpus_ref` y `mermaid.justification`. Antes este párrafo decía
  que Mermaid era «bloqueante implícito en el núcleo»: el código nunca hizo
  eso, y el hallazgo `mermaid_in_fence` que emitía `prepare.py` era `info`.

### 3.3 HTML embebido fuera de CommonMark

- Estado: **bloqueante** en el núcleo.
- Etiquetas y atributos permitidos por CommonMark (por ejemplo `<!-- … -->`, `<br>`, `<sub>`, `<sup>`, `<a id="…"></a>`) se aceptan; el resto se trata como construcción ajena y bloquea la aprobación del archivo.

### 3.4 Imágenes con texto

- Una imagen rasterizada con contenido textual no se traduce. Se conserva el recurso y se declara como limitación. La descripción alternativa traducida, cuando exista, sí entra en revisión.

## 4. Construcciones bloqueantes por defecto

Las siguientes construcciones bloquean la aprobación del archivo afectado. No se traducen ni se eliminan: el archivo queda en estado `blocked` hasta que el usuario decida su disposición.

Las cuatro primeras se levantan con `findings` de tipo `mdx_component`, `html_embebido`, `wikilink` y `unsupported_directive` en `scripts/prepare.py`. Las cuatro últimas son las que cada módulo opcional debe elevar a bloqueante cuando se enciende, y ninguna bloquea con el módulo apagado:

- MDX completo, incluyendo imports, exports y expresiones JSX.
- Componentes personalizados tipo `<Info>`, `<CodeGroup>`, `<Note>`, `<Warning>` y equivalentes, observados en `APIs/OpenRouter/01` y `04`.
- HTML embebido fuera del conjunto permitido por CommonMark.
- Wikilinks no estándar (`[[…]]`) y directivas de frameworks de documentación no listadas.
- Componentes React, Vue, Svelte o equivalentes dentro de Markdown.
- Fórmulas LaTeX crudas fuera de un bloque de código reconocido.
- Imágenes rasterizadas con texto crítico para la comprensión.
- Bloques con directivas `:::` (admonitions no reconocidas), observado en `mermaid/guides/presentation.md`.

**Corrección de una afirmación anterior:** esta lista declaraba «fórmulas LaTeX crudas» como bloqueantes por defecto y `directivas` solo cuando el módulo estaba apagado. Ninguna de las dos cosas era cierta: el núcleo preserva la matemática y no la detecta, y las directivas desconocidas bloquean tanto con el módulo apagado como encendido (salvo que el perfil las admita por nombre). Lo que se lista aquí es lo que `prepare.py` emite, no lo que este documento antes afirmaba.

## 5. Matriz de soporte con presencia confirmada en el piloto

La matriz se construye contra el corpus piloto descrito en `evals/cases/pilot.md`. La columna `presente en piloto` refleja lo observado en los 9 archivos seleccionados.

| Construcción | Presente en piloto | Soportada | Bloqueante |
|---|---|---|---|
| Encabezados ATX | sí (los 9) | sí | no |
| Encabezados Setext | no observado en el piloto | sí | no |
| Párrafos y saltos de línea | sí | sí | no |
| Listas ordenadas | sí | sí | no |
| Listas no ordenadas | sí | sí | no |
| Anidamiento de listas, tres niveles | sí | sí | no |
| Énfasis y negrita | sí | sí | no |
| Tachado | no observado en el piloto | sí | no |
| Enlaces inline | sí | sí | no |
| Enlaces con fragmento local | sí | sí | no |
| Enlaces de referencia | no observado en el piloto | sí | no |
| Imágenes inline | sí | sí | no |
| Imágenes de referencia | no observado en el piloto | sí | no |
| Código inline con backticks variables | sí | sí | no |
| Bloques de código fenced | sí | sí | no |
| Bloques de código indentados | no observado en el piloto | sí | no |
| Citas en bloque | sí (`APIs/OpenRouter/01`) | sí | no |
| Líneas horizontales | sí (`APIs/OpenRouter/01`) | sí | no |
| Entidades HTML funcionales | sí | sí | no |
| Anchor HTML inline `<a id="…"></a>` | sí (`typescriptlang/*`, `developer-mozilla/*`) | sí, política explícita | no |
| Tablas GFM con alineación | sí (`oracle/notas/Cap_14/...md`) | sí | no |
| Listas de tareas | no observado en el piloto | sí | no |
| Autolinks | no observado en el piloto | sí | no |
| Frontmatter YAML | sí (`oracle/notas/Cap_14/...md`) | sí, política explícita | no |
| Mermaid dentro de fences | sí (`mermaid/*`) | preservado, no traducido | sí |
| HTML embebido fuera de CommonMark | no observado en el piloto de esta categoría | no | sí |
| Componentes MDX/JSX (`<Info>`, `<CodeGroup>`) | sí (`APIs/OpenRouter/04`) | no | sí |
| Wikilinks no estándar | no observado en el piloto | no | sí |
| Directivas `:::` | sí (`mermaid/guides/presentation.md`) | no | sí |
| Fórmulas LaTeX crudas | no observado en el piloto | no | sí |

La columna `Bloqueante` indica si una construcción presente en el piloto y no soportada bloquea la aprobación del archivo. La presencia por sí sola no bloquea; lo que bloquea es la combinación de presencia y falta de soporte.

Para las filas marcadas `no observado en el piloto`, la columna `presente en piloto` se reconsiderará cuando el corpus autorizado cubra más archivos.

## 6. Método de validación

Cuando se reciba un nuevo corpus autorizado:

1. Recorrer cada documento del inventario.
2. Para cada construcción de la matriz, registrar presencia o ausencia por documento.
3. Las construcciones presentes no soportadas se marcan `bloqueante` para el archivo afectado.
4. Las construcciones presentes soportadas se confirman con casos de prueba del parser.
5. Las construcciones soportadas ausentes del piloto conservan el marcador `no observado` hasta que otro corpus autorizado las cubra.

La conformidad con un estándar externo (CommonMark o GFM) se demuestra ejecutando los fixtures definidos para el parser, no citando la especificación.

## 7. Relación con fases siguientes

| Fase | Relación |
|---|---|
| 014 | La elección de parser debe demostrar rangos fuente para cada fila soportada de la matriz. |
| 015 | Las construcciones no soportadas se clasifican con severidad `bloqueante` y el archivo no desaparece del inventario. |
| 016 | Los rangos de segmentos deben respetar los límites de cada construcción sin cortar UTF-8. |
| 017 | Los literales protegidos incluyen código inline, fences, bloques indentados, fórmulas, componentes MDX/JSX y destinos de enlace. |
| 020 | La prueba sin cambios debe recuperar los bytes originales sobre cada construcción soportada. |

Este contrato no demuestra paridad con el importador de Notion. La importación remota requiere evidencia manual separada.

## 8. Parser seleccionado

- **Nombre**: `markdown-it-py`
- **Versión fijada**: `3.0.0`
- **Cobertura de dialecto**: CommonMark 0.30 más extensiones GFM (`table`, `strikethrough`) habilitadas. La extensión para `front_matter` y `footnote` se activa solo cuando el perfil lo solicite.
- **Posiciones verificables**: cada token expone `map = [line_start, line_end]` con líneas 0-indexadas. La conversión a rangos de bytes se realiza con un `LineIndex` que precomputa los offsets de cada `\n`. Sobre el piloto:

| Archivo | Tokens | Con `map` | Coincidencias |
|---|---:|---:|---:|
| typescriptlang/handbook/2/basic-types.md | 50 | 33 | 16/16 |
| typescriptlang/handbook/2/functions.md | 54 | 38 | 22/22 |
| APIs/OpenRouter/01 - Introducción, Autenticación y Formato General.md | 58 | 38 | 17/17 |
| APIs/OpenRouter/04 - Capacidades Avanzadas Reasoning, Tool Calling.md | 106 | 74 | 40/40 |
| mermaid/build-and-edit/write-diagram-syntax.md | 209 | 92 | 59/59 |
| mermaid/guides/presentation.md | 108 | 73 | 38/38 |
| developer-mozilla/How_to/Layout_cookbook/Card.md | 33 | 23 | 13/13 |
| developer-mozilla/Guides/Cascading_variables/Using_custom_properties.md | 35 | 25 | 15/15 |
| oracle/notas/Cap_14/Cap_14_Physical_Storage_Structures.md | 350 | 212 | 71/71 |
| **Total** | **1003** | **608** | **291/291** |

Las **291/291 coincidencias** verifican que, para cada token con contenido propio, el corte del texto fuente entre las líneas declaradas contiene el `token.content` reportado.

- **Limitaciones conocidas**: las posiciones son a nivel de línea, no de byte nativo. La conversión a bytes exige un `LineIndex` por archivo y se ejecuta en `scripts/prepare.py`. El parser no valida Mermaid, MDX ni HTML embebido fuera de CommonMark; esas detecciones se hacen en `scripts/prepare.py` y en los clasificadores de cada módulo opcional.
- **Comparativa**: se evaluó `commonmark-py 0.9.2` sobre los mismos archivos. Produce nodos de bloque de alto nivel (1 por archivo) sin granularidad a nivel de inline ni soporte para GFM. **Descartado** por insuficiente para el dialecto declarado.
- **Política de actualización**: cualquier cambio de versión se anota en este apartado y exige reejecutar la verificación sobre el piloto. El campo `parser` del manifiesto refleja la versión efectiva en cada ejecución. El procedimiento ejecutable es `scripts/compare_parser.py`, documentado en `references/parser-upgrade.md` (fase 144). Comparación registrada el 2026-10-20 sobre los 9 documentos del piloto: `markdown-it-py 3.0.0` (fijada) frente a `2.2.0` (candidata realmente instalada en una venv aislada) produjo **rangos, slugs y recuentos idénticos**, por lo que no hay cambio que migrar. Comprobado además que no existe versión publicada posterior a la 3.0.0. Informe: `reports/maintenance/parser_comparison.json`.

## 9. Procedimiento de verificación del parser

1. Cargar el archivo origen como bytes UTF-8.
2. Construir `LineIndex` sobre el texto decodificado.
3. Parsear con `markdown-it-py` en modo `commonmark` con GFM (`table`, `strikethrough`) si el perfil lo declara.
4. Para cada token con `map` y `content`, calcular `[byte_start, byte_end)` desde `map` y verificar que `token.content` aparece dentro de `text[byte_start:byte_end]`.
5. Si la tasa de coincidencias baja del 100 % sobre el piloto, se documenta como regresión y se bloquea la promoción.