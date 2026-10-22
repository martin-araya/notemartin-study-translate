<!-- version: 1.1.0 -->

# Fallback en serie equivalente (fase 117)

Esta política fija el **modo serie** como fallback permanente del
modo concurrente. El modo serie **no** desaparece cuando se activa
el paralelismo: garantiza que la skill sigue produciendo el mismo
ledger si los workers fallan, si `fcntl.flock` no está disponible,
o si el usuario decide explícitamente desactivar la concurrencia.

> El modo serie es el valor por defecto. El modo concurrente
> (fase 116) requiere invocación explícita del orquestador.

## 1. Equivalencia de ledger

El ledger de un run es la lista de `segment_id` aprobados por el
orquestador. Dos runs sobre la misma entrada producen el mismo
ledger si y solo si:

1. Los `packets.json` son idénticos.
2. El `glossary.json` congelado es idéntico.
3. El `locale.variant` activo es idéntico.
4. La política de review (`review_mode`) es idéntica.

Un modo serie y un modo concurrente que cumplan 1–4 producen
**el mismo ledger**. La diferencia observable entre ellos es solo
técnica (modo de ejecución, timestamps, hilos).

## 2. Procedimiento del modo serie

1. `scripts/schedule_packets.py` produce el orden topológico.
2. `scripts/run_serial.py` recorre el orden en serie.
3. Por cada `packet_id`, llama a `scripts/worker.py` con
   `--id serial` y la partición de un único elemento.
4. Cada candidato se firma con `mode: serial` en el `state.json`.

## 3. Procedimiento del modo concurrente

1. Mismo plan de orden topológico.
2. Los paquetes se dividen entre N hilos que comparten el
   coordinador (`scripts/coordinator.py claim`).
3. Cada candidato se firma con `mode: concurrent` y
   `mode_thread_id: <id>`.

## 4. Comparación

`scripts/diff_ledgers.py` toma dos `manifest.json` y reporta:

- `only_in_a`: `segment_id` aprobados solo en `a`.
- `only_in_b`: `segment_id` aprobados solo en `b`.
- `state_distribution_a` y `state_distribution_b`: histogramas de
  `current_state` de cada lado.

Lo que **no** hace: comparar el `current_state` segmento a segmento. Es
decir, no existe un campo `conflicts_state`. Una versión anterior de este
documento lo prometía; el código no lo implementa y el gate 120 no lo usa. Un
documento que promete un campo que la herramienta no escribe convierte una
auditoría en una lectura de adivinanzas. Si algún día hace falta, se implementa
primero y se documenta después.

El gate 120 (`scripts/gate_scale.py`) compara los dos conjuntos de
`approved_segment_ids` directamente. La auditoría completa con
`--strict` la hace `diff_ledgers.py`, que devuelve código 1 si algún
`segment_id` aprobado aparece en un lado y no en el otro.

## 5. Lo que la equivalencia **NO** garantiza

- No garantiza tiempo de ejecución. El concurrente puede ser
  más rápido o más lento.
- No garantiza orden de aprobación. La cola FIFO produce el
  mismo orden aproximado, pero timestamps difieren.
- No garantiza identidad de `metadata.mode`. Eso es justo lo
  que difiere; ambos modos firman su identidad.
- No certifica fidelidad semántica. La equivalencia es **de
  forma**: los mismos `segment_id` aprueban en uno y otro modo.
  El contenido se trata por separado con la rúbrica de revisión.

## 6. Recuperación ante fallo del concurrente

Si la corrida concurrente aborta:

1. El orquestador detecta `coordination.log` con
   `graceful_shutdown` o errores irrecuperables.
2. Pasa a `mode: serial` con el mismo `packet_schedule.json`.
3. Las entradas ya escritas por los workers quedan; las restantes
   se completan en serie.
4. El gate 120 se evalúa sobre el resultado final (concurrente
   parcial + serie compensatorio).
