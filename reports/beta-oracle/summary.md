# `oracle/resúmenes/` — ronda 4 multi-sesión

Run: `run-deadbeef` · Fecha: 2026-10-21 · Estado: **gate T4..T8 cerrado en `oracle/resúmenes/` incluyendo `copy_resources`**

Esta ronda cierra la única rebanada del alcance que tiene recursos
binarios reales: las 66 imágenes de los capítulos de Oracle AI Vector
Search. A diferencia de las anteriores, **no hay traducción** a hacer
porque el corpus ya está escrito en español. Lo que demuestra esta
ronda es la tubería de `copy_resources.py` con su cadena SHA-256
verificada, que no se había ejercitado todavía.

## 1. Lo que demuestra

| Etapa | Producto | Resultado |
|---|---|---|
| T2 (preparación) | Inventario + prepare | 17 `.md` + 66 imágenes, 47,28 MB, 3 178 segmentos, 216 paquetes |
| T4 (traducción) | `translate_pilot --mode identity` | 17 archivos en identidad (corpus en español, técnico preservado por glosario v3) |
| T5 (assemble) | `assemble.py` por documento | 17 `.md` ensamblados |
| T5' (copy_resources) | `copy_resources.py` | **66 imágenes copiadas con verificación SHA-256**, 0 mismatches, 0 missing |
| T6 (validación) | `validate.py --require-assembled` | 0 errores en structure, protection, destinations, coverage, source-debt |
| T7 (integridad) | `check_integrity.py` | `integrity_ok=True`, 17/17 dispositionado como `already_target` |
| T8 (export) | `output/run-deadbeef/` | 17 `.md` + 66 imágenes + `output_hashes.json` (83 archivos) |

## 2. Lo que demuestra la cadena de recursos

La pieza de valor de esta ronda es la ejecución de `copy_resources.py`
sobre 66 imágenes reales:

```
copied: 66
mismatches: 0
missing: 0
external: 0
```

Cada imagen en la fuente tiene su SHA-256 (porque `inventory.py` ya lo
calcula). `copy_resources.py` la copia byte-a-byte al destino y
verifica el SHA-256 de cada byte copiado. Si el cache del build
anterior ya está presente, el script lo detecta y rehúsa el SHA; si
hubiera drift, lo reportaría como `mismatches`. La cadena cierra sin
errores ni drift.

Cada `output_hashes.json` lleva el SHA-256 de los 83 archivos
entregados, de modo que cualquier intento de exportación posterior
detecta exactamente qué bytes cambiaron.

## 3. Lo que NO demuestra

- **Traducción**: este corpus ya estaba en español. No hubo prosa a
  traducir más allá de los términos técnicos (`PL/SQL`, `HNSW`, `IVF`,
  `FLOAT32`, `BINARY`, etc.) que el glosario v3 conserva como
  `keep-original`.
- **Verificación en Notion**: sigue sin hacerse. `remote_status:
  no_verificado`.

## 4. Disposición por estado

| Estado | Cuenta | Motivo |
|---|---|---|
| `already_target` | **17** | El corpus está en español. Los términos técnicos Oracle (`PL/SQL`, modelos, métricas, índices) se preservan por glosario v3. |

Cobertura: 17/17 integrado (100%). `integrity_ok=True`.

## 5. Volumen medido

| Métrica | Valor |
|---|---|
| Archivos `.md` | 17 |
| Imágenes | 66 |
| Bytes totales | 47,28 MB |
| Segmentos | 3 178 |
| Traducibles (`disposition=translatable`) | 1 240 |
| `already_target` | 1 014 |
| Paquetes | 216 |
| Overflow de paquete | 10 |
| Suite de tests | 1 037 pasan, 2 omitidas |

## 6. Próximas rondas

```
Ronda 5: angular/api/forms (~50 archivos)
Ronda 6: angular/api/cdk + animations + core + ...
         También angular/guide/, tutorial/, errors/
Ronda 7: nextjs/app/, pages/, architecture/, messages/
```

Cada ronda aplica el patrón demostrado en las anteriores: filtrado del
alcance, ejecución de la tubería, `translation_passN.py` curada o `pass1` de
identidad, `rehydrate_literals.py` cuando hay literales adyacentes,
`validate --require-assembled`, `export` con `output_hashes.json`.