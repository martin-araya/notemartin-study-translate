<!-- version: 1.0.0 -->

# Contrato de los módulos opcionales (checklist G-EXT)

Todo lo que la skill hace por encima del núcleo es **opcional, apagado por
defecto y verificable**. Este documento define qué tiene que cumplir cada
módulo para poder declararse sustentado, y qué no puede afirmar.

El contrato ejecutable está en tres sitios, y los tres tienen que coincidir:

| Artefacto | Qué fija |
|---|---|
| `modules.json` | la declaración de cada módulo: activación, corpus, contrato, pruebas y política de fallo |
| `schemas/module_declaration.schema.json` | la forma válida de esa declaración |
| `scripts/gate_optional.py` | la comprobación, con un código de salida por casilla |

## 1. Las cuatro casillas

| # | Casilla | Se cumple cuando |
|---|---|---|
| 1 | Activación explícita justificada por un corpus concreto | El módulo es dormiente por defecto; encenderlo exige `corpus_ref` y `justification`, declarados en `modules.json` y, cuando la activación va por perfil, **exigidos por `schemas/profile.schema.json`**; existe un caso en `evals/cases/` con el recuento y el hash de su corpus; y hay un caso negativo que demuestra que no se puede encender sin corpus |
| 2 | Contrato, casos positivos y negativos y política de fallo | Cada documento del contrato existe y lleva `<!-- version: X.Y.Z -->`; **todas** las pruebas del módulo están declaradas en `modules.json` y pasan; la política de fallo existe en código, con entrada y códigos de salida, y el contrato la nombra |
| 3 | Regresión del núcleo intacta | `python3 -m pytest tests -q` en verde; ninguna herramienta del núcleo importa un módulo opcional sin una delegación declarada; ningún script queda sin clasificar |
| 4 | Desactivación sin efectos sobre el flujo básico | La prueba de desactivación del módulo se ejecuta y pasa: con el módulo apagado, el flujo del núcleo se reproduce byte a byte |

Lo no medido no es lo verde. Con `--no-run-tests` el gate marca las
comprobaciones de ejecución como `not_run` y sale con código 5: ese modo sirve
para revisar la estructura de las declaraciones, no para aprobar el gate.

## 2. Códigos de salida de `scripts/gate_optional.py`

| Código | Significado |
|---|---|
| 0 | las nueve declaraciones cumplen las cuatro casillas |
| 1 | activación sin corpus declarado, o el esquema de perfil no lo exige |
| 2 | contrato ausente, sin marca de versión, o política de fallo sin entrada ni códigos |
| 3 | pruebas del módulo sin declarar, pruebas declaradas que no existen, o pruebas del módulo en rojo |
| 4 | regresión del núcleo no medida, en rojo, o con una dependencia inversa sin declarar |
| 5 | la prueba de desactivación falla, o no se ejecutó |
| 6 | el candidato de release contradice la declaración |
| 7 | las declaraciones no se leen o no validan contra el esquema |

## 3. Qué es una «delegación declarada»

Hay dos dependencias legítimas del núcleo hacia un módulo opcional, y las dos
se declaran en `modules.json` (`core_delegations`) con su motivo:

- **`kind: detector`** — `scripts/prepare.py` importa librerías **puras**
  (`mdx_selector`, `html_parser`, `admonitions`, `directives`,
  `mermaid_adapter`) para reconocer una construcción y bloquearla cuando el
  módulo está apagado. Sin ese conocimiento el núcleo dejaría pasar, en
  silencio, exactamente lo que el módulo existe para tratar. No importa
  ninguna CLI ni estado del módulo.
- **`kind: regression`** — `scripts/regression_detectors.py` delega en los
  detectores de producción para no reimplementarlos. Solo corre al pasar el
  gate de release, nunca durante una traducción.

Cualquier otra dependencia del núcleo hacia un módulo es un defecto y el gate
sale con código 4. El caso que motivó la regla: el núcleo importaba
`detect_residual_language` (fase 126) y `check_approval_freshness` (fase
124), así que apagar el módulo de revisión rompía la verificación de
`already_target` y la promoción de aprobaciones. Las primitivas se movieron a
`scripts/text_signals.py` y `scripts/approval_freshness.py`, que son núcleo.

## 4. Correr el gate

```bash
python3 scripts/gate_optional.py \
    --declarations modules.json \
    --core-report reports/core/pytest.json \
    --candidate reports/maintenance/release_candidate.json \
    --out reports/maintenance/gate_optional.json
```

| Flag | Para qué |
|---|---|
| `--core-exit-code N` | código de salida de la suite del núcleo, si ya lo conoces |
| `--core-report PATH` | JSON con `exit_code` de la corrida del núcleo |
| `--candidate PATH` | contrasta la declaración con el candidato de release |
| `--no-run-tests` | pase estructural; el gate sale con 5 a propósito |

Sin `--core-exit-code` ni `--core-report`, la casilla 3 no está medida: el
gate falla. Es intencional; «no lo medí» no es «está bien».

## 5. Perfiles históricos

`reports/pilot/profile.json` y `reports/beta/profile.json` activan módulos sin
`corpus_ref` porque el esquema todavía no lo exigía. **No se corrigen**: su
hash está anclado en `reports/pilot/manifest.json`, y tocarlo invalidaría la
aprobación de G-PILOT (INV-13). Cada activación inmotivada queda declarada en
`evals/cases/<módulo>.md` con su archivo y su línea.

La herramienta para llevar un perfil antiguo al contrato es
`scripts/migrate_profile.py`, que añade `corpus_ref` y `justification` desde
el caso correspondiente sin tocar ningún otro valor.

## 6. Lo que este contrato no dice

- **No** afirma que un módulo con sus cuatro casillas en verde sirva para un
  corpus cualquiera. Cada caso dice sobre qué corpus se midió.
- **No** afirma equivalencia semántica de ninguna traducción.
- **No** sustituye a los huecos externos declarados por módulo en
  `known_external_gaps`: importación real en Notion, firma nativa, segunda
  ejecución de modelo, ejecución en Windows y ejecución del corpus grande.
  Bloquean la afirmación que describen, no el gate local.