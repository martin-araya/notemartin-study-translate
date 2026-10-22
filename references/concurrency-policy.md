<!-- version: 1.1.0 -->

# Política de concurrencia y recursos (fase 116)

Esta política decide cómo la skill `notemartin-study-translate` lanza
workers cuando el usuario activa el modo concurrente. Se aplica
junto a `references/worker-protocol.md` (fase 113) y a la política
de fallback serie (fase 117).

> El modo concurrente **no** se activa por defecto. Es una
> decisión del usuario. Cuando se activa, esta política aplica.

## 1. Modelo de paralelismo

El modo concurrente usa `concurrent.futures.ThreadPoolExecutor`.
La elección de hilos frente a procesos se justifica porque la cadena
del núcleo es de lectura de disco y serialización JSON: el GIL se
libera en cada `read()` y en cada `json.dumps()`. Multiprocessing
aporta poco a CPU-bound y complica el lock `fcntl.flock` del
manifiesto.

## 2. Límites

| Parámetro | Valor por defecto | Razón |
|---|---|---|
| `max_workers` | `min(8, os.cpu_count() or 1)` | Evita saturar un sistema pequeño. |

Si el sistema reporta `cpu_count == 1`, el modo concurrente se
rechaza y se sugiere el modo serie. Esa elección la aplica el
script `scripts/run_concurrent.py`, no la agente. Con
`--allow-single-cpu` se acepta, que es lo que usan las pruebas.

Los parámetros `max_queue_depth`, `min_workers`, `backoff_initial_sec`,
`backoff_max_sec` y `backoff_max_retries` **no están implementados**. Una
versión anterior de este documento los daba por vigentes y describía un
mecanismo de pausa y reintento que el código no ejecuta. Están aquí como
deuda declarada, no como política: nadie puede ajustar un backoff que no
existe.

## 3. Saturación y pausa segura

Lo que sí hace el orquestador hoy:

1. Atiende la admisión de particiones en un `ThreadPoolExecutor` acotado por
   `max_workers`, sin cola intermedia.
2. Espera cada worker con un tiempo máximo de 300 s; un worker que no
   responde se registra como `worker_error` y se sigue con los demás.
3. No descarta candidatos ya escritos: viven en el subdirectorio del worker
   y se leen después.
4. Propaga `--content-dir` a cada worker y **solo aprueba** los paquetes con
   traducción real entregada. Los que quedan como `pending_translation`
   aparecen en `pending_segment_ids` del manifiesto.

Lo que no hace: pausar por saturación de cola, consultar `shutil.disk_usage`,
aplicar backoff exponencial ni reintentar un worker caído. La política de
pausa segura real es la de la fase 117: pausa por señal y conservación de lo
escrito.

## 4. Cancelación

Al recibir `SIGINT` (Ctrl-C) o `SIGTERM`:

1. El orquestador avisa a todos los hilos.
2. Cada hilo termina el paquete actual antes de salir.
3. `executor.shutdown(wait=True)` espera a todos los hilos.
4. Se vuelca `reports/concurrency_log.json` con cada cierre
   limpio (`graceful_shutdown`) y cada hilo interrumpido
   (`interrupted_before_next_packet`).

## 5. No pérdida

Any candidato escrito por un worker **queda** en disco. La
cancelación no borra `translations/<packet_id>.json`. El orquestador los
recoge después, sin importar si el worker murió a mitad.

## 6. Procedimiento

```text
run_concurrent.py
  ├─ divide packets.json en N particiones disjuntas
  ├─ por cada partición, llama a worker.py con --id W{i}
  │    (propaga --glossary y --content-dir)
  ├─ espera cada worker (máx. 300 s) y registra worker_error si expira
  ├─ lee el estado y los candidatos de cada worker
  ├─ aprueba solo los paquetes con traducción real; el resto queda pendiente
  ├─ al cierre, vuelca reports/concurrency_log.json
  └─ al interrumpir, vuelca un partial y sale con código 130
```

Lo que este procedimiento **no** hace, frente a lo que este mismo documento
describía antes: los workers no reclaman `segment_id` al coordinador con
`claim` (eso lo ofrece `scripts/coordinator.py` como herramienta aparte, no
como paso de este orquestador), y no hay cola FIFO. El reparto es por
partición, no por reserva.

## 7. Lo que esta política **NO** hace

- No sustituye al coordinador. El lock sigue siendo
  `coordinator.py claim`; la fase 116 solo añade el reparto concurrente.
- No implementa backoff, pausa por saturación ni reintentos (§2 y §3).
- No promete que el modo concurrente sea más rápido. La
  velocidad depende del sistema y del corpus.
- No replica el manifiesto en otro proceso. Cada hilo escribe su
  `translations/` y el coordinador centraliza.
- No asume invariantes de proveedor.
