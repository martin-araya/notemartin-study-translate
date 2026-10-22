<!-- version: 1.0.0 -->

# Informe bilingüe (fase 121)

El comando `scripts/render_bilingual.py --translations <dir>` produce
un único archivo Markdown que lista, fila por fila, cada segmento
traducible del corpus y el candidato asociado.

## 1. Estructura del archivo

1. Encabezado `# Informe bilingüe` con un resumen (`N segmentos · M
   con literales alterados`) y, si se aporta `--manifest`, la ruta
   del manifiesto de referencia.
2. Tabla de contenidos navegable por ancla Markdown. Cada documento
   figura en su propia lista con un enlace por segmento.
3. Una sección `## \`<document_id>\`` por documento con la tabla
   lado a lado.

## 2. Columnas

| Columna | Contenido |
|---|---|
| `#` | Índice 1-based por documento. |
| `segment_id` | Identificador estable; cada fila se ancla al `segment_id`. |
| `trayectoria` | Encabezados padres concatenados (`H1 > H2`). |
| `source_hash` | SHA-256 hex del texto fuente del segmento. |
| `candidato` | Texto traducido exacto, con celdas escapadas (`\\|` para pipes, `<br>` para saltos). |
| `candidate_hash` | SHA-256 hex del candidato. |

Las filas con `flag_loss: true` se marcan con `_(literales
alterados)_` tras la celda de candidato. Esa marca **no es una
revisión**: la verificación del gate (fase 041) y la revisión
semántica (fase 042) la contrastan con el original.

## 3. Orden y anclas

- Documentos en orden lexicográfico ascendente.
- Filas en cada documento ordenadas por `byte_range.start` y, en
  empate, por `segment_id`.
- El ancla por fila combina slug del `document_id` con slug del
  `segment_id`, en minúsculas ASCII.

## 4. Lo que el informe NO hace

- No modifica archivos en `translations/` ni en `work_root/`.
- No reemplaza la revisión semántica (fase 042): un informe
  bilingüe sin findings puede contener errores críticos.
- No marca equivalencia semántica: el contenido se transcribe
  literal para inspección, no se evalúa.
- No sube documentación a servicios externos: el archivo se genera
  localmente y se abre sin conexión.

## 5. Relación con otras fases

| Fase | Relación |
|---|---|
| 042 | El informe es entrada visual para la revisión semántica; no la sustituye. |
| 041 | Las filas `flag_loss` complementan al reporte determinista. |
| 122 | El informe alimenta la vista estática con priorización. |
| 128 | El informe cumple el checklist de accesibilidad (sin recursos remotos, TOC navegable). |
