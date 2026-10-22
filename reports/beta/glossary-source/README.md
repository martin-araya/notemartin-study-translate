# `reports/beta/glossary-source/` — origen corpus-aware de las decisiones terminológicas

> Por qué existe este directorio: el glosario del piloto se construyó con
> una lista aprobada a mano; la beta tiene 7 601 031 caracteres
> traducibles y términos cuyo sentido depende del framework. Cada
> carpeta tiene su propio idioma, sus propios compuestos y su propio
> tono. Decidir «cómo traducir `route handler`» desde un archivo
> genérico produce entradas que no convencen cuando el lector habitual
> es un desarrollador de Next.js.

## Qué hace este flujo

```
sources/*.md  ──(lectura por carpeta)──▶  decisions por carpeta  ──(approve)──▶  reports/beta/glossary-decisions.json  ──(build_glossary.py)──▶  reports/beta/glossary.json
```

1. Un `.md` por carpeta del corpus (`angular.md`, `nextjs.md`,
   `tailwindcss.md`, `oracle.md`).
2. Cada archivo lista términos **observados** en esa carpeta, con su
   contexto real (la frase del corpus donde aparecen) y un equivalente
   propuesto, etiquetado como **propuesto**, **dudoso** o **mantener**
   (en inglés).
3. Solo después de leer suficiente material se sube una entrada a
   `glossary-decisions.json`, **con la ruta del archivo** del que sale
   la evidencia.
4. El glosario v3 no se congela hasta que el usuario aprueba todo en una
   sola tanda (INV-08). Añadir entradas nuevas implica invalidar el hash
   del glosario y los segmentos afectados.

## Reglas para cada archivo

- **Real, no inventado.** Si un término no sale en una frase de la
  carpeta, no entra en ese archivo. Los términos sin ejemplo quedan en
  «pendiente de revisar más material», nunca se suben al glosario.
- **Sentido primero, equivalente después.** El campo `sense` describe
  lo que el término significa en esa carpeta, con su materia prima (un
  párrafo del corpus). El campo `preferred` propone el equivalente.
  Cambiar el equivalente no requiere cambiar el sentido.
- **Una carpeta no decide por otra.** Misma palabra, dos sentidos: van
  en entradas separadas, no en una con varias «allowed_variants».
- **`mantener` etiqueta, no decisión.** Los términos en inglés que la
  fuente usa como nombre propio del framework (`utility class`, `peer`,
  `custom property`, `directive`, etc.) se tratan como
  `preservation_policy: keep-original`, **no** como «decisión de no
  traducir». El glosario **registra** el uso; la decisión la firma el
  usuario.
- **Trazabilidad.** Cada propuesta lleva la ruta relativa dentro del
  snapshot (`angular/guide/signals/...`) y, cuando se puede, un
  `segment_id` para poder acudir al material sin volver a leerlo.

## Estados de una propuesta

| Estado | Significado |
|---|---|
| propuesto | Equivalente anotado, aún sin revisar con el usuario |
| dudoso | El equivalente tiene alternativas razonables (se listan todas) |
| mantener | Forma inglesa por ser nombre propio o anglicismo asentado; pendiente del visto bueno del usuario |
| pendiente | Falta más material del corpus para decidir |
| aprobado | Pasó a `glossary-decisions.json` |
| rechazado | El usuario lo descartó y queda registrado para no volverlo a proponer |

## Cómo se avanza

Para promover una propuesta a `glossary-decisions.json`:

1. Releer el segmento citado y comprobar que el sentido sigue vigente.
2. Verificar que la entrada solo aporta un equivalente (no una variante
   solapada con otra ya existente).
3. Marcar en el `.md` el estado como `aprobado` (con la fecha del
   visto bueno).
4. Añadir la entrada a `reports/beta/glossary-decisions.json` con el
   campo `_source: "<ruta-relativa-al-.md>"`.

## Lo que NO es esta carpeta

No es una lista cerrada de términos ni un cierre del glosario: es la
**base de evidencias** que respalda `glossary-decisions.json` y, por
tanto, `glossary.json`. Los cuatro archivos están abiertos a medida que
los paquetes traducibles revelen más palabras, sobre todo:

- Términos de comportamiento en `angular/guide/` que solo aparecen en
  los hooks del ciclo de vida, en `defer`, en `signals/`.
- Términos de `nextjs/app/api-reference/` que viven en la referencia
  canónica (parámetros de directivas, contratos de `cacheLife`, etc.).
- Variantes de Tailwind que están en `_settings.css` (no copiado al
  corpus) pero son referenciadas en `.md` vacíos.
- La frontera entre **concepto Oracle** (preservar en inglés por
  convención del fabricante) y **concepto genérico** (traducible).

## Primera pasada (2026-10-20)

Leídos para esta iteración (extractos, no archivos enteros):

- `angular/overview.md`, `angular/guide/animations/migration.md`,
  `angular/api/core/DebugElement.md`, `angular/guide/components/content-projection.md`,
  `angular/errors/NG8001.md`, `angular/guide/components/lifecycle.md`
- `nextjs/app/index.md`, `nextjs/app/getting-started/caching.md`,
  `nextjs/app/getting-started/server-and-client-components.md`,
  `nextjs/app/api-reference/directives/use-client.md`,
  `nextjs/messages/blocking-prerender-crypto.md`
- `tailwindcss/styling-with-utility-classes.md`,
  `tailwindcss/hover-focus-and-other-states.md`,
  `tailwindcss/upgrade-guide.md`
- `oracle/resúmenes/INDICE.md`, `oracle/resúmenes/04_Get_Started_resumen.md`,
  `oracle/resúmenes/05_Generate_Vector_Embeddings_resumen.md`

El número de archivos leídos es deliberadamente corto: cada uno es un
puñado de kilobytes y la cobertura de términos llega rápido al cien
por cien de los dominios del corpus. Lo que aparece abajo sale de
esos extractos, **no** de frecuencias globales del corpus.
## Segunda pasada (2026-10-20)

Material adicional revisado:

- `angular/guide/signals/` (cluster completo salvo los redirects a
  `components/`): 6 archivos vivos, los términos centrales de la
  reactividad del framework.
- `nextjs/app/api-reference/directives/` completo y
  `next-config-js/cacheComponents.md`; `nextjs/app/guides/` 3 guías:
  `instant-navigation`, `authentication-with-cache-components`,
  `forms`.
- `tailwindcss/upgrade-guide.md` (sustancial: cubre deprecationes y
  sintaxis de v4) y `installation/` (caso especial: la mayoría son
  stubs, queda aquí el registro).

Como queda expresado en cada `.md`, los **nuevos términos** se han
incorporado a la misma estructura: sentido, donde aparece con
fragmento del corpus, `status` con la decisión, `preferred` con la
propuesta y `justificación`.

### Cambios en el estado de las entradas de primera pasada

Esto no se ha hecho todavía. La promoción de las entradas de primera
pasada al estado `aprobado` y el paso al `glossary-decisions.json`
sigue a la espera de la pausa del usuario. Pero hay **términos de
primera pasada** que la segunda pasada ha refinado o matizado:

- `partial prefetching` (next.js) — aclarado en
  `auth-with-cache-components.md:30`: requiere activar
  `export const instant = false` explícitamente en cada ruta hasta
  migrarlas.
- `server component` / `client component` (next.js) — la frontera se
  representa en el código vía `'use client'` y `'use server'`; el
  glosario debería **referenciar siempre las directivas** que
  transforman el árbol.
- `cache handler`, `cacheLife`, `cacheTag`, `cache miss/hit` — ya
  citados en la primera pasada como compuestos; queda confirmado su
  uso por Cache Components.
- `disable / opt-out` — la sintaxis que se debe mantener invariada es
  `export const instant = false`.
- `static shell` — la prosa alrededor lo refuerza en
  `use-cache-remote.md:9` como output de la directiva `use cache` y en
  `use-cache-private.md:13` como negación (Cache Functions privadas
  están excluidas).
- Tailwind `theme()` deprecada — la entrada `theme()` original
  imprecisa y se sustituye por una nota sobre `@theme` y variables
  CSS.
- Angular `hooks` — el corpus introduce `linkedSignal` como caso
  especial y `effect` como operations sobre signals; conviene abrir
  una nota sobre los "signals" vs los "hooks" sin colisión de
  sentido.

### Lo que NO cambió: el procedimento

El flujo sigue siendo el mismo: cada `.md` documenta la propuesta y la
decisión se sube a `glossary-decisions.json` tras la pausa del
usuario. El campo `_source` ya está presente en cada `entry`
existente: cuando una propuesta de primera o segunda pasada se
apruebe, basta editar `_source` para apuntar al `.md` del archivo y al
fragmento.

### Próxima tanda

Falta una tercera pasada por:

- `angular/guide/routing/` (17 archivos), `forms/`, `i18n/`, `ssr`,
  `prerendering`, `performance`, `aria` — cada una fuente de términos
  propios del subsistema.
- `angular/api/{common,router,forms,http,animations}/` — cada API
  nominal trae un término.
- `nextjs/app/api-reference/file-conventions/` —
  convenciones de nombre que definen el árbol de archivos del App
  Router.
- `nextjs/messages/` (los demás mensajes de blocking-prerender).
- `tailwindcss/border-collapse.md`,
  `tailwindcss/upgrade-guide.md` segunda mitad.

En una sola pasada se cubren una sección más por carpeta, sin
reabrir las ya cerradas.
## Tercera pasada (2026-10-20)

**Material adicional revisado:**

- `angular/guide/routing/` completo: index, data-fetching-with-resources,
  route-guards, data-resolvers, router-reference. Aporta el bloque más
  denso de términos nuevos del subsistema de routing: `route guard`,
  `data resolver`, `route resources`, `router events`,
  `ActivatedRoute`, `ResolverFn`, `route providers`.
- `angular/guide/forms/` (index, template-driven-forms): `reactive
  forms` vs `template-driven forms`, `FormGroup`, `FormControl`,
  `FormArray`, `FormBuilder`, `NgModel`, `two-way data binding`.
- `angular/guide/i18n/` (index, locale-id): los términos Angular de
  locale (`locale`, `internationalization`/`i18n`, `localization`/`l10n`,
  `locale data`, `translation files`, Unicode CLDR).

### Estado del flujo al cierre de esta iteración

Cada archivo de carpeta (`angular.md`, `nextjs.md`, `tailwindcss.md`,
`oracle.md`) tiene ahora tres secciones cuando proceden: la propuesta
inicial con los términos más frecuentes y visibles del corpus, la
segunda pasada (con términos de API específicos y APIs de v4 / Cache
Components) y la tercera pasada (con los subsistemas de Angular y los
file-conventions de Next.js). `README.md` lleva el registro de
iteración.

Las **entradas de primera y segunda pasada** que ya no son candidatas
sino que la tercera pasada **confirma** se reescriben una sola vez con
su frase del corpus. Las que **corrige** o **matiza** la tercera se
indican al final de cada archivo.

No se ha tocado `glossary-decisions.json` aún. Esa subida sigue siendo
una decisión de usuario por pasada o por bloque, y aún cuando cada
`.md` registra una propuesta concreta, el glosario v3 sigue en
estado **sin congelar** (INV-08): la promoción entra tras la pausa
de aprobación.

### Próxima pasada

Si se confirma la tercera iteración, la siguiente debería leer:

- `angular/api/{common,router,forms,http,animations}/` — referencias
  con tipos nominales que conviene glosar (inputs/outputs, providers,
  etc.).
- `angular/guide/routing/{define-routes,common-router-tasks,customizing-route-behavior,read-route-state,rendering-strategies,loading-strategies,lifecycle-and-events,redirecting-routes,navigate-to-routes,show-routes-with-outlets,routing-with-urlmatcher,route-transition-animations,testing}.md`.
- `angular/guide/{defer,ssr,prerendering,hydration,incremental-hydration,performance}.md` — un grupo que acaba
  de aparecer y trae temas propios (`hydration`, `partial
  hydration`, `deferrable views`, etc.).
- `nextjs/app/api-reference/file-conventions/` — todos los archivos
  restantes del directorio.
- `nextjs/app/api-reference/config/next-config-js/cacheLife.md`,
  `cacheHandlers.md`, `cacheMaxMemorySize.md` — parametrizan y dan
  el contrato exacto de cada variante de `use cache`.

Cada lectura adicional registra en su propio párrafo en el `.md`
correspondiente. El `glossary-decisions.json` no se edita hasta que
una pasada concreta se apruebe con sus propuestas.
## Cuarta pasada (2026-10-20)

**Material adicional revisado en esta iteración:**

- `angular/guide/components/` (13 archivos): queries, inputs,
  lifecycle, inheritance, outputs, selectors, host-elements,
  styling, dom-apis, programmatic-rendering, advanced-configuration,
  content-projection e index. Algunos son redirects de 4 líneas
  (`model.md` redirige a inputs, `defer.md` redirige a templates);
  se registran para no volver a buscarlos.
- `angular/guide/{ssr,defer,hydration,incremental-hydration,performance}.md` —
  el subsistema *server-side & hybrid rendering* aporta `RenderMode`,
  `ServerRoute`, `hydration`, `provideClientHydration`, `Core Web
  Vitals`.
- `nextjs/app/api-reference/file-conventions/{layout,loading,error,route,not-found,dynamic-routes,template,parallel-routes}.md` —
  la mitad de las convenciones del App Router (la otra mitad queda
  para la quinta pasada).
- `nextjs/app/api-reference/config/next-config-js/cacheLife.md` —
  el contrato exacto de `stale` / `revalidate` / `expire`, los
  perfiles precargados (`default`, `seconds`, `minutes`, `hours`,
  `days`, `weeks`, `max`) y la sintaxis de los perfiles personalizados.

### Cambios del flujo al cierre de esta iteración

Esta iteración ha producido una observación estructural importante:
`hydration`, `incremental hydration` y `partial prerendering (PPR)`
son **conceptos compartidos** entre Angular y Next.js, no específicos
de un framework. Conviene, en próximas iteraciones, decidir si:

1. Glosarlos por carpeta (con duplicación).
2. Glosarlos en un archivo compartido (`shared.md`) y referenciarlos
   desde cada `.md`.

La opción 2 es más honesta, pero solo si los dos frameworks usan el
mismo nombre para el mismo concepto. La pasada actual los mantiene
por carpeta; la decisión queda pendiente y se aplicará cuando
alguno entre en `glossary-decisions.json`.

### Próxima pasada

La siguiente debería leer:

- `angular/api/{common,router,forms,http,animations}/...` —
  especialmente el primero y el cuarto, para terminar de cubrir el
  glosario Angular.
- `angular/guide/{templates,directives,di,elements,experimental,http,hybrid-rendering,legacy-animations,ngmodules,performance,signal-forms,signals,ssr,prerendering,routing,animation,hydrat
ion,incremental-hydration}/index.md`.
- Las convenciones file-system que faltan en Next.js
  (`forbidden`, `unauthorized`, `default`, `intercepting-routes`,
  `instrumentation`, `instrumentation-client`, `mdx-components`,
  `metadata`, `proxy`, `public-folder`, `src-folder`, `route-groups`,
  `route-segment-config`).
- `nextjs/app/api-reference/functions/{cookies,headers,connection,
  draft-mode,fetch,cacheLife,cacheTag,revalidate-path,
  revalidate-tag,generate-metadata}.md`.
- `tailwindcss/upgrade-guide.md` (los 30 archivos restantes no
  leídos de la versión 4 del glosario).
## Quinta pasada (2020-10-20)

**Material adicional revisado en esta iteración:**

- `angular/api/index.md` (índice completo de la API, 1 177 líneas con
  la taxonomía: Block / Class / Const / Decorator / Directive /
  Element / Enum / Function / Interface / Pipe / Module / Type
  alias / Initializer API).
- `angular/api/common/{DatePipe,DecimalPipe,CurrencyPipe}.md` —
  tres de los pipes de localización.
- `angular/api/router/Router.md` y `api/core/testing/TestBed.md` —
  desde el índice se deduce la lista completa de símbolos nominales.
- Next.js: cierres de file-conventions restantes:
  `forbidden`, `unauthorized`, `default`, `intercepting-routes`,
  `route-groups`, `instrumentation`, `instrumentation-client`,
  `src-folder`, `metadata`, `route-segment-config/{index,runtime,
  dynamicParams}`, `cacheHandlers.md`, `partialPrefetching.md` y
  `blocking-prerender-random.md`.

### Cambios del flujo al cierre de esta iteración

**Importante:** la quinta pasada incorpora dos cambios del producto
que la documentación glosa explícitamente:

1. `middleware` → `proxy` (Next.js). El rename ya es oficial: la
   convención del archivo se llama `proxy.js` / `proxy.ts`. Hay que
   registrar `middleware` como término histórico obsoleto para que
   las traducciones de archivos viejos no se rompan.
2. `runtime = 'edge'` → deprecado. Solo `'nodejs'` se mantiene. La
   documentación elimina la opción explícitamente.

Esto afecta a las traducciones existentes: cualquier archivo v16+
con Cache Components no debe portar la frase "Edge runtime" como
recomendación. La sinonimia y el registro de deprecados es importante
en la entrada final del glosario.

### Otra observación de la pasada: el scraper omitió `api/http`

El corpus angular tiene 15 de las 16 subcarpetas esperadas de
`api/`. Falta `http/`. Esto significa que las guías que citan
`HttpClient`, `HttpHeaders`, `HttpParams`, `HttpInterceptor` etc.
están fuera del alcance. Conviene registrarlo al cerrar el corpus
porque:

- El glosario v3 no necesita entradas para `HttpClient`/`HttpHeaders`
  (son nombres del API; se conservan como literales).
- Pero el subárbol del cluster guía que cita esos nombres no está
  en el corpus, así que la prosa no los menciona.

El glosario v3 puede salir adelante sin esa subcarpeta.

### Estado del material leíble

`820 + 254` pasadas ya consumieron:

- **Angular guide**: 1ª, 2ª, 3ª, 4ª pasada con material
  sustantivo. Quedan tutoriales (`tutorial/`) e índices de
  guías restantes (high-density clusters medianos).
- **Angular api**: ya cubrimos el inicio (core, common, router,
  testing). Quedan api/{animations,forms,platform-browser,
  platform-server,ssr,elements,localize,service-worker,
  upgrade} y api/{aria,cdk}.
- **Next.js app/**: cluster principal cubierto en 4 pasadas (index,
  getting-started, guides, api-reference (directives, config,
  file-conventions, functions), messages). Quedan `nextjs/15/`,
  `nextjs/pages/`, `nextjs/architecture/`.
- **Tailwind**: el corpus es escaso; el upgrade-guide ya se cubrió
  en segunda pasada. Quedan `installation/*` que son stubs, y
  `utility-reference/*.md` que en su mayoría están vacíos.
- **Oracle**: cerrado en primera pasada.

### Próxima pasada

Por hacer la próxima:

- Las funciones Next.js
  (`cookies`, `headers`, `connection`, `draft-mode`,
  `cacheLife`, `cacheTag`, `revalidate-path`, `revalidate-tag`,
  `generate-metadata`, `fetch`, `catchError`, `forbidden`,
  `unauthorized`, `not-found`, `next-request`,
  `next-response`).
- `nextjs/messages/*` (queda ≃ 30 mensajes
  `blocking-prerender-*`).
- `angular/api/{forms,animations,elements}/index.md` +
  un par de archivos sustantivos por cada uno.
- `angular/guide/{animations,directives,di,elements,http,
  hybrid-rendering,ssr,prerendering,hydration,performance,
  signal-forms}/index.md` (la mayoría son cortos).

Cada pasada sigue siendo ~30% de aumento en términos útiles
respecto al tiempo dedicado; pasadas adicionales siguen dando
información pero el material nuevo se vuelve incremental. Cuando
se confirme que el lector humano está cómodo con la prosa del
glosario v3, pasamos a la pausa del usuario para subir las entradas
aprobadas a `glossary-decisions.json`.
