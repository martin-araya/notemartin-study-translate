<!-- version: 1.0.0 -->

# Reporte de inconsistencias (fase 125)

El reporte `scripts/group_inconsistencies.py` produce
`reports/inconsistencies.md` agrupando las divergencias
terminológicas **por sentido y dominio**, no sólo por palabra suelta.

## 1. Forma del reporte

```text
# Inconsistencias terminológicas (fase 125)

## Dominio `ui`

### estado (`ui / app.runtime_state`)

- Equivalente preferido: `estado`
- Variantes permitidas: `_(ninguna)_`
- Formas prohibidas: `estatus`
- Documentos con este sentido: doc-a, doc-b
- Variantes observadas:
  - `estado` en 2 documentos.

## Dominio `api`
…
```

## 2. Reglas de agrupación

1. Se construye un índice por `source_term.lower()`.
2. Para cada glosario y traducción, se agrupa por `(domain, sense_id)`.
3. Las `sense_id` se toman del glosario congelado. Si una entrada
   no tiene `sense_id`, se usa el `sense` textual. Si tampoco,
   el `source_term`.
4. Las variantes observadas incluyen el equivalente preferido,
   las variantes permitidas del glosario y, cuando corresponda,
   las formas prohibidas.

## 3. Lo que el reporte NO hace

- No aplica correcciones a `translations/`.
- No propone como definitivo un sinónimo: cada línea termina con
  una sugerencia explícita y un recordatorio de que el revisor
  humano debe confirmar antes de congelar en `glossary.json`.
- No borra entradas anteriores del glosario: cualquier cambio de
  términos invierte las aprobaciones vigentes (fase 124).

## 4. Atomicidad de la escritura

El archivo `reports/inconsistencies.md` se escribe atómicamente:
un fallo de medio de escritura no deja un reporte parcial.

## 5. Relación con otras fases

| Fase | Relación |
|---|---|
| 045 | Comparte objetivos con `scripts/audit_terminology.py`. La fase 125 añade agrupación por sentido; la 045 mantiene la cuenta palabra a palabra. |
| 091-100 | `glossary.json.domains[]` conduce la agrupación por dominio. |
| 124 | Cambiar el glosario invalida las aprobaciones existentes. |
