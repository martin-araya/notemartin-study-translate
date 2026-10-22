<!-- version: 1.0.0 -->

# Alcance de esta skill — qué entra y qué no

> Documento de referencia cruzado con `AGENTS.md §1`. Si una petición futura
> pide algo que **no** es la traducción de Markdown a español con destino
> a otra carpeta validada, este archivo dice explícitamente qué hacer.

## En alcance (sí)

- Traducir la prosa visible de la documentación Markdown al español.
- Clasificar, segmentar y proteger literales; preservar su `§§LITERAL§§`.
- Validar estructura, destinos y cobertura del alcance.
- Mantener `glossary.json` congelado por ejecución, con decisiones
  justificadas.
- Operar con glosario v3, manifiesto v3 (`translate/v1`) y `pipeline` T1..T8
  descrito en el roadmap (fases 001-150).
- Producir `output/run-id/` y su catálogo `output_hashes.json` cuando
  el gate cierre en verde.
- Las rondas multi-sesión del gate G-BETA documentadas en
  `reports/beta*/summary.md` cada vez que un run cierra.

## Fuera de alcance (no)

Cada uno de los siguientes ítems es un sistema o artefacto que se ha
mencionado en sesiones y se confirma fuera de esta skill:

- **Motor de export/import/publicación de 14 fases (`B4`)** —
  cualquier motor que mueva contenido a Notion o al catálogo Hermes
  pertenece a un proyecto aparte. Esta skill **no publica**,
  **no importa** y **no instala**. Confirmado en sesión del
  2026-10-21. AGENTS.md §1 lo dice de forma general; este
  documento lo dice con nombre propio. Si se reabre, se reabre
  como proyecto separado con su propio `AGENTS.md`.
- **Editor de HTML con encoder/decoder propio (`F19.2.8`)** — no
  existe aquí. La skill trata HTML solo como fuente de prosa,
  no lo crea ni lo transforma.
- **Sistemas de inferencia RAG / embeddings / LLM adicionales** —
  el alcance aprobado usa un proveedor de inferencia ya integrado;
  añadir otro requiere una solicitud posterior explícita.
- **Servidor, base de datos externa, framework de publicación,
  colección de Hermes o cambios de perfil** — fuera de alcance, sin
  cambios automáticos al catálogo.
- **Modificación del scraper o de `notemartin-study-notes`** —
  ajenos, no se tocan desde aquí.
- **Trabajos que requieren material fuente que no existe en este
  repositorio** — ante la ausencia de archivos referenciados
  (p. ej. un `plans/B.md`, un `F19.2.8`, un `OUT/22-preguntas-abiertas.md`),
  no se fabrican. Se pregunta o se documenta el alcance como
  externo, según AGENTS.md §4 («Las referencias detallan el procedimiento,
  no autorizan romper los contratos. Resolver contradicciones antes de
  modificar datos, sin inventar aprobaciones»).

## Procedimiento cuando aparece una petición fuera de alcance

1. Identificar el material externo referenciado (p. ej. «F19.2.8»,
   «plans/B.md», «OUT/22-preguntas-abiertas.md»).
2. Buscarlo en este repositorio. Si no aparece, listar lo encontrado
   y lo no encontrado, como en la sesión 2026-10-21.
3. Pedir la ruta explícita o el contenido a quien plantea la
   petición.
4. Si el contenido es material ajeno a este proyecto, no se incluye
   ni se fabrica; se ofrece como punto de partida un proyecto aparte.
5. Si la persona usuaria quiere empezar de cero en este repositorio,
   el archivo creado lleva cabecera explícita `DRAFT — pending real
   source material; do not reference as ground truth` y se anota su
   estado en este mismo `scope.md`.

## Cambios en este archivo

| Fecha | Cambio |
|---|---|
| 2026-10-21 | Creado durante la sesión que cerró G-BETA con varias rondas multi-sesión. Documenta el cierre del caso «motor `B4`» como externo a la skill. |