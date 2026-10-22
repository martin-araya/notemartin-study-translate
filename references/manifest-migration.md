<!-- version: 1.0.0 -->

# Migración de manifiestos (fase 143)

Un manifiesto de una versión anterior del contrato sigue siendo legible,
pero **no** puede seguir siendo una aprobación vigente. Esta fase fija el
procedimiento de migración de `translate/v0` a `translate/v1` y su regla
central: la migración no valida nada por la ejecución anterior.

## 1. Qué cambia en el esquema

`schemas/manifest.schema.json` sube a `x-schema-version` 1.1.0 y añade, de
forma aditiva:

| Campo | Dónde | Para qué |
|---|---|---|
| `manifest_version` | raíz, **obligatorio** | declara el contrato del manifiesto |
| `migrations[]` | raíz | registra cada migración aplicada con su hash de origen |
| `approval.stale`, `approval.stale_reason` | aprobación | marca de obsolescencia |
| `decision.stale`, `decision.stale_reason` | decisión | marca de obsolescencia |
| `file_record.requires_revalidation[]` | archivo | comprobaciones a repetir antes de aprobar o exportar |

`manifest_version` pasa a ser obligatorio: un manifiesto sin ese campo es
`translate/v0` y hay que migrarlo explícitamente.

## 2. Reglas de la migración

| Entrada | Salida | Por qué |
|---|---|---|
| sin `manifest_version` | `translate/v1` + entrada en `migrations[]` | la versión deja de ser implícita |
| `approval` vigente | `stale: true`, `stale_reason: manifest_migration`, `status: stale` | **una revisión antigua no es una aprobación vigente** |
| `decision` vigente | `stale: true`, `stale_reason: manifest_migration` | misma razón |
| archivo en `approved` o `exported` | `deterministic_pass` + `requires_revalidation` | el contenido se revalida contra el árbol actual |
| `state_history` | se conserva literal y se añade la transición de migración | no se reescribe la historia |
| `created_at`, `source_hash`, `skill_version` | sin cambios | son procedencia, no estado |

`requires_revalidation` incluye siempre `hashes`, `literals`, `structure`,
`links`, `semantic_pass` y `export`.

## 3. Procedimiento

```bash
# inspección, sin escribir nada
python3 scripts/migrate_manifest.py \
    --in work_root/run-0000beef/manifest.json \
    --dry-run --out /tmp/migrated.json

# aplicación, con autorización explícita
python3 scripts/migrate_manifest.py \
    --in work_root/run-0000beef/manifest.json \
    --out work_root/run-0000beef/manifest.json \
    --apply --authorized-by "nombre"
```

| Código | Significado |
|---|---|
| 0 | migración aplicada, o nada que hacer |
| 2 | la entrada no es un manifiesto legible |
| 3 | el resultado no valida contra el esquema, o `--apply` sin `--authorized-by` |
| 4 | el hash de origen no coincide con `--expected-source-hash` |
| 5 | `manifest_version` desconocida o futura |
| 6 | ya declara `translate/v1`; hace falta `--force-revalidate` |

## 4. Reglas duras

- La herramienta **no** lee ni escribe en `source_root` ni en
  `output_root`. Solo el archivo de manifiesto que se le pase.
- No inventa `approved` ni `exported`. Su estado más avanzado es
  `deterministic_pass`.
- No reescribe `state_history`: la añade al final.
- Es idempotente: migrar dos veces no vuelve a degradar el estado ni
  duplica aprobaciones obsoletas; solo añade una segunda entrada en
  `migrations[]`, que es la traza de que se volvió a ejecutar.
- No migra una versión que no conoce. Una versión futura se rechaza con el
  código 5 en lugar de interpretarse.

## 5. Qué NO es esta fase

- **No revalida el contenido.** Decir qué hay que volver a comprobar no es
  comprobarlo. La revalidación es trabajo de la ejecución, con su gate.
- **No arregla manifiestos inválidos.** Si el resultado no valida contra el
  esquema, la herramienta falla con 3 y no escribe.
- **No migra workdirs.** Solo el JSON del manifiesto.
- **No decide si una ejecución se puede reexportar.** Esa decisión es del
  gate global y, cuando hay duda, del usuario.

## 6. Relación con otras fases

| Fase | Relación |
|---|---|
| 123 | `decisions[]` es lo que la migración marca como obsoleta |
| 124 | `approvals[]` con vigencia por hash es lo que deja de ser vigente |
| 142 | esta migración es la primera entrada en `breaking_changes[]` del contrato |
| 143 | `tests/test_manifest_migration.py` fija cada regla de la tabla |
| 149 | `gate_extended.py` falla si un manifiesto declara `translate/v0` sin migrar |