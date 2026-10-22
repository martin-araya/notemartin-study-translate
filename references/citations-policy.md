<!-- version: 1.0.0 -->

# Política de citas (`notemartin-study-translate`, fase 105)

Esta política decide qué se traduce y qué se preserva cuando un
texto aparece como **cita** dentro de un documento Markdown.
Convive con `references/translation-policy.md` (prosa general) y con
el catálogo de literales protegidos del núcleo (`INV-05`).

> El soporte de la política de citas no hace garantía de fidelidad
> semántica. La auditoría la realiza la rúbrica y la revisión
> asistida; la revisión humana, cuando exista, firma cada segmento
> marcado como no traducible.

## 1. Tres categorías explícitas

| Categoría | Significado | Comportamiento | Estado en manifest |
|---|---|---|---|
| `cita_contractual` | Licencias, condiciones de uso, descargo de responsabilidad legal, garantías, copyright, términos contractuales. | **No se traduce.** Se preserva byte-a-byte. | `preserved_skipped` (no cuenta como traducción). |
| `literal_tecnico` | Código, comandos, identificadores, mensajes de error literales, fórmulas, unidades. | **No se traduce.** Cubierto por `INV-05` y por el catálogo de literales del núcleo. | `preserved_skipped`. |
| `prosa_traducible` | Citas que NO son contractuales: referencias bibliográficas, citas de autor, reflexiones entrecomilladas en prosa. | **Se traduce.** Forma parte del flujo normal. | `translatable`. |

Las tres categorías son excluyentes a nivel de bloque. Un mismo
archivo puede contener segmentos en las tres.

## 2. Heurísticas de detección (`scripts/citations.py`)

El clasificador opera por bloque y, dentro del bloque, por frase.
Las reglas siguientes son auditables; añadir una nueva regla
exige un test que falle primero (TDD, AGENTS.md §10).

1. Si el bloque es un bloque de código (`code_fenced`,
   `code_indented`, `code_inline`), es `literal_tecnico` por
   construcción.
2. Si el bloque es una `blockquote` que empieza por una
   **admonition legal** (`> **Note légale**`, `> **Licence**`,
   `> **Mentions légales**`, `> **Note de licence**`), es
   `cita_contractual`.
3. Si el bloque contiene un **marcador SPDX** (`SPDX-License-...`)
   o `Copyright ©`, es `cita_contractual`.
4. Si el bloque contiene una frase jurídica reconocible en francés
   (heurística ampliable): `« conditions d'utilisation »`,
   `« tous droits réservés »`, `« est autorisé »`, `« est interdit »`,
   `« aux termes de »`, `« garantie »`, `« limitation de
   responsabilité »`, `« éditeur »` en posición jurídica, es
   `cita_contractual`.
5. Cualquier otra `blockquote` se clasifica como
   `prosa_traducible`. Este es el comportamiento por defecto.

> Las reglas 2, 3 y 4 son conservadoras: si dudan, devuelven
> `prosa_traducible` y dejan que la revisión asistida o humana
> reclasifique. Un falso negativo se corrige en `reports/issues.json`.
> Un falso positivo **rompe** la fidelidad contractual.

## 3. Por qué no traducir `cita_contractual`

- Una traducción no certificada cambia el contenido del contrato o
  de la licencia. El lector, además de confiar en la versión
  traducida, debe poder cotejarla con el original si es necesario.
- En muchos marcos legales (UE, OHADA, jurisdicciones nacionales),
  la versión original es la vinculante.
- La calidad de la traducción importa menos que la trazabilidad: el
  lector debe poder decir « esto está aquí, y en este idioma, a
  sabiendas ».

Mantener la `cita_contractual` en idioma original no es una
imperfección. Es la decisión correcta. El `manifest.json` debe
reflejarlo mediante `preserved_skipped` y nunca como
`translatable`.

## 4. Citas no contractuales (`prosa_traducible`)

Las citas de autor, las referencias bibliográficas y los extractos
de fuentes externas que no son contratos ni licencias se traducen
con el resto del documento. Para evitar ambigüedad:

- Si la cita es corta y reconocible, se traduce y se enriquece con
  el autor en la prosa española.
- Si la cita es larga, se traduce y se conserva entre comillas
  tipográficas `« … »`.
- Si la cita contiene un fragmento contractual dentro (sub-bloque),
  ese sub-bloque se preserva en idioma original aunque el resto se
  traduzca. Esto requiere que el agente identifique el sub-bloque y
  lo proteja con marcadores.

## 5. Implementación

`scripts/citations.py` expone `classify(segment, source_text)` y
`write_protection_map(segments) -> dict`. El script es invocable
desde `prepare.py` y desde cualquier validador de corpus.

## 6. Limitaciones aceptadas

- Las heurísticas son francesas y españolas. Para otro par de
  idiomas se necesita una variante (`citations_policy_xx.py`).
- Las frases jurídicas se amplían por iteración. El primer conjunto
  cubre lo más común; un corpus real puede necesitar añadidos que
  se registran en `policy_revision` (rúbrica).
- El clasificador no reemplaza al abogado. Si un bloque plantea
  duda legal seria, se escala al usuario.

## 7. Lo que NO hace

- No traduce licencias ni términos contractuales.
- No añade disclaimers explicativos que la fuente no tenía.
- No inventa separación entre el contenido y la cita cuando la
  fuente no la marca.
- No reemplaza la revisión humana cuando el bloque es legalmente
  significativo.
