<!-- version: 1.0.0 -->

# Corpus permanente de regresión (fase 141)

Un fallo conocido que nadie puede reproducir deja de estar cubierto en la
siguiente versión. Esta fase convierte esa cobertura en un artefacto
versionado: `evals/regression/registry.json` declara, para cada fallo, un
**caso positivo** (que no debe generar hallazgo) y un **caso negativo**
(que sí debe generarlo), ambos reproducibles con `pytest`.

## 1. Estructura

```text
evals/regression/registry.json          # registro canónico
evals/regression/PROVENANCE.md          # origen y autorización de cada caso
schemas/regression_registry.schema.json  # contrato del registro
tests/fixtures/regression/*.json        # un fixture por fallo conocido
scripts/regression_detectors.py         # detectores puros
scripts/regression_gate.py              # gate con códigos de salida
tests/test_regression_cases.py          # ejecuta cada par positivo/negativo
tests/test_regression_registry.py       # integridad del registro y del gate
```

## 2. Fallos cubiertos

| Fallo | Origen | Detector | Severidad |
|---|---|---|---|
| `negation_inverted` | 52 | `negation_preserved` | major |
| `list_omission` | 52 | `structure_preserved` | critical |
| `command_altered` | 17, 52 | `literals_preserved` | critical |
| `table_trimmed` | 36, 52 | `structure_preserved` | critical |
| `prompt_injection` | 51 | `injected_instructions` | critical |
| `dangerous_links` | 51 | `unsafe_link_target` | critical |
| `path_traversal` | 12, 51 | `path_escapes_root` | critical |
| `script_block` | 51, 77 | `active_html_outside_code` | major |
| `anchor_collision` | 54 | `slug_collision` (`build_anchors.github_slug`) | major |
| `slug_truncation` | 54 | `slug_truncated` (`build_anchors.github_slug`) | major |
| `ambiguous_link` | 39, 54 | `fragment_resolution` (`build_anchors.github_slug`) | major |
| `foreign_segment_id` | 34 | `segment_ids_known` | critical |
| `extra_marker` | 22, 34 | `markers_wellformed` | critical |
| `truncated_response` | 34 | `all_segments_present` | critical |
| `cache_incompatible_reuse` | 118 | `cache_probe_compatible` (`translation_cache.key_short`) | critical |
| `stale_cache_on_glossary_change` | 119 | `cache_invalidated` | critical |
| `stale_approval` | 124 | `approval_fresh` (`check_approval_freshness.evaluate`) | critical |
| `package_member_not_declared` | 136 | `package_members_declared` | critical |
| `package_path_escape` | 136 | `package_member_safe` (`validate_zip_package.is_unsafe_path`) | critical |
| `delivery_content_loss` | 138 | `delivery_loss` (`compare_delivery.compare_documents`) | critical |
| `export_without_approval` | 47, 56 | `export_state_allowed` | critical |
| `route_collision_case_only` | 12 | `case_insensitive_collision` | major |

Un detector entre paréntesis delega en una implementación que ya existe en
otro script del proyecto: el registro no crea una segunda verdad.

## 3. Uso del gate

```bash
python3 scripts/regression_gate.py \
    --registry evals/regression/registry.json \
    --out reports/maintenance/regression.json

python3 scripts/regression_gate.py --reproduce \
    --out reports/maintenance/regression.json
```

`--reproduce` ejecuta los nodeids declarados en un subproceso y exige que
pasen. Sin ese flag el gate solo comprueba la integridad del registro, que
es lo que permite invocarlo desde dentro de una suite sin recursión.

| Código | Significado |
|---|---|
| 1 | estructura o esquema inválido, o `case_id` duplicado |
| 2 | el fixture del caso positivo no existe |
| 3 | el fixture del caso negativo no existe |
| 4 | el nodeid del caso positivo no existe |
| 5 | el nodeid del caso negativo no existe |
| 6 | procedencia ausente o incompleta |
| 7 | un fallo conocido no tiene entrada en el registro |
| 8 | la variante declarada no existe dentro del fixture |
| 9 | `--reproduce` falló: el registro no es reproducible |

## 4. Qué NO demuestra este registro

- **No demuestra equivalencia semántica.** Un par positivo/negativo
  comprueba que un detector distingue un caso del otro, no que la
  traducción sea correcta. La revisión semántica es otra fase (042, 115).
- **No sustituye a los validadores de producción.** Los detectores de
  `scripts/regression_detectors.py` son comprobaciones mínimas escritas para
  el registro; cuando existe un validador real se delega en él.
- **No cubre el corpus autorizado.** El registro usa material sintético.
  Los defectos que solo aparecen en la prosa real del corpus se detectan
  en la ejecución, no aquí.
- **No es una puerta de la suite.** `pytest` ejecuta los pares; el gate
  comprueba que el registro no se degrade. Un gate en verde con una suite
  roja es una contradicción que hay que resolver en las dos.

## 5. Relación con otras fases

| Fase | Relación |
|---|---|
| 052 | aporta los cuatro fallos de fidelidad que el registro conserva |
| 129 | los detectores devuelven identificadores y conteos, no prosa completa del corpus |
| 141 | este registro es su entregable |
| 149 | `gate_extended.py` ejecuta este gate como parte del módulo `maintenance` |