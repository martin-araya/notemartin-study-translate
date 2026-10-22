<!-- version: 1.0.0 -->

# Política de traducción fiel

Este documento codifica las reglas que el agente debe seguir al traducir la prosa técnica de un corpus Markdown. La rúbrica de evaluación vive en `evals/rubric.md`; este archivo es la fuente operativa de instrucciones.

## 1. Propósito y ámbito

Traducir prosa técnica preservando significado, estructura y literales. Sin resumen. Sin reorganización. Sin corrección. Sin explicación pedagógica añadida. La salida es una carpeta local lista para que el usuario la importe a Notion.

## 2. Reglas inviolables

1. La prosa visible se traduce completa. No se omiten pasos numerados, viñetas cerradas, ejemplos, advertencias ni notas al pie.
2. Los literales protegidos — código inline, bloques fenced, bloques indentados, destinos de enlace, destinos de imagen, anclas `<a id="…"></a>`, fórmulas LaTeX — no se alteran. Se conservan tal cual entre los marcadores `§§…§§`.
3. La fuerza normativa se preserva. `MUST NOT` no se convierte en `SHOULD`. `MUST` no se convierte en `puede`. `MAY` no se convierte en `debe`.
4. La negación se preserva. `not`, `never`, `without`, `don't` y sus equivalentes en español (`no`, `nunca`, `sin`) mantienen el alcance original. Invertir una negación es un fallo crítico.
5. Las condiciones y excepciones se preservan. `if/unless/when/provided that/as long as` y sus equivalentes (`si/a menos que/cuando/siempre que/con tal de que`) conservan el orden lógico del original.
6. Los cuantificadores totales se preservan. `all/every/none` se traducen como `todos/cada/ninguno`. Convertir `all` en `some` o en `none` es un fallo crítico.
7. Las unidades, intervalos y rangos numéricos no se modifican. `>=2.1`, `<3`, `1.x`, `500–1000 ms` se mantienen literalmente.
8. No se añaden explicaciones, analogías, ejemplos propios ni glosas. La fuente no contiene "es decir" a menos que ya lo contenga.
9. No se reescribe el orden de los pasos. La numeración y el orden léxico se conservan.
10. No se sustituye un identificador por otro equivalente. `commit()`, `message`, `TypeError` permanecen textuales.

## 3. Casos de prueba

Tres categorías de fallo que la rúbrica rechaza explícitamente.

### 3.1 Resumen

- **Original.** "Configure the cache, build the artifacts, deploy to staging, and verify the response."
- **Inaceptable.** "Configure el cache, despliegue al staging y verifique la respuesta." (Se omiten "build the artifacts" y la numeración se aplana.)
- **Razón.** La dimensión `omisiones` de `evals/rubric.md` califica esto como hallazgo crítico. Se perdió un paso numerado de una enumeración cerrada.

### 3.2 Explicación añadida

- **Original.** "The cache is invalidated when the token expires."
- **Inaceptable.** "La caché se invalida cuando el token expira, es decir, deja de ser válido para nuevas solicitudes." (Se añade la glosa "es decir, deja de ser válido para nuevas solicitudes".)
- **Razón.** La dimensión `omisiones` y la regla 8 de este documento prohíben añadir contenido. La fuente no contiene esa glosa.

### 3.3 Cambio de obligatoriedad

- **Original.** "You MUST call `commit()` before exiting."
- **Inaceptable.** "Puede llamar a `commit()` antes de salir."
- **Razón.** La dimensión `modalidad` de `evals/rubric.md` clasifica esto como hallazgo crítico. `MUST` se convierte en `puede`, lo cual invierte la fuerza normativa.

## 4. Procedimiento por paquete

1. Leer `translatable_text_with_markers` del paquete.
2. Identificar las regiones entre `§§…§§`. Su contenido no se traduce.
3. Traducir el resto conservando negación, modalidad, condiciones, cuantificadores y unidades.
4. Mantener el orden original de las oraciones.
5. No añadir explicaciones, analogías ni glosas.
6. Devolver `translated_text` sin los marcadores `§§…§§`.

Si una duda sobre la fuerza normativa o la condición no se resuelve con el contexto del paquete, registrar el segmento como `uncertain` y continuar con los demás. La resolución la toma el revisor en la fase 029.

## 5. Limitaciones

Esta política no garantiza paridad semántica absoluta. La revisión contra la fuente (fase 029) emite hallazgos con severidad explícita y los eleva al gate global. La aprobación final del piloto la realiza el usuario, no la automatización.