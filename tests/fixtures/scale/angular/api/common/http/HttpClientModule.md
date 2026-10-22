@angular/common/http

# HttpClientModule
NgModule
deprecated
[*code*](https://github.com/angular/angular/blob/main/packages/common/http/src/module.ts#L100-L107)

Configures the dependency injector for [`HttpClient`](/api/common/http/HttpClient)
with supporting services for XSRF. Automatically imported by [`HttpClientModule`](/api/common/http/HttpClientModule).
Deprecation warning
use `provideHttpClient(withInterceptorsFromDi())` as providers instead

![](assets/images/angie/orthos-back.svg)
## [API](#api) <a id="api"></a>

```text
      class HttpClientModule {}
```

## [Description](#description) <a id="description"></a>

Configures the dependency injector for [`HttpClient`](/api/common/http/HttpClient)
with supporting services for XSRF. Automatically imported by [`HttpClientModule`](/api/common/http/HttpClientModule).
You can add interceptors to the chain behind [`HttpClient`](/api/common/http/HttpClient) by binding them to the
multiprovider for built-in DI token [`HTTP_INTERCEPTORS`](/api/common/http/HTTP_INTERCEPTORS).
When importing the [`HttpClientModule`](/api/common/http/HttpClientModule), the [`HttpBackend`](/api/common/http/HttpBackend) is set to using the [`HttpXhrBackend`](/api/common/http/HttpXhrBackend).
If you want to use the [`FetchBackend`](/api/common/http/FetchBackend), use [`provideHttpClient`](/api/common/http/provideHttpClient) instead.