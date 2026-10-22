<!-- version: 1.0.0 -->

# Control de vigencia de aprobaciones (fase 124)

Una aprobación no sobrevive a una edición del artefacto aprobado.
Este documento fija **qué** invalida una aprobación y **cómo**
reactuar.

## 1. Forma de una aprobación

```json
{
  "approval_id": "app-1234abcd",
  "decision_id": "dec-1234abcd",
  "target_hash": "<sha256 del archivo traducido>",
  "target_glossary_hash": "<sha256 del glossary activo>",
  "target_anchor_hash": "<sha256 del anchors.json>",
  "target_profile_hash": "<sha256 del profile.json>",
  "approved_at": "2026-10-20T10:00:00Z",
  "artifact": "docs/install.md"
}
```

- `target_hash` siempre obligatorio.
- `target_glossary_hash`, `target_anchor_hash`, `target_profile_hash`
  son opt-in. Si están presentes, el script compara y marca `stale`
  ante cualquier cambio. Si no están presentes, ese eje no invalida.
- `artifact` describe la ruta o nombre lógico sobre el que aplica.

## 2. Estados posibles

| Estado | Causa |
|---|---|
| `valid` | Todos los hashes declarados coinciden con los actuales. |
| `stale` | Al menos un hash declarado difiere del actual. |
| `superseded` | Otra aprobación más reciente ocupa el mismo `artifact`. |

Sólo `valid` cuenta como aprobación vigente en el gate (fase 130).

## 3. Cálculo de hashes actuales

El script `check_approval_freshness.py` lee:

- `manifest.files[].source_hash` para cada artefacto.
- `manifest.glossary_snapshot.hash` (o `manifest.current_glossary_hash`
  si se ha emitido un override fuera del snapshot).
- `manifest.profile_snapshot.hash`.
- `manifest.current_anchor_hash` (opcional) o `--current-anchor-hash`.

El script nunca modifica el `manifest.json`. Su salida es
`reports/approvals.json` con el estado calculado y los motivos.

## 4. Re-firma tras edición

Cuando una aprobación queda `stale`:

1. El revisor (humano o asistido) verifica que el cambio de hash
   representa realmente una nueva edición semántica, no un cambio
   cosmético (UTF-8 BOM, saltos de línea o `state_history`
   adicional).
2. Si la edición es semántica, se registra una nueva `decision`
   con `kind: approve` y `reviewed_hashes` actualizados.
3. Se emite un nuevo `approval` vinculado a esa decisión, con
   `target_hash` recalculado.
4. Las aprobaciones obsoletas no se borran: permanecen como
   historial. Su estado `stale` queda reflejado en el gate.

## 5. Ediciones no semánticas

El cálculo de hash sobre `source_hash` y el `candidate_hash` ya
excluye cambios de `state_history`. La aprobación no se invalida
por:

- Reordenamiento de la lista `decisions[]` o `approvals[]`.
- Cambio de timestamp `last_transition_at` sin cambio de
  `current_state`.
- Re-formateo del JSON del manifiesto sin alterar hashes.

## 6. Relación con otras fases

| Fase | Relación |
|---|---|
| 123 | `decisions[]` produce los `decision_id` que `approvals[]` referencia. |
| 130 | El gate ampliado exige cero aprobaciones `stale`. |
| 119 | La invalidez por glosario convive con la invalidez transitiva de caché. |
