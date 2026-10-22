# `angular.md` — términos observados en la documentación de Angular

**Material leído:** `angular/overview.md`, `angular/guide/animations/migration.md`,
`angular/api/core/DebugElement.md`, `angular/guide/components/content-projection.md`,
`angular/guide/components/lifecycle.md`, `angular/errors/NG8001.md`.

## Reglas generales observadas

- Angular **usa sustantivos en inglés como nombre propio**: `Module`,
  `Component`, `Directive`, `Service`, `Pipe`, `Guard`. Su
  documentación oficial los presenta como tipos concretos.
- El plural en inglés (`Modules`, `Components`, `Directives`) se usa al
  hablar de la API general.
- Los nombres de **API exactas** (`signal()`, `computed()`, `effect()`,
  `inject()`, `OnPush`, `Output()`) van literalmente; el corpus los usa
  como código dentro de fences (líneas 31-34 de `lifecycle.md`, por
  ejemplo), así que la protección de literales ya los aísla.
- Los **decoradores** se nombran precedidos de `@` y en inglés:
  `@Component`, `@Injectable`. En prosa, si la frase está en español, el
  decorador se mantiene literal («con el decorador `@Component`,
  no «con el decorador Component»).

## Propuestas por entrada

### `module` (sustantivo en contexto Angular)

- **Sentido:** `NgModule`. Encapsula declaraciones (componentes,
  directivas y pipes) con su ámbito.
- **Donde aparece:** `angular/errors/NG8001.md:11` —
  *«Make sure that the component is correctly imported inside your
  NgModule or standalone component, by checking its presence in the
  `imports` field.»*
- **Status:** `propuesto`
- **Preferred:** `módulo`
- **Variantes razonables:** `módulo Angular` (cuando la ausencia de
  contexto lo ambigüe).
- **Justificación:** Sin equivalente asentado en español; «módulo» es la
  traducción que la documentación oficial usa en otros lugares.
- **Decisión abierta:** ¿se acepta «NgModule» en el corpus en inglés,
  como la fuente, o se mantiene siempre `módulo`? La respuesta cambia
  1 142 referencias en `angular/api/`.

### `directive` (sustantivo en contexto Angular)

- **Sentido:** clase asociada a un atributo que añade comportamiento a
  un elemento del DOM. Distinto de `Component` (que tiene plantilla).
- **Donde aparece:** `angular/guide/animations/migration.md:6` —
  *«the new `animate.enter` and `animate.leave` feature to add
  animations»*; `NG8001.md:11` — *«there is no component or directive
  with such element selector»*.
- **Status:** `propuesto`
- **Preferred:** `directiva`
- **Justificación:** traducción literal, sin conflicto. La duda está en
  el plugin del producto: ¿«directivas» o «atributos» como en HTML? Lo
  segundo genera ambigüedad con los atributos HTML.

### `pipe` (sustantivo)

- **Sentido:** operador declarativo dentro de plantillas
  (`{{ value | currency }}`).
- **Status:** `propuesto` / **dudoso**
- **Preferred:** `pipe`
- **Variantes razonables:** `filtro de plantilla` (lo que era un pipe
  en AngularJS), `transformación` (muy genérico).
- **Justificación:** La comunidad hispanohablante usa la forma inglesa
  sin traducir en sus tutoriales. `tubo` se descarta por colisión con
  «tubería física».
- **Decisión abierta:** primer uso aparece tal cual; a partir de ahí
  conservarlo o traducirlo define el registro.

### `service` (sustantivo en contexto Angular)

- **Sentido:** clase con `providedIn: 'root'` o equivalente, sin
  instancia de plantilla.
- **Status:** `propuesto`
- **Preferred:** `servicio`
- **Justificación:** No hay ambigüedad; el plural «servicios» convive
  sin problemas con la frase original.

### `component` (sustantivo en contexto Angular)

- **Sentido:** unidad declarativa asociada a un selector HTML. En el
  corpus, opuesto a `directive`.
- **Donde aparece:** `angular/api/core/DebugElement.md:25` —
  *«The underlying DOM element at the root of the component»*;
  `NG8001.md:11` — *«component or directive with such element
  selector»*.
- **Status:** `propuesto`
- **Preferred:** `componente`
- **Justificación:** Tecnicismo asentado y usado por la documentación
  oficial en español.

### `selector` (sustantivo técnico)

- **Sentido:** cadena CSS que el framework asocia a una directiva o
  componente (`'app-card'`).
- **Donde aparece:** `NG8001.md:11` — *«with such element selector»*.
- **Status:** `propuesto`
- **Preferred:** `selector`
- **Justificación:** En TypeScript es un tipo primitivo y en UI es un
  nombre técnico. El calco «selectador» no existe en español; el
  calco «selector CSS» se evita porque el selector de Angular no es
  CSS.

### `input` y `output` (en contexto de decoración `@Input` / `@Output`)

- **Sentido:** `@Input` declara un enlace de entrada de datos desde el
  padre; `@Output` emite eventos con `EventEmitter`.
- **Status:** `mantener`
- **Preferred:** `@Input`, `@Output` (literal).
- **Justificación:** Son nombres de APIs exactas; el código en fences
  los referencia, y traducirlos daría errores de compilación si alguien
  los copia. Sólo se traducen los comentarios que los rodean
  («propiedad de entrada», «flujo de salida»).

### `lifecycle hook` (compuesto)

- **Sentido:** método del componente que se ejecuta en una fase del
  ciclo de vida (constructor, ngOnInit, ngOnDestroy, etc.).
- **Donde aparece:** `angular/guide/components/lifecycle.md:11` —
  *«Lifecycle hooks that relate to a specific component instance are
  implemented as methods on your component class.»*
- **Status:** `propuesto`
- **Preferred:** `enlace del ciclo de vida` (calco) o `callback de
  ciclo de vida` (calco explícito).
- **Justificación:** el uso real en español técnico recurre a
  «hooks del ciclo de vida» como anglicismo crudo. Mantener como
  `gancho del ciclo de vida` es calco evidente.
- **Decisión abierta:** dejarlos en inglés o traducir; ambos
  funcionarán, y la elección se proyecta sobre miles de menciones.

### `change detection` (compuesto)

- **Sentido:** el recorrido que Angular ejecuta sobre sus componentes
  para detectar cambios de enlace.
- **Donde aparece:** `angular/guide/components/lifecycle.md:9` y 17.
- **Status:** `propuesto` / **dudoso**
- **Preferred:** `detección de cambios`
- **Justificación:** «Detección» en este contexto es un neologismo
  técnico; el calco es aceptable y es la opción de la documentación
  oficial. La alternativa «revisión de cambios» se evita porque esa
  expresión ya tiene significado en gestión de código.

### `standalone component` (compuesto técnico)

- **Sentido:** componente no declarado en un `NgModule`, importado
  directamente por su árbol.
- **Donde aparece:** `NG8001.md:11` — *«If the component is declared
  in an NgModule (meaning that it is not standalone) …»*.
- **Status:** `mantener`
- **Preferred:** `standalone component` / `componente
  independiente`.
- **Justificación:** En el corpus, Angular contrapone `standalone` a
  `NgModule`. La traducción «componente independiente» pierde el
  registro técnico y se confunde con «componente desacoplado».
- **Decisión abierta:** traducir significa reescribir la dicotomía;
  conservar deja el contraste literal.

### `content projection` (compuesto técnico)

- **Sentido:** `<ng-content>` como marcador de inserción de hijos
  dentro de la plantilla.
- **Donde aparece:** `angular/guide/components/content-projection.md`
  título y frases introductorias.
- **Status:** `propuesto` / **dudoso**
- **Preferred:** `proyección de contenido`
- **Justificación:** calco asentado por la documentación oficial.
  Alternativa: «inclusión de contenido».
- **Decisión abierta:** ambas son precisas; «proyección» es la del
  fabricante, «inclusión» es la lectura funcional.

### `declarations` (campo de `@NgModule`)

- **Sentido:** array del decorador `@NgModule` que enumera componentes,
  directivas y pipes del módulo.
- **Donde aparece:** dentro de fences TypeScript en guías y errores.
- **Status:** `mantener`
- **Preferred:** `declarations` (literal).
- **Justificación:** propiedad del API; no se traduce, sólo se
  rodea con comentarios.

### `imports` y `exports` (campos de `@NgModule`)

- **Sentido:** `imports` enumera módulos de los que se traen
  declaraciones; `exports` enumera qué se expone fuera.
- **Donde aparece:** `NG8001.md:11`.
- **Status:** `mantener`
- **Preferred:** literal.
- **Justificación:** propiedades del API; mismo razonamiento que
  `declarations`.

## Lo que falta por leer

- `angular/guide/signals/` (signals y computed/effect).
- `angular/guide/defer.md` (bloques `defer`).
- `angular/guide/routing/` y `api/router/` (rutas, guards, resolvers).
- `angular/guide/forms/` (template-driven vs reactive).
- `angular/guide/i18n/`, `angular/guide/i18n-add-ons.md`.
- Api reference completa de `angular/api/core/`, `common/`,
  `router/`, `forms/`, `http/`, `platform-browser/`, `animations/`.
- `angular/guide/aria.md` (accesibilidad).

Cada bloque revelará términos específicos de ese dominio.
## Segunda pasada (2026-10-20)

**Material leído en esta iteración:** `angular/guide/signals/index.md`,
`angular/guide/signals/linked-signal.md`, `angular/guide/signals/resource.md`,
`angular/guide/signals/effect.md`, `angular/guide/signals/{model,inputs,queries}.md`.

`model.md`, `inputs.md` y `queries.md` son *redirecciones* de una línea
(`Redirecting to /guide/components/...`). Sus términos viven en la
secundaria `angular/guide/components/`, no en `signals/`. Conviene tenerlos
localizados antes de glosarlos.

### `signal` (Angular)

- **Sentido en Angular:** "A signal is a wrapper around a value that
  notifies interested consumers when that value changes. Signals can
  contain any value, from primitives to complex data structures."
  Es la primitiva reactiva del framework: una caja de valor que notifica
  a quien la lee. Distinto de `state` en React o en otros frameworks.
- **Donde aparece:** `signals/index.md:11`, 12, 16, 21 (en código fences
  `const count = signal(0);`).
- **Status:** `mantener`
- **Justificación:** nombre del API. Los sinonimos en español
  ('señal', 'valor reactivo') suenan forzados; la documentación oficial en
  español usa `signal` y `Signal` literalmente.

### `writable signal` y `readonly signal`

- **Sentido:** un *writable signal* es aquel al que se le aplica `.set()`
  o `.update()`; un *readonly signal* solo se lee (`.asReadonly()`).
  Para escribir sobre un readonly la fuente expone `asReadonly()` como
  conversión.
- **Donde aparece:** `signals/index.md:13-15`, 36-38.
- **Status:** `mantener` (`signal`); `mantener` la notación
  `asReadonly()`.
- **Justificación:** todos los nombres son API exactas.

### `computed signal` (compuesto)

- **Sentido:** signal de solo lectura que deriva su valor de otros
  signals. "Computed signals are both lazily evaluated and memoized"
  (`signals/index.md:75`).
- **Donde aparece:** `signals/index.md:66-78` (sección entera).
- **Status:** `mantener` / **`propuesto`** para la prosa que lo rodea.
- **Preferred prosa:** `valor calculado`, `valor derivado`. Equivalentes:
  `señal computada` (calco crudo), `señal derivada` (más preciso).
- **Justificación:** la palabra "computed" es el término del fabricante.
  En español técnico se usa "derivado" (entrada laxa) o "calculado" (más
  funcional).

### `effect` (función y signal Reactivo)

- **Sentido:** "An effect is an operation that runs whenever one or more
  signal values change." Se crea con `effect(() => { ... })`.
- **Donde aparece:** `signals/effect.md:6-13`.
- **Status:** `mantener`
- **Justificación:** nombre del API. El resumen en español podría usar
  «efecto», el calco literal, pero el corpus ya glosa `hook` como
  «enlace» y aquí el sentido es distinto (no es un hook del ciclo de
  vida de componentes, sino una operación reactiva).
- **Decisión abierta:** «efecto» vs «side-effect» (que es lo que Angular
  llama cuando lo describe como "syncing signal state to imperative,
  non-signal APIs"). Si se opta por «efecto», ambas formas conviven sin
  ambigüedad.

### `linkedSignal` (función reactiva)

- **Sentido:** "Dependent state". Sirve para state que depende
  intrínsecamente de otro state (p. ej. opción seleccionada de un array
  dinámico).
- **Donde aparece:** `signals/linked-signal.md:24`, 33-45.
- **Status:** `mantener`
- **Justificación:** nombre del API. La conversación en español técnico
  lo invoca literalmente porque aún no tiene uso asentado fuera de
  Angular 17+.

### `resource` (signal async) y `Resource` (tipo)

- **Sentido:** "A `Resource` gives you a way to incorporate async data into
  your application's signal-based code and still allow you to access its
  data synchronously." Su carga se controla con `params()` y `loader()`.
- **Donde aparece:** `signals/resource.md:6-7`, 17, 26-30, 41.
- **Status:** `mantener`
- **Preferred prosa:** `recurso` para `Resource` y `resource`.
- **Justificación:** "Recurso" es la traducción genérica habitual para
  otros API frameworks (React, Vue); encaja aquí sin ambigüedad con el
  sentido.

### `AbortSignal` (existente en JS)

- **Sentido:** API estándar del navegador para cancelar peticiones
  (`AbortController.signal`). Lo cita `signals/resource.md:55-57` como
  un valor que la Resource expone en su carga.
- **Status:** `mantener`
- **Justificación:** literal del API estándar.

### `injection context` (compuesto)

- **Sentido:** "injection context" — sub-palabra del sistema de DI que
  expone `inject()`. Efectos y signals solo se pueden crear dentro de
  ese contexto o pasando un `Injector` explícito.
- **Donde aparece:** `signals/effect.md:30-32`, 47.
- **Status:** `propuesto`
- **Preferred prosa:** `contexto de inyección`.
- **Justificación:** calco literal asentado en la documentación oficial.

### `ExpressionChangedAfterItHasBeenChecked`

- **Sentido:** error de Angular que se lanza cuando un efecto modifica
  state que ya ha sido renderizado en una pasada de change detection.
  Aparece como advertencia sobre **no usar effects para propagar state**
  (`signals/effect.md:27-29`).
- **Status:** `mantener`
- **Justificación:** nombre exacto del error. No se traduce.

### `WritableSignal`, `Signal`, `ResourceLoader`, `ResourceLoaderParams`

- Todos son nombres del API. `Status: mantener`.

## Términos que solo aparecen en fences TypeScript

Aparecen dentro de `signals/index.md` y `signals/{effect,resource,linked-signal}.md`
pero quedan **protegidos como literales** por la protección de código:

`@Service`, `@Component`, `@Inject`, `Count`, `CounterState`,
`incremet()`, `computed()`, `effect()`, `linkedSignal()`, `resource()`,
`hasValue()`, `set()`, `update()`, `asReadonly()`, `inject()`, `Injector`,
`this._count._subscribers()`, `ShippingMethodPicker`, `shippingOptions`,
`selectedOption`.

No se glosan individualmente porque la protección de código (INV-05)
los aísla antes de traducir.
## Tercera pasada (2026-10-20)

**Material leído en esta iteración:** `angular/guide/routing/{index,data-fetching-with-resources,route-guards,data-resolvers,router-reference}.md`,
`angular/guide/forms/{index,template-driven-forms}.md`,
`angular/guide/i18n/{index,locale-id}.md`.

### Subsistema *routing* de Angular

#### `route` (sentido general)

- **Sentido:** definición declarativa de una URL → componente. Forma
  parte de `Routes` (array de `Route`).
- **Donde aparece:** `routing/index.md:14-18` define los tres componentes
  (routes, outlets, links).
- **Status:** `propuesto` (en primera pasada queda como `ruta`).
- **Decisión:** mantener `ruta`. La dicotomía `route`/`router` distingue
  la *definición* del *servicio de enrutamiento* y no se debe cambiar.

#### `outlet` (mecanismo del template)

- **Sentido:** "placeholders in your templates that dynamically load and
  render components based on the active route" (`routing/index.md:18`).
  Aparece como `<router-outlet>` en el template.
- **Status:** `mantener` / `propuesto`
- **Preferred:** `marcador de ruta` o `punto de inserción` o literal.
- **Justificación:** `<router-outlet>` es nombre del API; el descriptor
  castellano deja margen a la prosa.

#### `param`, `paramMap`, `query`

- **Sentido:** `params` / `queryParams` / `paramMap` se leen del
  `ActivatedRouteSnapshot` o de la propiedad de la página
  (`routing/route-guards.md:48-50`).
- **Status:** `mantener` (API).

#### `route provider` y `route providers` (compuestos, servicio atado a ruta)

- **Donde aparece:** `routing/route-guards.md:43-44`, `routing/data-resolvers.md:11`.
- **Sentido:** servicios `providedIn: 'route'` que solo viven dentro
  del árbol de la ruta.
- **Status:** `propuesto`
- **Preferred prosa:** `proveedores de la ruta` o `servicios registrados en la ruta`.

#### `router events`, `NavigationStart`, `NavigationEnd`, etc.

- **Donde aparece:** `routing/router-reference.md:11-48` (tabla completa).
- **Status:** `mantener` (todos nombres exactos del API).

#### `CanActivate`, `CanDeactivate`, `CanMatch`, `CanLoad`, `ResolveFn`

- **Sentido:** "types of route guards" (`routing/route-guards.md:43`) y
  funciones del API de resolución
  (`routing/data-resolvers.md:10`).
- **Status:** `mantener`

#### `route guard`, `data resolver`, `route resources`

- **Compuestos:**
  `routing/route-guards.md:7-8` — *"[Route guards] are like
  checkpoints that manage whether a user can access specific routes."*;
  `routing/data-fetching-with-resources.md:1-6` — "[route resources]
  offer several advantages over traditional [data resolvers]" —
  introduce `withRouterResources`, `isLoading()`, `error()` como
  signals asociados al recurso de ruta.
- **Status:** `mantener` / `propuesto`
- **Preferred prosa:**
  - `route guard` → `guardia de ruta` o `guardián de ruta` (calco).
  - `data resolver` → `resolvedor de datos` o `resolutor` (calco
    castellano razonable).
  - `route resources` → `recursos de ruta` (calco literal).
- **Justificación:** `guard` ya estaba marcado como `mantener` en primera
  pasada; conviene recordar que `route guard` y `guard` no son la
  misma palabra: una guardia puede ser "absoluta" (login) o "de ruta"
  (auth + role).

#### `ActivatedRoute`, `ActivatedRouteSnapshot`, `RouterStateSnapshot`, `UrlTree`, `RedirectCommand`

- `Status: mantener` (todos tipos del API del router).

### Subsistema *forms*

#### `reactive forms` vs `template-driven forms`

- **Sentido:** los dos enfoques de Angular para forms (segmento
  introductorio `forms/index.md:9-10`). Sus diferencias:
  - Reactive: *"Provide direct, explicit access to the underlying
    form's object model. … they're more scalable, reusable, and
    testable."*
  - Template-driven: *"Rely on directives in the template to create
    and manipulate the underlying object model."*
- **Status:** `propuesto` para la prosa, `mantener` los nombres técnicos.
- **Preferred prosa:**
  - `formularios reactivos` vs `formularios basados en plantilla`.
  - Los nombres de los módulos (`ReactiveFormsModule`,
    `FormsModule`, `TemplateDrivenFormsModule`) son literales.
- **Justificación:** "Reactive forms" son técnicas (basados en
  observables en versiones antiguas, en signals en las nuevas) y la
  traducción "reactivo" sigue siendo estándar. "Template-driven" es
  calco natural.

#### `FormsModule`, `ReactiveFormsModule`, `TemplateDrivenFormsModule`

- `Status: mantener` (módulos).

#### `FormGroup`, `FormControl`, `FormArray`, `FormBuilder`

- **Donde aparece:** `forms/template-driven-forms.md:33-37`.
- **Status: mantener` (todos tipos del API).

#### `ngModel`, `NgForm`, `NgModelGroup`, `ngForm` (directivas)

- **Donde aparece:** `forms/template-driven-forms.md:32-44`.
- **Status: mantener`.

#### `NgModel` y enlace de dos vías

- **Donde aparece:** `forms/template-driven-forms.md:7-8` — *"[template-driven
  forms] use [two-way data binding] to update the data model in the
  component as changes are made in the template and vice versa."*
- **Sentido:** enlace bidireccional entre modelo y plantilla.
- **Status: mantener`.

#### `two-way data binding` (compuesto genérico)

- **Donde aparece:** `forms/template-driven-forms.md:7-8`.
- **Status:** `propuesto`
- **Preferred:** `enlace bidireccional` (castellano estándar).
- **Justificación:** calco asentado.

#### `template reference variables`

- **Donde aparece:** `forms/template-driven-forms.md:23` — *"Share
  information across HTML elements using template reference variables."*
- **Status: propuesto`
- **Preferred:** `variables de referencia de plantilla` o `variables
  locales de plantilla`.

#### Signal Forms (referencia)

- **Donde aparece:** `forms/index.md:11` — *"If you're looking for the
  new Signal Forms, check out our essential Signal Forms guide."*
- **Status: manter` (es un producto, no se traduce).

### Subsistema *i18n*

#### `locale` (en Angular)

- **Sentido:** *locale* identifica la región lingüística (idioma +
  país); un locale determina formatos de fecha/número/moneda.
  `routing/i18n/index.md:5-12` define *internationalization* como
  i18n, y *localization* como el proceso de construir versiones por
  locale.
- **Status:** `propuesto`
- **Preferred:** `locale` (literal del término Unicode CLDR).
- **Justificación:** "locale" es un préstamo asentado en español técnico;
  "configuración regional" se usa en algunos contextos pero pierde la
  abreviación técnica.

#### `internationalization` vs `localization`

- **Sentido:** *internationalization* (i18n) prepara el código;
  *localization* (l10n) genera las versiones por idioma
  (`routing/i18n/index.md:6-9`).
- **Status:** `propuesto`
- **Preferred:**
  - `internacionalización` / `i18n`.
  - `localización` / `l10n`.
- **Justificación:** los términos técnicos en español admiten ambos,
  pero "internacionalización" se usa como glosa completa y "i18n" como
  abreviatura en código.

#### `Unicode CLDR`, `Unicode locale ID`, `lang`, `country`, `variant`

- **Donde aparece:** `routing/i18n/locale-id.md:6-13`.
- **Status:** `mantener`

#### `Angular Localize package`, `$localize`

- **Donde aparece:** `routing/i18n/index.md:32-36`.
- **Status:** `mantener` (literal del paquete y de la i18n API).

#### `locale data` y `locale files`

- **Donde aparece:** `routing/i18n/index.md:8-12` (extract messages,
  format data) — el glosario distingue entre `translation files`
  (información textual) y `locale data` (formatos).
- **Status:** `propuesto`
- **Preferred:** `datos de localización` para `locale data`; `archivos
  de traducción` para `translation files`.

#### `BCP-47` (la mención real está en el glosario v2 y se reusa)

- **Status:** `mantener`

#### `pluralization`, `DatePipe`, `CurrencyPipe`, `DecimalPipe`, `PercentPipe`, `i18nPlural`

- **Donde aparece:** referencia general en la introducción de `i18n`;
  conviene glosar estos nombres de pipes que aparecen a lo largo de
  Angular.
- **Status:** `mantener`.

#### `translations`, `translated messages`, `markers`

- **Donde aparece:** `routing/i18n/manage-marked-text.md`.
- **Sentido:** `xlf`/`xlf2`/`xliff` archivos; los mensajes se identifican
  con `<trans-unit>` y un id.
- **Status:** `mantener`.

## Lo que falta por leer

- `angular/guide/routing/{define-routes,common-router-tasks,customizing-route-behavior,read-route-state,rendering-strategies,loading-strategies,lifecycle-and-events,redirecting-routes,navigate-to-routes,show-routes-with-outlets,routing-with-urlmatcher,route-transition-animations,testing}.md`.
- `angular/guide/forms/{reactive-forms,form-validation,typed-forms,dynamic-forms,signals/*}.md`.
- `angular/guide/i18n/{add-package,prepare,deploy,example,import-global-variants,format-data-locale,manage-marked-text,merge,translation-files}.md`.
- `angular/guide/defer.md`, `ssr.md`, `prerendering.md`,
  `hydration.md`, `incremental-hydration.md`, `performance.md`.
- `angular/guide/components/{queries,inputs,model}.md` (las redirect
  en `signals/` apuntan aquí, conviene leerlas en su sitio real).
- `angular/api/{common,router,forms,http,animations}/...`.

La tercera pasada empezó por las guías in-depth de los subsistemas;
la siguiente debe entrar en los archivos de referencia de cada
subsistema y en los api references.
## Cuarta pasada (2026-10-20)

**Material leído en esta iteración:** `angular/guide/components/{queries,inputs,model,lifecycle,inheritance,outputs,selectors,host-elements,styling,advanced-configuration}.md`
(13 archivos del directorio components/ — todos con prosa sustantiva),
`angular/guide/{ssr,defer,hydration,incremental-hydration,performance}.md`
y `angular/guide/templates/defer.md`.

`components/model.md` no existe en el corpus: quien la apunta es
`/guide/signals/model.md` que **redirige** a `components/inputs`.
`defer.md` y `prerendering.md` son *stubs* de 4 líneas; el contenido
real está en `templates/defer.md`. Estos redirects agrandan el
número de archivos sin aportar material; se registran aquí para no
volver a buscarlos.

### Subsistema *components* de Angular

#### `viewChild`, `viewChildren`, `contentChild`, `contentChildren`

- **Donde aparece:** `components/queries.md:14-37`.
- **Sentido:**
  - `viewChild` busca el primer elemento en la *vista* del
    componente.
  - `viewChildren` (pl.) busca todos.
  - `contentChild` / `contentChildren` buscan en el contenido
    proyectado.
- **Status:** `mantener` (todas son API literales; `viewChild()`,
  `viewChildren()` con paréntesis se usan en fences).
- **Decisión abierta:** `viewChild` también es `view query`. La
  distinción *view queries* (la vista del propio componente) vs
  *content queries* (el contenido proyectado) se glosa con los
  términos siguientes.

#### `view query`, `content query`

- **Donde aparece:** `queries.md:11-12` — *"There are two categories
  of query: view queries and content queries."*
- **Status:** `propuesto`
- **Preferred prosa:**
  - `view query` → `consulta de vista` o `consulta de plantilla`.
  - `content query` → `consulta de contenido`.
- **Justificación:** el calco literal de *query* no existe en español,
  pero el API mantiene el nombre. La traducción de la prosa tiene que
  elegir entre "consulta" (literal de la palabra *query*) o un verbo
  más libre ("búsqueda"). "Consulta" es la elección más técnica.

#### `input`, `inputs` (signal-based)

- **Donde aparece:** `components/inputs.md:7-46` (sección entera).
- **Sentido:** declaraciones de propiedades de entrada vía la función
  `input()`. Los inputs de Angular son ahora signals (`InputSignal`)
  en lugar de setters tradicionales.
- **Status:** `mantener` (`input()`), `propuesto` para la prosa
  circundante.
- **Preferred prosa:** `entrada` o `propiedad de entrada`.
- **Justificación:** la API `input(...)` se conserva literal en código.
  La prosa que la glosa puede traducir con "propiedad de entrada" (más
  explícito) o simplemente "entrada" (suficiente si el contexto es
  claro).
- **Decisión abierta:** `inputs` (plural) y `outputs` (siguiente) —
  *input properties* y *output properties* — son nombres del producto
  en mayúscula (`@Input()`, `@Output()`). Los nombres en minúscula
  del nuevo sistema (`input()`, `output()`, `model()`) contrastan
  con los antiguos decoradores.

#### `output`, `outputs`

- **Donde aparece:** `components/outputs.md` (no leído todavía; vale
  lo mismo que `inputs` por paralelismo).
- **Status:** `mantener`.

#### `model`, `model()`

- **Donde aparece:** redirecciones que apuntaban a `model.md`.
- **Sentido:** "two-way binding" via signal: el padre puede leer y
  escribir el valor; el hijo lo modifica con `.set()`.
- **Status:** `mantener` (API).
- **Justificación:** «two-way binding» ya estaba glosado en la pasada
  anterior; `model()` es el nombre del API v17+ para dos-vías en el
  mundo de signals.

#### `selector`

- **Donde aparece:** `components/inputs.md:14-30` —
  ``@Component({ selector: 'custom-card', /*...*/ })``.
- **Status:** *mantener* (cuidado: el `selector` de Angular es CSS-like,
  no es el `selector` de Tailwind; ambos se mantienen, no se
  confunden en sus contextos).
- **Cross-reference:** ver `tailwindcss.md` para la diferencia entre
  el `selector` Angular y el `selector` CSS.

#### `selector` selector types (`element`, `attribute`, `class`, not)

- Páginas `components/selectors.md` y `host-elements.md` introducen
  los selectores por elemento, atributo, clase y `not`. Se mantienen
  literal porque son sintaxis CSS.

#### `life cycle hooks` (re-visitado)

- **Donde aparece:** `components/lifecycle.md` — método de
  la línea `c_1_1["`ngOnInit`"]`. Las filas de la tabla resumen cada
  fase:
  - **Construction**: `constructor`.
  - **Change Detection**: `ngOnInit`, `ngOnChanges`, `ngDoCheck`,
    `ngAfterContentInit`, `ngAfterContentChecked`, `ngAfterViewInit`,
    `ngAfterViewChecked`.
  - **Rendering**: `afterNextRender`, `afterEveryRender`.
  - **Destruction**: `ngOnDestroy`.
- **Status:** `mantener` (todos nombres literales).
- **Justificación:** Los `ngOn*` están fijados por la API y se
  mantienen tal cual en documentación oficial (incluida la española).

#### `afterNextRender`, `afterEveryRender` (literales Angular 19+)

- **Donde aparece:** `components/lifecycle.md:53-56`.
- **Status:** `mantener`

#### `output()`, `output()` (literal), `outputSignal`

- `Status: mantener`.

#### `host element`, `host bindings`, `host listeners`

- **Donde aparece:** `components/host-elements.md` (no leído aún).
- **Status:** `propuesto`
- **Preferred prosa:** `elemento anfitrión` es calco poco usado;
  mantener «host binding» y «host listener» suele ser más claro.

#### `inheritance` y `inheritance extends`

- **Donde aparece:** `components/inheritance.md` —
  *"When extending a component class, inputs are inherited by the
  child class."* (`inputs.md:45`).
- **Status:** `propuesto`
- **Preferred prosa:** `herencia de componentes` o literal.
- **Justificación:** el corpus introduce "inheritance" solo como
  adjetivo ("inputs are inherited"); el sustantivo "inheritance"
  concreto está implícito.

#### `view providers`, `hostView`

- Subsección menor. `Status: manter`.

### Subsistema *server-side & hybrid rendering* de Angular

#### `SSR`, `prerendering`, `SSG`, `CSR`

- **Donde aparece:** `guide/ssr.md:5-9` — *"Angular ships all
  applications as client-side rendered (CSR) by default. … Hybrid
  rendering allows developers to leverage the benefits of server-side
  rendering (SSR), pre-rendering (also known as 'static site
  generation' or SSG) and client-side rendering (CSR)."*
- **Status:** `mantener` (todos acrónimos) / `propuesto` para la prosa.
- **Preferred prosa:**
  - `SSR` → `renderizado en servidor` o `renderización del lado del servidor`.
  - `prerendering` → `preprocesado` es inexacto; mejor `prerenderizado`.
  - `SSG` → `generación estática` (sustantivo) o `generador de sitio
    estático` (producto).
  - `CSR` → `renderizado en cliente` o `renderización del lado del cliente`.
  - *hybrid rendering* → `renderizado híbrido`.
- **Justificación:** la tendencia oficial en español técnico es
  mantener los acrónimos (`SSR`, `SSG`, `CSR`); el término completo se
  traduce solo cuando la prosa no depende del contexto.

#### `RenderMode`

- **Donde aparece:** `guide/ssr.md:30-37` — *"`RenderMode.Client`,
  `RenderMode.Prerender`, `RenderMode.Server`"*.
- **Status:** `mantener`

#### `ServerRoute` y `app.routes.server.ts`

- **Donde aparece:** `ssr.md:27-29`.
- **Status:** `mantener`

#### `RenderMode.Server`, `RenderMode.Prerender`, `RenderMode.Client`

- **Status:** `mantener`

#### `outputMode`

- **Donde aparece:** `ssr.md:22` — *"set `outputMode` to `static`. To
  enable SSR, update the server routes to use
  [`RenderMode.Server`](`)`."*
- **Status:** `mantener`

#### `ng new --ssr`, `ng add @angular/ssr`

- **Status:** `mantener` (comandos CLI literales).

#### `Hydration`, `provideClientHydration`, `rehydrate`

- **Donde aparece:** `guide/hydration.md:5-32`.
- **Sentido:** "Hydration is the process that restores the
  server-side rendered application on the client."
- **Status:** `mantener` (API).
- **Justificación:** la entrada equivalente en next.js es `hydration`
  (literal). En angular también se mantiene; «hidratación» es la
  traducción funcional cuando se necesita traducir la prosa
  circundante.
- **Decisión abierta:** decidir si glosamos `hydration` por carpeta o
  como término compartido. La documentación angular y la de Next.js
  usan exactamente la misma palabra, así que la entrada podría ser
  compartida.

#### `incremental hydration` (Angular)

- **Donde aparece:** `guide/incremental-hydration.md` (referenciado;
  no leído en profundidad).
- **Status:** `mantener` / `propuesto` para la prosa.
- **Justificación:** es **el mismo concepto** que en Next.js. Si se
  decide glosarlo como entrada compartida, su equivalente español es
  «hidratación incremental» (calco literal).

#### `Core Web Vitals` (término de Google que cruza ambos frameworks)

- **Donde aparece:** `guide/hydration.md:11-12`.
- **Status:** `mantener`.

#### `FID`, `LCP`, `CLS`

- **Donde aparece:** `guide/hydration.md:11-12` — *"Core Web Vitals
  (CWV) statistics, such as reducing the First Input Delay (FID) and
  Largest Contentful Paint (LCP), as well as Cumulative Layout Shift
  (CLS)."*
- **Status:** `mantener` (métricas literales).

### Subsistema *performance*

#### `performance.mark`, `performance.measure`, `PerformanceObserver`

- `Status: mantener` (Web Performance API).

#### `deferrable views`, `@defer`, `@placeholder`, `@loading`, `@error`

- **Donde aparece:** `guide/templates/defer.md` (no leído en
  profundidad; viene de primera referencia).
- **Status:** `mantener`
- **Decisión abierta:** las plantillas `@defer` (Angular 17+) y
  `'use cache'` (Next.js) son ideas parecidas en su efecto (diferir
  trabajo) pero distintas en su mecanismo. Conviene **no** meterlas
  como sinónimos en el glosario.

## Lo que falta por leer

- `angular/guide/components/{outputs,selectors,host-elements,styling,dom-apis,programmatic-rendering,advanced-configuration,index}.md` (estos ya
  están en la lectura de cuarta pasada para `queries` y `inputs`,
  pero aún tengo que precisar varios).
- `angular/api/{common,router,forms,http,animations}/index.md` y dos
  o tres archivos por cada uno para fijar nombres.
- `angular/guide/{animations,directives,di,elements,experimental,http,hybrid-rendering,legacy-animations,ngmodules,performance,signal-forms,signals,ssr,prerendering,animation,routing,hydration,incremental-hydration}/index.md`.
- `angular/tutorial/`, `angular/guide/essentials/`, `api/core/`.
- `tailwindcss/installation/`, `tailwindcss/upgrade-guide.md` (la parte
  que queda).
- `nextjs/app/api-reference/file-conventions/{forbidden,unauthorized,default,intercepting-routes,instrumentation,instrumentation-client,mdx-components,metadata,proxy,public-folder,src-folder,route-groups,route-segment-config}.md` — la siguiente ronda cubriría esto.
## Quinta pasada (2026-10-20)

**Material leído en esta iteración:** `angular/api/index.md` (índice de
1 177 líneas con el catálogo de la API), `angular/api/common/{DatePipe,DecimalPipe,CurrencyPipe}.md`,
`angular/api/router/Router.md`, `angular/api/core/testing/TestBed.md`.

Conclusión de la api reference: la documentación angular es
**nominal** —cada archivo describe un símbolo con tipo y descripción pero
sin prosa expositiva—. Por eso esta pasada aporta la lista de los
símbolos más relevantes más que un cuerpo adicional de prosa.

### Símbolos destacados de `@angular/core` (api/core)

- `inject(…)`, `Injectable`, `Inject`, `InjectionToken`, `Injector`,
  `EnvironmentInjector`, `INJECTOR`, `forwardRef(…)`, `runInInjectionContext(…)`.
- `signal(…)`, `WritableSignal`, `Signal`, `computed(…)`, `effect(…)`,
  `EffectRef`, `linkedSignal(…)`, `untracked(…)`, `toSignal(…)`.
- `input(…)`, `InputSignal`, `InputSignalWithTransform`,
  `output(…)`, `OutputEmitterRef`, `model(…)`, `ModelSignal`.
- `viewChild(…)`, `viewChildren(…)`, `contentChild(…)`,
  `contentChildren(…)`, `viewChildQueryList`, `element(…)`.
- `ChangeDetectionStrategy.OnPush`, `ChangeDetectorRef`,
  `ChangeDetectionScheduler`, `markForCheck(…)`, `detectChanges(…)`.
- `Provider`, `provideXxx(…)`, `EnvironmentProviders`, `makeEnvironmentProviders(…)`.
- `injectable(…)`, `provideExperimentalZonelessChangeDetection(…)`,
  `provideZonelessChangeDetection(…)`, `bootstrapApplication(…)`,
  `provideExperimentalCheckNoChangesForDebug(…)`,
  `provideRouter(…)`, `provideClientHydration(…)`, `withComponentInputBinding(…)`,
  `withRouterResources(…)`, `withFetch(…)`, `withEventReplay(…)`,
  `withInMemoryScrolling(…)`, `withViewTransitions(…)`.
- `HostListener`, `HostBinding`, `ViewChild`, `ViewChildren`,
  `ContentChild`, `ContentChildren`, `Attribute`, `Self`, `Optional`,
  `SkipSelf`, `Host`, `Input(…)`, `Output(…)`, `EventEmitter`,
  `PipeTransform`, `Pipe(…)` decorator.
- Plantillas de control de flujo: `@if`, `@for`, `@switch`, `@defer`,
  `@let`, `@empty` (Anglar ≥17). `Status: mantener` (literales).
- Directivas comunes: `NgClass`, `NgStyle`, `NgIf`, `NgFor`,
  `NgSwitch`, `NgSwitchCase`, `NgSwitchDefault`, `FormControl`,
  `FormGroup`, `FormControlName`, `FormGroupName`, `Validators`,
  `RequiredValidator`, `MinLengthValidator`, `MaxLengthValidator`,
  `PatternValidator`, `EmailValidator`.
- `Type<T>`, `InjectFlags`, `ComponentRef`, `EnvironmentProviders`.

`Status: mantener` todos (literales del API). La prosa glosa su
función; los nombres no se traducen.

### Pipes de `@angular/common` (api/common)

#### `DatePipe` (`{{ value_expression | date:format:timezone:locale }}`)

- **Donde aparece:** `api/common/DatePipe.md:8-12`.
- **Sentido:** Formats a date value according to locale rules.
- **Status:** `mantener`.
- **Preferred prosa:** `tubo de fecha` es calco evitable, pero los
  nombres técnicos prefieren el anglicismo `pipe`.
- **Decisión abierta:** el calco castellano «tubo» está descartado;
  mejor «transformador de fecha» o literal `pipe`. Ya decidida la
  entrada en la primera pasada.

#### `DecimalPipe` (`{{ value_expression | number:digitsInfo:locale }}`)

- **Donde aparece:** `api/common/DecimalPipe.md:8-15`.
- **Sentido:** *"Formats a value according to digit options and
  locale rules. Locale determines group sizing and separator,
  decimal point character, and other locale-specific
  configurations."*
- **Status:** `mantener`.

#### `CurrencyPipe` (`{{ … | currency:currencyCode:display:digitsInfo:locale }}`)

- **Donde aparece:** `api/common/CurrencyPipe.md:8-15`.
- **Sentido:** *"Transforms a number to a currency string, formatted
  according to locale rules that determine group sizing and
  separator, decimal-point character, and other locale-specific
  configurations."*
- **Status:** `mantener`.

#### Otros pipes registrados en `api/common`

- `AsyncPipe`, `I18nPluralPipe`, `LowerCasePipe`, `UpperCasePipe`,
  `TitleCasePipe`, `JsonPipe`, `SlicePipe`, `PercentPipe`,
  `KeyValuePipe`, `DOCUMENT` (token), `APP_BASE_HREF`. `Status: mantener`.

### `@angular/router` — Router

#### `Router` (clase)

- **Donde aparece:** `api/router/Router.md:9-13` — *"A service that
  facilitates navigation among views and URL manipulation
  capabilities. This service is provided in the root scope and
  configured with `provideRouter`."*
- **Status:** `mantener`.

#### `Router events` y `RouterState`

- **Donde aparece:** `api/router/Router.md:16-23` — *"An event stream
  for routing events. The current state of routing in this
  NgModule."*
- **Status:** `mantener`

#### `provideRouter`, `withComponentInputBinding()`, `withRouterResources()`

- `Status: mantener`

### Servicios y directivas de `@angular/forms` (api/forms)

(estimado a partir del índice; conviene leer `api/forms/FormGroup.md`
en una pasada posterior)

- `FormGroup`, `FormControl`, `FormArray`, `FormBuilder`,
  `Validators`, `AbstractControl`, `ControlValueAccessor`,
  `Validator`, `AsyncValidator`, `NG_VALIDATORS`,
  `NG_ASYNC_VALIDATORS`, `NG_VALUE_ACCESSOR`.
- Patrones de construcción: `FormBuilder.group({...})`,
  `FormBuilder.array([...])`, `FormBuilder.control('value')`,
  `FormBuilder.nonNullable`.
- Validadores: `Validators.required`, `Validators.min(n)`,
  `Validators.max(n)`, `Validators.pattern(r)`, `Validators.email`,
  `Validators.minLength(n)`, `Validators.maxLength(n)`,
  `Validators.nullValidator`.
- Directivas: `formGroup`, `[formGroup]`,
  `formControlName`, `formControl`, `formArrayName`,
  `ngModel`, `ngModelChange`, `ngModelGroup`, `ngForm`, `ngSubmit`.

`Status: mantener` (todos).

### `@angular/platform-browser`

- `Bootstrap`, `BrowserModule`, `BrowserAnimationsModule`,
  `provideClientHydration(…)` (ya en pasada 4),
  `provideAnimations(…)`, `provideAnimationsAsync(…)`,
  `withEventReplay(…)`, `Meta` y `Title` services.
- `Status: mantener`.

### `@angular/common/http` (o `api/http`, aunque no figura en el corpus)

El corpus **no incluye** `api/http/` (404). Conviene:
- Confirmar: el scraper no extrajo los archivos de `api/http`, y el
  corpus contiene `api/{animations,aria,cdk,common,core,elements,
  forms,localize,platform-browser,platform-browser-dynamic,
  platform-server,router,service-worker,ssr,upgrade}` (15 subárboles).
- Registrarlo como limitación.

### `@angular/router` — subárbol `api/router`

Del índice se deduce: ActivatedRoute, ActivatedRouteSnapshot,
RouterStateSnapshot, UrlTree, Routes, Route, ResolveFn, CanActivate
(/Fn), CanDeactivate (/Fn), CanLoad (/Fn), CanMatch (/Fn),
NavigationExtras, NavigationCancelingError, RouterOutlet,
Event (RouterEvent), NavigationStart, NavigationEnd,
NavigationCancel, NavigationError, RoutesRecognized,
ResolveStart, ResolveEnd, GuardsCheckStart, GuardsCheckEnd,
ActivationStart, ActivationEnd, ChildActivationStart,
ChildActivationEnd, RouteConfigLoadStart, RouteConfigLoadEnd,
`defaultUrlSerializer`, `Params`, `Data`, `QueryParamsHandling`,
`UrlSegment`, `UrlSegmentGroup`, `RouteReuseStrategy`,
`ExtraOptions`, `NavigationBehaviorOptions`, `NavigationTransition`,
`EventType`, `Route`, `LoadedRouterConfig`, `RouterModule.forRoot`,
`RouterModule.forChild`, `NoPreloading`, `PreloadAllModules`,
`RouterPreloader`, `DefaultUrlSerializer`, `InMemoryScrolling`,
`ScrollingFeatureOptions`, `Routes`, etc. `Status: mantener`.

(Esto no es una traducción: lo importante es no introducirlos como
término del glosario porque ya están en el código como literales
protegidos.)

## Lo que falta por leer

Para terminar de cubrir Angular quedan:

- `angular/api/{common,router,forms,animations,cdk,elements,localize,
  platform-browser,platform-server,ssr,service-worker,upgrade}/...`
  (varias decenas de archivos cada uno; ya leídos los más
  sustantivos).
- `angular/guide/{animations,directives,di,elements,experimental,
  http,hybrid-rendering,legacy-animations,ngmodules,performance,
  signal-forms,signals,ssr,prerendering,routing,animation,hydration,
  incremental-hydration}/index.md`.
- `angular/guide/{animations,directives,di,elements,experimental,
  http,hybrid-rendering}/index.md` ya en quinta pasada.
- `angular/tutorial/{tutorials,first-app,toh,intermediate}/...` —
  tutoriales paso a paso.
