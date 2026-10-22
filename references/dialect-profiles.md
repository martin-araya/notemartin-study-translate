<!-- version: 1.0.0 -->

# Matriz de dialectos versionada (`notemartin-study-translate`)

Esta matriz declara explícitamente qué subconjunto del dialecto
soporta cada perfil. Activar un gate **no** activa los demás
implícitamente.

## 1. Perfiles iniciales

| profile_id | versión | extensions_enabled | supports |
|---|---|---|---|
| `core-v1` | `1.0.0` | (ninguna) | CommonMark + GFM básico, Mermaid preservado |
| `mild-extensions-v1` | `1.0.0` | footnotes, admonitions, definitions, directives | `core-v1` + las cuatro extensiones |
| `extended-mdx-v1` | `1.0.0` | mild + mdx | `mild-extensions-v1` + MDX con gate |
| `extended-html-v1` | `1.0.0` | mild + html | `mild-extensions-v1` + HTML embebido con gate |
| `experimental-v1` | `1.0.0` | mild + mdx + html + mermaid (labels: allow) | Todas las opt-in |
| `fr-es-experimental-v1` | `0.1.0` | (ninguna) sobre el par fr→es | CommonMark + GFM en francés, sin revisión humana nativa (fase 103 del roadmap). Ver `evals/cases/pilot-fr.md`. |
| `en-es-ar-v1` | `0.1.0` | (ninguna) sobre locale es-AR | CommonMark + GFM con voseo rioplatense. Firma nativa pendiente (fase 109). Ver `references/locale-policy.md`. |
| `en-es-mx-v1` | `0.1.0` | (ninguna) sobre locale es-MX | CommonMark + GFM con tratamiento de usted mexicano. Firma nativa pendiente. |
| `en-es-es-v1` | `0.1.0` | (ninguna) sobre locale es-ES | CommonMark + GFM en español de España. Firma nativa pendiente. |

## 2. Lo que NO se soporta implícitamente

- Activar `mdx` no activa `html` ni `mermaid`.
- Activar `html` no activa `mdx` ni `mermaid`.
- Activar `mermaid.labels: allow` requiere `mermaid.enabled: true`;
  la inversa no es válida.
- Activar `frontmatter_policy: translate-allowlist` no activa
  ninguna extensión de contenido.

## 4. Procedimiento para añadir un perfil

1. Definir `profile_id`, `version` y `extensions_enabled`.
2. Enumerar `supports` (qué incluye) y `does_not_support` (qué
   excluye).
3. Si el perfil implica combinaciones nuevas, escribir tests en
   `tests/test_extension_combinations.py`.
4. Actualizar la tabla de la sección 1.

## 5. Verificación

El script `scripts/dialect_matrix.py` vuelca la matriz a JSON:

```
python3 scripts/dialect_matrix.py --out dialect_matrix.json
```

Cada perfil tiene `version` con formato semver simple (`X.Y.Z`).

## 6. Perfiles lingüísticos

Los perfiles anteriores describen dialectos **Markdown**. La sección K
del roadmap (idioma de origen) añade una segunda dimensión que la
matriz Markdown sola no recoge: el par de idiomas.

| profile_id | language_pair | estado | restricción |
|---|---|---|---|
| `en-es-core-v1` | `en → es` | estable | Núcleo 0.1.0. Fase 060 cerrada. |
| `fr-es-experimental-v1` | `fr → es` | experimental | Sin revisor humano nativo en fr. Fases 101, 102, 104, 105 cerradas; fase 103 del roadmap en `revisión asistida registrada, pendiente de revisión humana`. Política lingüística en `references/source-language-policy-fr.md`. Política de citas en `references/citations-policy.md`. |
| `en-es-ar-v1` | `en → es-AR` | experimental | Voseo rioplatense. Sin firma humana nativa (fase 109). Política regional en `references/locale-policy.md`. |
| `en-es-mx-v1` | `en → es-MX` | experimental | Tratamiento de usted mexicano, sin vosotros. Sin firma humana nativa. |
| `en-es-es-v1` | `en → es-ES` | experimental | Español peninsular con vosotros. Sin firma humana nativa. |
| `ar-es-experimental-v1` (implícito en `language_matrix.json`) | `ar → es` | experimental | Texto bidireccional preservado byte-a-byte. Política RTL en `references/rtl-policy.md`. Sin firma humana nativa. |

Activar los perfiles regionales no toca el núcleo. Su encendido exige
haber autorizado un corpus real en `evals/cases/<variant>.md` y
haber aceptado el disclaimer de competencia de cada variante.

## 7. Matriz lingüística (`reports/language_matrix.json`)

La fase 110 del roadmap solicita una **matriz** que liste todos los
pares declarados. Este archivo la complementa: `scripts/language_matrix.py`
vuelca `reports/language_matrix.json` con un objeto por par y enumera
los pares planificados.

El umbral para considerar la matriz **estable** es de **tres pares
con `evaluation_kind: human_approved`**. Hasta entonces, la fila 110
del roadmap lleva `✅ ⚠` y el JSON se trata como **experimental**.

Forma del JSON:

```json
{
  "generated_at": "...",
  "skill": "notemartin-study-translate",
  "schema_version": "110",
  "threshold_human_approved": 3,
  "stable": false,
  "human_approved_count": 1,
  "pairs": [
    {
      "pair": "en-es",
      "locale": "es",
      "evaluation_kind": "human_approved",
      "reviewer_status": "human_approved",
      "human_reviewer": "núcleo-0.1.0",
      "corpus": "tests/fixtures/pilot/",
      "limits": ["CommonMark + GFM básico", "Mermaid preservado"]
    },
    ...
  ],
  "planned_pairs": [
    {"pair": "en-es-CL", "locale": "es-CL", "rationale": "Chile pendiente"},
    ...
  ]
}
```

Para que un par figure como `evaluation_kind: human_approved`, su
`manifest.json` debe incluir una entrada en `reviewers[]` con
`kind: "human"` y `scope: "global"`. El JSON se regenera tras
cada promoción.