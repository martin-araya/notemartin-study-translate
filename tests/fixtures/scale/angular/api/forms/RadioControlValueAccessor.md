@angular/forms

# RadioControlValueAccessor
directive
stable
[*code*](https://github.com/angular/angular/blob/main/packages/forms/src/directives/radio_control_value_accessor.ts#L123-L275)

The [`ControlValueAccessor`](/api/forms/ControlValueAccessor) for writing radio control values and listening to radio control
changes. The value accessor is used by the [`FormControlDirective`](/api/forms/FormControlDirective), [`FormControlName`](/api/forms/FormControlName), and
[`NgModel`](/api/forms/NgModel) directives.
## [API](#api) <a id="api"></a>

```text
      class RadioControlValueAccessor extends BuiltInControlValueAccessor implements ControlValueAccessor ,OnDestroy ,OnInit {}
```

### [constructor](#constructor)
`RadioControlValueAccessor`
@param
renderer
`Renderer2`
@param
elementRef
`ElementRef<any>`
@param
\_registry
`RadioControlRegistry`
@param
\_injector
`Injector`
@returns
`RadioControlValueAccessor`

### [name](#name)
`string`

Tracks the name of the radio input element.
### [formControlName](#formControlName)
`string`

Tracks the name of the [`FormControl`](/api/forms/FormControl) bound to the directive. The name corresponds
to a key in the parent [`FormGroup`](/api/forms/FormGroup) or [`FormArray`](/api/forms/FormArray).
### [value](#value)
`any`

Tracks the value of the radio input element
### [fireUncheck](#fireUncheck)
`void`

Sets the "value" on the radio input element and unchecks it.
@param
value
`any`
@returns
`void`
## [Description](#description) <a id="description"></a>

The [`ControlValueAccessor`](/api/forms/ControlValueAccessor) for writing radio control values and listening to radio control
changes. The value accessor is used by the [`FormControlDirective`](/api/forms/FormControlDirective), [`FormControlName`](/api/forms/FormControlName), and
[`NgModel`](/api/forms/NgModel) directives.
## [Exported by](#exported-by) <a id="exported-by"></a>

- `ReactiveFormsModule`
- `FormsModule`

## [Usage Notes](#usage-notes) <a id="usage-notes"></a>

### [Using radio buttons with reactive form directives](#using-radio-buttons-with-reactive-form-directives) <a id="using-radio-buttons-with-reactive-form-directives"></a>

The follow example shows how to use radio buttons in a reactive form. When using radio buttons in
a reactive form, radio buttons in the same group should have the same `formControlName`.
Providing a `name` attribute is optional.
```text
import {Component} from '@angular/core';
import {FormControl, FormGroup} from '@angular/forms';

@Component({
  selector: 'example-app',
  template: `
    <form [formGroup]="form">
      <input type="radio" formControlName="food" value="beef" /> Beef
      <input type="radio" formControlName="food" value="lamb" /> Lamb
      <input type="radio" formControlName="food" value="fish" /> Fish
    </form>

    <p>Form value: {{ form.value | json }}</p>
    <!-- {food: 'lamb' } -->
  `,
  standalone: false,
})
export class ReactiveRadioButtonComp {
  form = new FormGroup({
    food: new FormControl('lamb'),
  });
}
```