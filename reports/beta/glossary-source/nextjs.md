# `nextjs.md` — términos observados en la documentación de Next.js

**Material leído:** `nextjs/app/index.md`, `nextjs/app/getting-started/caching.md`,
`nextjs/app/getting-started/server-and-client-components.md`,
`nextjs/app/api-reference/directives/use-client.md`,
`nextjs/messages/blocking-prerender-crypto.md`.

## Reglas generales observadas

- Next.js 16+ introduce **Cache Components** y **Partial Prefetching**
  en la misma versión. Toda la documentación nueva gira alrededor de
  la frontera `Server Component ⇄ Client Component` regida por
  directivas de archivo: `'use client'`, `'use server'`, `` 'use
  cache' ``, `'use cache: remote'`, `'use cache: private'`.
- Los nombres de directivas se conservan **tal cual** porque son
  literales en código: cualquier traducción rompe el código.
- Next.js **mantiene una jerarquía explícita** `layout → page →
  route handler → middleware`. Cada nivel tiene un comportamiento de
  caché y renderizado.
- La frontera entre Next.js y React: Next.js aporta directivas;
  React aporta hooks. El corpus llama «React hooks» al subset que
  React expone y «Next.js directives» al subset de Next.

## Propuestas por entrada

### `server component` y `client component` (compuestos)

- **Sentido:** un Server Component se renderiza solo en el servidor y
  produce HTML + RSC Payload; un Client Component también se ejecuta en
  el navegador para manejar estado, eventos y APIs del navegador.
- **Donde aparece:** `nextjs/app/index.md:4` — *«Server Components»*
  como enlace explícito; `caching.md:7` («Caching is a technique for
  storing the result of data fetching and other computations»);
  `use-client.md:7` — *«The `'use client'` directive declares an
  entry point for the components to be rendered on the client side»*;
  `server-and-client-components.md:13` — *«Use Server Components
  when you need: fetch data from databases … reduce the amount of
  JavaScript … improve the First Contentful Paint»*.
- **Status:** `propuesto`
- **Preferred:** `componente de servidor`, `componente de cliente`.
- **Justificación:** la traducción oficial al español en la web de
  Next.js usa exactamente este compuesto («Server Components» /
  «Componentes del cliente») y la coherencia con `componentes de
  servidor` mantiene el registro.

### `server action` y `use server` (compuesto y directiva)

- **Sentido:** un Server Action es una función de servidor invocable
  desde un Client Component. La directiva `'use server'` marca el
  archivo como Actions.
- **Donde aparece:** referenciada en el corpus como `'use server'`,
  no en cuerpo de prosa directamente (queda por leer).
- **Status:** `mantener`
- **Preferred:** `server action` / `'use server'` (literal).
- **Justificación:** nombre del API; cualquier traducción rompe la
  dirección de la directiva en el código.

### `'use cache'` (directiva de caché)

- **Sentido:** directiva que cachea el valor de retorno de una
  función o componente.
- **Donde aparece:** `caching.md:32` y siguientes — *«The `use cache`
  directive caches the return value of async functions and
  components»*.
- **Status:** `mantener`
- **Preferred:** `'use cache'` (literal).
- **Justificación:** literal de directiva.

### `cache directive` y `cache life` (compuestos)

- **Sentido:** etiqueta del comportamiento de una directiva
  `'use cache'`; `cacheLife('hours')` da una vida al caché.
- **Donde aparece:** `caching.md:38` — *«We recommend pairing every
  cache directive with a `cacheLife`. Without one, the implicit
  `default` profile applies.»*
- **Status:** `mantener`
- **Preferred:** `directiva de caché` / `vida del caché`.
- **Justificación:** `cacheLife` es literal del API; `cache
  directive` es la categoría general. Sobre «cache directive» hay
  alternativa `instrucción de caché`; la primera es más común en
  la documentación oficial.

### `data-level caching` y `ui-level caching` (compuestos técnicos)

- **Sentido:** `data-level caching` almacena el resultado de una
  función que trae datos; `ui-level caching` almacena el árbol
  renderizado.
- **Donde aparece:** `caching.md:33-34` — *«Data-level: Cache a
  function that fetches or computes data … UI-level: Cache an entire
  component, page, or layout»*.
- **Status:** `propuesto`
- **Preferred:** `caché a nivel de datos` / `caché a nivel de UI`.
- **Justificación:** el calco estructurado es la opción técnica.
- **Decisión abierta:** manteniendo el guion, la frase queda más
  natural; sin él queda más limpia. Mantener la preposición.

### `cache key` y `cache output` (compuestos)

- **Sentido:** argumentos y valores capturados de la función
  cacheada; contenido de la entrada del caché.
- **Donde aparece:** `caching.md:38-39` — *«Arguments and any values
  captured from parent scopes automatically become part of the cache
  key … see cache output … for what an entry holds»*.
- **Status:** `mantener` para `cache key`, `cache output` como
  compuesto a revisar.
- **Preferred:** `clave del caché` / `contenido del caché`.

### `prefetching` y `partial prefetching` (compuestos)

- **Sentido:** mecanismo de Next.js para cargar por anticipado el
  contenido de rutas; desde Next.js 16.3 admite precargar sólo una
  parte del árbol.
- **Donde aparece:** `caching.md:27` — *«Set `partialPrefetching`
  explicitly. Leaving it unset logs a warning …»*.
- **Status:** `propuesto`
- **Preferred:** `precarga` / `precarga parcial`.
- **Justificación:** «prefetching» es término asentado en informática;
  la traducción técnica es «precarga».

### `prerendering` (sustantivo)

- **Sentido:** producción del HTML inicial en build time (o en el
  servidor) antes de que el cliente lo pida.
- **Donde aparece:** `caching.md:36` — *«how cached results become
  part of the static shell and may be included in a prefetch»*;
  `messages/blocking-prerender-crypto.md` título.
- **Status:** `propuesto`
- **Preferred:** `preprocesado` es inexacto; el término técnico
  asentado es **prerenderizado**. «Prerrenderizar» no existe;
  «prerrenderización» es calco cacofónico.
- **Justificación:** la documentación técnica de Next.js en español
  usa `prerender`.

### `route handler` (compuesto técnico)

- **Sentido:** función de servidor que responde a una ruta de API
  (no a una página).
- **Donde aparece:** `caching.md:29` — *«`GET` Route Handlers follow
  the same prerendering model as pages»*.
- **Status:** `propuesto` / **dudoso**
- **Preferred:** `handler de ruta` (con `handler` adaptado).
- **Justificación:** «handler» está asentado en backend; «controlador
  de ruta» es la alternativa explícita que el piloto tenía.

### `cache components` (compuesto, propiedad opt-in)

- **Sentido:** nueva capa de almacenamiento en caché que controla qué
  partes del árbol se sirven estáticamente.
- **Donde aparece:** `caching.md:7` — *«This page covers caching
  with Cache Components, enabled by setting `cacheComponents: true`
  in your `next.config.ts`»*.
- **Status:** `mantener`
- **Preferred:** literal, con la primera letra en mayúscula cuando
  sea nombre propio («Cache Components»).

### `serializable` (adjetivo técnico)

- **Sentido:** valor que puede pasarse del servidor al cliente
  (props de Client Component).
- **Donde aparece:** `use-client.md:33` — *«the props of the Client
  Components must be serializable»*.
- **Status:** `propuesto`
- **Preferred:** `serializable` (literal) o `serializable por la red`.
- **Justificación:** «Serializable» funciona; «serializable por la red»
  precisa el contexto sin alargar demasiado la frase.
- **Decisión abierta:** término UML/Java; tiene un significado
  propio fuera de Next.js.

### `entry point` (compuesto técnico)

- **Sentido:** archivo en el que `'use client'` declara la frontera
  cliente.
- **Donde aparece:** `use-client.md:10-12`.
- **Status:** `propuesto`
- **Preferred:** `punto de entrada`.
- **Justificación:** calco asentado en todo tipo de framework.

### `props` (sustantivo plural, en contexto React/Next.js)

- **Sentido:** propiedades que un padre pasa a un componente hijo.
- **Donde aparece:** `use-client.md:33-43`.
- **Status:** `mantener`
- **Preferred:** `props`.
- **Justificación:** plural técnico, español («las props del
  componente») se ve mal; el corpus lo usa como si fuera
  incontable en el singular («the props», «the props of the Client
  Components»).

### `Suspense` (compontente React) y sus compuestos

- **Sentido:** componente de React que delimita lo que puede
  renderizarse progresivamente.
- **Donde aparece:** `blocking-prerender-crypto.md:11-33` —
  *«outside of `<Suspense>`. With Cache Components enabled …»*.
- **Status:** `mantener`
- **Preferred:** `<Suspense>` literal del API React.

### `boundary` (sustantivo en contexto React)

- **Sentido:** punto donde un lado cede control al otro
  (servidor→cliente, suspense).
- **Donde aparece:** `use-client.md:10` — *«defines the server and
  client boundary»*; `server-and-client-components.md:9` — *«see
  The Server and Client Boundary»*.
- **Status:** `propuesto`
- **Preferred:** `frontera` (calco) o `límite` (más libre).
- **Justificación:** la documentación oficial usa «boundary»
  literalmente, pero en español técnico «límite» o «frontera» son las
  traducciones naturales.
- **Decisión abierta:** esta decisión cambia muchas frases y
  enlaces de la documentación («Server and Client Boundary»).

### `revalidating` y `revalidate`

- **Sentido:** invalidar la entrada de caché asociada a una clave;
  por extensión, `revalidatePath()`, `revalidateTag()`.
- **Donde aparece:** `caching.md:36` — *«on-demand revalidation after
  a mutation, see Revalidating»*.
- **Status:** `propuesto`
- **Preferred:** `revalidación` / `revalidar`.
- **Justificación:** calco asentado. `revalidate()` es literal del
  API.

### `unpredictable value` (compuesto, definido por el error)

- **Sentido:** valor que cambia entre la build time y el run time
  (UUID, random, etc.).
- **Donde aparece:** `messages/blocking-prerender-crypto.md:11`.
- **Status:** `mantener`
- **Preferred:** `valor no determinista` o `valor impredecible`.
- **Justificación:** calco explícito y técnico.

### `request time` (compuesto, contraste con build time)

- **Sentido:** momento en que se atiende una petición, fuera del
  build.
- **Donde aparece:** `caching.md:34`, `blocking-prerender-crypto.md:28`.
- **Status:** `propuesto`
- **Preferred:** `tiempo de petición`.
- **Justificación:** calco literal.

### `static shell` (compuesto técnico)

- **Sentido:** HTML pregenerado que se sirve en la primera
  petición.
- **Donde aparece:** `caching.md:36` — *«may be included in a
  prefetch … how cached results become part of the static shell»*.
- **Status:** `propuesto` / **dudoso**
- **Preferred:** `cascarilla estática` (calco) / `armazón estático`.
- **Justificación:** el calco suena forzado. «Armazón» o
  «envoltorio» son alternativas.
- **Decisión abierta:** esta es una de las traducciones más
  forzadas. Si el usuario quiere coherencia con términos de
  Angular, mantener `static shell` como compuesto literal y
  glosarlo puede ser mejor.

## Lo que falta por leer

- `nextjs/app/api-reference/directives/use-server.md`,
  `use-cache-remote.md`, `use-cache-private.md`.
- `nextjs/app/guides/prefetching.md`,
  `nextjs/app/guides/lazy-loading.md`,
  `nextjs/app/guides/authentication.md`,
  `nextjs/app/guides/server-and-client-boundary.md`.
- `nextjs/app/api-reference/config/next-config-js/cacheComponents.md`,
  `partialPrefetching.md`.
- `nextjs/messages/` completa: definir mejor los términos que
  introduce la documentación de errores.
- Toda la sección de `architecture/`.
- `nextjs/pages/` (si la diferencia con `app/` requiere términos
  adicionales).

Estas son las zonas donde aparecen los términos del nuevo modelo
(suspending, rendering revisado, deep dive en directivas).
## Segunda pasada (2026-10-20)

**Material leído en esta iteración:** `nextjs/app/api-reference/directives/use-server.md`,
`nextjs/app/api-reference/directives/use-cache.md`,
`nextjs/app/api-reference/directives/use-cache-remote.md`,
`nextjs/app/api-reference/directives/use-cache-private.md`,
`nextjs/app/api-reference/config/next-config-js/cacheComponents.md`,
`nextjs/app/guides/instant-navigation.md`,
`nextjs/app/guides/authentication-with-cache-components.md`,
`nextjs/app/guides/forms.md`.

### `server function` (compuesto, primitiva de React)

- **Sentido:** función ejecutada en el servidor que un Client Component
  puede invocar. "function or file to be executed on the server side"
  (`use-server.md:7`). Estrictamente, una *Server Function* es la
  primitiva de React; una *Server Action* es la convención de Next.js
  para usarla como manejador de mutación/formulario.
- **Donde aparece:** `use-server.md:7`, 13, 30, 32, 53-64.
- **Status:** `mantener`

### `server action` (compuesto, convención de Next.js)

- **Sentido:** "Server Actions and Mutations" — Server Action es una
  Server Function usada como handler de mutación (normalmente formularios).
  Recibe `FormData` directamente.
- **Donde aparece:** `guides/forms.md:5-10`, 11, 19-39.
- **Status:** `mantener`
- **Justificación:** nombre explícito en la documentación de Next.js.
  Conviene que no se traduzcan juntos "server function" y "server
  action": el primero es React, el segundo es Next.js, y el
  mismo nombre en ambos casos (*action* y *function*) es lo más fiel a
  la fuente.

### `FormData` (objeto global del navegador)

- **Sentido:** API estándar HTML para construir/recorrer datos de
  formulario. `Object.fromEntries(formData)` lo convierte en un objeto
  plano (los valores `$ACTION_*` se filtran después).
- **Donde aparece:** `guides/forms.md:11-19`, 42-43.
- **Status:** `mantener`

### `static shell` (compuesto, ya en primera pasada)

- **Refinamiento:** la `static shell` es el HTML estático que Next.js
  genera para servir inmediatamente; Cache Components la extiende con
  "the React Server Component Payload (RSC Payload)". Hay además un
  "App Shell" generado por ruta que renderiza durante las
  navegaciones cliente.
- **Donde aparece:** `instant-navigation.md:13`, `cacheComponents.md:8`,
  `use-cache-private.md:13`, `use-cache-remote.md:9`.
- **Status:** `mantener`, anotar "App Shell" como sinónimo de capa
  prerenderizada si se decide exponerlo.

### `dynamic shell` (compuesto, contraste con static shell)

- **Sentido:** la parte de la página que se sirve en tiempo de petición;
  streaming cuando los datos llegan.
- **Status:** `mantener`

### `cache key` y `cache tag`

- **Sentido:** la **clave** del caché es una versión serializada de los
  argumentos y los IDs del build, función y HMR. La **etiqueta** es una
  marca lógica que sirve para invalidar (`cacheTag('producto-A')`).
- **Donde aparece:** `use-cache.md:60-66`, `cacheComponents.md:30`.
- **Status:** `mantener`
- **Justificación:** `cacheLife()` y `cacheTag()` son APIs.

### `cacheLife`, `stale time`, `revalidateTag`, `revalidatePath`

- **Status:** `mantener` (todo literal del API).

### `cache handler` (compuesto técnico) y `'use cache: remote'`

- **Sentido:** directiva `'use cache: remote'` con handler dedicado
  configurable vía `cacheHandlers`. Añade un round-trip de red pero
  durabilidad entre instancias y reducción de carga en backend.
- **Donde aparece:** `use-cache.md:10`, `use-cache-remote.md:7-13`, 29.
- **Status:** `mantener`

### `build id` y `function id`

- **Sentido:** valores que forman parte de la cache key. El **build ID**
  identifica el despliegue (configurable vía `deploymentId`); el
  **function ID** es un hash seguro de la ubicación y firma de la
  función en el código.
- **Donde aparece:** `use-cache.md:60-63`.
- **Status:** `mantener`
- **Decisión abierta:** `build id` puede traducirse a `ID de build`,
  pero rompe la constancia con `'use cache'` y `cacheComponents` que
  llevan la palabra *build* en inglés. Mantener literal es lo más limpio.

### `partial prerendering (PPR)` (compuesto)

- **Sentido:** "PPR" es la estrategia por defecto del App Router en
  Next.js 16 cuando `cacheComponents` está activo: produce el HTML
  estático de la `static shell` y suspende la parte dinámica en
  `<Suspense>` para streaming posterior.
- **Donde aparece:** `cacheComponents.md:34`, `instant-navigation.md:54-56`.
- **Status:** `mantener` o **`propuesto`** en prosa:
- **Preferred:** `prerender parcial (PPR)` o literal `PPR`.
- **Justificación:** "Prerender" no existe como verbo en español ("render"
  tampoco). Las opciones son mantener el anglicismo o glosar como
  «prerrenderización parcial». La documentación oficial usa "PPR".
- **Decisión abierta:** mantenerlo como sigla es la elección más
  conservadora para 200+ apariciones.

### `instant navigation` (compuesto, "App Shell" implícito)

- **Sentido:** navegación cliente en la que el navegador puede empezar
  a renderizar la nueva página en el momento del clic con contenido
  estático, en caché y de respaldo mientras se transmite el resto
  ("instant navigation" de `instant-navigation.md:8-13`).
- **Status:** `mantener`

### `Activity` (componente de React, segundo plano)

- **Sentido:** componente de React 19 que conserva el state al
  "esconder" un componente durante la navegación. Next.js lo usa con
  dos modos: el visible y "hidden". Cuando se vuelve a la ruta, los
  componentes reaparecen con su state intacto.
- **Donde aparece:** `cacheComponents.md:40-46`.
- **Status:** `mantener` (`<Activity>`).

### `app shell`, `app shell per route`, `prefetched UI`

- **Sentido:** Cada ruta genera una **App Shell** que renderiza mientras
  los pendientes llegan (streaming). El **partial prefetching** usa la
  App Shell como pre-carga por defecto del `<Link>`.
- **Donde aparece:** `instant-navigation.md:54-60`.
- **Status:** `mantener`

### `cacheHit`, `cache miss` (en uso de `use cache: remote`)

- **Sentido:** resultado positivo (entrada ya en caché) o negativo
  (entrada regenerada).
- **Status:** `mantener` o **`propuesto`** para "miss".
- **Preferred:** `acierto de caché` / `fallo de caché`. Calco funcional.
- **Justificación:** `cache hit` literal aparece en `use-cache-remote.md:33-35`
  y `use-cache-remote.md:42-43`. La traducción suena forzada y la
  audiencia del framework lo lee en inglés; mantenerlo literal.

### `opt-out` (en migración a Cache Components)

- **Sentido:** "set `export const instant = false` on the page or layout to
  let it keep blocking on the server" (`authentication-with-cache-components.md:30`).
- **Status:** `propuesto`
- **Preferred:** `desactivar manualmente`, `desactivar esta ruta`.
- **Justificación:** calco asentado; "opt-out" es término del producto,
  equivalente a "salir de" en español de producto.

### `FormData` fields prefix `$ACTION_`

- **Donde aparece:** `guides/forms.md:42` — *"Note that this object will
  contain extra properties prefixed with `$ACTION_`."*
- **Status:** `mantener` (literal del comportamiento).

### `instanceof`, `Server Function`, `Cache Function`, `Private Cache Function`

- Todas se usan como categorías de objetos. `Status: mantener` (API).

### `authentication`, `authorization`, `session`, `iron-session`

- **Donde aparece:** `guides/authentication-with-cache-components.md:6-7`
  y throughout; usan `auth()` como helper genérico.
- **Status:** `propuesto`
- **Preferred:** `autenticación`, `autorización`, `sesión`.
- **Justificación:** términos de seguridad clásicos. `iron-session` es
  el nombre de la librería, literal.

### `Data Access Layer`

- **Sentido:** la capa entre Server Actions y la base de datos, donde
  aplica la regla "no pongas SQL en el componente".
- **Donde aparece:** `authentication-with-cache-components.md:24-25`.
- **Status:** `propuesto`
- **Preferred:** `capa de acceso a datos`.

### `cold cache`, `warm cache`

- **Sentido:** "cold caches still require the server to compute the cached
  result once" (`instant-navigation.md:11`).
- **Status:** `propuesto`
- **Preferred:** `caché frío`, `caché templado` / `caché vacío / caliente`.
- **Justificación:** el uso en español técnico prefiere "frío" y
  "caliente" (consistente con CPU "frío" / "caliente"), o "vacío /
  activo". El calco "cálido" suena raro.

## Lo que falta por leer

- `nextjs/app/api-reference/config/next-config-js/cacheLife.md`,
  `cacheHandlers.md`, `cacheMaxMemorySize.md` — parametrizan el
  comportamiento de `use cache` y declaran los sentidos propios de
  "stale", "revalidate" y "expires".
- `nextjs/app/guides/migrating-to-cache-components.md` — la guía de
  migración suele introducir los términos conflictivos con v15
  (PPR opt-in, dynamicIO, useCache experimental).
- `nextjs/app/api-reference/file-conventions/` — convenciones de
  nombre: `page.tsx`, `route.ts`, `layout.tsx`, `loading.tsx`,
  `error.tsx`, `not-found.tsx`, `default.tsx`. Estos nombres definen
  contratos y conviene registrarlos como glosario de archivos.
- `nextjs/messages/` completa (especialmente los 20 mensajes de
  *blocking-prerender-*) para confirmar que la frontera "instant
  navigation" se respeta en cada caso de error.
- `nextjs/pages/` si conserva diferencias con `app/` (cliente vs
  servidor).
## Tercera pasada (2026-10-20)

**Material leído en esta iteración:** `nextjs/app/api-reference/file-conventions/page.md`. Complementa y precisa las entradas del App Router.

### `page` (archivo del App Router)

- **Sentido:** archivo `page.tsx` que define la UI única de una ruta:
  "A `page` file is required to make a route segment **publicly
  accessible**" (`page.md:26`).
- **Status:** `mantener`

### Jerarquía del App Router: `page` envuelta por otros archivos

- **Donde aparece:** `page.md:28-29` — *"In the component hierarchy,
  `page.js` is the innermost file convention. It is wrapped by
  `loading.js` (Suspense boundary), `error.js` (error boundary),
  `template.js`, and `layout.js` in the same segment."*
- **Sentido:** el árbol de convenciones file-system de Next.js envuelve
  cada `page` con: `loading` (boundary `<Suspense>`), `error`
  (boundary de error), `template` (intermedio), `layout`
  (preservado entre navegaciones con `<Activity>` "hidden").
- **Status:** `mantener` (los nombres de archivo son APIs literales).

### `params`, `searchParams` (ambos `Promise`)

- **Donde aparece:** `page.md:36-72` — *"A promise that resolves to an
  object containing the dynamic route parameters from the root
  segment down to that page"*.
- **Status:** `mantener`
- **Decisión abierta:** en la prosa que rodee a estas variables, los
  sinónimos usuales son `parámetros de ruta` y `parámetros de búsqueda`.
- **Justificación:** se introduce **una distinción clave**: en
  Next.js ≥15 ambos son `Promise`, no objetos síncronos (cambio v15
  respecto a v14).

### `dynamic route`, `[slug]`, `[...catchAll]`

- **Donde aparece:** `page.md:62-70` — *"`app/shop/[slug]/page.js`,
  `app/shop/[category]/[item]/page.js`, `app/shop/[...slug]/page.js`"*.
- **Status:** `mantener`
- **Justificación:** la sintaxis `[slug]` y `[...slug]` es literal del
  API file-system.

### `Route segment`, `route segment config`, `segment`, `children`

- **Donde aparece:** `page.md:28` — *"A `page` file is required to
  make a route segment publicly accessible."*
- **Status:** `mantener`

### `App Shell`, `Activity` (React 19)

- **Sentido (vista aquí desde la jerarquía):** la App Shell por ruta
  contiene `layout → template → ... → page`. Cada navegación cliente,
  cuando cambia de ruta, hace `"hidden"` a `<Activity>` (visto en
  segunda pasada, `cacheComponents.md:41-44`).
- **Decisión abierta:** `App Shell` como término convive con `static
  shell` en `caching.md:36`; conviene diferenciarlos en prosa
  ("App Shell se renderiza en el cliente durante navegaciones; static
  shell se sirve como HTML inicial").
- **Status:** `mantener`

### `loading.js`, `error.js`, `not-found.js`, `default.js`

- Las cuatro convenciones que añade v13 al App Router. Aparecen en
  introducciones cruzadas (`caching.md` y `page.md`).
- **Status:** `mantener`

### `template.js`

- **Sentido:** aparece en `page.md:28` como un wrap intermedio entre
  `page` y `layout`. En v13 Next.js añadió `template.js` como un
  componente que se **re-monta** en cada navegación (a diferencia de
  `layout.js`, que se preserva).
- **Status:** `mantener`

### `dynamic IO`, `experimental.useCache`, `experimental.dynamicIO`

- **Donde aparece:** `cacheComponents.md:33` — *"If you used
  `experimental.useCache` or `experimental.dynamicIO`, migrate using
  the Version 16 upgrade guide."*
- **Status:** `mantener`
- **Justificación:** son opciones obsoletas de `next.config.ts` en v15.
  Conviene registrar que ya **no son necesarias** y que su antigua
  función vive en `cacheComponents`.

### `runtime`

- **Donde aparece:** `cacheComponents.md:27` — *"Cache Components
  requires the Node.js runtime and does not support the `runtime`
  route segment config."*
- **Status:** `mantener`
- **Justificación:** es configuración de Next.js; el `runtime =
  'edge'` ha desaparecido en v16 con Cache Components.

### `revalidate`

- **Donde aparece:** `use-cache.md:34-40` y todos los mensajes de
  prerender.
- **Status:** `mantener`

### `redirect()`, `revalidatePath`, `revalidateTag`

- **Donde aparece:** `use-server.md:74-79` y secuencia completa.
- **Status:** `mantener`

### `Suspense`, `ErrorBoundary`, `useSearchParams`, `usePathname`, `useRouter`

- APIs React y Next.js. `Status: mantener`.

### `generateStaticParams`

- Aparece en `use-cache-private.md:42-46`. `Status: mantener`.

### `instantNavigation`, `instant = false` (export opt-out)

- **Sentido:** el export `export const instant = false` desactiva el
  patrón Instant Navigation para una página concreta; la página
  sigue siendo SSR con bloqueo en servidor.
- **Donde aparece:** `authentication-with-cache-components.md:29`.
- **Status:** `mantener` (literal del export).

### Note: on `searchParams` en `use client`

- "On a client navigation, the router already has the params from the
  URL and the hook resolves synchronously" — `instant-navigation.md:18`.
  Esto es relevante para revisar frases que en español técnico
  suelen confundir momento cliente con servidor.
- **Status:** `propuesto`
- **Preferred:** matizar explícitamente "en cliente vs en servidor" en
  la prosa que rodea a `searchParams`.

### Términos que aún faltan por documentar en los file-conventions

Estos viven en los archivos adyacentes del mismo directorio:

- `layout.md` — diferencias con `template`, jerarquía de layouts anidados.
- `loading.md` — comportamiento de `<Suspense>`, `loading.tsx` con
  streaming.
- `error.md` — `error.tsx`, `global-error.tsx`.
- `not-found.tsx`, `default.tsx`, `route.ts` (route handlers),
  `middleware.ts`, `opengraph-image.tsx`, `sitemap.ts`,
  `robots.ts`, `dynamic-routes.md`.

Cuando entremos a estos en una cuarta pasada definiremos `route
handler`, `layout`, `streaming`, `fetch`, `generateMetadata`,
`opengraph`, etc.
## Cuarta pasada (2026-10-20)

**Material leído en esta iteración:** `nextjs/app/api-reference/file-conventions/{layout,loading,error,route,not-found,dynamic-routes,template,parallel-routes}.md` y `nextjs/app/api-reference/config/next-config-js/cacheLife.md`.

El cluster `file-conventions/` describe cada archivo del App Router: cómo vive dentro del árbol, qué props recibe, qué sustenta y qué envuelve. Como ya se introdujo en la tercera pasada la jerarquía, esta pasada nombra con precisión cada uno.

### Convenciones del App Router, archivo por archivo

#### `layout.js` (envoltura persistente)

- **Donde aparece:** `layout.md:5-22`.
- **Sentido:** archivo que define la *layout* persistente de un segmento
  de ruta; acepta una prop `children` y, opcionalmente, `params`.
- **Status:** `mantener` (API).
- **Preferred prosa:** `diseño` (calco) o `estructura visual` o literal.
  Una frase típica: *"la layout `/dashboard` envuelve a sus páginas"*.

#### `root layout`

- **Donde aparece:** `layout.md:21` — *"A root layout is the top-most
  layout in the root app directory. It is used to define the `<html>`
  and `<body>` tags and other globally shared UI."*
- **Status:** `mantener` / `propuesto`
- **Preferred prosa:** `layout raíz` o `layout principal` (calco).
- **Justificación:** en la prosa oficial conviven "root layout"
  (literal) y "app layout" (genérico); la primera es la opción más
  técnica.

#### `loading.js` (Suspense boundary automática)

- **Donde aparece:** `loading.md:7-60`.
- **Sentido:** archivo que muestra un fallback mientras los segmentos
  hijos transmiten. *"With this convention, you can show an instant
  loading state from the server while the content of a route segment
  streams in."*
- **Status:** `mantener`

#### `instant loading states`

- **Sentido:** *"An instant loading state is fallback UI that is
  shown immediately upon navigation"* (`loading.md:37`).
- **Status:** `propuesto`
- **Preferred:** `fallback inmediato` o `estado de carga inmediato`.
- **Justificación:** calco literal; "instant loading state" puede
  traducirse sin perder la frase.

#### `error.js` (boundary de error por segmento)

- **Donde aparece:** `error.md:5-55`.
- **Sentido:** *"`error.js` wraps a route segment and its nested children
  in a React Error Boundary."*
- **Status:** `mantener` (API).

#### `global-error.js`

- **Donde aparece:** `error.md:55` — *"To handle errors in the root
  layout, use `global-error.js`."*
- **Status:** `mantener`

#### `notFound()`, `not-found.js`, `global-not-found.js`

- **Donde aparece:** `not-found.md:5-50`.
- **Sentido:** *"`not-found.js`: Used when you call the `notFound`
  function in a route segment."*; el "global" lo da la app entera.
- **Status:** `mantener`

#### `<meta name="robots" content="noindex" />`

- Aparece en `not-found.md:14` como comportamiento que Next.js
  inyecta automáticamente en páginas 404.
- **Status:** `mantener` (literal).

#### `template.js` (envoltura con clave nueva)

- **Donde aparece:** `template.md:7-47`.
- **Sentido:** *"A template file is similar to a layout … Unlike
  layouts that persist across routes and maintain state, templates
  are given a unique key, meaning children Client Components reset
  their state on navigation."*
- **Status:** `mantener` / `propuesto`
- **Preferred prosa:** `plantilla` (calco) o literal.
- **Justificación:** mantiene la diferenciación de *layout* y
  *template*, que también es útil en componentes-vista de Angular y
  en el sentido "vista de Drupal".

#### `route handler`, `route.js`, `route.ts`, `route.tsx`

- **Donde aparece:** `route.md:5-60`.
- **Sentido:** *"Route Handlers allow you to create custom request
  handlers for a given route using the Web Request and Response APIs."*
  Acepta exportación de métodos HTTP literal (`GET`, `POST`, `PUT`,
  `PATCH`, `DELETE`, `HEAD`, `OPTIONS`).
- **Status:** `mantener`
- **Justificación:** la entrada existe desde la primera pasada con
  *preferred* dudoso (`handler de ruta`). Confirmada por la prosa de
  `route.md` — mantenemos `handler de ruta` o literal.

#### `NextRequest`, `NextResponse`

- **Donde aparece:** `route.md:44-48`.
- **Status:** `mantener`

#### `dynamic segments`, `static segments`, `path params`, `route params`, `URL params`

- **Donde aparece:** `dynamic-routes.md:5-9` — *"Dynamic Segments
  are often referred to as path params, route params, or URL params."*
- **Status:** `propuesto`
- **Preferred prosa:** `segmento dinámico`, `parámetro de URL` o
  `parámetro de ruta`. Los tres plurales coexisten en la prosa
  oficial.
- **Justificación:** la sinonimia múltiple es propia del framework;
  convendría registrar los tres sentidos como variantes, no como
  entradas separadas.

#### `catch-all` y `params?.slug`

- **Donde aparece:** `dynamic-routes.md:62-70` (sintaxis `[...slug]`).
- **Status:** `mantener`
- **Justificación:** literal del API file-system.

#### `parallel routes`, `slots`, `@folder`, `parallel-routes.md`

- **Donde aparece:** `parallel-routes.md:5-50`.
- **Sentido:** *"Parallel Routes allows you to simultaneously or
  conditionally render one or more pages within the same layout."*
  Los **slots** se crean con la convención `@folder` (`@analytics`,
  `@team`).
- **Status:** `mantener` para los nombres de archivo (`@folder`);
  `propuesto` para la prosa.
- **Preferred prosa:**
  - `parallel routes` → `rutas en paralelo` (calco castellano).
  - `slots` → `ranuras` (calco literal, suena forzado) o `tragamonedas`
    (incorrección: viene del boxeo). Mantener literal: `slots` es la
    elección más limpia.
- **Decisión abierta:** *"ranuras"* vs literal. Recomiendo literal.

#### `default.js` (fallback para slots sin match)

- **Donde aparece:** `parallel-routes.md:47-50`.
- **Status:** `mantener` (API).

#### `route groups`, `(folder)`, paréntesis

- **Donde aparece:** `route-groups.md` (no leído aún; mencionado en
  `not-found.md:41-42`).
- **Status:** `mantener`

#### `intercepting routes`, `@modal`, `@default`, `@slot`

- **Donde aparece:** `intercepting-routes.md` (no leído).
- **Status:** `mantener`

#### `Next.js` *prefetch* y *partial prefetching* en el routing

- **Donde aparece:** `loading.md:31` — *"The Fallback UI is
  prefetched, making navigation immediate unless prefetching hasn't
  completed."*
- **Status:** `mantener`

#### `dynamic rendering`, `prerendering`, `static rendering`

- **Donde aparece:** `parallel-routes.md:43` — *"you cannot have
  separate prerendered and dynamically rendered slots at the same
  route segment level. If one slot is dynamic, all slots at that
  level must be dynamic."*
- **Status:** `propuesto`
- **Preferred:**
  - `dynamic rendering` → `renderizado dinámico` (calco literal).
  - `prerendering` → `prerenderizado` (calco, ver glosario 1ª
    pasada).
  - `static rendering` → `renderizado estático`.

## `cacheLife` (config y contrato)

### `cacheLife` (API) y `cacheLife` (config)

- **Donde aparece:** `cacheLife.md:6-9`.
- **Sentido:** *"The `cacheLife` option allows you to define custom
  cache profiles when using the `cacheLife` function inside
  components or functions, and within the scope of the `use cache`
  directive."*
- **Status:** `mantener`

### `cache profile` (compuesto)

- **Sentido:** objeto dentro de `cacheLife` que define `stale`,
  `revalidate` y `expire`. Trae valores opcionales con requisitos
  cruzados (`expire` debe ser mayor que `revalidate`).
- **Donde aparece:** `cacheLife.md:13-30`.
- **Status:** `propuesto`
- **Preferred:** `perfil de caché`.
- **Justificación:** calco literal y castellano estándar.

### `stale`, `revalidate`, `expire` (campos del perfil)

- **Donde aparece:** `cacheLife.md:57-69`.
- **Status:** `propuesto`
- **Preferred:**
  - `stale` → `stale` (literal) o `obsoleto` (calco). Mismo riesgo
    que `deprecated`. Mantener literal.
  - `revalidate` → `revalidar` / `revalidación` (calco útil).
  - `expire` → `expirar` / `expiración` (calco útil).
- **Decisión abierta:** los nombres técnicos se citan sin traducir en
  prosa; `expire` se traduce a "expirar" o "caducar". Misma dicotomía
  `revalidate`/`revalidar`. La comunidad ha fijado en GitHub
  Issues/PRs ambos sentidos; lo más limpio es dejar las variables
  como literales.

### `default`, `seconds`, `minutes`, `hours`, `days`, `weeks`, `max`

- **Donde aparece:** `cacheLife.md:46`.
- **Status:** `mantener` — son **perfiles precargados** que el corpus
  lista explícitamente. Conviene registrarlos porque aparecen en
  documentación sin formalismo adicional.

### `site_components` flag, `experimental`, `next.config.ts`

- **Donde aparece:** `cacheComponents.md` (segunda pasada) y
  `cacheLife.md:18-21` (similar).
- **Status:** `mantener`.

## Lo que falta por leer

- `nextjs/app/api-reference/file-conventions/{forbidden,unauthorized,default,intercepting-routes,instrumentation,instrumentation-client,mdx-components,metadata,proxy,public-folder,src-folder,route-groups,route-segment-config}.md` — quedan unas diez convenciones por cubrir.
- `nextjs/app/api-reference/config/next-config-js/cacheHandlers.md`,
  `cacheMaxMemorySize.md` — parametrizan las dos directivas que
  faltan.
- `nextjs/app/api-reference/functions/{cookies,headers,connection,
  draft-mode,fetch,cacheLife,cacheTag,revalidate-path,
  revalidate-tag,generate-metadata,generate-image-metadata}.md` —
  introducen la API funcional para Server Components.
- `nextjs/app/getting-started/project-structure.md` y
  `linking-and-navigating.md` — contexto de la jerarquía.
- Los restantes mensajes en `nextjs/messages/` (aprox. 30 archivos).
## Quinta pasada (2026-10-20)

**Material leído en esta iteración:** el resto del cluster Next.js:
`file-conventions/{forbidden,unauthorized,default,intercepting-routes,route-groups,instrumentation,instrumentation-client,src-folder,route-segment-config/{index,runtime,dynamicParams}}.md`, `metadata/index.md`, `config/next-config-js/{cacheHandlers,partialPrefetching}.md`, `messages/blocking-prerender-random.md`.

Este lote destapa dos cambios del producto importantes:

1. **`middleware` se renombró a `proxy`**. La documentación dice
   literalmente: *"The `middleware` file convention is deprecated and
   has been renamed to `proxy`."*
2. **`runtime = 'edge'` deprecado**. La documentación literal: *"The
   Edge Runtime is deprecated. Remove the `runtime` export from your
   route files. See Edge Runtime Deprecated."*
   Esto afecta al glosario: `edge runtime` debe pasar de `mantener`
   a `obsoleto` (manteniendo el nombre como histórico).

### `proxy` (sustantivo y archivo del App Router)

- **Donde aparece:** `proxy.md:8` — *"The `proxy.js|ts` file is used
  to write Proxy and run code on the server before a request is
  completed."*
- **Sentido:** archivo que ejecuta código antes de que una petición
  llegue a una ruta; útil para autenticación, logs, rediciones,
  reescritura de cabeceras.
- **Status:** `mantener` (literal del nombre del producto).
- **Justificación:** ya no se llama `middleware`; la prosa debe reflejar
  el cambio. Conviene **registrar `middleware` como sustantivo
  histórico obsoleto** para evitar que se introduzca en futuras
  traducciones.

### `middleware` (sustantivo obsoleto)

- **Donde aparece:** `proxy.md:8` — *"The `middleware` file
  convention is deprecated and has been renamed to `proxy`."*
- **Status:** `obsoleto`
- **Preferred:** `middleware` (mantiene su nombre inglés) — se traduce
  *como* «middleware» (castellano admite este anglicismo histórico).
- **Decisión abierta:** el producto lo deprecó al renombrarlo. El
  corpus conserva referencias viejas. Mantener ambos nombres
  registrados como entradas separadas para que la traducción de
  archivos antiguos pueda seguir produciendo `middleware` y la de
  v16+ produzca `proxy`.

### `Proxy function` (literal del archivo)

- **Donde aparece:** `proxy.md:34-37` — *"The file must export a
  single function, either as a default export or named `proxy`."*
- **Status:** `mantener`

### `matcher` (configuración del archivo `proxy`)

- **Donde aparece:** `proxy.md:28-29` — *"`export const config = {
  matcher: '/about/:path*', }`"*.
- **Status:** `mantener`

### `experimental.globalNotFound`, `globalNotFound` (experiment)

- **Donde aparece:** `not-found.md:44-50`.
- **Status:** `mantener` (config literal de `next.config.ts`).

### `forbidden()`, `forbidden.js`, `notFound()`, `unauthorized()`

- **Donde aparece:** `forbidden.md:12-13`, `not-found.md:7-13`,
  `unauthorized.md:12`.
- **Sentido:** lanzan una UI con status code fijo (403 / 404 / 401) si
  se invocan durante el render.
- **Status:** `mantener`

### `default.js` (fallback para slots sin match)

- **Donde aparece:** `default.md:7-14` —
  *"Next.js cannot recover a slot's active state after a full-page
  load. … `default.js` file can be rendered for subpages that don't
  match the current URL."*
- **Status:** `mantener`
- **Decisión abierta:** el corpus define `default.js` específicamente
  en el contexto de Parallel Routes. Conviene no **confundirlo** con
  `default.ts` de configuración del framework.

### `soft navigation` y `hard navigation`

- **Donde aparece:** `intercepting-routes.md:8-13` — *"during soft
  navigation, Next.js intercepts the `/photo/123` route, masks the
  URL, and overlays it over `/feed`. However, when navigating to the
  photo by clicking a shareable URL or by refreshing the page, the
  entire photo page should render instead of the modal. No route
  interception should occur."*
- **Status:** `propuesto`
- **Preferred:** `navegación suave` / `navegación dura` — los términos
  son literalmente del producto, sin traducción oficial.
- **Decisión abierta:** mantener literal (`soft navigation` /
  `hard navigation`) es coherente con la prosa oficial española de
  Next.js.

### `intercepting route` (compuesto técnico)

- **Donde aparece:** `intercepting-routes.md:5-8`, capturada en
  tercera pasada como `intercepting routes`.
- **Status:** `mantener`.
- **Preferred prosa:** `rutas interceptoras`.

### `(.)`, `(..)`, `(..)(..)`, `(...)` (convención de segmentos)

- **Donde aparece:** `intercepting-routes.md:18-25` —
  *"`(.)` to match segments on the same level, `(..)` to match
  segments one level above, `(..)(..)` to match segments two levels
  above, `(...)` to match segments from the root app directory."*
- **Status:** `mantener` (literal del API file-system).

### `route groups`, `(folder)`

- **Donde aparece:** `route-groups.md:5-11` — *"Route Groups are a
  folder convention that let you organize routes by category or
  team. A route group can be created by wrapping a folder's name in
  parenthesis: `(folderName)`."*
- **Status:** `mantener` (literal del API file-system).
- **Preferred prosa:** `grupos de rutas`.
- **Justificación:** "(folder)" como sintaxis no se traduce; el
  descriptor genérico sí.

### `instrumentation.js`, `register()`, `onRequestError()`

- **Donde aparece:** `instrumentation.md:7-30`.
- **Sentido:** archivo que integra APIs de observabilidad con la
  aplicación; define el momento de ejecución.
- **Status:** `mantener` (API).

### `instrumentation-client.js` (homólogo cliente)

- **Donde aparece:** `instrumentation-client.md:5-15`.
- **Sentido:** código de monitoreo en cliente; sin exports
  requeridos, ejecución directa al inicio.
- **Status:** `mantener`
- **Justificación:** corre en el navegador, mientras `instrumentation.js`
  corre en el servidor. Con la misma forma de archivo, son archivos
  distintos.

### `performance.mark`, `performance.measure`, `reportError`

- **Donde aparece:** `instrumentation-client.md:16-23`.
- **Status:** `mantener` (Web Performance API).

### `Route Segment Config`

- **Donde aparece:** `route-segment-config/index.md:5-9` — *"The
  Route Segment Config options allow you to configure the behavior
  of a Page, Layout, or Route Handler by directly exporting the
  following variables."*
- **Opciones:** `dynamicParams`, `runtime`, `preferredRegion`,
  `maxDuration`. Con Cache Components activan opciones adicionales
  (`instant`, etc.).
- **Status:** `mantener`

### `dynamicParams` (Route Segment Config)

- **Donde aparece:** `dynamic-segment-config/dynamicParams.md:6-13`.
- **Sentido:** *"The `dynamicParams` option allows you to control what
  happens when a dynamic segment is visited that was not generated
  with `generateStaticParams`."*
- **Status:** `mantener`
- **Decisión abierta:** `"This option replaces the `fallback: true |
  false | blocking` option of `getStaticPaths` in the `pages`
  directory."* — la prosa conviene recordar que es **el sustituto**
  de `getStaticPaths`.

### `runtime` (Route Segment Config)

- **Donde aparece:** `route-segment-config/runtime.md:8-17`.
- **Estado oficial:** `'edge'` deprecated, `'nodejs'` único valor.
- **Status:** `mantener` / **`propuesto`** el sentido de la deprecation.
- **Preferred:**
  - `'nodejs'` literal.
  - `'edge'` literal, ya deprecado.
- **Justificación:** el producto lo deprecó; el glosario debe registrar
  el cambio para que la prosa no diga *"usa 'edge' para baja
  latencia"* en archivos traducidos.

### `preferredRegion`, `maxDuration`, `instant`, `prefetch`, `ensureStatic`, `dynamicParams`

- `Status: mantener` (todos API literales).

### `Cache Components`, `static shell`, `dynamic shell`, `cache hit`, `cache miss`

- Confirmaciones transversales (segunda y tercera pasada). `Status: mantener`.

### `cacheHandlers` (config + tipos)

- **Donde aparece:** `cacheHandlers.md:6-46`.
- **Sentido:** *"The `cacheHandlers` configuration allows you to
  define custom cache storage implementations for `'use cache'` and
  `'use cache: remote'`."*
- **Tipos de handler:** `default` (para `'use cache'`) y `remote`
  (para `'use cache: remote'`).
- **Status:** `mantener`.

### `CacheHandler`, `CacheEntry` (tipos exportados)

- **Donde aparece:** `cacheHandlers.md:48-50` — *"A cache handler
  stores and returns `CacheEntry` objects. Both this type and
  `CacheHandler` are exported from `next/cache`."*
- **Status:** `mantener` (literal).

### `LRU` (algoritmo de caché)

- **Donde aparece:** `cacheHandlers.md:44` — *"Next.js uses an
  in-memory LRU (Least Recently Used) cache for both `default` and
  `remote`."*
- **Status:** `mantener` (algoritmo estándar con nombre propio).
- **Decisión abierta:** `LRU` se conserva literal; en la prosa
  castellana puede apoyarse como *caché LRU* o *caché por uso*.

### `partialPrefetching` y validación de config

- **Donde aparece:** `partialPrefetching.md:6-24` — *"`partialPrefetching`
  enables Partial Prefetching at the app level. […] requires
  [`cacheComponents`]. Without it, `next dev` and `next build` throw
  at config validation."*
- **Status:** `mantener`
- **Justificación:** presencia literal en `next.config.ts`.

### Errores `blocking-prerender-*`

- **Donde aparece:** `messages/blocking-prerender-random.md:5-15`.
- **Sentido:** mensajes de error paralelos de Next.js 16.3 cuando un
  Server Component accede a APIs no estables (`Math.random()`,
  `Date.now()`, `crypto.randomUUID()`, etc.) fuera de
  `<Suspense>`. Las opciones de solución son: *Generate on every
  request* (con `await connection()`), *Cache* (con `'use cache'`),
  *Client* (con `'use client'`).
- **Status:** `mantener` (literal del API).

### `unpredictable value`, `unstable value`, `request time`

- `Status: mantener` (literal del producto).

### `connection()`

- **Donde aparece:** `messages/blocking-prerender-crypto.md:33-37` y
  `blocking-prerender-random.md:28` — *"Add `await connection()`
  before the call to tell Next.js the surrounding component is
  request-bound."*
- **Status:** `mantener`
- **Justificación:** API literal de Next.js (de `'next/server'`).

## Lo que falta por leer para completar el archivo `nextjs.md`

- Funciones Next.js:
  `nextjs/app/api-reference/functions/{cookies,headers,connection,
  draft-mode,cacheLife,cacheTag,revalidate-path,revalidate-tag,
  generate-metadata,fetch,catchError,forbidden,unauthorized,
  not-found,next-request,next-response}.md`.
- Resto de archivos metadata (opengraph-image, sitemap, robots,
  manifest, app-icons).
- Resto de route-segment-config (instant, maxDuration, prefetch,
  preferredRegion, runtime, ensureStatic, dynamicParams ya
  leídos).
- `nextjs/messages/*` completa (~30 archivos).
