# Rúbrica distribuida (separación autor/revisor, fase 115)

Esta rúbrica complementa `evals/rubric.md` para el modo distribuido.
El revisor contrasta cada candidato del autor con la fuente usando
los criterios de esta rúbrica **y** los del modo base. La diferencia
es que aquí se evalúa, además, que el input del revisor no haya sido
contaminado por información del autor.

## 1. Criterios base (heredados)

Estos son los criterios ya definidos en `evals/rubric.md`:

- Fidelidad semántica: negación, modalidad, causalidad.
- Cobertura: sin omisiones, sin resúmenes.
- Literales preservados: código, URLs, identificadores.
- Anclas internas correctamente reescritas.
- Tablas y listas: celdas, alineación, orden.

## 2. Criterios distribuidos (nuevos)

| Criterio | severidad | descripción |
|---|---|---|
| Contaminación por `author_notes` | error | El input del revisor contiene el campo `author_notes`. El orquestador debe sanear antes de pasar al revisor. |
| Contaminación por `tokens_estimated` | error | El input contiene costos/tokens del autor, que no son visibles al revisor. |
| Contaminación por `metadata.author` | error | El input identifica al autor. |
| Identidad del revisor declarada | info | Cada veredicto lleva `reviewer_id` y `reviewed_at` para auditoría. |
| Bitácora por línea | error | Cada segmento del lote produce una línea JSONL, sin agrupamientos. |
| Veredicto cerrado | error | El campo `verdict` ∈ {`accept`, `reject_with_reason`, `needs_human`}. Cualquier otro valor aborta la revisión. |
| Aislamiento del estado del autor | warn | El revisor no abrió `state.json` del autor; si lo abrió, se documenta en `bitácora`. |

## 3. Severidades

- `error`: bloquea el lote; el segmento se rechaza.
- `warn`: se registra en `bitácora`; el segmento puede aceptarse.
- `info`: solo anotación.

## 4. Plantilla de veredicto

```json
{
  "reviewer_id": "R1",
  "segment_id": "seg-deadbeef",
  "verdict": "accept",
  "rubric_checks": {
    "fidelidad": "pass",
    "cobertura": "pass",
    "literales": "pass",
    "anclas": "pass",
    "sin_contaminacion_autor": "pass"
  },
  "reason": "Segmento conforme con la rúbrica base y sin contaminación.",
  "reviewed_at": "2026-10-20T14:30:00Z"
}
```

Si `verdict == "reject_with_reason"`, el campo `reason` es
obligatorio y debe contener una observación de, al menos, 20
caracteres referidos al fallo.

## 5. Procedimiento de cierre

1. Todos los segmentos reciben un veredicto.
2. Si algún veredicto es `needs_human`, el lote queda en
   `awaiting_human_review`; el orquestador pausa.
3. Si todos los veredictos son `accept` o `reject_with_reason`,
   el orquestador cierra el segmento y aplica la transición
   correspondiente en el manifiesto.
