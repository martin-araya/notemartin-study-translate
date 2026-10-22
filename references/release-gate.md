<!-- version: 1.0.0 -->

# Gate del release ampliado (fase 149)

El release 0.2.0 activa nueve módulos que antes no formaban parte de la
entrega más que el núcleo. Un candidato sin gate por módulo es un candidato
que no sabe qué demuestra. Este documento explica qué exige el gate y qué
significa cada código.

## 1. Qué hace un gate

`scripts/gate_extended.py` no comprueba el código del proyecto: comprueba
que las **afirmaciones** del candidato estén respaldadas. Corre sobre el
candidato (`reports/maintenance/release_candidate.json`) y sobre los
informes que las demás fases dejaron en `reports/maintenance/`.

| Código | Comprobación | Fase |
|---|---|---|
| 1 | regresión permanente sin huecos y reproducible con pytest | 141 |
| 2 | versionado coherente | 142 |
| 3 | ningún manifiesto sin `manifest_version`, ninguna aprobación vigente tras migrar | 143 |
| 4 | parser: promoción bloqueada sin dependientes declarados | 144 |
| 5 | el candidato no afirma verificación remota fuera de la lista de huecos | 145 |
| 6 | auditoría documental limpia | 146 |
| 7 | ninguna fila `verified` sin evidencia ni fecha de ejecución | 147 |
| 8 | política de retención presente y purgas con trazabilidad | 148 |
| 9 | suite del núcleo en verde | 059/060 |
| 0 | todo lo interno en verde | — |

## 2. Huecos externos: qué son y qué no son

Un hueco externo es evidencia que **no existe** y que depende de una persona
o de un sistema fuera del repositorio: importar de verdad en Notion, una
firma de revisor nativo, una segunda ejecución de modelo, una máquina con
Windows.

Los huecos externos **no** hacen fallar el gate. Hacen otra cosa: aparecen
en `open_external_items` con identificador, fases, motivo, responsable,
procedimiento para cerrarlos y el alcance que bloquean:

| Alcance | Qué bloquea |
|---|---|
| `remote_verification_claim` | afirmar que algo está importado o verificado en un destino |
| `human_signature` | afirmar que una persona revisó o firmó algo |

Lo que sí hace fallar al gate es **mentir**: declarar `verified` sin
evidencia, afirmar una verificación remota fuera de la lista de huecos, o
declarar un módulo activo sin gate. Esa es la diferencia entre una fase
abierta y una afirmación falsa.

## 3. Construcción del candidato

```bash
python3 scripts/build_release_candidate.py --root . --version 0.2.0 \
    --out reports/maintenance/release_candidate.json

python3 scripts/gate_extended.py \
    --candidate reports/maintenance/release_candidate.json \
    --out reports/maintenance/gate_extended.json
```

El candidato se valida contra `schemas/release_candidate.schema.json`. Si no
valida, la herramienta no escribe nada y sale con código 2.

Cada módulo lleva su comando de gate, su código de salida **real** y la cola
de la salida (`gate_detail`), también cuando pasa. Un módulo que pasa sin
que se vea su salida es un módulo que nadie puede auditar.

## 4. Inventario de módulos del 0.2.0

| Módulo | Fases | Gate |
|---|---|---|
| `core` | 001–060 | `python3 -m pytest tests/ -q` + `scripts/check_distribution.py` |
| `mdx` | 061–070 | `tests/test_mdx_gate.py` |
| `html` | 071–080 | `tests/test_html_gate.py` + `tests/test_html_release_gate.py` |
| `markdown-extensions` | 081–090 | `tests/test_extension_combinations.py` |
| `terminology` | 091–100 | perfiles, precedencia y procedencia de términos |
| `language` | 101–110 | matriz de idioma y evaluación fr→es |
| `scale` | 111–120 | gate de escala y reserva en serie |
| `review` | 121–130 | gate de revisión |
| `delivery` | 131–140 | gate de entrega |
| `maintenance` | 141–150 | este gate |

## 5. Lo que NO es requisito de este release

`not_required[]` declara las opciones desactivadas para que no se conviertan
en requisitos ocultos: `delivery.enabled`, `html.enabled`,
`mixed_profile.enabled`, `rtl.enabled`, etiquetas Mermaid y frontmatter
traducible. Ninguna se activa por declarar un módulo activo: activar un
módulo es una decisión de perfil, no de release.

## 6. Qué NO demuestra un gate en verde

- **No demuestra que la traducción sea buena.** Los gates son deterministas.
- **No demuestra que algo esté importado en un destino.** Por definición:
  esa evidencia no existe todavía.
- **No demuestra que la salida del modelo sea reproducible.**
- **No demuestra que el corpus completo se procese bien.** La escala está
  medida sobre una muestra.
- **No cierra los huecos externos.** Solo los hace visibles y exigibles.

## 7. Relación con otras fases

| Fase | Relación |
|---|---|
| 059 | `test_release.py` genera las notas de release; este gate las valida |
| 140 | el gate de entrega es el gate propio del módulo `delivery` |
| 149 | entregable de esta fase |
| 150 | el acta enumera los códigos de salida reales y los huecos externos |