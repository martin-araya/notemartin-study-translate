<!-- version: 1.0.0 -->

# Glosarios por dominio (`notemartin-study-translate`)

Este documento indexa los glosarios JSON sintéticos que extienden
`references/terminology.md` con decisiones específicas por dominio.
Cada glosario valida contra `schemas/glossary.schema.json`.

## 1. Estado del corpus

- **Activación:** opt-in. Por defecto no se carga ningún glosario;
  cada ejecución decide qué glosarios aplicar.
- **Decisiones sintéticas:** `decided_by: example-agent`. El usuario
  puede sobrescribir editando el JSON o reemplazándolo con decisiones
  reales firmadas por un humano.

## 2. Glosarios disponibles

| Dominio | Archivo | Términos clave | Política principal |
|---|---|---|---|
| `database` | `tests/fixtures/glossaries/databases.json` | schema, instance, transaction, query, connection pool | `translate` |
| `network` | `tests/fixtures/glossaries/networks.json` | socket, endpoint, packet, protocol, port | `keep-original` para socket/endpoint; `translate` para packet/protocol/port |
| `frontend` | `tests/fixtures/glossaries/frontend.json` | render, state, binding, component, hook | `translate` salvo hook (`keep-original`) |
| `systems` | `tests/fixtures/glossaries/systems.json` | thread, lock, process, mutex, deadlock | `translate` salvo mutex (`keep-original`) |
| `ml_ai` | `tests/fixtures/glossaries/ml_ai.json` | training, inference, embedding, gradient, fine-tuning | `translate` salvo embedding (`keep-original`); `translate-with-original-on-first-mention` para fine-tuning |

## 3. Cómo añadir un término

1. Aportar la entrada al glosario JSON correspondiente (no a un
   archivo nuevo; mantener la agrupación por dominio).
2. Si la entrada contradice `terminology.md`, gana `terminology.md`
   salvo cambio explícito en el index.
3. Documentar `sense` con un solo objetivo operativo.
4. Incluir al menos un `context_examples` con `document_id` y
   `segment_id` reales (o `synthetic` si es del corpus de pruebas).
5. Incluir `justification` con la razón de la política.

## 4. Validación

`schemas/glossary.schema.json` exige:

- `version: integer ≥ 1`
- `frozen: boolean`
- `allowed_languages: array BCP-47 no vacío`
- `entries: array con ≥ 1 entrada`
- Cada entrada: `id` con formato `g-XXXX`, `source_term`,
  `sense`, `preferred.lang`, `preferred.term`,
  `preservation_policy ∈ {translate, keep-original,
  translate-with-original-on-first-mention}`, `context_examples` con
  ≥ 1 entrada, `justification`, `decided_by`, `decided_at` (ISO 8601).

Las pruebas `tests/test_glossary_*.py` validan cada archivo con
`jsonschema.validate`.

## 5. Procedimiento para añadir un dominio

1. Crear `tests/fixtures/glossaries/<domain>.json` siguiendo el
   schema.
2. Crear `tests/test_glossary_<domain>.py` con al menos 4 pruebas.
3. Actualizar la tabla de la sección 2.
4. Si el dominio requiere un cambio en el runtime (selector,
   `audit_terminology.py`), coordinarlo con las fases 026–030 ya
   implementadas.