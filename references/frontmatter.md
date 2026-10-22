<!-- version: 1.0.0 -->

# Frontmatter traducible (fase 088)

El frontmatter YAML de la cabecera es, por defecto, **literal**. La política
del núcleo es `preserve`: ni las claves ni los valores se tocan. La fase 088
añade una capacidad opt-in, no un comportamiento por defecto.

## 1. Estado del módulo

- **Activación:** `frontmatter_policy: translate-allowlist` en el perfil.
  Con `preserve`, este módulo no hace nada.
- **Activación con corpus:** desde `profile.schema.json` 1.1.0,
  `translate-allowlist` exige además `frontmatter_allowed_fields`
  no vacío, `frontmatter_corpus_ref` y `frontmatter_justification`. Sin
  corpus declarado no hay traducción de frontmatter (criterio 1 de G-EXT).
- **Corpus que lo justifica hoy:** ninguno. Los dos corpus autorizados
  tienen frontmatter, pero la política activa es `preserve`
  (`reports/pilot/profile.json`). `evals/cases/markdown-extensions.md` §3
  lo declara.

## 2. Qué se traduce

Solo los campos cuyo nombre está en `frontmatter_allowed_fields`:

| Tipo de campo | Qué ocurre |
|---|---|
| Texto plano (`title: Un título`) | Se emite un segmento traducible |
| Lista (`tags: [uno, dos]`) | **No se traduce.** El extractor solo reconoce `clave: valor` en una línea; una lista o un bloque queda literal |
| Fecha (`date: 2026-10-20`) | Solo si su nombre está en la lista de campos permitidos |
| Valor con referencia (`slug: /ruta/real`) | **No se traduce.** La clave es funcional; traducirla rompe la URL |

La regla de seguridad es simple: un campo permitido se traduce, y cualquier
otro se preserva y se reporta como `literal_frontmatter_field`. El informe
enumera los campos preservados para que la decisión sea visible, no
necesariamente incorrecta.

## 3. Lo que nunca se traduce

- La **clave** del campo, aunque esté permitida. Las claves son
  identificadores funcionales del documento.
- El delimitador `---`, los saltos de línea y la indentación.
- Un valor que sea una ruta, un identificador o un literal técnico.

## 4. Política de fallo

| Código de salida de la herramienta | Significado |
|---|---|
| 0 | se emitieron los segmentos permitidos; el resto quedó literal |
| 2 | faltan `frontmatter_allowed_fields`, `frontmatter_corpus_ref` o `frontmatter_justification` con `translate-allowlist` |

El rechazo ocurre en la validación del perfil (`profile.schema.json`
1.1.0), antes de leer un solo documento. Un frontmatter mal formado no se
repara: se preserva literal y el archivo sigue su curso, con el hallazgo
registrado. Repararlo en silencio violaría INV-03.

## 5. Evidencia

- Caso positivo: `tests/test_frontmatter_translate.py`.
- Combinaciones con otras extensiones: `tests/test_extension_combinations.py`.
- Corpus: `tests/fixtures/frontmatter/with_translatable.md` (sintético, 234 B).