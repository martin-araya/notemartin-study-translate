<!-- Evidencia del gate G-PILOT (fase 030). Ejecutado el 2026-10-20. -->

# Piloto autorizado: informe de ejecución

Corrida completa del corpus piloto sobre los 9 documentos autorizados, con
traducción, ensamblado, validación, revisión y aprobación. Este archivo es la
evidencia que respalda las cuatro casillas de `### G-PILOT, fase 030`.

La corrida vive fuera del paquete de la skill, en
`/Users/martin/Desktop/projects/notemartin-pilot/`, para no empaquetar 823 KB
de documentación de terceros dentro de lo que se distribuye. Al repositorio
llegan solo los artefactos de este directorio.

## 1. Fuente

| Documento | SHA-256 (16) | Bytes | Segmentos | Traducidos | Literales |
|---|---|---|---|---|---|
| `typescriptlang/handbook/2/basic-types.md` | `5602380ce79fa687` | 20 442 | 81 | 45 | 3 |
| `typescriptlang/handbook/2/functions.md` | `461b6cd35a1e372d` | 30 782 | 173 | 102 | 5 |
| `APIs/OpenRouter/01 - Introducción, Autenticación y Formato General.md` | `ef8f4c49d1c26354` | 201 287 | 132 | 56 | 1 |
| `APIs/OpenRouter/04 - Capacidades Avanzadas Reasoning, Tool Calling.md` | `1e74cd4b9be34d61` | 464 977 | 259 | 112 | 3 |
| `mermaid/build-and-edit/write-diagram-syntax.md` | `1e57d898caaa6895` | 7 866 | 33 | 22 | 0 |
| `mermaid/guides/presentation.md` | `b8cb5af114daab0e` | 9 445 | 64 | 35 | 0 |
| `developer-mozilla/How_to/Layout_cookbook/Card.md` | `58e4cbffec89245c` | 9 217 | 25 | 0 | 5 |
| `developer-mozilla/Guides/Cascading_variables/Using_custom_properties.md` | `6192fc4ddee0b44b` | 13 057 | 52 | 0 | 7 |
| `oracle/notas/Cap_14/Cap_14_Physical_Storage_Structures.md` | `8607448205a83aec` | 66 240 | 404 | 87 | 153 |
| **Total** | | **823 313** | **1 223** | **459** | **177** |

Los nueve hashes coinciden con los declarados en `evals/cases/pilot.md`.
`literales` son segmentos ya en español que se verificaron y se devolvieron
sin reescribir (disposición `already_target`).

## 2. Perfil

`reports/pilot/profile.json`: destino `es`, dialecto `commonmark+gfm`,
conservación estricta de código, frontmatter preservado, presupuesto de
contexto 1500. Dos módulos opt-in activados con su gate verificado antes de
arrancar: `mdx.enabled` y `html.enabled`, ambos con su `contract_path`.

## 3. Glosario congelado

`reports/pilot/glossary.json`, versión 2, `frozen: true`, 31 entradas:
14 con equivalente español decidido y 17 preservadas (nombres propios, siglas
y referencias de código). Aprobado por el usuario en la tanda del 2026-10-20.

Dos términos aprobados **no** entran en el glosario: `custom property` y
`anchor`. El esquema exige un ejemplo de contexto real y ninguno de los dos
aparece en un segmento traducible del piloto. Fabricar un ejemplo sería
inventar evidencia, así que quedan como candidatos para el siguiente corpus.

## 4. Resultado de la validación

`reports/pilot/validate.json` con `structure`, `protection`, `destinations`,
`coverage` y `source-debt`: **0 errores**.

| Comprobación | Resultado |
|---|---|
| Identidad byte a byte (`assemble.py --identity`) | los 9 documentos se reconstruyen idénticos al original |
| Literales protegidos | 636 segmentos, 0 pérdidas (`flag_loss: false` en los 9 documentos) |
| Estructura | 0 desajustes de encabezados, niveles, listas, tablas y fences |
| Destinos | 0 errores; los fragmentos explícitos `<a id>` siguen resolviendo |
| Cobertura del ledger | 9/9 documentos integrados, `integrity_ok: true` |
| Recursos | 0 copiados, 0 ausentes (el piloto es solo Markdown) |

## 5. Revisión

`reports/pilot/review.json`: 636 segmentos revisados, 635 aceptados, 1
corregido. Corrección: `seg-9bd369e7` convertía «$5 per 1,000 posts» en
«5 USD por cada 1000 publicaciones» y «September 21, 2026» en «1 de
septiembre de 2026», es decir, cambiaba el separador de millares, la moneda y
un dígito de la fecha. Corregido y revalidado.

### 5.1 Lo que quedó para decisión humana

El resumen de Oracle mezcla inglés dentro de frases españolas («Cuando se
issues un `CREATE DATABASE` statement para create un CDB») en 153 segmentos.
No es un defecto de traducción: repararlo sería corregir el producto en
origen, que `AGENTS.md` prohíbe. Se devuelve el texto literal y se registra
aquí.

### 5.2 Limitación declarada de una herramienta

`scripts/detect_residual_language.py` marca 273 «advertencias» que son prosa
española corriente («tipo», «nodos, conexiones»). Su lista de palabras
vacías es demasiado corta para corpus técnico, así que su salida no sirve
como evidencia de residuo. La comprobación que sí se usó fue una búsqueda
directa de palabras funcionales inglesas fuera de código y anclas: 0 residuos
reales; las 2 coincidencias iniciales estaban dentro de bloques mermaid
protegidos. Arreglar el detector de residuos queda fuera de esta fase.

## 6. Defectos del pipeline que encontró el piloto

Seis defectos reales, los seis corregidos con prueba:

| Defecto | Gravedad | Corrección | Prueba |
|---|---|---|---|
| El código inline se confundía con componentes JSX (`Array<T>`) | major | `prepare.py` enmascara el código inline antes de buscar JSX | `tests/test_pilot_detections.py` |
| Los `[[term:…]]` del frontmatter bloqueaban la nota de Oracle | major | `prepare.py` excluye el frontmatter de la detección | `tests/test_pilot_detections.py` |
| El gate MDX exigía `flag_mdx`, que solo significa extensión `.mdx` | critical | el gate se levanta por el hallazgo, no por la extensión | `tests/test_pilot_detections.py` |
| El manifiesto dejaba de validar tras `check_integrity` y `approve_pilot` | critical | `manifest.schema.json` declara lo que las herramientas escriben | `tests/test_pilot_manifest_contract.py` |
| `byte_range` cubría el marcador `## ` y el salto de línea, y el ensamblado los borraba | critical | `prepare.py` estrecha el rango a la prosa exacta | `tests/test_segment_range_covers_text.py` |
| El glosario dejaba de validar al congelarse (`approved_at`) | major | `glossary.schema.json` declara `approved_at` | `tests/test_pilot_manifest_contract.py` |

El quinto es el más grave y solo apareció al **leer el documento ensamblado**:
el entregable perdía los encabezados aunque `validate.py` declarara la
estructura intacta. Esa comprobación sigue siendo parcial y queda anotada
como pendiente en `reports/pilot/review.json`.

## 7. Artefactos

| Ruta | SHA-256 (16) |
|---|---|
| `reports/pilot/manifest.json` | `9a16260d27b37abe` |
| `reports/pilot/glossary.json` | `12f89253251ffd93` |
| `reports/pilot/validate.json` | `56a5e58f0671cf07` |
| `reports/pilot/review.json` | `4c90bff189c1970b` |
| `reports/pilot/profile.json` | `08456dc67e84a1f8` |
| `reports/pilot/classified.json` | `8af592aeb31251a9` |
| `reports/pilot/inventory.json` | `ba7e6cbe8f558e89` |
| `reports/pilot/copy_resources.json` | `7b56e943f050510a` |

El manifiesto aprobado declara `run-0000f1a0`, `pilot_approved: true`,
`approved_by: usuario (tanda de aprobación del 2026-10-20)` y el
`provenance_baseline` con los hashes de los nueve archivos de origen.

## 8. Qué este informe NO afirma

- No afirma que la traducción sea equivalente al original: la revisión es
  asistida por agente, no una certificación humana.
- No afirma nada sobre la calidad del resumen de Oracle, cuya fuente mezcla
  idiomas por construcción.
- No afirma que el corpus completo de 4 832 archivos se pueda procesar igual:
  el piloto son 9 documentos.
- No afirma que los módulos MDX y HTML sean correctos en general: aquí solo
  se verificó que su gate está en verde y que levantan el bloqueo del piloto.
- No afirma ninguna verificación remota: nada se importó a ningún destino.