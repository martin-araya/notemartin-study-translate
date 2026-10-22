<!-- version: 1.0.0 -->

# Matriz de destinos de entrega (fase 139)

La matriz enumera los destinos que la skill sabe **preparar**. No
enumera los destinos que funcionan. La diferencia importa: preparar un
paquete para un destino es una operación local y determinista;
comprobarlo es otra cosa, y casi siempre depende de una persona.

Artefacto generado: `reports/delivery_matrix.json`, con
`scripts/delivery_matrix.py`.

## 1. Destinos declarados

| Destino | Tipo | Importación | Activación | Evidencia | ¿Verificado? |
|---|---|---|---|---|---|
| `notion-manual` | canónico | manual por el usuario | explícita | `user_reported` | No |
| `plain-markdown-local` | adaptador interno | sistema de archivos | explícita | `local_fixture_only` | No |

### `notion-manual`

Es el destino canónico del núcleo: el paquete contiene la traducción
tal cual, sin adaptación. Lo que haga el destino con esos archivos no lo
decide la skill. La verificación vive en
`schemas/import_evidence.schema.json` y se alimenta del checklist de
`references/delivery-notion-checklist.md`.

### `plain-markdown-local`

Es un **adaptador interno de la propia skill**, no una aplicación de
escritorio. Existe porque en el entorno de desarrollo no hay ningún
importador local instalado, y porque el contrato de adaptación de la
fase 134 necesitaba un segundo destino para comprobar que desactivar un
adaptador no altera la traducción canónica.

Por eso declara `real_app_evidence: false`. Su evidencia es
`local_fixture_only`: los fixtures de `tests/fixtures/delivery/` y las
pruebas de adaptación y degradación.

Qué **no** cubre esa evidencia:

- Que un editor de escritorio abra el árbol como se espera.
- Que los enlaces internos naveguen en esa aplicación.
- Que las tablas y los bloques de código se representen igual.
- Que las imágenes relativas se carguen.

## 2. Reglas para activar un destino

1. Un destino solo existe en la matriz si tiene `cases` y
   `limitations` no vacíos.
2. `activation` es siempre `explicit`. Ningún destino se activa por
   omisión.
3. `verified: true` exige `real_app_evidence: true`. El gate de entrega
   (fase 140) rechaza un destino marcado verificado sin evidencia de
   aplicación real.
4. Un destino nuevo se añade con su perfil en
   `references/delivery-profiles/` y con pruebas propias. No se añade
   porque suene razonable.

## 3. Limitaciones declaradas por destino

| Destino | Limitaciones |
|---|---|
| `notion-manual` | No se verifica navegación, render de tablas, código ni imágenes. Un Markdown válido no demuestra nada del destino. El comportamiento puede cambiar entre versiones. |
| `plain-markdown-local` | No se ha probado en una aplicación real. Renombrar recursos rompe enlaces externos con la ruta antigua. Solo normaliza rutas y nombres. |

## 4. Relación con las demás fases

| Fase | Aportación a la matriz |
|---|---|
| 131–133 | `remote_status` e `import_evidence.json` marcan si hay evidencia remota. |
| 134 | El perfil de entrega declara reglas, justificación y limitaciones. |
| 138 | Las degradaciones informe qué pierde o cambia una adaptación. |
| 140 | El gate exige que todo destino declare activación y limitaciones. |

## 5. Cómo extenderla

Añadir un destino real exige, en este orden:

1. Corpus concreto que justifique la adaptación (G-EXT).
2. Perfil en `references/delivery-profiles/` con `justification`,
   `limitations` y `cases`.
3. Fixtures y pruebas de adaptación y degradación.
4. Fila en `scripts/delivery_matrix.py` con su estado de evidencia real.
5. Ejecución del gate de entrega sobre un paquete de ese destino.

Sin el paso 5, el destino se declara con `verified: false` aunque todo
lo demás exista.