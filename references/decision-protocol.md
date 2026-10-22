<!-- version: 1.0.0 -->

# Decisiones humanas estructuradas (fase 123)

Las decisiones humanas se almacenan en el campo `decisions[]` del
`manifest.json` (extensión del esquema, fase 123). Cada decisión
asocia un autor declarado con el contenido efectivamente
revisado, medido por hashes SHA-256.

## 1. Forma de una decisión

```json
{
  "decision_id": "dec-1234abcd",
  "author": "alias",
  "role": "reviewer",
  "pair": "en -> es",
  "scope": "global",
  "reason": "Revisado en pasada sobre informe bilingüe.",
  "reviewed_hashes": ["<sha256 del segmento o archivo>"],
  "decided_at": "2026-10-20T10:00:00Z",
  "kind": "approve",
  "references": ["issue-0007"]
}
```

### Campos obligatorios

- `author`: alias declarado, **no** un nombre completo.
- `role`: `reviewer`, `lead`, `domain_expert`, `owner`.
- `pair`: origen y destino, formato `origen -> destino` o
  `origen → destino`.
- `scope`: `global` o lista de rutas relativas.
- `reason`: ≥ 10 caracteres. No se acepta una cadena vacía ni
  un placeholder.
- `reviewed_hashes`: ≥ 1 SHA-256.
- `decided_at`: ISO 8601 UTC.
- `kind`: `approve`, `reject`, `defer`.

### Restricciones adicionales

- `kind=defer` exige `references[]` no vacío.
- `scope` lista debe contener ≥ 1 ruta no vacía.
- `decision_id` se asigna al registrar y nunca se reutiliza.

## 2. Cuándo se firma

| Caso | Política |
|---|---|
| Aprobación global del corpus | `scope: global` con `reviewed_hashes` de muestra representativa (≥ 5 % o ≥ 50 segmentos, lo mayor). |
| Aprobación local de un archivo | `scope: ["path/al/archivo.md"]` con el `source_hash` o `candidate_hash` del archivo. |
| Rechazo | `kind: reject` con `reason` que indique el hallazgo. |
| Pospuesto | `kind: defer` con al menos una referencia a `issue_id` y un `scope` específico. |

## 3. Diferencia con `reviewers[]`

El campo `reviewers[]` (fase 109) registra firmantes de **par
lingüístico** que cubren el corpus entero. `decisions[]` (fase 123)
captura **decisiones individuales** sobre artefactos específicos.
Conviven:

- `reviewers[]` afecta a `evaluation_kind` y al desbloqueo del par.
- `decisions[]` afecta a la vigencia de las aprobaciones
  (`approvals[]`, fase 124).

## 4. Lo que NO hace

- No publica la decisión en un servicio externo.
- No autoriza la firma automáticamente: el `decision_id` requiere
  un `decisions` válido pero la vigencia la marca el hash.
- No convierte un rechazo en una aprobación: `rejection_source`
  sigue siendo necesario para distinguir entradas firmadas.

## 5. Relación con otras fases

| Fase | Relación |
|---|---|
| 124 | Cada `decisions[]` se vincula a un `approvals[]` con `target_hash`. |
| 130 | El gate ampliado exige al menos una decisión `kind=approve` `global`. |
| 042 | Las decisiones sustituyen hallazgos críticos mediante `references`. |
