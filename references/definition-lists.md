<!-- version: 1.0.0 -->

# Contrato de Definition Lists (`notemartin-study-translate`)

Este contrato cubre listas de definiciones Markdown (sintaxis
Pandoc/Markdown extra):

```
Término
:   Definición del término.
```

## 1. Estado del módulo

- **Activación:** opt-in por perfil (`profile.definition_lists.enabled`).
- Por defecto **desactivado**: `prepare.py` no las procesa como
  contenido.
- **Corpus de referencia:** `tests/fixtures/definitions/`.

## 2. Reglas

1. El **término** es la línea que precede al `:`. Es traducible.
2. La **definición** es el texto que sigue al `:` (con dos o más
   espacios de indentación o un `:` al inicio de la línea). Es
   traducible.
3. Cada término tiene al menos una definición; un término con
   varias definiciones se considera multilínea.
4. La correspondencia término↔definición se preserva por posición.

## 3. Lo que NO se hace

- No se reordenan los pares.
- No se normaliza la indentación del `:`.
- No se traducen los marcadores (`:`) ni la estructura.

## 4. Procedimiento para añadir al corpus

1. Aportar al menos un archivo en `tests/fixtures/definitions/`.
2. Si el formato excede este contrato, dividir el bloque en
   párrafos o listas normales.
3. Actualizar `manifest.json` con `policy_decisions` si cambia la
   política.