<!-- version: 1.0.0 -->

# Revisión semántica

La revisión semántica es el último pase antes de la aprobación. No es una verificación automática: el revisor humano aplica la rúbrica de `evals/rubric.md` sobre cada unidad traducible. El objetivo es detectar cambios de significado que las verificaciones deterministas no capturan.

## 1. Propósito y ámbito

La rúbrica de `evals/rubric.md` define diez dimensiones y tres niveles de fallo. Este documento formaliza **cómo** revisar cada unidad. Las verificaciones deterministas (fase 041) cubren estructura, protecciones, destinos, cobertura y deuda de origen. La revisión semántica cubre el contenido traducible.

## 2. Unidades a revisar

La revisión aplica a las siguientes unidades, en este orden:

1. **Encabezados**: cada `heading` con su `heading_path`. La jerarquía debe preservarse.
2. **Celdas de tabla**: cada celda se revisa individualmente. La alineación no se revisa semánticamente, pero la separación entre celdas debe respetarse.
3. **Ítems de lista**: ordenadas o no, anidadas o planas. La jerarquía y el orden textual deben preservarse.
4. **Citas en bloque**: el texto de la cita, los marcadores `>` y los párrafos internos.
5. **Párrafos**: el grueso del texto traducible.
6. **Descripciones alternativas de imágenes**: se revisan como texto traducible; el destino de la imagen se conserva.
7. **Anclas explícitas**: el texto del heading que las precede y el identificador `<a id="…">` (este último no se traduce).

No se revisan los literales protegidos: el validador determinista de la fase 041 los cuenta byte a byte.

## 3. Procedimiento

Por cada unidad:

1. Localizar el segmento en `translations/<doc_id>.json` por `segment_id`.
2. Leer `entry.original_text` y `entry.translated_text`.
3. Aplicar las diez dimensiones de `evals/rubric.md` en este orden:
   - negación
   - modalidad
   - condiciones
   - omisiones
   - causalidad
   - cuantificadores
   - sujetos
   - versiones
   - referencias
   - numeración cerrada
4. Para cada hallazgo, registrar:
   - `dimension`
   - `severity` (`critical` o `major`)
   - `evidence` (original y candidato, con `byte_range` o `segment_id`)
   - `resolution` propuesta
5. Si el hallazgo es `critical`, el archivo no se aprueba. Si es `major`, se corrige antes de la exportación.

## 4. Severidad

La rúbrica define dos niveles:

- **Crítico**: cambia el significado obligatorio, invierte una negación, convierte una obligación en recomendación, omite un elemento numerado, rompe un rango cuantitativo o modifica una URL externa. Bloquea la aprobación.
- **Mayor**: cambia fuerza normativa sin invertir obligación, suaviza una condición, pierde un cuantificador total, equivoca causalidad simple. Se corrige antes de la exportación.

Los hallazgos `menores` no se registran: saturan la revisión sin ayudar al gate. La rúbrica explícita `umbral mínimo de gravedad` los descarta.

## 5. Limitaciones

La auditoría semántica no es exhaustiva sin muestreo humano. Las severidades se documentan como hallazgos; el revisor decide. La revisión no reemplaza la corrección automática; produce un reporte que la fase 043 consume. La auditoría tampoco intenta resolver tareas de código-fuentes: ante un bloque de código con contenido semántico, el revisor decide si el bloque es literal o traducible, y registra la decisión en `reports/issues.json` para que el usuario decida.

## 6. Relación con otras fases

| Fase | Relación |
|---|---|
| 041 | Aporta verificaciones deterministas. Las unidades que pasan se revisan semánticamente; las que fallan se corrigen antes de la revisión. |
| 043 | Consume los hallazgos críticos y aplica correcciones explícitas. Cada corrección invalida la revisión actual. |
| 044 | Recibe las decisiones que la revisión no puede tomar por sí sola: ambigüedades, dudas sobre contenido técnico, omisiones intencionales. |
| 045 | Verifica que las decisiones de la revisión se aplican de forma consistente entre documentos. |