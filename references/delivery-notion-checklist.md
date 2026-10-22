<!-- version: 1.0.0 -->

# Checklist de importación de muestra (fase 131)

Este documento es el procedimiento que el usuario sigue para comprobar
qué hace un destino con el Markdown entregado. No certifica nada por sí
solo: la skill no importa en ningún servicio y no puede observar el
resultado de una importación hecha a mano.

La lista de construcciones y sus limitaciones esperadas está en
`references/notion-handoff.md` §7. Este checklist añade **qué evidencia
hay que aportar** y **qué queda sin verificar** cuando esa evidencia no
llega.

## 1. Principio

| Nivel | Qué demuestra | Qué no demuestra |
|---|---|---|
| Markdown válido en el dialecto declarado | Que el archivo entregado se puede parsear. | Que el destino lo represente igual. |
| Resolución local de enlaces | Que el enlace apunta a un archivo y a un fragmento que existen en el árbol entregado. | Que al importar se pueda navegar. |
| Evidencia remota aportada por el usuario | Que una comprobación concreta se observó en el destino. | Que se cumpla para el resto del corpus o para otra versión del destino. |

`scripts/record_import_evidence.py` separa esos niveles en campos
distintos: `local_resolution`, `remote_result` y `evidence`. El primero
lo calcula la skill; los otros dos solo los rellena el usuario.

## 2. Preparación

1. Ejecutar la exportación local con `scripts/export.py`. El árbol
   entregado queda en `output_root/<run_id>/` y no contiene reportes.
2. Elegir una muestra de **3 a 5 documentos** representativos del corpus:
   al menos uno con tabla, uno con bloques de código y uno enlazado con
   los demás. `scripts/record_import_evidence.py` toma los primeros
   documentos aprobados del manifiesto en orden estable, de modo que la
   selección es reproducible.
3. Generar el registro inicial:

   ```bash
   python scripts/record_import_evidence.py \
       --manifest work_root/<run_id>/manifest.json \
       --output-tree output_root/<run_id> \
       --check-links \
       --matrix-out reports/import_matrix.json \
       --out work_root/<run_id>/reports/import_evidence.json
   ```

   El registro nace con `verified: false`, `remote_status:
   no_verificado` y todos los `remote_result` en `unknown`.

## 3. Comprobaciones que debe hacer el usuario

Importar la muestra en el destino y, para cada construcción, registrar
el resultado observado.

| `check_id` | Qué observar | Si falla |
|---|---|---|
| `table_structure` | La tabla conserva filas, columnas y el separador de celdas escapado. | No importar el documento o aceptar la limitación por escrito. |
| `code_block_bytes` | El bloque conserva su contenido literal, incluidos comentarios en español. | Reportar pérdida de contenido: es un bloqueante. |
| `code_inline_bytes` | El código inline no se altera ni se traduce. | Reportar alteración de literal: es un bloqueante. |
| `internal_link_local` | Solo comprobable antes de importar: la resolución de archivo y fragmento. | Corregir el enlace en la fuente y repetir el gate. |
| `internal_link_remote` | Al pulsar el enlace se llega al encabezado de destino. | Registrar como limitación del destino, no como error de traducción. |
| `image_and_alt` | La imagen carga y conserva su texto alternativo. | Revisar la ruta; las rutas del scraper pueden no resolver. |
| `callout_warning` | La advertencia conserva su carácter de advertencia. | Nunca degradarla a nota. |
| `task_list` | `- [ ]` y `- [x]` sobreviven como texto. | Las casillas interactivas requieren API del destino. |
| `frontmatter` | El frontmatter se conserva literal o se muestra como texto plano. | El núcleo lo preserva; el destino decide cómo mostrarlo. |

## 4. Evidencia que hay que aportar

La evidencia se registra en un JSON aparte que se fusiona con
`--record`. Este es el formato mínimo aceptable:

```json
{
  "verified": true,
  "reviewer": { "kind": "human", "name": "quien-lo-comprobo", "declared_at": "2026-10-20T12:00:00Z" },
  "sample_documents": [
    { "path": "index.md", "imported": true, "destination_url": "https://…" }
  ],
  "checks": [
    {
      "check_id": "internal_link_remote",
      "remote_result": "pass",
      "evidence": [{ "kind": "user_report", "ref": "descripción de lo observado" }]
    }
  ],
  "matrix": [{ "construction": "internal_link_remote", "destination_id": "notion-manual", "status": "pass" }]
}
```

Tipos de evidencia admitidos: `user_report`, `screenshot` y `url`. El
script valida la **presencia** de la referencia, nunca su veracidad. Por
eso el firmante humano es obligatorio.

```bash
python scripts/record_import_evidence.py \
    --manifest work_root/<run_id>/manifest.json \
    --output-tree output_root/<run_id> \
    --record evidencia_del_usuario.json \
    --out work_root/<run_id>/reports/import_evidence.json
```

## 5. Qué rechaza el script

`scripts/record_import_evidence.py` sale con código **3** y degrada el
registro a `verified: false` cuando:

- se declara `verified: true` sin revisor humano con nombre;
- se declara `verified: true` sin ningún documento marcado como
  importado;
- alguna comprobación remota figura como `pass` sin evidencia adjunta.

El registro se escribe igualmente, con la nota del rechazo, para que el
motivo quede auditado.

## 6. Qué sigue sin verificarse

Mientras el usuario no aporte evidencia, y aunque la aportara para una
muestra:

- El comportamiento del destino para el corpus completo.
- El comportamiento bajo otra versión del destino.
- La navegación en archivos no incluidos en la muestra.
- Cualquier cambio del destino posterior a la fecha de la evidencia.

El informe final declara el estado remoto como `no verificado` mientras
`remote_status` sea ese valor. Esa distinción es obligatoria en
`RELEASE.md`, en el informe de entrega y en el manifiesto.

## 7. Relación con las fases siguientes

- La fase 132 usa `--check-links` para calcular la resolución local; esa
  salida no se mezcla con la navegación remota.
- La fase 133 usa `--matrix-out` para emitir la matriz construcción por
  destino.
- La fase 135 usa este registro como entrada del paquete: un destino
  con `remote_status: no_verificado` se etiqueta como tal dentro del
  paquete y en la guía de entrega.