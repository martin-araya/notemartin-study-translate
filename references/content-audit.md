<!-- version: 1.0.0 -->

# Auditoría del contenido de la skill (fase 146)

`scripts/check_distribution.py` (fase 058) comprueba que el paquete esté
listo para entregar: que `SKILL.md` tenga frontmatter, que las rutas citadas
existan y que las dependencias estén pinneadas. Eso es **empaque**.

Esta fase audita lo que la skill **dice**:

| Código | Comprobación | Qué atrapa |
|---|---|---|
| 1 | rutas citadas | un script o una referencia que no existe |
| 2 | comandos documentados | un flag que el script no expone, o un script que no documenta `--help` |
| 3 | reglas canónicas | dos documentos que dan valores distintos a la misma cosa |
| 4 | afirmaciones remotas | decir que algo está verificado en Notion sin evidencia |
| 5 | versión de referencias | una referencia sin marca `<!-- version: X.Y.Z -->` |
| 6 | alcanzabilidad | una referencia que ningún documento menciona |

```bash
python scripts/audit_docs.py --root . \
    --out reports/maintenance/docs_audit.json
```

## 1. Comandos documentados

Se extraen las invocaciones de la forma `python3 scripts/<x>.py [flags]` de
`SKILL.md`, `RELEASE.md`, `CHANGELOG.md`, `roadmap.md`, `AGENTS.md`,
`references/`, `templates/` y `evals/`. Para cada una se ejecuta
`python3 <script> --help` en un subproceso y se comparan los flags
documentados con las opciones que el script expone de verdad.

Un script que no expone `--help` no se considera inválido: se marca como
**no verificable**, y eso también es un hallazgo, porque un comando que nadie
puede comprobar no debería estar en la documentación.

## 2. Reglas canónicas

`references/rule-registry.json` declara los valores que varios documentos
repiten y de dónde sale el canónico:

| Clave | Valor canónico | Fuente de verdad |
|---|---|---|
| `skill_name` | `notemartin-study-translate` | frontmatter de `SKILL.md` |
| `parser_version` | `3.0.0` | `release_contract.json` |
| `anchor_algorithm` | `github-slug-v1` | `release_contract.json` y el contrato Markdown |
| `manifest_version_or_origin` | `translate/v1`, `translate/v0` | `schemas/manifest.schema.json` |
| `remote_status` | `no_verificado`, `verificado_con_evidencia` | `schemas/import_evidence.schema.json` |

El auditor busca cada valor en todos los documentos y falla si aparece uno
distinto del canónico. Dos reglas que hay que entender:

- El patrón de `skill_name` excluye `notemartin-study-notes`: Mentionar
  **otra** skill no es una contradicción.
- `translate/v0` está permitido **solo** como origen de una migración. Es un
  valor enum, no un valor único, precisamente porque la documentación de la
  migración tiene que poder nombrar la versión anterior.

Añadir una regla nueva es una entrada más en el registro, no un cambio de
código.

## 3. Afirmaciones remotas

Las frases prohibidas viven en el mismo registro
(`forbidden_remote_claims`). El auditor solo marca una frase como hallazgo
cuando **el documento la sostiene**: si la misma frase aparece negada
—«no significa verificado en Notion»— no es una afirmación y no se marca.

Una versión naïve de esta comprobación habría marcado la prohibición de
INV-15 como si fuera una afirmación. Por eso el corte es por frase y con
marcadores de negación.

## 4. Qué encontró esta auditoría al aplicarse

La primera ejecución sobre el repositorio encontró cuatro rutas rotas que
llevaban meses en la documentación, y ninguna era un error de código:

| Documento | Ruta citada | Corrección |
|---|---|---|
| `references/markdown-contract.md` | un script de análisis que no existe | se eliminó; la detección se hace en `prepare.py` y en los módulos opcionales |
| `references/locale-policy.md` | una rúbrica regional que no existe | apunta a la rúbrica real del repositorio |
| `references/report-accessibility.md` | una carpeta de estilos que no existe | la política dice hoy que la skill no genera hojas de estilo |
| `references/versioning-policy.md` | un puntero JSON dentro de una ruta | se separó ruta y campo |

Ese es el tipo de defecto que la fase busca: no rompe la ejecución, rompe la
confianza en la documentación.

## 5. Relación con otras fases

| Fase | Relación |
|---|---|
| 058 | `check_distribution.py` sigue siendo la comprobación de empaque; esta la complementa y no la sustituye |
| 142 | el código 5 comparte la lista de referencias con `check_versioning.py` |
| 146 | entregable de esta fase |
| 149 | `gate_extended.py` incluye esta auditoría como módulo `maintenance` |

## 6. Qué NO hace esta auditoría

- **No revisa la calidad de la prosa.** Detecta contradicciones
  mecánicas, no argumentos mal construidos.
- **No ejecuta los comandos documentados** con datos reales: solo verifica
  que el flag existe.
- **No comprueba que las rutas citadas estén donde dicen.** Verifica que
  existan; que apunten al sitio correcto es lectura humana.
- **No sustituye la revisión del contenido de la rúbrica.** Esa revisión es
  un pase aparte (fase 042).