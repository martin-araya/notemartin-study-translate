<!-- version: 1.0.0 -->

# Variación entre modelos (fase 145)

Medir cuánto cambia la traducción cuando cambia el modelo es útil para
saber cuánto depende el resultado de una decisión de proveedor. No es una
prueba de corrección: es una medida de dispersión.

La aceptación de la fase tiene dos mitades y las dos importan:

1. **Registrar ejecuciones reales.** El registro lo produce
   `scripts/record_model_run.py` sobre un `work_root` existente.
2. **No comparar respuestas sintéticas con producción.** El comparador
   rechaza cualquier registro que no sea `real_runs`.

## 1. Qué guarda el registro

`scripts/record_model_run.py` escribe en
`reports/maintenance/model_runs/<run_id>.json`:

| Campo | Para qué |
|---|---|
| `model`, `provider`, `prompt_version` | qué produjo la traducción |
| `glossary_hash`, `profile_hash`, `parser`, `anchor_policy`, `skill_version` | con qué contexto |
| `source_hashes` | sobre qué archivos |
| `segments[].sha256`, `.chars`, `.markers` | medida de la respuesta |
| `segments[].preview` | vista truncada para inspección rápida |
| `evidence_kind`, `synthetic` | si la ejecución fue real o declarada sintética |
| `problems` | traducciones ilegibles encontradas al registrar |

**El texto traducido no se copia a `reports/`.** Vive en el `work_root`, que
es donde debe estar. El registro lleva `texts_stored: false` para que nadie
lo confunda con una copia.

| Código | Significado |
|---|---|
| 2 | el run no tiene manifiesto legible |
| 3 | evidencia sintética sin `--allow-synthetic` |
| 4 | el manifiesto no declara modelo, prompt, glosario o perfil |

## 2. Qué compara el script

`scripts/compare_model_runs.py` exige, antes de comparar:

- `evidence_kind == "real_runs"` en los dos lados,
- el mismo `prompt_version`, `glossary_hash` y `profile_hash`,
- el mismo `parser`, `anchor_policy` y `skill_version`,
- los mismos `source_hashes`.

Si algo no cuadra, **no** produce una comparación: escribe el motivo y
termina. Comparar dos ejecuciones con glosarios distintos no mide
variación del modelo, mide otra cosa.

Después calcula, por segmento: respuesta idéntica, divergente o ausente en
alguno de los dos lados, y agrega `variation_rate`.

La razón de longitudes se emite siempre con `signal_only: true` y su propio
`meaning`. Una razón de longitud no demuestra equivalencia semántica, y el
informe lleva `no_semantic_claim: true` para que nadie pueda citarlo como si
la demostrara.

| Código | Significado |
|---|---|
| 0 | comparación hecha |
| 2 | un registro no es legible |
| 3 | algún registro no es una ejecución real |
| 5 | difieren prompt, glosario, perfil, parser o hashes de fuente |

## 3. Línea base registrada

```text
run_id: run-0000d3mo
modelo: kilo / minimax-coding-plan/MiniMax-M3   (modelo activo de la sesión)
prompt_version: 1.0.0
segmentos: 10 de prosa del documento piloto typescriptlang/handbook/2/functions.md
evidence: real_runs
registro: reports/maintenance/model_runs/run-0000d3mo.json
```

Qué es y qué no es esa línea base:

- **Es** una traducción real hecha por el modelo activo en esta sesión,
  sobre prosa real del corpus autorizado, con los literales protegidos
  intactos.
- **No es** una ejecución completa del corpus: son 10 segmentos de un
  documento. Su propósito es tener un punto de partida verificable.
- **No se versiona el texto.** El `work_root` con la traducción vive fuera
  del repositorio; al repositorio solo llega el registro de metadatos.

## 4. Cómo cerrar la fase con un segundo modelo

La fase queda `✅ ⚠` hasta que existan **dos** ejecuciones reales
comparables. Para añadir la segunda:

1. Ejecutar la traducción con otro modelo sobre el mismo corpus piloto,
   con el mismo `prompt_version`, el mismo glosario congelado y el mismo
   perfil. Guardar su `work_root` fuera del repositorio.
2. Registrarlo con `record_model_run.py --evidence real`.
3. Comparar:

   ```bash
   python scripts/compare_model_runs.py \
       --run-a reports/maintenance/model_runs/run-0000d3mo.json \
       --run-b reports/maintenance/model_runs/<run_b>.json \
       --out reports/maintenance/model_variation.json
   ```

Mientras no exista ese segundo registro, `model_variation.json` no se puede
emitir y la fila del roadmap lleva aviso. Un informe comparando la línea base
consigo misma **no** cierra la fase: sería variación cero por construcción,
no una medición.

## 5. Qué NO demuestra esta fase

- **No demuestra que un modelo sea mejor que otro.** Solo mide cuánto
  cambia la salida. La calidad se evalúa con la rúbrica, no con una tasa de
  divergencia.
- **No mide estabilidad temporal.** Dos ejecuciones del mismo modelo en
  fechas distintas también divergen; eso no se ha medido aquí.
- **No cubre el corpus completo.** La línea base son 10 segmentos.
- **No valida el texto.** Un registro puede ser real y estar mal traducido.

## 6. Relación con otras fases

| Fase | Relación |
|---|---|
| 111 | `measure_execution.py` mide tiempo y coste; esta mide dispersión |
| 124 | la vigencia de una aprobación depende de `target_hash`, no del modelo |
| 129 | el registro usa `redact.truncate_for_log` para las vistas previas |
| 145 | entregable de esta fase |
| 149 | el gate extendido falla si alguien declara variación sin dos ejecuciones reales |