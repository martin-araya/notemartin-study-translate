@angular/platform-browser

# withEventReplay
function
stable
[*code*](https://github.com/angular/angular/blob/main/packages/platform-browser/src/hydration.ts#L127-L129)

Enables support for replaying user events (e.g. `click`s) that happened on a page
before hydration logic has completed. Once an application is hydrated, all captured
events are replayed and relevant event listeners are executed.
## [API](#api) <a id="api"></a>

```text
function withEventReplay(): HydrationFeature<HydrationFeatureKind.EventReplay>;
```
@returns
`HydrationFeature<HydrationFeatureKind.EventReplay>`

## [Usage Notes](#usage-notes) <a id="usage-notes"></a>

Basic example of how you can enable event replay in your application when
[`bootstrapApplication`](/api/platform-browser/bootstrapApplication) function is used:
```text
bootstrapApplication(App, {
  providers: [provideClientHydration(withEventReplay())]
});
```