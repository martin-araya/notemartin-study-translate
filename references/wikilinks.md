<!-- version: 1.1.0 -->

# Contrato de Wikilinks (`notemartin-study-translate`)

Este contrato cubre los wikilinks estilo Obsidian:

- `[[Target]]` — enlace simple.
- `[[Target|Alias]]` — enlace con alias visible.
- `[[Target#Section]]` — enlace con sección.
- `[[Target#Section|Alias]]` — enlace completo.

## 1. Estado del módulo

- **Activación:** opt-in por perfil (`profile.wikilinks.enabled`).
- Por defecto **desactivado** y los wikilinks se marcan como
  bloqueantes: el hallazgo `wikilink` lo emite `scripts/prepare.py`
  (`detect_findings`) y lo eleva a `verdict: blocked` en `classify_file`.
- **Encenderlo exige corpus declarado** (`wikilinks.corpus_ref` y
  `wikilinks.justification`) desde `profile.schema.json` 1.1.0.
- **Corpus de referencia:** `tests/fixtures/wikilinks/` (sintético). Los
  `[[…]]` que sí aparecen en el corpus Beta están dentro de bloques de
  código y no son wikilinks (`evals/cases/markdown-extensions.md` §1).

## 2. Reglas

1. El **target** (`Target`, `Target#Section`) es **literal**. No se
   traduce. El target determina la resolución del enlace.
2. El **alias** (la parte tras `|`) es **traducible** y emite un
   segmento con `parent: wikilink_target`.
3. El alias no puede contener `|`. Solo se admite un único alias.
4. Los wikilinks con secciones se manejan como un solo enlace
   resuelto contra la sección.

## 3. Lo que NO se hace

- No se resuelven los targets a archivos del corpus.
- No se cambia la sección del target.
- No se cambian los separadores `[[`, `]]`, `|`, `#`.

## 4. Activación y desactivación

Con `profile.wikilinks.enabled: false` (default), el comportamiento
es el histórico: `prepare.py` marca `wikilink` como bloqueante. Con
`profile.wikilinks.enabled: true`, los wikilinks pasan a formar
parte del flujo traducible.