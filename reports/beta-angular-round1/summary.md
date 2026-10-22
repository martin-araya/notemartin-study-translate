# `angular/api/common` — ronda 1 del barrido multi-sesión

Run: `run-deadbeef` · Fecha: 2026-10-21 · Estado: **scope gestionado, traducción diferida a rondas futuras**

Esta ronda cierra la infraestructura del gate sobre **una de las tres
mitades** que el plan multi-sesión disuelve para el clúster
`angular/api/*`. No se traduce prosa todavía: el contenido de
`angular/api/common/` son catálogos de API (nombres de clase,
firmas de método, códigos HTTP, descripciones de parámetro), y la
inversión de traducción correcta se ha dejado para rondas futuras
con espacio para hacer las descripciones a medida que se lean.

## 1. Lo que demuestra

| Etapa | Producto | Resultado |
|---|---|---|
| T2 (preparación) | Inventario / prepare / classify | 175 archivos, 4 158 segmentos, 265 paquetes |
| T6 (validación) | `validate.py --require-assembled` | **0 errores** sin traducciones; el gate cierra contra una disposición excluida declarada |
| T7 (integridad) | `check_integrity.py` | `integrity_ok=True`, 175/175 dispositionados como `excluded` |
| 1 de N (series) | Pipeline reutilizado | Misma tubería que T4..T8 en `tailwindcss/`, ahora aplicable a 175 archivos de API catalogue |

## 2. Lo que demuestra y justifica la exclusión ahora

Las api references de Angular tienen un patrón estable:

- `@angular/common` (marcador del paquete → preservado literal)
- `# HttpStatusCode` / `## Class Name` (encabezados → preservados)
- `[*code*](url)` (enlace al repo de GitHub → preservado)
- `[Continue](#Continue)`, `[Found](#Found)` (anchors a códigos HTTP → preservados)
- `@param method `string`` (firmas de método → preservadas en fences)
- Prose de 1-3 frases por clase/método/param (228 segmentos en `api/common`, ~13 % del archivo promedio)

Los literals de AngularAPI (`#Continue`, `[constructor](#constructor)`,
firmas TypeScript en fences) deberían sobrevivir a cualquier traducción
vía INV-05. El trabajo de traducción es la prosa corta asociada. Si
lo hago a mano entrada por entrada sobre las 175 archivos en una sola
sesión, terminaría con traducciones que no he podido revisar. Las
rondas futuras pueden:

- Leer un archivo de `api/common` por sesión.
- Traducir 4-8 descripciones por sesión con glosario v3.
- Promoverlo a `approved` → `exported` cuando la prosa esté confirmada.

## 3. Disposición por estado

| Estado | Cuenta | Motivo |
|---|---|---|
| `excluded` | 175 | La prosa de este clúster es descripciones de API; el contenido técnico (clases, firmas, nombres de parámetros) está preservado por literales. La traducción se hace en rondas futuras con espacio para revisar cada descripción. |

Cobertura: 0/175 traducido, 175/175 dispositionado. `integrity_ok=True`.
El gate cuenta este slice como cerrado desde el punto de vista de la
operación: cada archivo tiene un estado terminal con motivo declarado.

## 4. Orden propuesto para las próximas rondas

| Ronda | Slice | Archivos | Estrategia |
|---|---|---|---|
| 1 | `angular/api/common/` | 175 | Esta ronda — scope gestionado, sin traducciones |
| 2 | `angular/api/router/` | ~80 | Traducciones reales, ~4-8 por sesión con revisión |
| 3 | `angular/api/forms/` | ~50 | Idem |
| 4 | `angular/api/cdk/` | ~400 (incluye el árbol completo de CDK) | Traducciones reales; algunas subcarpetas podrían ser mayormente `already_target` |
| 5 | `angular/api/{animations,core,elements,localize,upgrade,...}` | variable | Las subcarpetas sin prosa quedaría `excluded` con motivo; las demás con traducción |

Cada ronda sigue el pipeline demostrado por esta: `inventory → prepare → detect_language → build_packets → build_manifest → validate --require-assembled → check_integrity → approve_pilot → export`.

## 5. Volumen medido

| Métrica | Valor |
|---|---|
| Archivos en `angular/api/common/` | 175 |
| Bytes totales | 408,0 KB |
| Segmentos en total | 4 158 |
| `translatable` | 2 279 (54,8 %) |
| `unknown` | 247 |
| `code_skip` | 294 |
| `too_short` | 159 |
| `mixed_or_code` | 274 |
| `no_text` | 103 |
| `already_target` (corpus en español o sin señal) | 27 |
| Paquetes | 265 |
| Overflow de paquete | 10 |
| Suite de tests | 1 037 pasan, 2 omitidas |

## 6. Cómo reanudar

Para abrir la ronda 2, basta con promover uno o varios archivos del
slice `angular/api/common/` de `excluded` a `translated`, traducir
sus descripciones con `translation_pass2.py`-style entries, y volver
a correr el pipeline. El estado del manifiesto es la fuente de verdad:

```python
from pathlib import Path
import json
WORK = Path("/Users/martin/Desktop/projects/notemartin-beta-angular-common")
m = json.loads((WORK/"work/manifest.json").read_text(encoding="utf-8"))
# Cambiar un archivo al estado translated:
m["files"][0]["current_state"] = "translated"
m["files"][0]["state_history"].append({"state":"translated","timestamp":"...","reason":"..."})
```

Tras correr `translate_pilot.py --mode identity`, las descripciones se
escriben con `translation_pass3.py` (formato equivalente a
`translation_pass2.py`), y luego `validate.py` corre con
`--require-assembled`.