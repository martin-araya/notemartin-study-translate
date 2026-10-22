<!-- version: 1.0.0 -->

# Protocolo de revisión (separación autor/revisor, fase 115)

Esta fase separa el rol del **autor** (quien traduce) del rol del
**revisor** (quien decide aceptar o rechazar). La separación es
lógica y la ejecuta el orquestador; el modelo no debe nunca
autoevaluarse.

> La separación autor/revisor **no** exige dos modelos distintos.
> Basta con que el contexto que recibe el revisor sea distinto del
> contexto que recibió el autor. El orquestador se encarga de esa
> disyunción.

## 1. Lo que el revisor recibe

El revisor `R_i` opera sobre la siguiente bolsa:

| Campo | Descripción |
|---|---|
| `source_path` | Ruta del archivo Markdown original. |
| `source_text` | Texto íntegro del archivo sin traducir. |
| `candidate_path` | Ruta del `candidate.json` del autor. |
| `candidate_content` | Contenido propuesto por el autor, **sin** sus notas privadas. |
| `glossary.json` | Glosario congelado. |
| `anchor_map.json` | Mapa de anclas resueltas tras la traducción. |
| `rubric_path` | Ruta del archivo de rúbrica (p. ej. `evals/rubric-distributed.md`). |

El revisor **NO** recibe:

- `author_notes`: notas privadas del autor.
- `metadata.author`: identificador del autor.
- Mensajes de chat internos del autor.
- `tokens_estimated` ni `cost_estimated_usd` del autor.

Si el input del revisor contiene cualquiera de los campos
anteriores, el script `scripts/reviewer_role.py` lo rechaza con
un error de contaminación.

## 2. Lo que el revisor emite

Por cada segmento, el revisor produce una entrada JSONL con:

```json
{
  "reviewer_id": "R1",
  "segment_id": "seg-...",
  "verdict": "accept" | "reject_with_reason" | "needs_human",
  "rubric_checks": { "...": "pass | fail | warn" },
  "reason": "...",
  "reviewed_at": "ISO 8601"
}
```

La bitácora completa queda en `work_root/reviews/<reviewer_id>.jsonl`.

## 3. Anti-contaminación

- El revisor **no** abre el `state.json` del autor.
- El revisor **no** lee `translations/<packet_id>.json` del autor
  directamente; el orquestador preprocesa para eliminar campos
  privados.
- Si el script detecta `author_notes`, `tokens_estimated` u otros
  campos prohibidos en el input, aborta con código no cero.

## 4. Procedimiento recomendado

1. El orquestador prepara una copia del `candidato.json` con
   campos privados eliminados.
2. El revisor recibe la copia saneada.
3. El revisor emite sus veredictos en JSONL.
4. El orquestador reconcilia veredictos con el `manifest.json`
   mediante el coordinador (fase 114).
5. Si el veredicto es `reject_with_reason`, el orquestador
   rechaza el segmento y vuelve al autor para una nueva pasada.

## 5. Lo que esta política **NO** hace

- No exige dos instancias del modelo. La separación la aplica el
  orquestador sobre el input, no la arquitectura.
- No publica nombres de revisores en los outputs del importador
  (Notion, navegador, etc.).
- No reemplaza la rúbrica de fidelidad (`evals/rubric.md`). Esta
  política añade una capa: además del contenido, el revisor
  verifica que no hubo contaminación por información privada.
- No firma equivalencia semántica absoluta. Firma conformidad con
  la rúbrica.
