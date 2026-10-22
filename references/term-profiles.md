<!-- version: 1.1.0 -->

# Perfiles terminológicos reutilizables (`notemartin-study-translate`)

Este documento indexa los **perfiles terminológicos** que activan
glosarios por dominio. Cada perfil se aprueba por una persona
(`approver`), declara el corpus que lo justifica y conserva excepciones
auditables. El contrato ejecutable es
`schemas/term_profile.schema.json`; la comprobación es
`term_profiles.validate_profile()` y `term_profiles.validate_against_schema()`.

## 1. Estado del módulo

- **Activación:** opt-in y **dormiente por defecto**. Ningún perfil está
  activo.
- **Un perfil sin corpus no activa nada.** `corpus_ref` y `justification`
  son obligatorios: sin ellos el perfil es de laboratorio y así se declara
  con `corpus_real: false`.
- **Decisión humana obligatoria:** cada perfil declara `approver` y
  `approved_at`. Sin ellos, el perfil no se puede activar.
- **Sin auto-aprobación.** La skill no aprueba perfiles por sí sola, y un
  perfil que declare `corpus_real: true` no puede llevar un aprobador de
  laboratorio.

## 2. Perfiles iniciales

Los cuatro son **perfiles de laboratorio**: se escribieron para las pruebas y
llevan `corpus_real: false`. No se han derivado de ningún corpus real.

| profile_id | versión | enabled_domains | approver | corpus_real | notas |
|---|---|---|---|---|---|
| `database-only` | `1.0.0` | `database` | example-agent | false | Solo bases de datos. Útil para documentación técnica SQL. |
| `web-stack` | `1.0.0` | `frontend`, `network` | example-agent | false | Documentación web: front-end y redes. |
| `ml-pipeline` | `1.0.0` | `ml_ai`, `systems` | example-agent | false | Sistemas con ML/IA. |
| `mixed-default` | `1.0.0` | `database`, `frontend`, `ml_ai`, `network`, `systems` | example-agent | false | Perfil amplio; útil para corpus mixtos. |

El corpus que hoy justificaría un perfil real está medido en
`evals/cases/terminology.md` §1: los cinco dominios existen como fixtures,
pero ningún `glossary.json` real los activa.

## 3. Excepciones auditables

Si un perfil necesita un equivalente distinto al del glosario por
dominio, la excepción se registra como entrada adicional en el
glosario con `sense` específico y `justification` que apunte al
perfil. Las excepciones viven en el propio perfil, bajo `exceptions[]`
(`source_term`, `reason`, `domain`), y se validan contra el esquema.

Anotación de una versión anterior: este documento decía que las
excepciones se registraban en `manifest.json` bajo `term_exceptions`. Ese
campo **no existe** en `schemas/manifest.schema.json`, que lo rechazaba. La
excepción vive ahora donde el esquema la acepta, no en un documento que la
prohibía.

## 4. Procedimiento para añadir un perfil

1. Definir `profile_id`, `version`, `enabled_domains`.
2. Declarar `corpus_ref` (un caso de `evals/cases/`) y `justification`:
   por qué ese corpus activa esos dominios.
3. Asignar `approver` y `approved_at` de una persona. La skill no aprueba
   perfiles.
4. Declarar `corpus_real`. Si es `true`, el aprobador no puede ser de
   laboratorio.
5. Si hay excepciones, declararlas en `exceptions[]`.
6. Actualizar la tabla de la sección 2.
7. Añadir prueba positiva en `tests/test_term_profiles.py` y ejecutar
   `scripts/gate_optional.py`, que exige que cada módulo con activación
   declarada tenga su `corpus_ref` y su justificación.

## 5. Lo que NO se hace

- La skill no activa un perfil sin `approver`, `approved_at`, `corpus_ref` y
  `justification`.
- La skill no combina perfiles sin declarar el perfil sobre la
  combinación.
- La skill no sobrescribe equivalentes fuera del dominio del perfil
  activo.
- La skill no inventa un dominio: `enabled_domains` es un enumerado cerrado
  en el esquema.