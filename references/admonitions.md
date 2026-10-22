<!-- version: 1.0.0 -->

# Contrato de la extensión Admonitions (`notemartin-study-translate`)

Este contrato cubre los bloques de admonición tipo
`:::tipo ... :::` que aparecen en Docusaurus, Material for MkDocs
y otras variantes Markdown.

## 1. Estado del módulo

- **Activación:** opt-in por perfil (`profile.admonitions.enabled`).
- Por defecto **desactivado**: `prepare.py` sigue marcando
  `directive_admonition` como bloqueante (comportamiento histórico).
- **Corpus de referencia:** `tests/fixtures/admonitions/`.

## 2. Tipos soportados

| Tipo | Uso | Severidad |
|---|---|---|
| `note` | Información neutral | baja |
| `tip` | Sugerencia | baja |
| `info` | Información adicional | baja |
| `warning` | Advertencia | alta |
| `caution` | Riesgo de pérdida | alta |

Cualquier otro tipo (`danger`, `custom`, etc.) se reporta como
`unsupported_admonition` con severidad `critical` y bloquea el archivo.

## 3. Reglas

1. El **tipo** (`warning`, `note`, etc.) es **literal**. No se
   traduce. Las advertencias no se rebajan a notas.
2. El **contenido** entre `:::tipo` y `:::` es **traducible**.
   Emite segmentos con `parent: admonition_type`.
3. Las líneas vacías dentro del bloque se mantienen.
4. La indentación se respeta: `:::note` debe cerrarse con `:::`
   al inicio de la línea.

## 4. Validación

El validador emite issue `severity: major, category:
clarification_needed` si una traducción cambia `warning` por `note`,
`caution` o cualquier tipo de menor severidad. Esto preserva la
fuerza normativa de la advertencia.