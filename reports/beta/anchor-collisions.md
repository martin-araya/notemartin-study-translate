# Colisiones de anclas

## Colisiones dentro de un documento (bloqueantes)

Dos encabezados del mismo documento que generan la misma ancla: el fragmento lleva al primero y el segundo deja de ser alcanzable. Es lo que hay que decidir antes de reescribir (INV-09).

| Métrica | Valor |
|---|---|
| Documentos con encabezado repetido | 0 |
| Anclas repetidas dentro de un documento | 0 |

Ninguna. No hay colisiones intra-documento en este corpus.


## Colisiones entre documentos (no bloqueantes)

Un fragmento solo se resuelve dentro del documento que lo contiene. Reutilizar un slug entre rutas distintas no rompe la navegación, así que este recuento **no bloquea** la reescritura. Se conserva por trazabilidad.

| Métrica | Valor |
|---|---|
| Documentos con mapa de anclas | 2483 |
| Anclas compartidas entre documentos | 3110 |
| Rutas implicadas | 2298 |

## Lo que este informe no afirma

- **No** reescribe nada.
- **No** decide qué encabezado gana una colisión intra-documento: requiere ver el documento y decidir con el usuario.
- **No** demuestra que la resolución en Markdown se conserve al importar en Notion (INV-15).
