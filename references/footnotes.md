<!-- version: 1.1.0 -->

# Contrato de la extensión Footnotes (`notemartin-study-translate`)

Este contrato delimita cómo se traducen las notas al pie Markdown.
**No es una promesa de soporte universal**: solo el patrón
`[^id]` y la definición `[^id]: texto` descritos aquí entran en el
flujo de traducción. Cualquier variante fuera de este contrato se
preserva literal.

## 1. Estado del módulo

- **Activación:** sin interruptor propio. El núcleo trata las footnotes
  como parte del dialecto y las preserva enteras.
- **Contradicción declarada:** `references/dialect-profiles.md` y
  `scripts/dialect_matrix.py` listan `footnotes` entre lo que el perfil
  `commonmark-basic` **no** soporta. Las dos cosas son ciertas a la vez:
  el perfil no las soporta, y el flujo nuclear las preserva sin traducir.
  Lo que este módulo **no** hace es traducirlas. Traducirlas exige activar
  la extensión correspondiente del dialecto, que hoy no existe como
  capacidad: hay que quitar su etiqueta de "siempre activa" y darla por
  no implementada, o implementarla.
- **Corpus de referencia:** `tests/fixtures/footnotes/`. Es un
  corpus sintético, y el corpus piloto y el Beta no contienen ninguna
  footnote (`evals/cases/markdown-extensions.md` §1).

## 2. Reglas

1. El **identificador** `id` en `[^id]` y `[^id]: ...` es **literal**.
   No se traduce ni se transforma.
2. La **referencia** `[^id]` en el cuerpo del documento es literal.
   No se traduce.
3. El **texto de la definición** que sigue a `[^id]: ` es
   **traducible**. Emite un segmento con `parent: footnote_id`.
4. La asociación referencia↔definición se preserva: tras traducir
   el texto, el `id` y la referencia `[^id]` no cambian.

## 3. Lo que NO se hace

- No se numeran automáticamente las notas.
- No se reordenan las definiciones por idioma.
- No se traducen los identificadores ni las referencias.

## 4. Activación y desactivación

No hay bandera que apagar: las footnotes se preservan enteras porque el
núcleo no las traduce. Un corpus sin footnotes no emite segmentos y no
diferencia nada. La prueba `tests/test_optional_deactivation.py`
comprueba que encender o apagar los módulos opcionales deja estos
artefactos byte a byte idénticos.