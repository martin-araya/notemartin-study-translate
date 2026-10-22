# Procedencia del corpus permanente de regresión (fase 141)

Este archivo declara el origen, la autorización y la anonimización de cada
caso del registro `evals/regression/registry.json`. El gate
`scripts/regression_gate.py` lo considera obligatorio: una entrada sin
`source`, `license_note`, `anonymized: true` y justificación (cuando el
material es un extracto) falla con el código de salida 6.

## Decisión aplicada

La decisión tomada al planificar esta fase es **sintético por defecto**:
un caso de regresión se escribe, no se copia. Solo entraría material real si
la construcción fuera irreproducible de otra forma, y entonces la entrada
declararía `kind: fixture_excerpt` junto con la justificación concreta.

**Resultado real: las 22 entradas son `kind: synthetic`.** Ninguna prosa de
terceros se añadió al registro permanente durante esta fase.

## Qué significa «sintético» aquí

Cada fixture `tests/fixtures/regression/<fallo>.json` contiene:

- `case`: las entradas compartidas por ambos lados (el documento fuente, el
  manifiesto, el conjunto de segmentos, las claves de caché, etc.).
- `positive`: la variante **sin** defecto. El detector no debe marcarla.
- `negative`: la variante **con** el defecto. El detector debe marcarla.

Los textos están escritos para el caso: no reproducen el corpus autorizado
de `tests/fixtures/pilot/` ni el corpus grande del usuario, no contienen
nombres de personas, ni rutas del sistema de archivos de la máquina, ni
identificadores de producto reales.

## Material de terceros ya presente en el repositorio

El repositorio **sí** contiene material de terceros en:

| Ruta | Origen | Uso |
|---|---|---|
| `tests/fixtures/pilot/` | TypeScript, OpenRouter, Mermaid, MDN, apuntes Oracle | corpus piloto autorizado por el usuario en la fase 002 |
| `tests/fixtures/scale/` | muestreo de 30 archivos del corpus del usuario | muestreador de CI de la fase 111 |
| `tests/fixtures/pilot-fr/` | corpus derivado CC0 | evaluación del par fr→es |

Ese material **no forma parte del registro de regresión** y no se modifica
con esta fase. Su autorización y sus exclusiones siguen documentadas en
`evals/cases/pilot.md` y `evals/cases/corpus-full.md`.

## Cómo añadir un caso nuevo

1. Escribir el fixture en `tests/fixtures/regression/<fallo>.json` con las
   claves `case`, `positive` y `negative`.
2. Añadir el detector en `scripts/regression_detectors.py`, o delegar en un
   script existente declarándolo en `detector.delegates_to`.
3. Añadir la entrada al registro con su `provenance` completa.
4. Declarar los dos nodeids en `tests/test_regression_cases.py`.
5. Ejecutar `python3 scripts/regression_gate.py --reproduce --out
   reports/maintenance/regression.json`.

Si el fallo es nuevo y no entra todavía en `known_failures`, el gate lo
señala como hueco (código 7) en cuanto se declara sin entrada. Un fallo
conocido sin par completo es un hueco: no se puede cerrar la fase 141.