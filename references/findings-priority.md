<!-- version: 1.0.0 -->

# Vista estática con priorización (fase 122)

La priorización de hallazgos es una **vista estática para revisión
humana**: reordena los hallazgos existentes sin ocultar los
bloqueantes y sin transformar contenido.

## 1. Categorías de riesgo

| Categoría | Qué cubre | Severidad de entrada |
|---|---|---|
| Riesgo alto | Cambios que afectan obligatoriedad: negación invertida u omitida, MUST/SHOULD/MAY alterado, cuantificador cambiado, causalidad inversa, URL externa modificada. | `error` o `warning`. |
| Riesgo medio | Cambios de forma con potencial semántico: lista reordenada o truncada, código reescrito sin cambiar el significado, encabezado reordenado, sujeto intercambiado, referencia de versión perdida. | `warning` o `info`. |
| Riesgo bajo | Estilo, consistencia, puntuación localizada. | `info`. |

Las categorías se calculan a partir del campo `category` de cada
hallazgo. Las desconocidas se tratan como **bajo riesgo** por
defecto, **nunca** como altas.

## 2. Gate pendiente (no oculta nunca)

Tres activan esta sección:

- Archivo con `current_state ∈ {blocked, failed, gate_pending}`.
- Archivo con al menos un `issue.severity = error`.
- Hallazgo en `semantic.findings` con `flags.gate_blocking = True`
  (cuando aplique).

Esta sección precede siempre a las tres de riesgo.

## 3. Fórmula de orden estable

```text
score = (-severity_norm, evidence_strength, -scope_impact, segment_id)
```

- `severity_norm`: 3 = error, 2 = warning, 1 = info.
- `evidence_strength`: número de hallazgos correlacionados.
- `scope_impact`: 1 (global) > 0.5 (archivo) > 0.25 (segmento).
- `segment_id`: desempate final.

La vista es determinista: dos ejecuciones sobre el mismo manifiesto
producen el mismo orden byte a byte.

## 4. Lo que NO hace

- No escribe en `translations/` ni en `work_root/`.
- No modifica el `manifest.json`.
- No suprime hallazgos: solo los reordena.
- No infiere categorías: las que no aparecen se tratan como bajo
  riesgo, no se inventan reglas.

## 5. Relación con otras fases

| Fase | Relación |
|---|---|
| 121 | Esta vista se complementa con el informe bilingüe; ambos se generan al final de la pasada. |
| 128 | Cumple el checklist de accesibilidad: sin recursos externos. |
| 130 | El gate de revisión falla si la vista no existe en modo ampliado. |
