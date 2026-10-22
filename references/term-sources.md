<!-- version: 1.0.0 -->

# Fuentes oficiales autorizadas de terminología (`notemartin-study-translate`)

Este documento registra las **fuentes externas** de las que la skill
puede importar terminología oficial. **No sustituye** la
documentación que se traduce: la terminología importada se
referencia con `provenance` en cada entrada del glosario y se
mantiene intacta durante la traducción.

## 1. Estado del corpus

- **Activación:** opt-in. Por defecto no se importa ninguna fuente
  externa.
- **Uso:** `scripts/term_provenance.py` añade `provenance` a cada
  entrada sin modificar `source_term`, `sense` ni `preferred`.

## 3. Fuentes declaradas

| source | source_version | url | notas |
|---|---|---|---|
| `rfc-example` | `2026-10-20` | `https://www.rfc-editor.org/` | Marcador de posición. Las IETF RFC son la fuente oficial para terminología de red. |
| `mdn-example` | `2026-10-20` | `https://developer.mozilla.org/` | Marcador de posición. MDN Web Docs es la fuente oficial para terminología web. |
| `internal-example` | `2026-10-20` | `internal://terminology/v1` | Marcador para glosarios internos del equipo. |

## 4. Procedimiento para añadir una fuente

1. Documentar la fuente en la tabla anterior (nombre, versión, URL).
2. Importar el glosario siguiendo `glossary.schema.json`.
3. Aplicar `attach_provenance(glossary, source, source_version)`.
4. Verificar que el JSON resultante valida contra el schema.
5. Registrar la fecha de importación en `provenance.fetched_at`.

## 5. Lo que NO se hace

- La skill no descarga automáticamente la fuente.
- La skill no sustituye entradas existentes.
- La skill no fusiona decisiones con la documentación que se
  traduce.