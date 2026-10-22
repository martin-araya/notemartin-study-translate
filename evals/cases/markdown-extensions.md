# Caso extensiones de Markdown (fases 081-090)

Estado: **material sintético declarado y gates ejecutados**. La evidencia está
en `reports/optional/markdown-extensions.json` y en la suite
(`tests/test_footnotes.py`, `test_admonitions.py`, `test_definition_lists.py`,
`test_directives.py`, `test_mermaid_labels.py`, `test_math.py`,
`test_wikilinks.py`, `test_frontmatter_translate.py`,
`test_extension_combinations.py`, `test_content_gates.py`,
`test_dialect_matrix.py`: 82 pruebas en 11 ficheros).

## 1. Medición sobre los corpus reales autorizados

| Construcción | Piloto | Beta |
|---|---|---|
| `:::tipo` de admonition | 0 | 0 |
| `[^id]:` de footnote | 0 | 0 |
| `:param:` / `:returns:` en prosa | 0 | 0 |
| `$$…$$` o `$…$` de ecuación | 0 | 0 |
| fence ```` ```mermaid ```` | presente (`mermaid/`) | presente (`angular/`) |
| frontmatter YAML | presente (`oracle/notas/…`) | presente |
| wikilinks `[[…]]` reales | 0 | 0 |
| listas de definiciones | 0 | 0 |

Corrección de una afirmación previa: `evals/cases/pilot.md` declaraba
«Admonition con `:::` presente». La única ocurrencia real está dentro de un
fence `plaintext` (`mermaid/guides/presentation.md`, `:::{.text-right}`, que es
atributo de Pandoc, no admonition). El ejemplo no es una admonition.

## 2. Corpus sintético que activa cada sub-módulo

| Sub-módulo | Fixture | Bytes | Árbol |
|---|---|---|---|
| 082 admonitions | `tests/fixtures/admonitions/basic.md` | 214 | `b1a1375db56bdb10` |
| 083 listas de definiciones | `tests/fixtures/definitions/basic.md` | 184 | `d3476d765fa70579` |
| 084 directivas | `tests/fixtures/directives/basic.md` | 349 | `24d7d3a9ebf6bb68` |
| 085 Mermaid | `tests/fixtures/mermaid/` (2 archivos) | 193 | `158b0040512fcbaf` |
| 086 matemáticas | `tests/fixtures/math/basic.md` | 292 | `66530d68b4367fd1` |
| 087 wikilinks | `tests/fixtures/wikilinks/basic.md` | 277 | `37da003cf6de31e3` |
| 088 frontmatter traducible | `tests/fixtures/frontmatter/with_translatable.md` | 234 | `9d060c1b3f2ee308` |
| 089 combinaciones | `tests/fixtures/combined/all_ext.md` | 460 | `25897ab0ae7d3021` |
| 081 footnotes | `tests/fixtures/footnotes/basic.md` | 203 | `608d887da5a90ca8` |

Todos son **sintéticos**. Ninguno tiene procedencia, hash de origen ni excerpt
real: existen para ejercitar el comportamiento, no para justificar una
activación sobre documentación de verdad.

## 3. Estado de cada sub-módulo

| Sub-módulo | Activación | Corpus que la justifica |
|---|---|---|
| footnotes | núcleo, sin interruptor | sintético; `references/footnotes.md` lo declara siempre activo |
| admonitions | dormiente (`admonitions.enabled`) | sintético; 0 ocurrencias en material real |
| listas de definiciones | dormiente (`definition_lists.enabled`) | sintético; 0 ocurrencias reales |
| directivas | dormiente (`directives.enabled`) | sintético; 0 ocurrencias reales |
| etiquetas Mermaid | dormiente (`mermaid.labels: allow`) | sintético; hay Mermaid real pero el núcleo lo preserva literal |
| matemáticas | núcleo, sin interruptor | sintético |
| wikilinks | dormiente (`wikilinks.enabled`) | sintético; los `[[…]]` reales del corpus son rutas de Next.js dentro de código |
| frontmatter traducible | dormiente (`frontmatter_policy: translate-allowlist`) | sintético; el frontmatter real existe pero la política es `preserve` |

## 4. Qué no afirma este caso

- **No** afirma que ninguna documentación real contenga estas construcciones:
  afirma que los dos corpus autorizados medidos no las contienen.
- **No** autoriza activar ningún sub-módulo por defecto. Todos son opt-in y,
  con el perfil 1.1.0, exigen `corpus_ref` y `justification`.