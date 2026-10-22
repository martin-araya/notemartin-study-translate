# Paquete de revisión {%packet_id%}

## Documento

- `document_id`: {%document_id%}
- `path`: {%path%}

## Segmentos revisados

{%segments_review%}

## Hallazgos

{%findings%}

## Resolución

{%resolution_summary%}

## Criterio de revisión

Aplica la rúbrica de `evals/rubric.md` sobre cada segmento: negación, modalidad, condiciones, omisiones, causalidad, cuantificadores, sujetos, versiones, referencias y numeración cerrada. Severidades:

- **Crítico**: bloquea la aprobación del archivo.
- **Mayor**: se corrige antes de la exportación.

Cada hallazgo registra archivo, `segment_id` o rango, dimensión, severidad, evidencia (original y candidato) y resolución propuesta.