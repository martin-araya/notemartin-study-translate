<!-- version: 1.1.0 -->

# Contrato de la extensión MDX (`notemartin-study-translate`)

Este contrato delimita el subconjunto MDX que la skill soporta. **No
es una promesa de soporte universal**: cualquier componente, atributo
o patrón no listado aquí queda bloqueado por el gate MDX y se
preserva como literal.

## 1. Estado del módulo

- **Activación:** opt-in y dormiente por defecto, es decir,
  desactivado hasta que el perfil lo encienda. Encenderlo exige que el
  perfil declare `mdx.corpus_ref` y `mdx.justification` (criterio 1 de
  G-EXT). El corpus que lo justifica en este repositorio es el piloto,
  `tests/fixtures/pilot/`, declarado en `evals/cases/mdx.md`.
- **Gating:** `scripts/prepare.py` consulta `profile.mdx.enabled`. Con el
  módulo apagado, cualquier JSX fuera de fence bloquea el archivo. Con el
  módulo encendido, el bloqueo desaparece **solo para lo que este contrato
  admite**: `mdx_selector.contract_findings()` emite un hallazgo propio por
  cada componente, atributo o patrón no listado. Encender el módulo no
  permite cualquier JSX.
- **Corpus de referencia:** `tests/fixtures/mdx/` (sintético) para los casos
  de contrato, y `tests/fixtures/pilot/` (material real autorizado) para
  los componentes que la documentación real usa.

## 2. Componentes soportados

| Componente | Hijos traducibles | Atributos permitidos | Notas |
|---|---|---|---|
| `Info` | Texto plano entre `<Info>` y `</Info>` | `title` | Render como admonition neutra. |
| `Note` | Texto plano | `title` | Render como nota al pie. |
| `Warning` | Texto plano | `title` | Render como advertencia. Severidad preservada. |
| `Tabs` | Solo contenedor; no se traduce directamente | `defaultValue` | Hijos `<TabItem>` se traducen individualmente. |
| `TabItem` | Texto plano | `label`, `value` | `value` preservado literal. |
| `TabPanel` | Solo contenedor; no se traduce directamente | `id` | Ancla de panel (ver §5). `id` literal. |
| `Card` | Texto plano | `title`, `icon` | `icon` preservado literal. |
| `CardGroup` | Contenedor; no se traduce directamente | `cols` | Hijos `<Card>` se traducen individualmente. |
| `Callout` | Texto plano | `type`, `title` | `type` preservado literal. |
| `CodeGroup` | Contenedor; no se traduce directamente | `title` | Presente en el corpus piloto real. |

Cualquier otro componente (por ejemplo `<Info2>`, `<CustomThing>`)
se reporta como `unsupported_component` y bloquea el archivo.

## 3. Reglas por construcción

### 3.1 Frontmatter

YAML al inicio del archivo. Se preserva íntegro: ni las claves ni
los valores se modifican.

### 3.2 Imports

`import X from 'Y';` y `import {A, B} from 'Y';`. Se preservan
byte a byte (literales protegidos por la fase 063). No se evalúa
ni se resuelven rutas.

### 3.3 Exports

`export const X = ...;` y `export function f() { ... }`. Se
preservan byte a byte. Las expresiones dentro de la exportación no
se traducen.

### 3.4 Expresiones JSX embebidas

`{...}` dentro de atributos o como hijos. Se preservan byte a byte.
Las referencias `{frontMatter.title}`, `{severity}` y similares
siguen literales; el traductor no resuelve su valor.

### 3.5 Bloques de código

Fenced con tres o más backticks, con o sin lenguaje. Se preservan
byte a byte. Siguen siendo literales protegidos aunque estén dentro
de un `<TabItem>`.

### 3.6 Encabezados, listas, citas, tablas, imágenes

Soportados por el núcleo CommonMark + GFM. Su semántica es la misma
dentro de MDX; el traductor no distingue si están al nivel raíz o
dentro de un componente.

## 4. Lo que NO está soportado

- Componentes personalizados no listados arriba (se bloquean).
- Props que ejecuten código o resuelvan recursos (`onClick`,
  `style` con valores dinámicos, `as`).
- Componentes con `children` que sea una función o una expresión
  compleja.
- Bloques `<script>` y `<style>` inline (el parser los marca como
  `unsafe_html`).
- MDX v2 con pipes (`export const x = |>`). Si el corpus los usa,
  se bloquea.

## 5. Tabs y paneles

El atributo `value` de `<TabItem>` es un identificador funcional.
Vincula la pestaña con el panel que muestra su contenido. Tres
formas de panel son reconocidas:

- `<TabPanel id="X">` con `id="X"`.
- Cualquier etiqueta HTML/MDX con `data-tab="X"`.
- Encabezado Markdown con anchor explícito `{#X}`.

Reglas:

1. `value` es literal. La traducción no debe modificarlo nunca.
2. `id`, `data-tab` y anchors referenciantes son literales.
3. `label` puede traducirse; es visible.
4. Si no se encuentra un panel que coincida con `value`, el
   archivo no se bloquea, pero el validador emite un aviso
   `info` con severidad `warning`.

## 6. Activación y desactivación

- `prepare.py` consulta `profile.mdx.enabled`. Si es `false`, los
  archivos con JSX fuera de fence se clasifican como `blocked` y no entran
  al flujo de traducción.
- Con el módulo encendido, `mdx_selector.contract_findings()` aplica este
  contrato y emite, por cada violación, un hallazgo con `severity:
  bloqueante`: `unsupported_component`, `unsupported_attribute`,
  `unsafe_html` o `unsupported_mdx_syntax`.
- Desactivar MDX restaura el bloqueo seguro y no altera otros
  archivos del corpus (fase 070). La identidad byte a byte de esa
  afirmación se comprueba en
  `tests/test_optional_deactivation.py::test_desactivacion_mdx`.

| Código de salida de `prepare.py` | Significado |
|---|---|
| 0 | el corpus se clasificó; los hallazgos bloqueantes van en el informe |
| 2 | falta `--inventory`, `--out` o `--segments` |

`prepare.py` no bloquea el proceso por un archivo bloqueado: los registra
con su evidencia para que la decisión sea de quien dirige la ejecución.
El proceso sale distinto de cero solo cuando la entrada es inválida.