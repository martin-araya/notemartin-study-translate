<!-- version: 1.0.0 -->

# Gate del flujo ampliado de revisión (fase 130)

`scripts/gate_review.py` es el orquestador del flujo ampliado de
revisión (121-129). Su regla más importante: **el modo `basic` del
flujo de núcleo sigue siendo la ruta por defecto**. El modo
ampliado se activa sólo cuando el operador lo solicita.

## 1. Modos

| Modo | Comportamiento |
|---|---|
| `basic` (default) | Comprueba que el `manifest.json` cumple los controles del núcleo. No lee los flags `--bilingual-report`, `--residuals`, etc. No ralentiza el flujo. |
| `expanded` | Exige los artefactos de las fases 121-129. Devuelve códigos de salida distintos por requisito faltante. |

## 2. Códigos de salida en modo `expanded`

| Código | Significado |
|---|---|
| 0 | Todas las verificaciones pasan. |
| 1 | Falta el informe bilingüe (fase 121). |
| 2 | Falta una decisión humana global (fase 123). |
| 3 | Alguna aprobación quedó obsoleta por hash (fase 124). |
| 4 | El detector de idioma residual deja `warning` abiertos (fase 126). |
| 5 | Métricas de retrotraducción fuera de tolerancia (fase 127). |
| 6 | Accesibilidad del reporte o redacción de logs falla (fase 128). |

Si varias verificaciones fallan a la vez, el código de salida
refleja el **primer** código en orden numérico. El JSON de salida
incluye todos los fallos en `failures[]` y todos los códigos en
`exit_codes[]`.

## 3. Activación

```bash
python3 scripts/gate_review.py --mode basic  --manifest work/.../manifest.json --out reports/gate_review.json
python3 scripts/gate_review.py --mode expanded \
    --manifest work/.../manifest.json \
    --bilingual-report reports/bilingual/<run>.md \
    --prioritized-report reports/prioritized/<run>.md \
    --residuals reports/residual_language.json \
    --back-translation reports/back_translation.json \
    --out reports/gate_review.json
```

Alternativamente, el perfil puede fijar `review_mode: expanded`
en `profile.json` para activar la verificación automáticamente.

## 4. Lo que el gate NO hace

- **No modifica** `translations/`, `work_root/` ni
  `output_root/`. Sólo produce `reports/gate_review.json`.
- **No ejecuta el flujo**: es un verificador, no un orquestador.
- **No convierte el modo ampliado en obligatorio**: el núcleo
  sigue operando con `--mode basic` por defecto.

## 5. Política de tolerancia

`--tolerance` (default `0.3` = 30 %) define la tasa máxima de
errores aceptable del comparador de retrotraducción. Para
corpus con muchos cognados, bajar a `0.2` reduce falsos
positivos. Para corpus pequeño o exploratorio, subir a `0.5` es
aceptable.

## 6. Relación con otras fases

| Fase | Relación |
|---|---|
| 121 | El gate falla sin informe bilingüe en `expanded`. |
| 124 | Recorre `approvals[]` y compara con `files[].source_hash` y glosario. |
| 126 | Comprueba el contador `warnings` del detector residual. |
| 127 | Evalúa `(fp + fn) / total <= --tolerance`. |
| 128 | Verifica que los reportes no contengan URLs externas. |
| 130 | Esta misma fase. |
