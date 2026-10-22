<!-- version: 1.0.0 -->

# Protocolo de workers aislados (fase 113)

Un **worker** es una unidad de trabajo que recibe una partición
disjunta de paquetes y devuelve candidatos de traducción para esa
partición. El orquestador (fase 114) es quien escribe el manifiesto.
Este protocolo fija las reglas de aislamiento para que el paralelismo
no rompa el invariante « un segmento solo se aprueba una vez ».

> La fase 113 **no** arranca paralelismo operativo. Solo formaliza
> el protocolo y ofrece un esqueleto ejecutable en serie. La
> ejecución paralela real es decisión del usuario.

## 1. Conjunto disjunto

Cada worker `W_i` recibe una partición `P_i ⊆ {packet_id}` de
forma que:

```
⋃ P_i = {todos los packet_id del scope}
∀ i ≠ j : P_i ∩ P_j = ∅
```

La disyunción la valida el orquestador antes de invocar a los
workers. Si la partición tiene solapamientos, el script
`scripts/coordinator.py` aborta.

## 2. Glosario congelado

- El worker **lee** `glossary.json` solo al inicio.
- Mientras el worker opera, **no modifica** el archivo.
- Al cierre del worker, el orquestador verifica que el hash del
  glosario no haya cambiado. Cualquier cambio invalida los
  candidatos del worker.

## 3. Manifiesto aislado

Cada worker escribe en su subdirectorio:

```
work_root/workers/<worker_id>/
  translations/
    <packet_id>.json   # candidato por paquete
  state.json           # estado local (running, done, failed)
  errors.jsonl         # log de incidentes
```

El worker **no** escribe en el `manifest.json` central. Esa es
responsabilidad del coordinador.

## 4. Mensajería

| Mensaje | Dirección | Contenido |
|---|---|---|
| `dispatch` | orquestador → worker | `worker_id`, `packet_ids[]`, `packet_source`, `out_dir`, `glossary_hash` |
| `candidate` | worker → orquestador | `worker_id`, `packet_id`, `content`, `from_state`, `to_state`, `evidence` |
| `progress` | worker → orquestador | `worker_id`, `packet_id`, `state`, `timestamp` |
| `failure` | worker → orquestador | `worker_id`, `packet_id`, `error`, `recoverable` |

El orquestador usa lock `fcntl.flock` sobre el `manifest.json` para
serializar las escrituras (fase 114).

## 5. Pérdida de un worker

Si un worker `W_i` cae a mitad:

1. Su subdirectorio `work_root/workers/W_i/` queda con los
   candidatos ya entregados.
2. El orquestador registra `W_i` como `failed` en `manifest.json`.
3. El usuario (no el agente) decide si reasignar la partición a
   otro worker o cancelar el lote.

## 6. Lo que el protocolo **NO** hace

- No ejecuta traducción real. El script `scripts/worker.py` es un
  esqueleto que escribe `content: null`.
- No garantiza atomicidad entre dos `dispatch` consecutivos; esa
  garantía corresponde a la **sesión de batch** del orquestador.
- No bloquea el uso de glosarios parciales por worker; un worker
  puede ver solo los términos relevantes para su partición.
- No comparte estado mutable entre workers; cualquier caché se
  reconstruye por worker desde la fuente.
