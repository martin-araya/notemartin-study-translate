@angular/common

# NgSwitch
directive
deprecated
since v20.0
[*code*](https://github.com/angular/angular/blob/main/packages/common/src/directives/ng_switch.ts#L117-L168)

The `[ngSwitch]` directive on a container specifies an expression to match against.
The expressions to match are provided by `ngSwitchCase` directives on views within the container.
- Every view that matches is rendered.
- If there are no matches, a view with the `ngSwitchDefault` directive is rendered.
- Elements within the `[NgSwitch]` statement but outside of any [`NgSwitchCase`](/api/common/NgSwitchCase)
or `ngSwitchDefault` directive are preserved at the location.

Deprecation warning
Use the `@switch` block instead. Intent to remove in a future major release

![](assets/images/angie/orthos-back.svg)
## [API](#api) <a id="api"></a>

```text
      class NgSwitch {}
```

### [ngSwitch](#ngSwitch)
`any`
@deprecated
Use the `@switch` block instead. Intent to remove in a future major release


## [Description](#description) <a id="description"></a>

The `[ngSwitch]` directive on a container specifies an expression to match against.
The expressions to match are provided by `ngSwitchCase` directives on views within the container.
- Every view that matches is rendered.
- If there are no matches, a view with the `ngSwitchDefault` directive is rendered.
- Elements within the `[NgSwitch]` statement but outside of any [`NgSwitchCase`](/api/common/NgSwitchCase)
or `ngSwitchDefault` directive are preserved at the location.

## [Exported by](#exported-by) <a id="exported-by"></a>

- `CommonModule`

## [Usage Notes](#usage-notes) <a id="usage-notes"></a>

Define a container element for the directive, and specify the switch expression
to match against as an attribute:
```text
<container-element [ngSwitch]="switch_expression">
```

Within the container, `*ngSwitchCase` statements specify the match expressions
as attributes. Include `*ngSwitchDefault` as the final case.
```text
<container-element [ngSwitch]="switch_expression">
   <some-element *ngSwitchCase="match_expression_1">...</some-element>
...
   <some-element *ngSwitchDefault>...</some-element>
</container-element>
```

### [Usage Examples](#usage-examples) <a id="usage-examples"></a>

The following example shows how to use more than one case to display the same view:
```text
<container-element [ngSwitch]="switch_expression">
  <!-- the same view can be shown in more than one case -->
  <some-element *ngSwitchCase="match_expression_1">...</some-element>
  <some-element *ngSwitchCase="match_expression_2">...</some-element>
  <some-other-element *ngSwitchCase="match_expression_3">...</some-other-element>
  <!--default case when there are no matches -->
  <some-element *ngSwitchDefault>...</some-element>
</container-element>
```

The following example shows how cases can be nested:
```text
<container-element [ngSwitch]="switch_expression">
      <some-element *ngSwitchCase="match_expression_1">...</some-element>
      <some-element *ngSwitchCase="match_expression_2">...</some-element>
      <some-other-element *ngSwitchCase="match_expression_3">...</some-other-element>
      <ng-container *ngSwitchCase="match_expression_3">
        <!-- use a ng-container to group multiple root nodes -->
        <inner-element></inner-element>
        <inner-other-element></inner-other-element>
      </ng-container>
      <some-element *ngSwitchDefault>...</some-element>
    </container-element>
```