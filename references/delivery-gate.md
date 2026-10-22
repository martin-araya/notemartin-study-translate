<!-- version: 1.0.0 -->

# Gate de entrega (fase 140)

El gate de entrega es la última comprobación antes de entregar un
paquete. Solo lee: no escribe en `output_root/`, en `work_root/` ni
dentro del paquete. Su resultado se vuelca en
`reports/delivery/gate_delivery.json`.

## 1. Comprobaciones y códigos de salida

| Código | Comprobación | Qué exige |
|---|---|---|
| 1 | `canonical_untouched` | El árbol canónico no cambió y sus hashes coinciden con los del informe de adaptación. |
| 2 | `package_matches_manifest` | El manifiesto del paquete declara `guide_outside_package`, la revalidación en vivo no encuentra violaciones y el informe de la fase 136 está en verde. |
| 3 | `guide_outside_importable_tree` | La guía existe, no está dentro del árbol importable y no es miembro del paquete. |
| 4 | `no_content_loss` | El reporte de degradaciones no declara ninguna diferencia `content_loss`. |
| 5 | `rules_declared` | Cada cambio de adaptación lleva `rule_id` y `lossiness`, ninguna regla se declara `content_loss` y no quedan reglas rechazadas sin resolver. |
| 6 | `destinations_declared` | Todo destino de la matriz declara `activation: explicit` y limitaciones, y ninguno está marcado verificado sin evidencia de aplicación real. |
| 7 | `disabled_adapter_reproduces_canonical` | Si el paquete lleva adaptación, el paquete canónico debe existir y ser idéntico en miembros y bytes. |

El gate devuelve el código de la **primera** comprobación fallida, en el
orden de la tabla. Con todas en verde devuelve 0.

## 2. Por qué el gate revalida el paquete

No basta con leer el informe de `scripts/validate_zip_package.py`: entre
la validación y la entrega el paquete puede cambiar. El gate vuelve a
abrir el ZIP y a compararlo con el manifiesto de paquete usando el mismo
código, de modo que un paquete alterado después de su validación se
detecta igual.

## 3. Check 7 en detalle

Es la comprobación que sostiene el criterio de la fase: **desactivar un
adaptador no modifica la traducción canónica**.

- Si el paquete **no** declara adaptación, el check se cumple por
  construcción y el gate lo registra con ese detalle.
- Si el paquete **sí** la declara, hace falta `--canonical-package`. Sin
  él el check falla con código 7. Con él, el gate compara el conjunto de
  miembros y el hash completo.

Un paquete adaptado legítimamente **no** puede ser idéntico al canónico:
por eso, cuando hay adaptación aplicada, este check falla salvo que se
demuestre lo contrario. La comprobación que sí se ejecuta en ese caso es
la 4: ninguna adaptación puede perder contenido.

## 4. Uso

```bash
python scripts/gate_delivery.py \
    --manifest work_root/<run_id>/manifest.json \
    --canonical output_root/<run_id> \
    --package dist/<run_id>-notion-manual.zip \
    --package-manifest reports/delivery/package_manifest.json \
    --package-validation reports/delivery/package_validation.json \
    --guide reports/delivery/<run_id>/DELIVERY.md \
    --output-tree output_root/<run_id> \
    --adaptation-report reports/delivery/adaptation_report.json \
    --degradation-report reports/delivery_degradations.json \
    --delivery-matrix reports/delivery_matrix.json \
    --canonical-package dist/<run_id>-canonical.zip \
    --out reports/delivery/gate_delivery.json
```

## 5. Recorrido completo del lote

```text
export.py                         → árbol canónico
adapt_delivery.py                 → árbol adaptado + informe
export_zip.py                     → ZIP + manifiesto de paquete
validate_zip_package.py           → validación del paquete
render_delivery_guide.py          → guía fuera del árbol
compare_delivery.py               → reporte de degradaciones
delivery_matrix.py                → matriz de destinos
gate_delivery.py                  → veredicto con código de salida
```

## 6. Qué no demuestra el gate

- Que la traducción sea fiel. Eso lo decide el gate del núcleo y la
  revisión semántica, no este.
- Que el destino importe bien el paquete. Solo lo demuestra la
  evidencia que aporte el usuario.
- Que un destino futuro se comporte igual. El comportamiento puede
  cambiar sin que nada de este gate lo detecte.