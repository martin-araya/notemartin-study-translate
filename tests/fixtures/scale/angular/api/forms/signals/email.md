@angular/forms/signals

# email
function
stable
since v22.0
[*code*](https://github.com/angular/angular/blob/main/packages/forms/signals/src/api/rules/validation/email.ts#L61-L82)

Binds a validator to the given path that requires the value to match the standard email format.
This function can only be called on string paths.
## [API](#api) <a id="api"></a>

```text
function email<TPathKind extends PathKind = PathKind.Root>(
  path: SchemaPath<string, 1, TPathKind>,
  config?: BaseValidatorConfig<string, TPathKind> | undefined,
): void;
```
@param
path
`` SchemaPath<string, 1, TPathKind> ``

Path of the field to validate
@param
config
`` BaseValidatorConfig<string, TPathKind> | undefined ``
Optional, allows providing any of the following options:
- `error`: Custom validation error(s) to be used instead of the default [`emailError()`](/api/forms/signals/emailError)
or a function that receives the [`FieldContext`](/api/forms/signals/FieldContext) and returns custom validation error(s).
@returns
`void`