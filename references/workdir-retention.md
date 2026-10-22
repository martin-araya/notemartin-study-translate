<!-- version: 1.0.0 -->

# Retención y limpieza de workdirs (fase 148)

Un `work_root` es trabajo provisional: segmentos, paquetes, traducciones en
curso, informes intermedios. Crece sin límite y nadie lo limpia. Esta fase
fija qué sobrevive, cuánto tiempo y quién puede borrarlo.

La regla de fondo: **el trabajo es lo único desechable**. Una fuente nunca
se toca, una salida nunca se toca, y borrar trabajo siempre deja rastro.

## 1. Tabla de retención

| Ruta | Retención | Quién la borra |
|---|---|---|
| `source_root/**` | permanente | nadie: no existe flag que lo permita |
| `output_root/<run_id>/` | hasta que la retire el usuario | nadie: la herramienta lo rechaza |
| `reports/**` | permanente | nadie |
| `work_root/<run_id>/` | 30 días por defecto | `purge_workdir.py` con autorización |
| `dist/*.zip` | hasta que la retire el usuario | fuera del alcance de esta herramienta |
| caché de traducción | su propia política (fase 118) | `invalidate_cache.py` |
| venv del parser alterno (fase 144) | efímera, fuera del repositorio | quien la creó |

## 2. Procedimiento

```bash
# ver qué se borraría, sin borrar nada
python scripts/purge_workdir.py \
    --work-root /ruta/work --run-id run-0000beef \
    --source-root /ruta/corpus --output-root /ruta/salida \
    --dry-run

# borrar de verdad, con autorización
python scripts/purge_workdir.py \
    --work-root /ruta/work --run-id run-0000beef \
    --apply --authorized-by "nombre" --reason "cierre de ejecución"
```

| Código | Significado |
|---|---|
| 0 | purga aplicada, o simulación informativa |
| 2 | las raíces se solapan: `work_root` está dentro o contiene `source_root` o `output_root` |
| 3 | `--apply` sin `--authorized-by` |
| 4 | la ejecución está en un estado protegido y no hay autorización |
| 5 | enlace simbólico: se conserva y se registra |
| 6 | el workdir no existe |

## 3. Garantías del código

Estas no son recomendaciones del documento: son comprobaciones del script,
cubiertas por `tests/test_purge_workdir.py`.

- **Seco por defecto.** Sin `--apply` no se borra nada y se escribe la lista
  de candidatos con su tamaño.
- **`--apply` exige `--authorized-by`.** No hay borrado anónimo.
- **Doble comprobación de raíz.** `check_roots` rechaza que `work_root`
  esté dentro de `source_root` o de `output_root`, y viceversa, usando
  `delivery_common.is_within`.
- **No se siguen enlaces simbólicos.** Un symlink se registra como omitido
  y sobrevive: borrar su destino sería borrar algo fuera del workdir.
- **Una ejecución `exported` exige autorización explícita.** Se comprueba
  el estado real del manifiesto, no el nombre del directorio.
- **El log se escribe fuera del workdir.** Por defecto en
  `reports/maintenance/purge_log.json`. Nunca dentro de lo que se borra.

## 4. Contenido del log

Cada purga deja, aunque sea una simulación:

| Campo | Para qué |
|---|---|
| `run_id`, `workdir`, `work_root` | qué se tocó |
| `dry_run` | si fue simulación |
| `authorized_by`, `reason` | quién decidió y por qué |
| `run_state` | estado real de la ejecución según su manifiesto |
| `manifest_sha256` |huella del manifiesto en el momento de la purga |
| `candidates`, `deleted`, `skipped` | qué se iba a borrar, qué se borró y qué se conservó |
| `bytes_candidate`, `bytes_reclaimed` | tamaño esperado y realmente recuperado |
| `retention_days` | la ventana declarada en la llamada |

## 5. Lo que esta política NO hace

- **No borra caches de traducción.** Tienen su propio ciclo (fase 118) y su
  propia trazabilidad.
- **No borra nada fuera de `work_root`.** El alcance es un run, no un árbol.
- **No aplica la ventana de 30 días automáticamente.** La retención es un
  compromiso declarado; la purga la decide una persona. Automatizar el
  borrado sin que alguien mire el manifiesto sería una pérdida de datos
  silenciosa.
- **No conserva el texto traducido que se purga.** El registro de una
  ejecución conserva metadatos, no prosa. Si el texto importa, hay que
  exportarlo antes.

## 6. Relación con otras fases

| Fase | Relación |
|---|---|
| 008 | los `work_root` son el directorio de trabajo que crea esa fase |
| 118 | la caché se invalida por glosario, no se purga aquí |
| 123 | el estado `exported` que protege la purga lo fija la cadena de estados |
| 129 | los informes que se conservan no llevan prosa completa |
| 148 | entregable de esta fase; sustituye la mención colgante de `references/log-redaction.md` |