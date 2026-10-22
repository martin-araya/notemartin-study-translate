@angular/forms/signals

# LogicFn
Type Alias
stable
since v22.0
[*code*](https://github.com/angular/angular/blob/main/packages/forms/signals/src/api/types.ts#L881-L883)

A function that receives the [`FieldContext`](/api/forms/signals/FieldContext) for the field the logic is bound to and returns
a specific result type.
## [API](#api) <a id="api"></a>

```text
      type LogicFn<TValue, TReturn, TPathKind extends PathKind = PathKind.Root> = (  ctx: FieldContext<TValue, TPathKind>,) => TReturn
```