# Caso de corpus completo (fase 111)

> Caso **experimental** para la fase 111. El corpus real vive en
> `/Users/martin/Desktop/documentacion` con 4832 archivos `.md`
> repartidos en 25 directorios. La suite de CI **no** corre sobre
> el corpus completo: muestrea 30 archivos en
> `tests/fixtures/scale/` para mantener el tiempo de CI acotado.

## 1. Origen autorizado

| Campo | Valor |
|---|---|
| Ruta del corpus | `/Users/martin/Desktop/documentacion` |
| Total de archivos `.md` | 4832 |
| Directorios | 25 (`angular`, `nextjs`, `tailwindcss`, `typescriptlang`, `developer-mozilla`, etc.) |
| Tamaño total en disco | ≈ 291 MB |
| Codificación mayoritaria | UTF-8 |
| Saltos de línea | LF en la mayoría; algunos CRLF puntuales |
| Fecha de inventario | 2026-10-20 |

## 2. Muestreo para CI

| Campo | Valor |
|---|---|
| Directorio del muestreo | `tests/fixtures/scale/` |
| Cantidad de archivos | 30 |
| Semilla | 42 |
| Tamaño total del muestreo | ≈ 244 KB |
| Documentos muestreados | Ver `tests/fixtures/scale/_sample.json` (con SHA-256 corto). |

El muestreo se selecciona con `random.Random(42).sample` para ser
reproducible. Los archivos viven dentro de 9 directorios para
mantener variedad: `angular`, `code-visualstudio`, `dart`,
`developer-mozilla`, `docs-flutter`, `nextjs`, `robyn`,
`tailwindcss`, `typescriptlang`.

## 3. Por qué un muestreo y no el corpus completo

- **Tiempo de CI**: 4832 archivos en la cadena
  inventario→preparación→detección→paquetería disparan los tests
  más allá de los umbrales razonables.
- **Reproducibilidad**: el muestreo es determinista, así que dos
  CI runs idénticos en el mismo commit producen el mismo perfil.
- **Aislamiento**: el muestreo refleja suficientemente la
  variedad de dialectos Markdown, tablas, código y enlaces para
  validar `measure_execution.py` sin arrastrar dependencias
  externas.

## 4. Ejecución sobre el corpus completo

Fuera de CI, la medición completa se lanza con:

```bash
python3 scripts/measure_execution.py \
    --corpus /Users/martin/Desktop/documentacion \
    --pair en-es \
    --out reports/execution_profile_full.json
```

El JSON resultante puede incluir el campo `sample` con
`files_sampled == total_files`, lo cual se considera
**muestreo no aplicado** y vuelve al corpus íntegro.

## 5. Riesgos declarados

- Los tokens y costos siguen siendo `null` por política. Aunque se
  observen tiempos reales, ningún campo que requiera datos del
  proveedor se infiere.
- El renderizado del navegador o Notion no entra en
  `execution_profile.json`; es responsabilidad del operador.
- Si el corpus cambia (nuevos commits), el muestreo y el corpus
  completo divergen. El campo `sample.seed` permite reproducirlo.
