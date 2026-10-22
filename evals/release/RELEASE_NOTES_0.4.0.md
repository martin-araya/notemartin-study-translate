<!-- Acta de la subrelease 0.4.0 · generada por scripts/gate_optional.py -->

# Acta G-EXT 0.4.0 — los nueve módulos opcionales, comprobados

Fecha de generación: 2026-10-22 · skill `0.4.0`

Este acta **no** es un acta de release de traducción. No cierra G-BETA ni
G-CORE, no aprueba ninguna traducción y no afirma equivalencia semántica.
Registra una sola cosa: que el checklist `G-EXT, cada módulo opcional` del
roadmap se puede marcar porque un gate ejecutable lo comprobó y dejó
evidencia por módulo.

## 1. Qué se comprobó

| Casilla | Cómo se comprobó | Caso negativo |
|---|---|---|
| 1. Activación con corpus | `schemas/profile.schema.json` 1.1.0 exige `corpus_ref` y `justification`; la CLI exige justificación donde el módulo es opt-in | `tests/test_optional_activation.py`, `tests/test_gate_optional.py` |
| 2. Contrato, casos ± y política de fallo | Cada contrato existe y lleva `<!-- version -->`; cada módulo declara **todas** sus pruebas y su entrada con códigos de salida | Un caso por código de salida en `tests/test_gate_optional.py` |
| 3. Regresión del núcleo | Suite completa + dirección de dependencias: ningún script del núcleo importa un módulo opcional sin delegación declarada | `test_el_nucleo_no_importa_modulos_opcionales_sin_declarar` |
| 4. Desactivación sin efectos | `prepare.json`, `segments.json` y `packets.json` byte a byte con el módulo apagado y con el módulo ausente | `tests/test_optional_deactivation.py` |

## 2. Resultado por módulo

| Módulo | Activación | Corpus real | Pruebas del módulo | Gate |
|---|---|---|---|---|
| mdx (061–070) | dormiente | sí, piloto | 10 ficheros | ✅ `reports/optional/mdx.json` |
| html (071–080) | dormiente | no | 11 ficheros | ✅ `reports/optional/html.json` |
| markdown-extensions (081–090) | dormiente | no | 11 ficheros | ✅ `reports/optional/markdown-extensions.json` |
| terminology (091–100) | dormiente | no | 10 ficheros | ✅ `reports/optional/terminology.json` |
| language (101–110) | dormiente | no | 11 ficheros | ✅ `reports/optional/language.json` |
| scale (111–120) | dormiente | sí, declarado sin ejecutar | 10 ficheros | ✅ `reports/optional/scale.json` |
| review (121–130) | dormiente | no | 10 ficheros | ✅ `reports/optional/review.json` |
| delivery (131–140) | dormiente | no | 8 ficheros | ✅ `reports/optional/delivery.json` |
| maintenance (141–150) | opt-in | no | 13 ficheros | ✅ `reports/optional/maintenance.json` |

Cifras del núcleo: `1296 passed, 2 skipped`
(`reports/core/pytest.json`). El gate devuelve 0 solo si la suite del núcleo
está medida y en verde: sin `--core-exit-code` ni `--core-report`, falla con 4.

## 3. Lo que este gate NO midió

- **Equivalencia semántica.** Ninguna casilla lo contempla.
- **El corpus completo.** `/Users/martin/Desktop/documentacion` (4 832 `.md`)
  está declarado en `evals/cases/scale.md` y **no se ha ejecutado**.
- **Importación real en Notion.** `remote_status: no_verificado`.
- **Firma nativa de revisor.** 1 de 3 pares humanos.
- **Windows** (`design_only`) y **variación entre modelos** (una sola corrida
  registrada).

Cada hueco tiene dueño, procedimiento y alcance en `modules.json` →
`known_external_gaps`.

## 4. Activaciones inmotivadas que no se corrigieron

`reports/pilot/profile.json` y `reports/beta/profile.json` activan HTML y
wikilinks sin corpus que lo justifique. Su hash está anclado en el manifiesto
del piloto, así que corregirlos invalidaría G-PILOT (INV-13). Quedan
registradas en `evals/cases/html.md` §1 y en `reports/optional/html.json`.
La medición de 0 ocurrencias en los dos corpus autorizados es la que sostiene
el registro.

## 5. Comandos que reproducen esta acta

```bash
python3 -m pytest tests -q --no-header            # → reports/core/pytest.json
python3 scripts/gate_optional.py \
    --declarations modules.json \
    --core-report reports/core/pytest.json \
    --candidate reports/maintenance/release_candidate.json \
    --evidence-dir reports/optional \
    --out reports/maintenance/gate_optional.json    # → exit 0
python3 scripts/build_release_candidate.py --version 0.4.0 \
    --out reports/maintenance/release_candidate.json
python3 scripts/gate_extended.py --candidate reports/maintenance/release_candidate.json \
    --out reports/maintenance/gate_extended.json
python3 scripts/check_versioning.py --root . --out reports/maintenance/versioning.json
python3 scripts/audit_docs.py --root . --out reports/maintenance/docs_audit.json
```

Todos en código 0 el 2026-10-22. Si alguno deja de estarlo, el acta deja de
servir y hay que rehacerla: no es una lista de intentions.