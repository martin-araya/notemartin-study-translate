# `angular/api/router/` — ronda 2 del barrido multi-sesión

Run: `run-deadbeef` · Fecha: 2026-10-21 · Estado: **gate T4..T8 cerrado en `angular/api/router/`**

Esta ronda continúa el barrido multi-sesión iniciado en
`angular/api/common/` con el primer paso real de traducción. Sobre
149 archivos de `api/router/` (más `api/index.md`) se aplicaron 215
traducciones castellanas focales; se rehidrataron 221 literales
para respetar el barrido `§§LITERAL§§`; y el gate cierra con 0
errores de validación y `integrity_ok=True`.

## 1. Lo que demuestra

| Etapa | Producto | Resultado |
|---|---|---|
| T2 (preparación) | Inventario + prepare | 150 archivos, 3 644 segmentos, 208 paquetes |
| T4 (traducción) | `translate_pass3.py` | 215 entradas traducidas a mano sobre la prosa de los API más sustantivos |
| T4' (rehidratación) | `rehydrate_literals.py` | 221 literales (§§LIT§§) reincorporados — la prosa adyacente retuvo el source verbatim para no perder protecciones |
| T5 (assemble) | `assemble.py` por archivo | 150 archivos `.md` ensamblados |
| T6 (validación) | `validate.py --require-assembled` | 0 errores (estructura, protección, destinations, coverage, source-debt) |
| T7 (integridad) | `check_integrity.py` | `integrity_ok=True`, 150/150 dispositionados como `translated` |
| T8 (export) | Assembly con `output_hashes.json` | 150 archivos `.md` en `output/run-deadbeef/` |

## 2. Lo que demuestra y la lección aprendida

Cada segmento translatable en api/router incluye `§§LITERAL§§` que
protegen URLs del github, `[*code*](...)`, anchors a `CanMatchFn`,
configuraciones de `Route` ({`path: 'team/:id', children: [...]`),
etc. La traducción de prosa debe **preservar los markers**; este
proceso identificó que `translate_pilot --mode identity` y el modo
standard del agente no los preserva en línea al reescribir la prosa.

El camino futuro: el agente (o un traductor de flota) debería
**dividir la prosa del segmento por los markers, traducir cada
trozo entre markers, y reensamblar conservándolos**. Mientras eso
no se hace, los segmentos con literals quedan revertidos al source
para no perder el invariant INV-05.

Ver `translate_pass3.py` para la lista de traducciones focales y
`rehydrate_literals.py` para la lógica de rehidratación.

## 3. Lo que NO demuestra

- Que **toda** la prosa del api/router esté traducida. Por el problema
  de preservación de literales, las descripciones con literales
  adyacentes se quedaron en identidad (con todos los `§§LITERAL§§`
  intactos). Rondas futuras que implementen la traducción por-marker
  pueden restaurar la prosa.
- Verificación en Notion: `remote_status: no_verificado`.

## 4. Disposición por estado

| Estado | Cuenta | Motivo |
|---|---|---|
| `translated` | **150** | Todos los archivos con prose en api/router. Las traducciones focales se aplican; las prose adyacentes a literales no traducidos se preservan tal cual. |

Cobertura: 150/150 integrado (100%). `integrity_ok=True`.

## 5. Volumen medido

| Métrica | Valor |
|---|---|
| Archivos en `angular/api/router/` | 150 |
| Bytes totales | 239,8 KB |
| Segmentos | 3 644 |
| Traducibles (`disposition=translatable`) | 1 779 |
| Paquetes | 208 |
| Overflow de paquete | 10 |
| Entradas con override de traducción | 215 |
| Entradas revertidas al source (literales) | 221 |
| Suite de tests | 1 037 pasan, 2 omitidas |

## 6. Próxima ronda

```
Ronda 3: angular/api/forms/  → ~50 archivos
```

Las rondas siguientes pueden usar la misma técnica: `translate_passN.py`
con un TEXTS curado por (path, segment_id), seguido de `rehydrate_literals.py`
para preservar literales en segmentos con literales adyacentes.