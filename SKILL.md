---
name: notemartin-study-translate
description: Traduce documentación técnica en Markdown al español sin convertirla en resumen, notas de estudio ni contenido nuevo. Conserva significado, terminología, cobertura y estructura del corpus original y entrega una carpeta local lista para que el usuario la importe manualmente a Notion. Dispara cuando hay una fuente Markdown que traducir preservando fidelidad; no dispara para resumir, reorganizar, corregir, generar apuntes pedagógicos ni publicar por API en Notion.
---

# `notemartin-study-translate`

Esta skill traduce prosa técnica preservando fidelidad. No resume, no reorganiza, no corrige, no publica.

## §1 · Cuándo dispara

- Hay una carpeta local de archivos Markdown que el usuario quiere traducir al español.
- Cuando el usuario pide una traducción fiel y reproducible de documentación técnica.
- Cuando hay que entregar un árbol local listo para subir manualmente a Notion u otro destino.

**No dispara** para: resumir, generar apuntes, corregir el original, traducir código, hacer OCR, publicar por API ni traducir prosa libre sin destino documental.

## §2 · Lo que no hace

- No resume. Cada fase preserva la prosa completa.
- No reorganiza. El orden de secciones y la estructura documental no cambian.
- No corrige. Errores técnicos de la fuente se conservan y se declaran.
- No publica por API en Notion ni en otros servicios remotos.
- No promete inferencia local. El procesamiento sigue al proveedor del agente activo.

## §3 · Entradas requeridas

| Campo | Descripción |
|---|---|
| `source_root` | Ruta absoluta del corpus a traducir. Debe ser legible y estar inventariada antes de traducir. |
| `target_language` | Idioma destino. Por defecto `es`. |
| `source_language` | Idioma de origen declarado o detectado. Por defecto `auto`. |

Tres rutas adicionales (`work_root` y `output_root`) se derivan y deben ser distintas de `source_root` y entre sí. Esta disyunción se valida con `schemas/profile.schema.json`.

## §4 · Procedimiento

Resumen del flujo definido en `references/workflow.md`. Cada paso produce un artefacto verificable.

1. **Descubrimiento seguro.** Confirmar las tres raíces reales, permisos, sin seguir symlinks por defecto.
2. **Inventario y perfil.** Registrar hash, codificación y tipo por archivo. Definir `profile.json` según `schemas/profile.schema.json`.
3. **Preparación y piloto.** Construir segmentos con rangos verificables. Traducir un piloto representativo y obtener aprobación del usuario. Congelar `glossary.json` tras el piloto, según `schemas/glossary.schema.json`.
4. **Disposiciones.** `detect_language.py` deja `unknown`, `mixed_or_code` y `too_short` sin decidir. `resolve_dispositions.py` mide la prosa que queda tras enmascarar los literales y asigna una disposición con su motivo. Sin ese paso, esas categorías son trabajo no dispositionado.
5. **Traducción por unidades.** Procesar cada paquete con su contexto de lectura. Cada respuesta se identifica por `segment_id`. No se reconstruye el documento completo a partir de recuerdos. `receive_translations.py` valida la respuesta y la persiste: rechaza IDs ajenos, segmentos ausentes, marcadores desequilibrados y literales perdidos, y retira los marcadores `§§…§§` antes de escribir. La traducción se persiste en `translations/<clave>.json`, donde la clave es `document_id` salvo que ese identificador colisione entre rutas, en cuyo caso es `translation_id` (`scripts/translation_key.py`). Verificar con `scripts/inject_translation_ids.py` que no queda ninguna colisión antes de traducir: dos archivos byte a byte idénticos comparten `document_id` y `segment_id`, y sin desambiguar una traducción pisaría a la otra sin aviso.
6. **Ensamblado.** Aplicar parches sobre rangos autorizados. Copiar recursos preservando rutas y bytes.
7. **Estado del manifiesto.** `advance_state.py --translations <dir>` solo avanza a un estado de trabajo los documentos que tienen traducción persistida. Sin ese flag no se comprueba evidencia y la herramienta puede fabricar progreso.
8. **Revisión semántica separada.** Contrastar cada segmento contra el original siguiendo `references/semantic-review.md`, que aplica la rúbrica de `evals/rubric.md` sobre cada unidad traducible. No autocertificar la propia traducción.
9. **Gate y entrega.** Verificar el gate global con `schemas/manifest.schema.json`. `export.py` revalida antes de promover: si el corpus está incompleto, no escribe `output_root`. Solo entonces se promociona.

## §5 · Invariantes clave

| ID | Regla |
|---|---|
| INV-01 | La fuente permanece inmutable. |
| INV-03 | Un identificador de documento o de paquete nombra **una** unidad de trabajo. Si dos archivos byte a byte idénticos lo comparten, la traducción de uno se escribiría sobre la del otro. |
| INV-04 | Traducir no significa resumir, ampliar, reorganizar ni corregir. |
| INV-05 | Los literales protegidos conservan bytes exactos. |
| INV-07 | Un término mantiene su sentido, no necesariamente una traducción universal. |
| INV-12 | Una ejecución parcial nunca se presenta como completa. |

## §6 · Archivos de la skill

Rutas que existen en este árbol, ordenadas por rol:

| Ruta | Rol |
|---|---|
| `references/workflow.md` | Flujo operativo completo, paso a paso. |
| `references/markdown-contract.md` | Dialecto soportado, construcciones bloqueantes y matriz de presencia. |
| `references/semantic-review.md` | Revisión semántica por unidad: qué se revisa, en qué orden y con qué rúbrica. |
| `references/operation.md` | Confianza de entrada, privacidad, permisos y comportamiento adversarial. |
| `references/notion-handoff.md` | Qué se entrega y qué se excluye del árbol importable a Notion. |
| `references/delivery-notion-checklist.md` | Checklist de importación de muestra y evidencia que debe aportar el usuario (131). |
| `references/delivery-contract.md` | Qué puede y qué no puede hacer una adaptación local opt-in (134). |
| `references/delivery-matrix.md` | Destinos de entrega, su evidencia real y cómo activar uno nuevo (139). |
| `references/delivery-gate.md` | Las siete comprobaciones del gate de entrega (140). |
| `evals/cases/pilot.md` | Selección autorizada del corpus piloto, hashes y criterios. |
| `evals/rubric.md` | Rúbrica de fidelidad y criticidad para la revisión semántica. |
| `schemas/profile.schema.json` | Modelo del perfil: idioma, exclusiones, dialecto, anclas, entrega. |
| `schemas/glossary.schema.json` | Modelo del glosario por dominio y sentido. |
| `schemas/manifest.schema.json` | Modelo del manifiesto de ejecución con estados, procedencia y entrega. |

### Módulos opcionales, desactivados por defecto

Ninguna de estas referencias se activa sola. Encender un módulo exige que el
perfil declare `corpus_ref` y `justification`: qué corpus lo justifica y por
qué. La regla completa, el gate que la verifica y sus códigos de salida están
en `references/optional-modules.md`; el estado declarado de cada módulo, con
su evidencia, está en `modules.json`.

| Módulo | Fases | Referencias |
|---|---|---|
| MDX | 061–070 | `references/mdx-contract.md`, `references/mdx-attributes.md`, `references/mdx-review.md` |
| HTML embebido | 071–080 | `references/html-contract.md`, `references/html-attributes.md`, `references/html-compatibility.md` |
| Dialecto y extensiones | 081–090 | `references/footnotes.md`, `references/admonitions.md`, `references/definition-lists.md`, `references/directives.md`, `references/mermaid-labels.md`, `references/math.md`, `references/wikilinks.md`, `references/frontmatter.md` |
| Terminología por dominio | 091–100 | `references/domain-glossaries.md`, `references/term-profiles.md`, `references/term-sources.md` |
| Idioma y variantes | 101–110 | `references/source-language-policy-fr.md`, `references/locale-policy.md`, `references/rtl-policy.md`, `references/reviewer-policy.md`, `references/dialect-profiles.md`, `references/citations-policy.md` |
| Escala y paralelismo | 111–120 | `references/scheduler-policy.md`, `references/worker-protocol.md`, `references/reviewer-protocol.md`, `references/concurrency-policy.md`, `references/serial-fallback.md`, `references/translation-cache.md` |
| Revisión ampliada | 121–130 | `references/bilingual-report.md`, `references/findings-priority.md`, `references/decision-protocol.md`, `references/approval-freshness.md`, `references/inconsistency-report.md`, `references/residual-language.md`, `references/back-translation-eval.md`, `references/report-accessibility.md`, `references/log-redaction.md`, `references/review-gate.md` |
| Mantenimiento | 141–150 | `references/regression-corpus.md`, `references/versioning-policy.md`, `references/manifest-migration.md`, `references/parser-upgrade.md`, `references/model-variation.md`, `references/content-audit.md`, `references/portability.md`, `references/workdir-retention.md`, `references/release-gate.md` |

## §7 · Verificación al cierre

Antes de subir el árbol al destino, comprobar:

1. `manifest.json` declara todos los archivos del alcance en estado `approved` o terminal con motivo.
2. La cobertura del alcance es total o los `excluded` están aprobados.
3. Los hashes SHA-256 de los archivos en `output_root` coinciden con los del manifiesto.
4. `glossary.json` está congelado y su hash está registrado.
5. `reports/` y `glossary.json` no aparecen dentro de `output_root`.

La entrega empaquetada (`ZIP`, adaptación local y guía) es una extensión
opcional desactivada por defecto. Si se activa, se comprueba con
`scripts/gate_delivery.py`, que devuelve un código distinto por
comprobación fallida. `references/delivery-gate.md` documenta los siete
checks.

## §8 · Mantenimiento y releases

Estas herramientas no traducen. Comprueban que lo que la skill afirma siga
siendo cierto.

| Qué cambió | Qué hay que ejecutar |
|---|---|
| Algo falló y hay que blindarlo | añadir el par positivo/negativo al registro y `scripts/regression_gate.py --reproduce` |
| Esquema, contrato o dependencia | `scripts/check_versioning.py` |
| Manifiesto de una versión anterior | `scripts/migrate_manifest.py` (nunca fabrica aprobaciones vigentes) |
| Versión del parser | `scripts/compare_parser.py` antes de promover |
| Modelo o prompt | `scripts/record_model_run.py` y `scripts/compare_model_runs.py` |
| Documentación | `scripts/audit_docs.py` |
| Sistema operativo nuevo | `scripts/probe_platform.py` y `scripts/check_portability.py` |
| Workdir que ocupa demasiado | `scripts/purge_workdir.py` (seco por defecto, con autorización) |
| Release | `scripts/build_release_candidate.py` y `scripts/gate_extended.py` |

Reglas que no se saltan: una migración no crea aprobaciones vigentes, un
informe sin evidencia no puede decir `verified`, y un hueco externo se
declara con responsable y procedimiento en vez de omitirse. El detalle de
cada política está en las referencias de la tabla de módulos de arriba y en
`evals/release/RELEASE_NOTES_0.2.0.md`.