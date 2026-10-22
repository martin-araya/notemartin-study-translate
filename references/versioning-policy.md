<!-- version: 1.0.0 -->

# Política de versionado (fase 142)

Qué se versiona en este proyecto, quién lo incrementa y qué obliga a una
migración. El contrato ejecutable vive en `release_contract.json` y su
esquema en `schemas/release_contract.schema.json`. La comprobación es
`scripts/check_versioning.py`.

## 1. Familias de versión

| Familia | Dónde se declara | Quién la incrementa | Regla |
|---|---|---|---|
| Skill | `release_contract.json.skill_version`, `CHANGELOG.md`, `RELEASE.md`, `manifest.skill_version` | release | semver |
| Contratos | `release_contract.json.contracts[].version` | cambio incompatible | `translate/vN`, major por cambio incompatible |
| Esquemas | clave `x-schema-version` del propio esquema + `release_contract.json.schemas[]` | cambio de contrato | minor aditivo, major incompatible |
| Referencias | marca `<!-- version: X.Y.Z -->` + `release_contract.json.docs[]` | quien edite el documento | patch editorial, minor si cambia una regla |
| Parser | `references/markdown-contract.md` §8 + `release_contract.json.parser.pinned` | fase 144 | major si cambian rangos o slugs |
| Política de anclas | `manifest.anchor_policy` | fase 039 | major si cambia el algoritmo |
| Prompt | `release_contract.json.prompt_version`, `manifest.model_metadata.prompt_version` | cambio del prompt de traducción | minor |
| Registro de regresión | campo `registry_version` de `evals/regression/registry.json` | alta de caso | entero |

## 2. Qué cuenta como cambio incompatible

Los cinco casos siguientes obligan a **major** y a una entrada en
`breaking_changes[]` con su herramienta de migración:

1. Eliminar o renombrar un campo de contrato, o cambiar su tipo.
2. Cambiar una enumeración de estados, severidades o categorías.
3. Cambiar el algoritmo de slugs de anclas.
4. Cambiar la granularidad, las unidades o la numeración de los rangos.
5. Relajar una comprobación de gate sin viñeta explícita en el changelog.

No son incompatibles: añadir un campo opcional, añadir un valor a una
enumeración que ya tenía sentido cerrado y documentado, corregir una
redacción o añadir un fixture.

## 3. Migraciones

Una migración es un script ejecutable que toma un artefacto de la versión
anterior y devuelve uno de la nueva **sin inventar datos**. En este proyecto
la regla es dura: una migración nunca convierte una revisión antigua en una
aprobación vigente (fase 143).

| Origen | Destino | Herramienta |
|---|---|---|
| `translate/v0` | `translate/v1` | `scripts/migrate_manifest.py` |

Toda migración se declara en `release_contract.json.migrations[]` con su par
`from`/`to` y su herramienta. Una entrada en `breaking_changes[]` sin
`migrations[]` hace fallar el gate con el código 4.

## 4. Reglas de incremento de la skill

- **patch**: corrección de redacción, fixture nuevo, prueba nueva.
- **minor**: capacidad nueva opt-in que no cambia ningún valor por defecto
  (fue el caso de 0.1.1 a 0.1.5, cada lote opcional como subrelease).
- **major**: cambia un contrato en uso, un formato de salida o un gate.

0.2.0 es **minor**: añade las herramientas de mantenimiento (141–148) y
declara qué módulos entran en el candidato. No cambia el comportamiento del
núcleo ni ningún valor por defecto.

## 5. Qué NO versiona esta política

- Las respuestas del modelo. No son reproducibles aunque el manifiesto
  registre modelo, prompt y hashes de procedencia.
- El estado remoto de un destino (Notion u otro). Se declara
  `no_verificado` hasta que exista evidencia humana.
- El contenido del corpus del usuario. Ni su hash se versiona en este
  repositorio: solo los hashes que el manifiesto de una ejecución declara.

## 6. Procedimiento

```bash
python3 scripts/check_versioning.py --root . \
    --out reports/maintenance/versioning.json
```

| Código | Significado |
|---|---|
| 1 | la versión de la skill no tiene entrada propia en `CHANGELOG.md` |
| 2 | esquema sin `x-schema-version`, `$id` incoherente o versión que no cuadra con el contrato |
| 3 | referencia sin marca de versión, versión que no cuadra, o referencia listada que no existe |
| 4 | cambio incompatible sin migración declarada y existente |
| 5 | contrato incoherente con el changelog, con un `translate/vN` o con el parser fijado |
| 6 | `requirements.txt` falta, está vacío o tiene dependencias sin `==` |

Al cambiar un contrato: actualizar el esquema, el `release_contract.json`,
el `CHANGELOG.md`, la referencia afectada con su marca de versión, y —si es
incompatible— la migración y sus pruebas antes de tocar ningún manifiesto
existente.