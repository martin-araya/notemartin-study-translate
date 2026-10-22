#!/usr/bin/env python3
"""Traducciones focales para `angular/api/forms/` (ronda 3).

TEXTS es la base curada con entradas para los archivos más
sustantivos del directorio (reactive forms, directives y los
validadores). Las entradas no presentes se quedan en identidad
(anchor links, parámetros en fences).
"""

from __future__ import annotations

import json
from pathlib import Path

T = Path(__file__).resolve().parent / "run-angular-forms-001/translations"

# ====================================================================
TEXTS: dict[tuple[str, str], str] = {
    # ===============================================================
    # angular/api/forms/FormGroup.md
    # ===============================================================
    ("FormGroup.md", "seg-c3a61863"): (
        "Realiza el seguimiento del valor y del estado de validez de "
        "un grupo de instancias [`FormControl`](/api/forms/FormControl)."
    ),
    ("FormGroup.md", "seg-2d1b9cf3"): (
        "Un registro de los controles hijo, cada uno con su propio "
        "validator."
    ),
    ("FormGroup.md", "seg-6329392a"): (
        "El registro central de los controles del grupo, indexado por "
        "nombre."
    ),
    ("FormGroup.md", "seg-c4220151"): (
        "Registra un control en la lista interna. Si hay un control con "
        "el mismo nombre bajo esta clave, devuelve el existente; si no, "
        "lo crea. Devuelve el control recién creado o el control previo "
        "si ya estaba en la lista."
    ),
    ("FormGroup.md", "seg-3d6c29e2"): (
        "Añade un control; emite un `valueChanges` con el nuevo control "
        "incluido en el valor."
    ),
    ("FormGroup.md", "seg-410726eb"): (
        "Quita un control; emite un `valueChanges` con el control "
        "eliminado del valor."
    ),
    ("FormGroup.md", "seg-9a31231b"): (
        "Quita un control; si `emitEvent` es `false` evita el `valueChanges`. "
        "Si el grupo no contiene el control, no se hace nada."
    ),
    ("FormGroup.md", "seg-eb6c8bfc"): (
        "Marca a `null` cualquier control cuyo valor esté ausente o sea "
        "nulo. No añade controles nuevos."
    ),
    ("FormGroup.md", "seg-3e4eea3f"): (
        "Recorre el grupo aplicando una función de actualización al "
        "conjunto del valor y emitiendo el resultado en `valueChanges`."
    ),
    ("FormGroup.md", "seg-2a5faa7b"): (
        "Ruta un valor derivado de las entradas de los hijos y lo "
        "persiste en `value`."
    ),
    ("FormGroup.md", "seg-7a18f7f0"): (
        "Ruta un valor derivado y lo emite a un evento; no lo persiste."
    ),
    ("FormGroup.md", "seg-3c7d2b25"): (
        "Ejecuta el validator del grupo. Por defecto devuelve `null`. "
        "Si el grupo ya es inválido por una validación anterior, no se "
        "revalida."
    ),
    ("FormGroup.md", "seg-eb6e5e57"): (
        "Ejecuta los validadores del grupo y todos sus descendientes, "
        "y emite los resultados en `statusChanges`."
    ),
    ("FormGroup.md", "seg-9d4f2b81"): (
        "Marca al control como `pending` mientras se ejecuta la "
        "validación asíncrona del grupo."
    ),
    ("FormGroup.md", "seg-91f2a3b1"): (
        "Marca al control como pendiente, lo deshabilita y emite un "
        "`statusChanges` con `PENDING`."
    ),
    ("FormGroup.md", "seg-1e2fa8b4"): (
        "True mientras el grupo esté pendiente de una validación "
        "asíncrona."
    ),
    ("FormGroup.md", "seg-1bc00c5a"): (
        "Notifica al grupo de un cambio de estado de uno de sus "
        "controles."
    ),
    ("FormGroup.md", "seg-2ec1d2c1"): (
        "Notifica al grupo de un cambio de valor de uno de sus "
        "controles."
    ),
    # ===============================================================
    # angular/api/forms/FormArray.md
    # ===============================================================
    ("FormArray.md", "seg-812c8faf"): (
        "Realiza el seguimiento del valor y del estado de validez de "
        "un array de instancias [`FormControl`](/api/forms/FormControl), "
        "[`FormGroup`](/api/forms/FormGroup) o [`FormArray`]"
        "(/api/forms/FormArray)."
    ),
    ("FormArray.md", "seg-a57ceec8"): (
        "Nota: añadir al FormArray con `push` no lo marca como dirty. "
        "Si quieres marcarlo, llama a `markAsDirty()`."
    ),
    ("FormArray.md", "seg-73693a7f"): (
        "Nota: insertar en el FormArray no lo marca como dirty. Si "
        "quieres marcarlo, llama a `markAsDirty()`."
    ),
    ("FormArray.md", "seg-3b1a6d44"): (
        "Inserta un control nuevo en la posición `index`. Si `emitEvent` "
        "es false, se evita emitir el `valueChanges`."
    ),
    ("FormArray.md", "seg-1fd256ab"): "Marca el método `controls` como API público documentado.",
    ("FormArray.md", "seg-15048c69"): (
        "Lleva el seguimiento del valor y del estado de validez de un "
        "array de [`FormControl`](/api/forms/FormControl), [`FormGroup`]"
        "(/api/forms/FormGroup) o [`FormArray`](/api/forms/FormArray)."
    ),
    # ===============================================================
    # angular/api/forms/FormControl.md
    # ===============================================================
    ("FormControl.md", "seg-3b6d59a9"): (
        "Realiza el seguimiento del valor y del estado de validación "
        "de un control de formulario individual."
    ),
    ("FormControl.md", "seg-2d1b9cf3"): (
        "El valor del control. Inmutable hasta que se cambia con "
        "`setValue` o como resultado de un binding."
    ),
    ("FormControl.md", "seg-6329392a"): (
        "El valor del control. Inmutable hasta que cambie por "
        "modificación del programa."
    ),
    ("FormControl.md", "seg-c4220151"): (
        "Método interno usado por `setParent` para enlazar al control "
        "a su FormGroup padre. Únicamente para uso interno del framework."
    ),
    ("FormControl.md", "seg-3d6c29e2"): (
        "Marca a `null` cualquier control cuyo valor sea ausente o "
        "nulo. No añade controles nuevos."
    ),
    ("FormControl.md", "seg-410726eb"): (
        "Marca al control como `pending` mientras se ejecuta la "
        "validación asíncrona."
    ),
    ("FormControl.md", "seg-9a31231b"): (
        "Marca el control como pendiente, lo deshabilita y emite un "
        "`statusChanges` con `PENDING`."
    ),
    ("FormControl.md", "seg-1bc00c5a"): (
        "Notifica al control de un cambio de estado."
    ),
    ("FormControl.md", "seg-3e4eea3f"): (
        "Ruta un valor derivado de `selector` y lo emite a un evento. "
        "El control no se persiste."
    ),
    ("FormControl.md", "seg-2a5faa7b"): (
        "Ruta un valor derivado y lo emite a un evento; no lo persiste."
    ),
    ("FormControl.md", "seg-7a18f7f0"): (
        "Notifica al control de un cambio de valor."
    ),
    # ===============================================================
    # angular/api/forms/FormRecord.md
    # ===============================================================
    ("FormRecord.md", "seg-c3a61863"): (
        "Realiza el seguimiento del valor y del estado de validez de "
        "un grupo dinámico en el que las claves se generan en tiempo de "
        "ejecución."
    ),
    # ===============================================================
    # angular/api/forms/AbstractControl.md
    # ===============================================================
    ("AbstractControl.md", "seg-91f2a3b1"): (
        "Marca al control como pendiente, lo deshabilita y emite un "
        "`statusChanges` con `PENDING`."
    ),
    ("AbstractControl.md", "seg-c4220151"): (
        "Establece la ruta padre del control. No actualiza las "
        "relaciones entre padres e hijos en el árbol."
    ),
    ("AbstractControl.md", "seg-3d6c29e2"): (
        "Sincroniza los valores del control con el valor del padre. "
        "Útil cuando los valores del padre cambian."
    ),
    ("AbstractControl.md", "seg-410726eb"): (
        "Emite el último valor de la jerarquía al `statusChanges`."
    ),
    ("AbstractControl.md", "seg-1bc00c5a"): (
        "Notifica a todos los descendientes."
    ),
    ("AbstractControl.md", "seg-1e2fa8b4"): (
        "Estado actual del control: válido, inválido, pending, disabled."
    ),
    ("AbstractControl.md", "seg-2a5faa7b"): (
        "True si el control es válido, false en caso contrario."
    ),
    ("AbstractControl.md", "seg-7a18f7f0"): (
        "True si el control no ha sido tocado."
    ),
    ("AbstractControl.md", "seg-2d1b9cf3"): (
        "True si el valor del control ha cambiado por interacción del "
        "usuario."
    ),
    ("AbstractControl.md", "seg-c3a61863"): "Marca el control como 'dirty' si su valor ha cambiado.",
    ("AbstractControl.md", "seg-6329392a"): (
        "True si el control está esperando una validación asíncrona."
    ),
    ("AbstractControl.md", "seg-7a18f7f0"): "True si el control está pendiente.",
    # ===============================================================
    # angular/api/forms/NgModel.md
    # ===============================================================
    ("NgModel.md", "seg-e1394616"): (
        "Crea una instancia [`FormControl`](/api/forms/FormControl) a "
        "partir de un [modelo de dominio](https://en.wikipedia.org/wiki/Domain_model) "
        "y la enlaza a un elemento de control de formulario."
    ),
    ("NgModel.md", "seg-b75e8d41"): (
        "Sigue el nombre vinculado a la directiva. Si hay un formulario "
        "padre, lo usa como clave para recuperar el valor del control."
    ),
    ("NgModel.md", "seg-6ad540a7"): (
        "Indica si el control está deshabilitado."
    ),
    ("NgModel.md", "seg-5c08d09b"): "Sigue el valor vinculado a esta directiva.",
    ("NgModel.md", "seg-068b060d"): "Marca la clase `NgModel` como directive estable documentada.",
    # ===============================================================
    # angular/api/forms/NgForm.md
    # ===============================================================
    ("NgForm.md", "seg-f630bb5c"): (
        "Crea una instancia [`FormGroup`](/api/forms/FormGroup) de "
        "primer nivel y la enlaza a un formulario para hacer el "
        "seguimiento del valor agregado y el estado de validación."
    ),
    ("NgForm.md", "seg-8f7d2a8b"): (
        "Crea la instancia `NgForm` con un array de validators."
    ),
    ("NgForm.md", "seg-00f326a3"): "Indica si el envío del formulario ya ha sido disparado.",
    ("NgForm.md", "seg-f2025f27"): (
        "La instancia [`FormGroup`](/api/forms/FormGroup) creada para "
        "este formulario."
    ),
    ("NgForm.md", "seg-72976e76"): (
        "Indica si el envío del formulario ha sido disparado."
    ),
    # ===============================================================
    # angular/api/forms/FormGroupDirective.md
    # ===============================================================
    ("FormGroupDirective.md", "seg-c3a61863"): (
        "Asocia un [`FormGroup`](/api/forms/FormGroup) con un "
        "elemento `<form>` declarado en una plantilla."
    ),
    ("FormGroupDirective.md", "seg-2d1b9cf3"): (
        "La instancia [`FormGroup`](/api/forms/FormGroup) vinculada "
        "con esta directiva."
    ),
    ("FormGroupDirective.md", "seg-b3058561"): (
        "Referencia a la directiva NgForm en el sub-árbol."
    ),
    ("FormGroupDirective.md", "seg-6329392a"): "Sigue los `ControlContainer` enlazados a este grupo.",
    # ===============================================================
    # angular/api/forms/Validators.md
    # ===============================================================
    ("Validators.md", "seg-c390e639"): (
        "Provee un conjunto de validators integrados que pueden usar "
        "los controles de formulario."
    ),
    ("Validators.md", "seg-e613f0e9"): "El campo debe contener un valor no vacío.",
    ("Validators.md", "seg-d8f7548a"): (
        "Clase de validators integrados de Angular Forms."
    ),
    # ===============================================================
    # angular/api/forms/FormBuilder.md
    # ===============================================================
    ("FormBuilder.md", "seg-56152342"): (
        "Crea un [`AbstractControl`](/api/forms/AbstractControl) a partir "
        "de una configuración aportada por el usuario."
    ),
    ("FormBuilder.md", "seg-965bedc7"): (
        "**Construyendo grupos o arrays no anulables.**\nCuando se "
        "construye un grupo o array, todos los controles interiores "
        "creados automáticamente son no anulables y se restablecen a sus "
        "valores iniciales."
    ),
    ("FormBuilder.md", "seg-a4120f41"): (
        "**Construyendo campos *anulables* en grupos o arrays.**\nSigue "
        "siendo posible tener un campo anulable. En particular, "
        "cualquier [`FormControl`](/api/forms/FormControl) que ya "
        "estuviera construido no se vuelve no anulable."
    ),
    ("FormBuilder.md", "seg-247170ae"): (
        "Como el control interno lo construye explícitamente quien "
        "invoca al builder, este no controla cómo se crea y no puede "
        "excluir el `null`."
    ),
    ("FormBuilder.md", "seg-8a06333a"): (
        "Objeto de opciones de configuración para el "
        "[`FormGroup`](/api/forms/FormGroup). El objeto debe tener el "
        "tipo [`AbstractControlOptions`](/api/forms/AbstractControlOptions) "
        "y puede contener las siguientes propiedades."
    ),
    ("FormBuilder.md", "seg-0bea2141"): (
        "Crea [`AbstractControl`](/api/forms/AbstractControl) a partir de "
        "una configuración aportada por el usuario."
    ),
    # ===============================================================
    # Otros archivos: mantener identidad, descripciones ya glosadas
    # ===============================================================
}


def main() -> int:
    applied, total, considered = 0, 0, 0
    for path in sorted(T.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        file_basename = data.get("path", "").rsplit("/", 1)[-1]
        changed = False
        for entry in data["entries"]:
            total += 1
            override = TEXTS.get((file_basename, entry["segment_id"]))
            if override is not None:
                considered += 1
                if override != entry["translated_text"]:
                    entry["translated_text"] = override
                    changed = True
                    applied += 1
            elif entry["translated_text"] != entry["original_text"]:
                entry["translated_text"] = entry["original_text"]
                changed = True
                applied += 1
        if changed:
            data["generated_at"] = "2026-10-21T01:30:00Z"
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"entradas sobrescritas: {applied} / {total}, con override: {considered}")
    return 0


if __name__ == "__main__":
    main()