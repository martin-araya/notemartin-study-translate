<!-- version: 1.0.0 -->

# Evaluación de una actualización del parser (fase 144)

La política del contrato Markdown dice que cualquier cambio de versión del
parser exige reejecutar la verificación sobre el piloto. Esta fase convierte
esa frase en un procedimiento ejecutable: `scripts/compare_parser.py`.

## 1. Qué se compara

Por cada documento del corpus, el comparador extrae:

| Feature | Para qué sirve detectarla |
|---|---|
| rangos de línea de cada token con `map` | los `segment_id` y los parches de ensamblado dependen de ellos |
| slugs de cada encabezado | de ellos dependen `anchors.json` y la reescritura de fragmentos |
| conteo de tokens y tokens con `map` | un cambio aquí significa que la candidata interpreta el documento de otra forma |
| número de líneas, bloques fenced y código inline | control de que el dialecto se sigue leyendo igual |

## 2. Regla de promoción

La promoción se permite **solo** si `changed_ranges`, `changed_slugs` y
`changed_counts` están vacíos a la vez.

La aceptación de la fase exige bloquear cuando cambian rangos o slugs. Aquí
se bloquea también ante un cambio de recuento: es la regla más estricta y es
la que se aplica, porque un recuento distinto implica una interpretación
distinta aunque los rangos declarados coincidan.

Cuando queda bloqueada, el informe lista `dependents_to_migrate`:

- `anchors.json` y los fragmentos reescritos,
- `segments/` (los `segment_id` dependen de los rangos),
- `translations/` de las ejecuciones ya hechas,
- la caché de traducción, cuyas entradas fijan la versión del parser,
- `reports/` derivados del pase determinista.

## 3. Procedimiento

```bash
# 1. entorno aislado con la versión candidata
python3 -m venv /tmp/nst-parser-alt
/tmp/nst-parser-alt/bin/pip install "markdown-it-py==X.Y.Z"

# 2. comparación real sobre el corpus piloto
python3 scripts/compare_parser.py \
    --corpus tests/fixtures/pilot \
    --candidate-interpreter /tmp/nst-parser-alt/bin/python \
    --out reports/maintenance/parser_comparison.json
```

La venv vive fuera del repositorio y **no** se añade a `requirements.txt`:
la versión fijada del contrato sigue siendo la del núcleo.

| Código | Significado |
|---|---|
| 0 | promoción permitida |
| 2 | corpus inválido |
| 3 | la sonda falló con un intérprete |
| 4 | promoción bloqueada: cambiaron rangos, slugs o recuentos |
| 5 | la versión candidata no está instalada |

## 4. Ejecución real registrada

```text
promotion: allowed
baseline_parser: 3.0.0   candidate_parser: 2.2.0
documents_compared: 9
changed_ranges: []  changed_slugs: []  changed_counts: []
alternate_installed: true
informe: reports/maintenance/parser_comparison.json
```

Qué demuestra y qué no:

- **Demuestra** que el comparador funciona contra una segunda versión
  realmente instalada y que, sobre el corpus piloto de 9 documentos,
  `2.2.0` y `3.0.0` producen los mismos rangos, slugs y recuentos.
- **No demuestra** que la comparación cubra todo el corpus real, ni que
  otra versión dé el mismo resultado. El corpus piloto es una muestra.
- **No es una promoción.** No se cambió la versión fijada. Al ejecutar
  `pip install` se comprobó que **no existe una versión publicada posterior
  a la 3.0.0**, así que hoy no hay candidata de mejora que evaluar. La
  comparación registrada es entre la fijada y la anterior, y sirve como
  prueba de que el procedimiento funciona, no como aprobación de un salto
  de versión.

Si en el futuro aparece una versión nueva, el procedimiento es el mismo y
el resultado solo se acepta con `promotion: allowed` **y** los dependents
sin cambios.

## 5. Pruebas del mecanismo

`tests/test_compare_parser.py` no necesita red: usa adaptadores de
`tests/fixtures/parser_alt/` que simulan una versión con los rangos
desplazados, con un slug distinto y con un recuento distinto.

| Adaptador | Simula | Resultado exigido |
|---|---|---|
| `ranges_shift.py` | una línea de desplazamiento por rango | bloqueado |
| `slug_change.py` | un slug distinto para el mismo encabezado | bloqueado |
| `counts_shift.py` | un recuento distinto sin tocar rangos | bloqueado |

Un baseline comparado consigo mismo debe dar `allowed`: si no, el
comparador estaría bloqueando por su cuenta.

## 6. Relación con otras fases

| Fase | Relación |
|---|---|
| 014 | este comparador es la ejecución continua de la decisión de parser |
| 038 | `anchors.json` es el primer dependiente que hay que migrar |
| 055 | el invalidador selectivo marca los segmentos afectados al cambiar rangos |
| 118 | las entradas de caché fijan la versión del parser en su clave |
| 142 | `release_contract.json.parser.pinned` y `check_versioning.py` comprueban que el contrato y `markdown-contract.md` digan lo mismo |