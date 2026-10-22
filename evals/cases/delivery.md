# Caso entrega local (fases 131-140)

Estado: **herramientas probadas sobre fixtures; destino real ausente**.
La evidencia está en `reports/optional/delivery.json` y en la suite
(`tests/test_adapt_delivery.py`, `test_export_zip.py`,
`test_compare_delivery.py`, `test_gate_delivery.py`,
`tests/test_import_evidence.py`, `test_delivery_guide.py`,
`test_delivery_matrix.py`, `test_delivery_docs.py`: 71 pruebas en 8 ficheros).

## 1. Corpus que activa el módulo

| Campo | Valor |
|---|---|
| Ruta | `tests/fixtures/delivery/canonical/` |
| Naturaleza | **sintético**, declarado como tal |
| Archivos | 3 |
| Bytes | 1 465 |
| Árbol (prefijo) | `eb79fc6cbafef850` |

Perfil de entrega declarado:
`references/delivery-profiles/plain-markdown-local.json`, con `activation:
explicit` y `justification` concreta.

## 2. Recorrido verificado sobre el corpus piloto

Ejecutado sobre `tests/fixtures/pilot/` (9 documentos reales), en este orden y
con esta salida real:

```text
record_import_evidence.py --check-links → verified=False remote_status=no_verificado
                             resolución local: pass · 28 enlaces · 18 site_relative · 0 rotos
adapt_delivery.py   (2 reglas)         → cambios=0 byte_identical=True
compare_delivery.py                     → 9 documentos · content_loss=0
export_zip.py                           → 9 miembros · excluidos=0 · remote_status=no_verificado
validate_zip_package.py                 → 9 miembros validados contra 9 declarados
render_delivery_guide.py                → DELIVERY.md + delivery_manifest.json
delivery_matrix.py                      → 2 destinos
gate_delivery.py                        → ok: gate de entrega aprobado (7 comprobaciones)
```

**Las reglas de adaptación no se disparan sobre ese corpus.** Su justificación
está en `tests/fixtures/delivery/canonical/`, no en el piloto. Encenderse ahí
sería activarlo sin motivo, que es lo que este caso documenta.

## 3. Estado de la activación

`delivery.enabled` es **dormiente** y, con el perfil 1.1.0, exige `corpus_ref`
y `justification`; `schemas/profile.schema.json` rechaza
`delivery.enabled: true` sin `destination_id` y `profile_ref`.

## 4. Qué no afirma este caso

- **No** afirma que nada se haya importado en Notion. Nadie lo ha hecho: la
  plantilla de evidencia nace con `verified: false` y
  `remote_status: no_verificado`, y promoverla exige revisor humano.
- **No** afirma que exista un segundo destino de entrega real. El destino
  `plain-markdown-local` es un adaptador interno y declara
  `real_app_evidence: false` y `evidence_kind: local_fixture_only`.