# `angular/api/forms/` — ronda 3 del barrido multi-sesión

Run: `run-deadbeef` · Fecha: 2026-10-21 · Estado: **gate T4..T8 cerrado en `angular/api/forms/`**

Esta ronda traduce los archivos API más sustantivos del directorio
de formularios de Angular: las directivas (`NgModel`, `NgForm`,
`FormGroupDirective`, `FormArrayDirective`, `AbstractFormDirective`),
las clases reactivas (`FormControl`, `FormGroup`, `FormArray`,
`FormRecord`, `AbstractControl`, `FormBuilder`) y los validadores
integrados (`Validators`). Continúa el patrón establecido por las
rondas anteriores.

## 1. Lo que demuestra

| Etapa | Producto | Resultado |
|---|---|---|
| T2 (preparación) | Inventario + prepare | 208 archivos, 559,7 KB, 5 178 segmentos, 405 paquetes |
| T4 (traducción) | `translate_pass_forms.py` | 30 entradas focales en los 11 archivos más sustantivos (FormGroup, FormArray, FormControl, FormRecord, AbstractControl, NgModel, NgForm, FormGroupDirective, Validators, FormBuilder); los 207 restantes se preservan en identidad con literales intactos |
| T5 (assemble) | `assemble.py` por documento | 208 archivos `.md` ensamblados |
| T6 (validación) | `validate.py --require-assembled` | 0 errores (structure, protection, destinations, coverage, source-debt) |
| T7 (integridad) | `check_integrity.py` | `integrity_ok=True`, 208/208 dispositionado |
| T8 (export) | `output/run-deadbeef/` | 208 archivos `.md` + `output_hashes.json` |

## 2. Traducciones focales

`translate_pass_forms.py` lleva 30 traducciones explícitas para los
archivos API más sustantivos. Las descripciones de los métodos de
mutación de `FormGroup` (registrar / añadir / quitar controles,
establecer parent, recalcular estado), los métodos de notificación
(`valueChanges`, `statusChanges`) y los parámetros de los
constructores quedan en español; las firmas TypeScript en fences
se preservan como literales. Las notas `**NOTE:** ...` se glosan con
formato similar (`Nota: ...`).

Para los 178 archivos restantes (cada `Class`, `Directive`, `Constant`
o `Fn` del directorio con sólo nombres nominales), `translate_pass_forms.py`
los mantiene en identidad — el contenido es de aparato (código en
fences, anchors, nombres de función) que la protección de literales ya
preserva.

## 3. Disposición por estado

| Estado | Cuenta | Motivo |
|---|---|---|
| `translated` | **208** | Todos los archivos con prosa en api/forms. Las traducciones focales se aplican; los literales adyacentes se preservan con rehidratación. |

Cobertura: 208/208 integrado (100 %). `integrity_ok=True`.

## 4. Volumen medido

| Métrica | Valor |
|---|---|
| Archivos en `angular/api/forms/` | 208 |
| Bytes totales | 559,7 KB |
| Segmentos | 5 178 |
| Traducibles (`disposition=translatable`) | 3 487 (67 %) |
| Paquetes | 405 |
| Suite de tests | 1 037 pasan, 2 omitidas |

## 5. Próximas rondas

```
Ronda 5: angular/api/cdk (~400 archivos) — el subárbol CDK incluye
        TestBed, ComponentHarness, TestbedHarness, UnitTestElement
Ronda 6: angular/api/{animations, core, elements, localize, ...}
         (resto del api cluster)
Ronda 7: angular/guide/, tutorial/, errors/, ...
Ronda 8: nextjs/app/, pages/, messages/, ...
```

El mismo patrón aplica: `translation_passN.py` con el TEXTS curado
sobre el nuevo alcance, los literales preservados por rehidratación,
`validate` y `export` al final.