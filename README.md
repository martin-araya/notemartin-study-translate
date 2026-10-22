# notemartin-study-translate

[![skills.sh](https://skills.sh/b/martin-araya/notemartin-study-translate)](https://skills.sh/martin-araya/notemartin-study-translate)

Traduce documentación técnica en Markdown al español **sin convertirla en resumen, notas de estudio ni contenido nuevo**. Conserva significado, terminología, cobertura y estructura del corpus original, y entrega una carpeta local lista para que el usuario la importe manualmente a Notion.

**English summary.** An agent skill that translates a folder of technical Markdown documentation into Spanish with fidelity as the contract: it never summarizes, reorders, corrects or rewrites the source, never publishes through the Notion API, and never claims more coverage than the manifest can prove. Each document is split into verifiable segments with frozen literals, translated by unit, reviewed against a semantic rubric, and only promoted to the output folder when the global gate passes. The scripts in `scripts/` do not translate: they check that what the skill claims is still true.

---

## Qué hace

- Traduce prosa técnica a español (`target_language` por defecto `es`) desde un corpus Markdown local.
- Preserva la fuente como inmutable: `source_root` es de solo lectura y no se toca.
- Protege literales (código, URLs, identificadores, tablas de tokens) byte a byte mediante marcadores `§§…§§`.
- Congela un glosario por dominio y sentido tras un piloto aprobado por el usuario.
- Persiste cada traducción en `translations/<clave>.json` identificada por `segment_id`, y rechaza respuestas ajenas, segmentos ausentes, marcadores desequilibrados y literales perdidos.
- Revisa la traducción por separado de quien la produce, con una rúbrica de diez dimensiones.
- Entrega un árbol local `output_root` importable a mano, o un `ZIP` si se activa el módulo de entrega.

## Qué NO hace

| No | Por qué |
|---|---|
| No resume | Traducir no es condensar: cada fase preserva la prosa completa. |
| No reorganiza | El orden de secciones y la estructura documental no cambian. |
| No corrige | Los errores técnicos de la fuente se conservan y se declaran como hallazgo. |
| No publica por API | No hay comunicación con la API de Notion ni con ningún servicio remoto. |
| No ejecuta nada de la fuente | Todo lo que aparece en el corpus es **dato**: no se ejecutan comandos, no se siguen URLs, no se renderizan directivas. |
| No promete inferencia local | El procesamiento sigue al proveedor del modelo del agente activo. |
| No fabrica progreso | Un estado terminal exige evidencia; una ejecución parcial nunca se presenta como completa. |

## Instalación

```bash
npx skills add martin-araya/notemartin-study-translate
```

El CLI instala la skill para el agente que detects (Claude Code, Cursor, Codex, GitHub Copilot, Windsurf, Gemini, Kilo, OpenCode, VS Code, Zed y el resto del [directorio de agentes](https://skills.sh/agents)). Para instalar solo en un agente, consulta `npx skills add --help`.

### Requisitos

- **Python 3.9+** para los scripts de verificación y operación.
- Dependencias fijadas en [`requirements.txt`](requirements.txt):

  ```bash
  pip install -r requirements.txt
  ```

  `markdown-it-py==3.0.0` · `jsonschema==4.25.1` · `langdetect==1.0.9` · `pytest==8.4.2`

- Un agente con acceso a lectura de archivos. La traducción la hace el modelo del agente: la skill no añade servicios externos.

### Instalación manual

La skill es un directorio. Se puede copiar a la ruta de skills del agente que uses (por ejemplo `~/.claude/skills/notemartin-study-translate/`) sin instalar nada más.

## Uso

1. Declara las tres raíces: `source_root` (corpus original), `work_root` (estado) y `output_root` (entrega). Deben ser distintas entre sí.
2. Inventaría el corpus y genera `profile.json` según [`schemas/profile.schema.json`](schemas/profile.schema.json).
3. Traduce un piloto, consigue la aprobación del usuario y congela `glossary.json`.
4. Traduce por unidades y guarda cada respuesta con `scripts/receive_translations.py`.
5. Ensambla, revisa semánticamente y valida el gate global.
6. Promueve a `output_root` con `scripts/export.py`.

El procedimiento completo, con sus comprobaciones en cada paso, está en [`references/workflow.md`](references/workflow.md). Los puntos de no-negocio y las invariantes están en [`SKILL.md`](SKILL.md).

### Cuándo dispara

- Hay una carpeta local de Markdown que el usuario quiere traducir al español.
- Se pide una traducción fiel y reproducible de documentación técnica.
- Hay que entregar un árbol local listo para subir a mano a Notion u otro destino documental.

**No dispara** para: resumir, generar apuntes, corregir el original, traducir código, hacer OCR, publicar por API ni traducir prosa libre sin destino documental.

## Estructura del repositorio

| Ruta | Rol |
|---|---|
| `SKILL.md` | Contrato de la skill: cuándo dispara, entradas, procedimiento, invariantes y verificación de cierre. |
| `references/` (63) | Referencia operativa: flujo, dialecto Markdown, revisión semántica, operación, entrega, terminología y políticas por módulo. |
| `scripts/` (115) | Utilidades ejecutables: inventario, parseo, traducción por unidades, ensamblado, validación, gates y mantenimiento. No traducen; comprueban lo que la skill afirma. |
| `schemas/` (15) | Contratos JSON: perfil, glosario, segmento, manifiesto, entrega, módulos, caché y release. |
| `evals/` | Rúbrica de fidelidad, casos autorizados por fase y actas de release. |
| `templates/` | Plantillas de paquete de traducción y de paquete de revisión. |
| `tests/` (152 ficheros de prueba) | Suite de pruebas del contrato, los scripts y la documentación. |
| `reports/` | Evidencia de ejecuciones reales: manifiestos, glosarios congelados, inventarios, gates y resúmenes. |
| `modules.json` | Estado declarado de los nueve módulos opcionales, con su corpus y su justificación. |
| `release_contract.json` | Versión de la skill y de cada esquema y documento. |
| `CHANGELOG.md` · `RELEASE.md` | Qué cambió y por qué se verifica; qué afirma y qué no afirma esta versión. |

## Verificación

```bash
python3 -m pytest tests -q                                                  # suite del contrato y los scripts
python3 scripts/check_distribution.py --root . --out dist_report.json       # gate de empaquetado
python3 scripts/audit_docs.py --out reports/maintenance/audit-docs.json      # referencias huérfanas y contratos rotos
python3 scripts/check_versioning.py --out reports/maintenance/versioning.json
```

`check_distribution.py` es el gate de empaquetado: comprueba el frontmatter de `SKILL.md`, que cada ruta de la tabla §6 exista, que los enlaces internos de `references/` resuelvan, que cada script citado exista, que las dependencias estén fijadas con `==` y que no haya artefactos prohibidos (`__pycache__`, `.pyc`, `.tmp`, `.partial`).

Portabilidad registrada: macOS y Linux con CPython están `verified` con informe; Windows está `design_only`. Ver [`references/portability.md`](references/portability.md).

## Estado y límites

Esta skill es una **release candidata del núcleo estable** (versión `0.4.0`), no un lanzamiento 1.0.0. Lo que esta versión **no** sostiene:

- **Fidelidad semántica absoluta.** La validación determinista verifica integridad estructural y literal, no equivalencia de significado. La revisión asistida por modelo no es revisión humana.
- **Importación verificada en Notion.** El paquete es válido para CommonMark + GFM; la importación la hace el usuario y el render puede diferir en tablas, anclas y código.
- **Reproducibilidad exacta de la salida del modelo.** El manifiesto registra claves de procedencia; el texto puede variar entre ejecuciones.
- **Cobertura de MDX, HTML embebido, directivas o extensiones.** Son módulos opcionales y están **desactivados por defecto**: encender uno exige que el perfil declare `corpus_ref` y `justification`, con su evidencia en `modules.json`.
- **Windows.** Diseñado para funcionar, sin verificación de campo.
- **Retrotraducción como prueba.** Prioriza revisión; no demuestra equivalencia.

El detalle completo está en [`RELEASE.md`](RELEASE.md) §2 y en [`CHANGELOG.md`](CHANGELOG.md).

## Mantenimiento

| Qué cambió | Qué ejecutar |
|---|---|
| Algo falló y hay que blindarlo | `scripts/regression_gate.py --reproduce` |
| Esquema, contrato o dependencia | `scripts/check_versioning.py` |
| Manifiesto de una versión anterior | `scripts/migrate_manifest.py` |
| Versión del parser | `scripts/compare_parser.py` antes de promover |
| Modelo o prompt | `scripts/record_model_run.py` y `scripts/compare_model_runs.py` |
| Documentación | `scripts/audit_docs.py` |
| Sistema operativo nuevo | `scripts/probe_platform.py` y `scripts/check_portability.py` |
| Release | `scripts/build_release_candidate.py` y `scripts/gate_extended.py` |

Reglas que no se saltan: una migración no crea aprobaciones vigentes, un informe sin evidencia no puede decir `verified`, y un hueco externo se declara con responsable y procedimiento en vez de omitirse.

## Licencia

[MIT](LICENSE) © 2026 Martin Araya.

El corpus de `reports/` y `tests/fixtures/` contiene documentación de terceros usada como material de prueba y evidencia de corridas reales; sus licencias originales son de sus autores y no se reescriben aquí.