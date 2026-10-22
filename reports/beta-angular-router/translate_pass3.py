#!/usr/bin/env python3
"""Traducciones focales para `angular/api/router/` (ronda 2).

TEXTS es la base curada. Las entradas presentes se traducen
explícitamente; las ausentes quedan en identidad (lo correcto para
anchors y literals preservados por INV-05). Cada pair (path, seg_id)
es un commit manual sobre el corpus real.
"""

from __future__ import annotations

import json
from pathlib import Path

T = Path(__file__).resolve().parent / "run-angular-router-001/translations"

# ====================================================================
TEXTS: dict[tuple[str, str], str] = {
    # ===============================================================
    # angular/api/router/Route.md
    # ===============================================================
    ("Route.md", "seg-2d014c18"): (
        "Una configuración que define una ruta. Un conjunto de rutas "
        "se agrupa en un array [`Routes`](/api/router/Routes) para "
        "definir la configuración de un [`Router`](/api/router/Router). "
        "El router intenta hacer coincidir segmentos de una URL contra "
        "cada ruta, usando las opciones configuradas en su `data` y los "
        "parámetros resueltos en cada `resolve`."
    ),
    ("Route.md", "seg-d38e3053"): (
        "Se usa para definir el título de la página de la ruta. Puede "
        "ser una cadena literal o un [`Injectable`](/api/core/Injectable) "
        "que implemente [`Resolve`](/api/router/Resolve)."
    ),
    ("Route.md", "seg-ac6e3082"): (
        "La ruta con la que comparar. No se puede usar junto con una "
        "función `matcher` personalizada. Cadena URL que sigue la "
        "notación de matching del router. Admite wildcards `**` que "
        "capturan cualquier URL (ver Notas de Uso). Por defecto `/` "
        "(la raíz)."
    ),
    ("Route.md", "seg-c9adc1b7"): "Estrategia de matching de la ruta, una de 'prefix' o 'full'. Por defecto 'prefix'.",
    ("Route.md", "seg-f0de4bf7"): (
        "Por defecto, el router revisa los elementos de la URL de "
        "izquierda a derecha para decidir si la URL coincide con la ruta; "
        "se para cuando hay match. Importante: debe haber match por "
        "cada segmento. La estrategia 'full' verifica la URL completa. Útil "
        "al redirigir rutas vacías para evitar bucles cuando la ruta de "
        "destino es prefijo del origen."
    ),
    ("Route.md", "seg-75f12fd9"): "Una función de matching de URL personalizada. No se puede usar junto con `path`.",
    ("Route.md", "seg-13acf07c"): (
        "El componente a instanciar cuando la ruta coincide. Puede ser "
        "vacío si las rutas hijo declaran componentes."
    ),
    ("Route.md", "seg-cbb8dd37"): (
        "Array de [`CanMatchFn`](/api/router/CanMatchFn) o tokens DI, "
        "en orden de ejecución, para decidir si el usuario actual puede "
        "acceder a la ruta."
    ),
    ("Route.md", "seg-68a13027"): (
        "Array de [`CanActivateChildFn`](/api/router/CanActivateChildFn) "
        "o tokens DI, en orden de ejecución, para decidir si el usuario "
        "puede acceder a las rutas hijo."
    ),
    ("Route.md", "seg-94ad76df"): (
        "Array de [`CanDeactivateFn`](/api/router/CanDeactivateFn) o "
        "tokens DI, en orden de ejecución, para decidir si el usuario "
        "puede salir de la ruta."
    ),
    ("Route.md", "seg-efa52f9d"): (
        "Array de [`CanLoadFn`](/api/router/CanLoadFn) o tokens DI, "
        "en orden de ejecución, para decidir si el usuario puede cargar "
        "el módulo de la ruta en lazy loading. Deprecated: usar `canMatch` "
        "en su lugar."
    ),
    ("Route.md", "seg-56fbd26d"): (
        "Datos adicionales definidos por el desarrollador, enviados al "
        "componente vía [`ActivatedRoute`](/api/router/ActivatedRoute). "
        "Por defecto no se pasa ninguno."
    ),
    ("Route.md", "seg-c951c15d"): (
        "Mapa de tokens DI usados para resolver datos antes de la "
        "activación. Ver [`Resolve`](/api/router/Resolve)."
    ),
    ("Route.md", "seg-28dd1e03"): (
        "Una función que devuelve un registro de recursos. Se ejecuta "
        "durante la fase principal de carga de la navegación."
    ),
    ("Route.md", "seg-3aad45c6"): (
        "Array de [`Route`](/api/router/Route) hijos, anidados, que "
        "extiende la configuración de la ruta."
    ),
    ("Route.md", "seg-e9072c56"): "Una configuración de rutas hijo con lazy loading.",
    ("Route.md", "seg-1f7d0d2f"): (
        "Política que decide cuándo ejecutar guards y resolvers en la "
        "ruta. Por defecto solo se ejecutan cuando se activa o desactiva "
        "la ruta; este hook permite ajustar el caso en el que la ruta "
        "no cambió."
    ),
    ("Route.md", "seg-54aaa8dd"): (
        "Array de [`Provider`](/api/core/Provider) para usar en esta "
        "ruta y sus `children`. El [`Router`](/api/router/Router) crea "
        "un nuevo [`EnvironmentInjector`](/api/core/EnvironmentInjector) "
        "para la ruta."
    ),
    ("Route.md", "seg-7ac20812"): (
        "Una configuración que define una ruta. Un conjunto de rutas se "
        "agrupa en un array [`Routes`](/api/router/Routes) para definir "
        "la configuración de un [`Router`](/api/router/Router). El router "
        "intenta hacer coincidir segmentos de una URL contra cada ruta."
    ),
    ("Route.md", "seg-c9ece4b5"): (
        "La siguiente ruta especifica que, al navegar a `/team/11/user/bob`, "
        "el router crea el componente Team con el componente User hijo "
        "dentro."
    ),
    ("Route.md", "seg-0da1f624"): (
        "La siguiente ruta crea componentes hermanos con múltiples "
        "outlets. Al navegar a `/team/11(aux:chat/jim)`, el router crea "
        "el componente Team junto al componente Chat en otro outlet."
    ),
    ("Route.md", "seg-b9e6665f"): (
        "La siguiente ruta usa notación wildcard para especificar un "
        "componente que se instancia siempre, sin importar dónde se "
        "navegue."
    ),
    ("Route.md", "seg-efdb4936"): (
        "La siguiente ruta usa la propiedad `redirectTo` para ignorar un "
        "segmento de la URL al buscar el siguiente path hijo. Al navegar "
        "a `/team/11/legacy/user/jim`, el router cambia la URL a "
        "`/team/11/user/jim` antes de resolver la siguiente ruta."
    ),
    ("Route.md", "seg-2c7c108a"): (
        "La ruta de la redirección puede ser relativa, como en este "
        "ejemplo, o absoluta."
    ),
    ("Route.md", "seg-2852145f"): (
        "Las rutas con path vacío pueden instanciar componentes sin "
        "consumir segmentos de URL. En la configuración siguiente, al "
        "navegar a `/team/11`, el router instancia el componente Team."
    ),
    ("Route.md", "seg-e2c6e549"): (
        "Las rutas con path vacío pueden tener hijos. En el ejemplo "
        "siguiente, al navegar a `/team/11/user/jim`, el router instancia "
        "el componente wrapper con el componente user dentro."
    ),
    ("Route.md", "seg-33e5225e"): (
        "La estrategia de matching por defecto es 'prefix': el router "
        "revisa los elementos de la URL de izquierda a derecha para "
        "decidir si la URL coincide con la ruta especificada. Por ejemplo, "
        "`/team/11/user` coincide con `team/:id` si alguna ruta hija "
        "coincide con el segmento `user`."
    ),
    ("Route.md", "seg-bb6248b2"): (
        "Puedes especificar la estrategia 'full' para asegurarte de "
        "que la ruta cubre toda la URL sin consumir. Importante al "
        "redirigir rutas vacías: si no, el router aplicaría la "
        "redirección aún al destino, creando un bucle infinito."
    ),
    ("Route.md", "seg-3939fe1e"): (
        "Puedes compartir parámetros entre componentes hermanos. Por "
        "ejemplo, dos componentes hermano que van juntos y necesitan "
        "un parámetro `id`: `'/team/11/user'` puede llevar `Team` con "
        "`id: 11` y `User` con `id: 11`."
    ),
    ("Route.md", "seg-a0c529a1"): (
        "El router une los parámetros, data y resolve del padre "
        "componente-less con los del hijo. Útil cuando las rutas hijo "
        "necesitan los mismos parámetros que su padre."
    ),
    ("Route.md", "seg-0c80300b"): (
        "Lazy loading acelera el tiempo de carga dividiendo la "
        "aplicación en paquetes y cargándolos bajo demanda. Para usar "
        "lazy loading, declara la propiedad `loadChildren`."
    ),
    # ===============================================================
    # angular/api/router/Router.md
    # ===============================================================
    ("Router.md", "seg-c70e6a8c"): (
        "Servicio que facilita la navegación entre vistas y la "
        "manipulación de la URL. Se provee en el ámbito raíz y se "
        "configura con [provideRouter](api/router/provideRouter)."
    ),
    ("Router.md", "seg-b183cdb5"): (
        "Una fuente de eventos para los eventos de enrutado. El router "
        "emite eventos `NavigationStart`, `NavigationEnd`, etc.; el "
        "servicio expone el último `RouterStateSnapshot`."
    ),
    ("Router.md", "seg-883dc967"): "El estado actual del enrutado de este NgModule.",
    ("Router.md", "seg-1d9fa660"): (
        "Verdadero si ha ocurrido al menos un evento de navegación, "
        "falso en caso contrario."
    ),
    ("Router.md", "seg-72b0997d"): (
        "@deprecated. Configurar vía `providers`: "
        "`{provide: RouteReuseStrategy, useClass: MyStrategy}`."
    ),
    ("Router.md", "seg-85f3c00b"): "Estrategia para reutilizar rutas.",
    ("Router.md", "seg-b9234f03"): (
        "@deprecated. Configurar esto a través de [`provideRouter`]"
        "(/api/router/provideRouter) o "
        "[`RouterModule.forRoot`](/api/router/RouterModule#forRoot)."
    ),
    ("Router.md", "seg-bda95b3d"): (
        "Cómo gestionar una navegación a la URL actual."
    ),
    ("Router.md", "seg-9266aea4"): (
        "Indica si la aplicación ha activado el binding de los datos del "
        "Router a las entradas del componente. Es la opción que activa "
        "[`withComponentInputBinding`]"
        "(/api/router/withComponentInputBinding)."
    ),
    ("Router.md", "seg-52901ab4"): (
        "Signal del objeto [`Navigation`](/api/router/Navigation) actual "
        "cuando el router está navegando, y `null` cuando está inactivo."
    ),
    ("Router.md", "seg-f1910e6e"): (
        "Configura el listener de cambios de ubicación y realiza la "
        "navegación inicial."
    ),
    ("Router.md", "seg-ea6c9cb6"): (
        "Configura el listener de cambios de ubicación. Este listener "
        "detecta navegaciones disparadas desde fuera del Router (los "
        "botones de back/forward del navegador, por ejemplo) y programa "
        "una navegación correspondiente."
    ),
    ("Router.md", "seg-12f40e78"): "La URL actual.",
    ("Router.md", "seg-fd489585"): (
        "@deprecated Usar la señal `currentNavigation` en su lugar. "
        "Devuelve el objeto [`Navigation`](/api/router/Navigation) actual "
        "cuando el router está navegando, y `null` cuando está inactivo."
    ),
    ("Router.md", "seg-d1ad28e8"): (
        "El objeto [`Navigation`](/api/router/Navigation) de la navegación "
        "más reciente que haya tenido éxito, y `null` si aún no se ha "
        "completado una navegación con éxito."
    ),
    ("Router.md", "seg-76897023"): (
        "Restablece la configuración de rutas usada para la navegación "
        "y la generación de enlaces."
    ),
    ("Router.md", "seg-62c85297"): "Libera los recursos del router.",
    ("Router.md", "seg-790fec6f"): (
        "Añade segmentos de URL al árbol actual para crear uno nuevo."
    ),
    ("Router.md", "seg-9c048460"): (
        "Un valor `null` o `undefined` para `relativeTo` indica que el "
        "árbol debe crearse relativo a la raíz."
    ),
    ("Router.md", "seg-ba8eaa13"): (
        "Navega a una vista usando una ruta absoluta. La función no "
        "aplica delta alguno a la URL actual."
    ),
    ("Router.md", "seg-c7268d1d"): (
        "Navega según el array de comandos y un punto de partida. Si "
        "no se da ruta de partida, la navegación es absoluta."
    ),
    ("Router.md", "seg-266317dc"): "Serializa un [`UrlTree`](/api/router/UrlTree) en una cadena.",
    ("Router.md", "seg-eedaf3d3"): "Analiza una cadena y devuelve un [`UrlTree`](/api/router/UrlTree).",
    ("Router.md", "seg-7de4a2e5"): (
        "@deprecated Usar [`IsActiveMatchOptions`]"
        "(/api/router/IsActiveMatchOptions) en su lugar. Devuelve si la "
        "URL está activada."
    ),
    ("Router.md", "seg-54927553"): (
        "Servicio que facilita la navegación entre vistas y la "
        "manipulación de la URL. Se provee en el ámbito raíz y se "
        "configura con [provideRouter](api/router/provideRouter)."
    ),
    # ===============================================================
    # angular/api/router/RouterLink.md
    # ===============================================================
    ("RouterLink.md", "seg-5ee70d2c"): (
        "Cuando se aplica a un elemento en una plantilla, convierte ese "
        "elemento en un enlace que inicia la navegación a una ruta. La "
        "navegación abre uno o más componentes enrutados en uno o más "
        "puntos `<router-outlet>` de la página."
    ),
    ("RouterLink.md", "seg-79ec8cd3"): (
        "Marca el elemento como destino de navegación. La dirección del "
        "enlace se calcula a partir de la URL de la ruta. Las expresiones "
        "en la matriz `queryParams` se aplican para construir la URL final "
        "con todos los parámetros opcionales."
    ),
    ("RouterLink.md", "seg-16eb53e3"): (
        "Representa el valor del atributo `href` aplicado al elemento "
        "host, cuando es una etiqueta `<a>`/`<area>` o un elemento "
        "personalizado compatible. Para otras etiquetas, el valor es "
        "`null`."
    ),
    ("RouterLink.md", "seg-1d455699"): (
        "Representa el atributo `target` en el elemento host. Solo se "
        "usa cuando el host es `<a>`/`<area>` o un elemento compatible."
    ),
    ("RouterLink.md", "seg-8bedd1c5"): (
        "Se pasa a [`Router#createUrlTree`]"
        "(/api/router/Router#createUrlTree) como parte de "
        "[`UrlCreationOptions`](/api/router/UrlCreationOptions)."
    ),
    ("RouterLink.md", "seg-8a445771"): (
        "Se pasa a [`Router#createUrlTree`]"
        "(/api/router/Router#createUrlTree) como parte de "
        "[`UrlCreationOptions`](/api/router/UrlCreationOptions)."
    ),
    ("RouterLink.md", "seg-6fa6ba28"): (
        "Se pasa a [`Router#createUrlTree`]"
        "(/api/router/Router#createUrlTree) como parte de "
        "[`UrlCreationOptions`](/api/router/UrlCreationOptions)."
    ),
    ("RouterLink.md", "seg-48f88a37"): (
        "Se pasa a [`Router#navigateByUrl`]"
        "(/api/router/Router#navigateByUrl) como parte de "
        "[`NavigationBehaviorOptions`](/api/router/NavigationBehaviorOptions)."
    ),
    ("RouterLink.md", "seg-4eab7f82"): (
        "Se pasa a [`Router#createUrlTree`]"
        "(/api/router/Router#createUrlTree) como parte de "
        "[`UrlCreationOptions`](/api/router/UrlCreationOptions). "
        "Especifica un valor aquí cuando no quieres calcular relativo "
        "a la ruta activa."
    ),
    ("RouterLink.md", "seg-a02822a2"): (
        "Se pasa a [`Router#createUrlTree`]"
        "(/api/router/Router#createUrlTree) como parte de "
        "[`UrlCreationOptions`](/api/router/UrlCreationOptions)."
    ),
    ("RouterLink.md", "seg-29389676"): (
        "Se pasa a [`Router#navigateByUrl`]"
        "(/api/router/Router#navigateByUrl) como parte de "
        "[`NavigationBehaviorOptions`](/api/router/NavigationBehaviorOptions)."
    ),
    ("RouterLink.md", "seg-90ee66c3"): (
        "Se pasa a [`Router#navigateByUrl`]"
        "(/api/router/Router#navigateByUrl) como parte de "
        "[`NavigationBehaviorOptions`](/api/router/NavigationBehaviorOptions)."
    ),
    ("RouterLink.md", "seg-2ee48818"): (
        "Se pasa a [`Router#navigateByUrl`]"
        "(/api/router/Router#navigateByUrl) como parte de "
        "[`NavigationBehaviorOptions`](/api/router/NavigationBehaviorOptions)."
    ),
    ("RouterLink.md", "seg-159bb569"): (
        "Comandos que pasan a [`Router#createUrlTree`]"
        "(/api/router/Router#createUrlTree) o un "
        "[`UrlTree`](/api/router/UrlTree)."
    ),
    ("RouterLink.md", "seg-76ebbf9e"): (
        "Cuando se aplica a un elemento en una plantilla, convierte ese "
        "elemento en un enlace que inicia la navegación a una ruta. La "
        "navegación abre uno o más componentes enrutados en uno o más "
        "puntos `<router-outlet>` de la página."
    ),
    ("RouterLink.md", "seg-d8e7eef9"): (
        "Puedes usar rutas absolutas o relativas en un enlace, pasar "
        "query parameters, controlar cómo se manejan y mantener un "
        "historial de los estados de navegación."
    ),
    ("RouterLink.md", "seg-283ab25c"): (
        "El nombre del primer segmento puede ir precedido de `/`, "
        "`./`, o `../`."
    ),
    ("RouterLink.md", "seg-90dde566"): (
        "El siguiente enlace añade un query parameter y un fragment a "
        "la URL generada."
    ),
    ("RouterLink.md", "seg-a51256a0"): (
        "Por defecto, la directiva construye la nueva URL con los "
        "query parameters dados. El ejemplo genera el enlace "
        "`/user/bob?debug=true#education`. Puedes indicar a la "
        "directiva otra forma de manejar los parámetros."
    ),
    ("RouterLink.md", "seg-8e8b8107"): (
        "`queryParams`, `fragment`, `queryParamsHandling`, "
        "`preserveFragment` y `relativeTo` no se pueden usar cuando "
        "la entrada `routerLink` es un [`UrlTree`](/api/router/UrlTree). "
        "Ver [`UrlCreationOptions`](/api/router/UrlCreationOptions)."
    ),
    ("RouterLink.md", "seg-36745306"): (
        "Puedes pasar un valor `state` para que se persista en la "
        "propiedad [`History.state`](https://developer.mozilla.org/en-US/docs/Web/API/History#Properties) del navegador. Por ejemplo:"
    ),
    ("RouterLink.md", "seg-f2d3f149"): (
        "Usa [`Router#currentNavigation`]"
        "(/api/router/Router#currentNavigation) para recuperar un "
        "valor de navigation-state guardado como Signal. Por ejemplo, "
        "para capturar el `tracingId` durante la `Navigation`."
    ),
    ("RouterLink.md", "seg-c2784b64"): (
        "Para que un elemento personalizado funcione con routerLink, "
        "ese elemento debe implementar el atributo `href` y listar "
        "`href` en el array de propiedades estáticas."
    ),
    # ===============================================================
    # angular/api/router/RouterLinkWithHref.md
    # ===============================================================
    ("RouterLinkWithHref.md", "seg-5ee70d2c"): (
        "Versión de `RouterLink` que acepta un `href` literal. Se usa "
        "cuando el destino no es una ruta del router sino una URL "
        "estática."
    ),
    ("RouterLinkWithHref.md", "seg-79ec8cd3"): (
        "Variante que toma la URL final como `href` literal en vez de "
        "decomponerla en una matriz `commands`."
    ),
    ("RouterLinkWithHref.md", "seg-16eb53e3"): (
        "Representa el valor del atributo `href` aplicado al host, "
        "cuando es `<a>`/`<area>` o un elemento personalizado compatible. "
        "Para otras etiquetas, el valor es `null`."
    ),
    ("RouterLinkWithHref.md", "seg-1d455699"): (
        "Representa el atributo `target` en el host. Solo se usa cuando "
        "el host es `<a>`/`<area>` o un elemento personalizado compatible."
    ),
    # ===============================================================
    # angular/api/router/RouterLinkActive.md
    # ===============================================================
    ("RouterLinkActive.md", "seg-f15352c7"): (
        "Verifica si la ruta enlazada de un elemento está activa y "
        "permite especificar una o más clases CSS para añadir al "
        "elemento cuando lo está."
    ),
    ("RouterLinkActive.md", "seg-c35a0289"): (
        "Construye una instancia nueva con un router y un elemento "
        "determinado."
    ),
    ("RouterLinkActive.md", "seg-3bb565d2"): (
        "Construye `RouterLinkActive` con un router, un `ElementRef` y "
        "un `Renderer2`."
    ),
    ("RouterLinkActive.md", "seg-0b3518f5"): "Determina si el link del router está activo.",
    ("RouterLinkActive.md", "seg-454330ad"): "Opciones para configurar cómo se decide la activación del link.",
    ("RouterLinkActive.md", "seg-4a563ff3"): (
        "Opciones para configurar cómo se determina si un link del "
        "router está activo. Estas opciones se pasan a "
        "[`isActive()`](/api/router/isActive). Si es `undefined`, "
        "el comportamiento por defecto compara subpaths y query "
        "parámetros."
    ),
    ("RouterLinkActive.md", "seg-37c0dee7"): (
        "Vector de clases o array de pares clave-valor de "
        "clase-origen/destino para añadir al elemento host cuando "
        "la ruta está activa."
    ),
    ("RouterLinkActive.md", "seg-bb0823f8"): "Cuando se aplica al elemento, se activa la ruta actual.",
    ("RouterLinkActive.md", "seg-f650b349"): (
        "Atributo aria-current a aplicar cuando el link del router "
        "está activo. Valores posibles: `'page'` | `'step'` | "
        "`'location'` | `'date'` | `'time'` | `true` | `false`."
    ),
    ("RouterLinkActive.md", "seg-8b8c0f21"): (
        "Emite los mismos pares clave-valor que el `routerLinkActive` "
        "de entrada."
    ),
    ("RouterLinkActive.md", "seg-2ccc3bc7"): (
        "Puedes usar el output `isActiveChange` para ser notificado "
        "cada vez que el link se vuelve activo o inactivo. Emite:"
    ),
    ("RouterLinkActive.md", "seg-216c2bdc"): (
        "Verifica si la ruta enlazada de un elemento está activa y "
        "permite especificar una o más clases CSS para añadir al "
        "elemento cuando lo está."
    ),
    ("RouterLinkActive.md", "seg-57bef778"): (
        "Cada vez que la URL es `/user` o `/user/bob`, se añade la "
        "clase `active-link` al enlace. Si la URL cambia, la clase se "
        "retira. Puedes configurar más de una clase."
    ),
    ("RouterLinkActive.md", "seg-6318d508"): (
        "Para añadir las clases solo cuando la URL coincide exactamente "
        "con el enlace, añade la opción `exact: true`."
    ),
    ("RouterLinkActive.md", "seg-533dc50f"): (
        "Para consultar directamente el estado [`isActive`]"
        "(/api/router/isActive) del link, asigna la instancia de "
        "[`RouterLinkActive`](/api/router/RouterLinkActive) a una "
        "variable de plantilla."
    ),
    ("RouterLinkActive.md", "seg-6ac0631a"): (
        "Puedes aplicar la directiva [`RouterLinkActive`]"
        "(/api/router/RouterLinkActive) al ancestro de los elementos "
        "enlazados. Por ejemplo, el siguiente código añade la clase "
        "`active-link` al `<div>` envolvente."
    ),
    ("RouterLinkActive.md", "seg-cd3e703c"): (
        "La directiva [`RouterLinkActive`](/api/router/RouterLinkActive) "
        "también puede usarse para fijar el atributo `aria-current` "
        "y dar una distinción alternativa a los elementos activos, "
        "visible y semánticamente útil para usuarios de lectores de "
        "pantalla y otras tecnologías asistivas."
    ),
    ("RouterLinkActive.md", "seg-36df100c"): (
        "Nota: `RouterLinkActive` es una consulta [`ContentChildren`]"
        "(/api/core/ContentChildren). Las consultas de content children "
        "no recuperan elementos o directivas que estén dentro de otros "
        "componentes. Por este motivo, las directivas se aplican solo "
        "en descendientes directos."
    ),
    # ===============================================================
    # angular/api/router/ActivatedRoute.md
    # ===============================================================
    ("ActivatedRoute.md", "seg-6ba03b30"): (
        "Acceso a la información de una ruta asociada al componente "
        "cargado en un outlet. Sirve para recorrer el árbol de "
        "[`RouterState`](/api/router/RouterState) y extraer información "
        "de los nodos."
    ),
    ("ActivatedRoute.md", "seg-e27a492b"): (
        "El componente tiene una `ActivatedRoute` cuando es el objetivo "
        "de una `<router-outlet>`."
    ),
    ("ActivatedRoute.md", "seg-23744e12"): (
        "El snapshot actual de esta ruta."
    ),
    ("ActivatedRoute.md", "seg-bbbfbedc"): (
        "Un `Observable` del título de la ruta resuelta."
    ),
    ("ActivatedRoute.md", "seg-74315f7f"): (
        "Un `Observable` de los segmentos de URL que coinciden con "
        "esta ruta."
    ),
    ("ActivatedRoute.md", "seg-7eb5367e"): (
        "Un `Observable` de los parámetros de matriz scoped a esta "
        "ruta."
    ),
    ("ActivatedRoute.md", "seg-598cea63"): (
        "Un `Observable` de los query parameters compartidos por todas "
        "las rutas."
    ),
    ("ActivatedRoute.md", "seg-df766367"): (
        "Un `Observable` del fragmento de URL compartido por todas las "
        "rutas."
    ),
    ("ActivatedRoute.md", "seg-53763cd7"): (
        "Un `Observable` de los datos estáticos y resueltos de esta ruta."
    ),
    ("ActivatedRoute.md", "seg-f545a545"): (
        "Un mapa de recursos para esta ruta."
    ),
    ("ActivatedRoute.md", "seg-869e5a75"): (
        "El nombre del outlet de la ruta, una constante."
    ),
    ("ActivatedRoute.md", "seg-ddbfe7f7"): "El componente de la ruta, una constante.",
    ("ActivatedRoute.md", "seg-56728f3f"): (
        "La configuración usada para hacer coincidir esta ruta."
    ),
    ("ActivatedRoute.md", "seg-9ea2e9b3"): "La raíz del estado del router.",
    ("ActivatedRoute.md", "seg-c9b45d88"): (
        "El padre de esta ruta en el árbol de estado del router."
    ),
    ("ActivatedRoute.md", "seg-a3447192"): (
        "El primer hijo de esta ruta en el árbol de estado del router."
    ),
    ("ActivatedRoute.md", "seg-17c73fcf"): (
        "Los hijos de esta ruta en el árbol de estado del router."
    ),
    ("ActivatedRoute.md", "seg-57e1e2ca"): (
        "La ruta desde la raíz del estado del router hasta esta ruta."
    ),
    ("ActivatedRoute.md", "seg-33a2eb4a"): (
        "Un `Observable` que contiene un mapa de los parámetros "
        "requeridos y opcionales específicos de la ruta. El mapa "
        "soporta recuperación de uno o varios valores del mismo "
        "parámetro."
    ),
    ("ActivatedRoute.md", "seg-409dd438"): (
        "Un `Observable` que contiene un mapa de los query parameters "
        "disponibles para todas las rutas. El mapa soporta "
        "recuperación de uno o varios valores del parámetro."
    ),
    # ===============================================================
    # angular/api/router/ActivatedRouteSnapshot.md
    # ===============================================================
    ("ActivatedRouteSnapshot.md", "seg-f64506b6"): "Contiene la información de una ruta asociada a un componente cargado en un outlet en un momento dado.",
    ("ActivatedRouteSnapshot.md", "seg-ccc8dca5"): (
        "Contiene la información de una ruta asociada a un componente "
        "cargado en un outlet en un momento dado. `ActivatedRouteSnapshot` "
        "también se usa para recorrer el árbol del router."
    ),
    ("ActivatedRouteSnapshot.md", "seg-1ed93572"): (
        "Construye `ActivatedRouteSnapshot` con la URL, los "
        "parámetros y los datos resueltos."
    ),
    ("ActivatedRouteSnapshot.md", "seg-4663ff25"): (
        "Los segmentos de URL que coinciden con esta ruta."
    ),
    ("ActivatedRouteSnapshot.md", "seg-19dd0e05"): "Los query parameters compartidos por todas las rutas.",
    ("ActivatedRouteSnapshot.md", "seg-8ebb00b7"): (
        "Los query parameters compartidos por todas las rutas."
    ),
    ("ActivatedRouteSnapshot.md", "seg-8dd9650e"): "La configuración usada para hacer coincidir esta ruta.",
    ("ActivatedRouteSnapshot.md", "seg-ac519e7b"): (
        "El resultado de ejecutar la función `resources` de la ruta."
    ),
    ("ActivatedRouteSnapshot.md", "seg-11721325"): "El título de la ruta resuelta.",
    ("ActivatedRouteSnapshot.md", "seg-e90ad353"): (
        "Los segmentos de URL que coinciden con esta ruta."
    ),
    ("ActivatedRouteSnapshot.md", "seg-8355c32c"): (
        "Los parámetros de matriz scoped a esta ruta. Puedes calcular "
        "todos los parámetros en el estado del router, o acceder desde "
        "fuera de un componente activado recorriendo el "
        "[`RouterState`](/api/router/RouterState)."
    ),
    ("ActivatedRouteSnapshot.md", "seg-c3bae03e"): (
        "Los query parameters compartidos por todas las rutas."
    ),
    ("ActivatedRouteSnapshot.md", "seg-a3e5cae4"): "El fragmento de URL compartido por todas las rutas.",
    ("ActivatedRouteSnapshot.md", "seg-0b9a3af2"): (
        "El fragmento de URL compartido por todas las rutas."
    ),
    ("ActivatedRouteSnapshot.md", "seg-18afa533"): (
        "Los datos estáticos y resueltos de esta ruta."
    ),
    ("ActivatedRouteSnapshot.md", "seg-7b86f017"): "El nombre del outlet de la ruta.",
    ("ActivatedRouteSnapshot.md", "seg-d10097f8"): "El componente de la ruta.",
    ("ActivatedRouteSnapshot.md", "seg-24d4ce79"): "La raíz del estado del router.",
    ("ActivatedRouteSnapshot.md", "seg-2b8a5aff"): (
        "El padre de esta ruta en el árbol de estado del router."
    ),
    ("ActivatedRouteSnapshot.md", "seg-4550c73c"): (
        "El primer hijo de esta ruta en el árbol de estado del router."
    ),
    ("ActivatedRouteSnapshot.md", "seg-39b5fb99"): (
        "Los hijos de esta ruta en el árbol de estado del router."
    ),
    ("ActivatedRouteSnapshot.md", "seg-188ef8ed"): (
        "La ruta desde la raíz del estado del router hasta esta ruta."
    ),
    ("ActivatedRouteSnapshot.md", "seg-a96c7607"): (
        "Contiene la información de una ruta asociada a un componente "
        "cargado en un outlet en un momento dado. `ActivatedRouteSnapshot` "
        "también se usa para recorrer el árbol del router."
    ),
    # ===============================================================
    # angular/api/router/ExtraOptions.md
    # ===============================================================
    ("ExtraOptions.md", "seg-402448dd"): (
        "Un conjunto de opciones de configuración para un módulo de "
        "router, pasadas al método `forRoot()`."
    ),
    ("ExtraOptions.md", "seg-95b6296b"): (
        "Si es `true`, registra en consola todos los eventos de "
        "navegación internos. Útil para depuración."
    ),
    ("ExtraOptions.md", "seg-61485cd4"): (
        "Si es `true`, activa la estrategia de ubicación que usa el "
        "fragmento de la URL en vez de la History API."
    ),
    ("ExtraOptions.md", "seg-d6e11422"): (
        "Uno de `enabled`, `enabledBlocking`, `enabledNonBlocking` o "
        "`disabled`. Cuando es `enabled` o `enabledBlocking`, la "
        "navegación inicial empieza antes de que se cree el componente "
        "raíz."
    ),
    ("ExtraOptions.md", "seg-73bb971c"): (
        "Si es `true`, activa el binding de información del estado del "
        "[`Router`](/api/router/Router) directamente a las entradas del "
        "componente en las configuraciones [`Route`](/api/router/Route). "
        "También puede activarse con [`withComponentInputBinding`]"
        "(/api/router/withComponentInputBinding)."
    ),
    ("ExtraOptions.md", "seg-48f6a333"): "(@experimental) Sin descripción detallada más allá de que habilita view transitions.",
    ("ExtraOptions.md", "seg-18d4a1fa"): (
        "Si es `true`, activa las view transitions en el Router "
        "ejecutando la activación y desactivación de la ruta dentro de "
        "`document.startViewTransition`."
    ),
    ("ExtraOptions.md", "seg-3a5f8153"): (
        "Manejador personalizado de errores para navegaciones fallidas. "
        "Si devuelve un valor, la `Promise` de navegación se resuelve "
        "con ese valor. Si lanza una excepción, la `Promise` se rechaza. "
        "Las excepciones no manejadas podrían aparecer en "
        "[`console.error`](https://developer.mozilla.org/en-US/docs/Web/API/Console/error)."
    ),
    ("ExtraOptions.md", "seg-1194b536"): (
        "Configura una estrategia de precarga. Uno de "
        "[`PreloadAllModules`](/api/router/PreloadAllModules) o "
        "[`NoPreloading`](/api/router/NoPreloading) (por defecto)."
    ),
    ("ExtraOptions.md", "seg-cd8b36d5"): (
        "Configura el desplazamiento de scroll que el router usará "
        "al saltar a un elemento. Dada una tupla con valores `x` e "
        "`y`, el router usa ese desplazamiento cada vez que hace "
        "scroll."
    ),
    ("ExtraOptions.md", "seg-d411d02d"): (
        "Cuando es `'enabled'`, salta al elemento ancla si la URL "
        "tiene un fragmento. El anchor scrolling está desactivado "
        "por defecto. No ocurre en `popstate`; en su lugar, se "
        "invierte la navegación."
    ),
    ("ExtraOptions.md", "seg-f8d05934"): (
        "Configura si la posición de scroll se restaura al navegar "
        "hacia atrás."
    ),
    ("ExtraOptions.md", "seg-cd4ef282"): (
        "Puedes implementar un comportamiento de restauración de "
        "scroll personalizado adaptando el comportamiento `enabled` "
        "como en el ejemplo siguiente."
    ),
    ("ExtraOptions.md", "seg-6974fa93"): (
        "Configura cómo el Router intenta restaurar el estado cuando "
        "una navegación se cancela. "
        "`replace` siempre usa `location.replaceState` para fijar el "
        "estado del navegador al de la ruta anterior."
    ),
    ("ExtraOptions.md", "seg-d83dd068"): (
        "Configura el comportamiento por defecto para una petición de "
        "navegación a la URL actual. Si no se especifica, el "
        "[`Router`](/api/router/Router) usará `'ignore'`."
    ),
    ("ExtraOptions.md", "seg-055a9705"): (
        "Define cómo el router une parámetros, data y resolved data "
        "de rutas padre a hijas. Por defecto ('always'), una ruta "
        "hereda todos los parámetros de sus rutas padre. Configurar "
        "en `'emptyOnly'` obliga a que solo se hereden parámetros "
        "vacíos."
    ),
    ("ExtraOptions.md", "seg-26355664"): (
        "Define cuándo el router actualiza la URL del navegador. Por "
        "defecto ('deferred'), actualiza tras una navegación exitosa. "
        "Configurar en 'eager' si prefieres actualizar la URL al "
        "comienzo de la navegación."
    ),
    ("ExtraOptions.md", "seg-26f4c271"): (
        "La estrategia por defecto para manejar query params en "
        "[`Router.createUrlTree`](/api/router/Router#createUrlTree) "
        "cuando no se facilita otra."
    ),
    ("ExtraOptions.md", "seg-2da0f9ef"): (
        "Si es `true`, la `Promise` se resolverá con `false`, igual "
        "que en otras navegaciones fallidas (por ejemplo, cuando los "
        "guards se rechazan). Si no, la `Promise` se rechaza."
    ),
    # ===============================================================
    # angular/api/router/NavigationExtras.md
    # ===============================================================
    ("NavigationExtras.md", "seg-f754ec79"): (
        "Opciones que modifican la estrategia de navegación del "
        "[`Router`](/api/router/Router). Pasa un objeto con estas "
        "propiedades a una función de navegación para ajustar el "
        "comportamiento."
    ),
    ("NavigationExtras.md", "seg-3cd6d975"): (
        "Especifica una URI raíz para usar en navegación relativa. "
        "Por ejemplo, en una configuración de rutas con padre y dos "
        "hijos."
    ),
    ("NavigationExtras.md", "seg-a24ad84c"): (
        "La siguiente función `go()` navega a la ruta `list` "
        "interpretando la URI de destino como relativa a la ruta "
        "`child` activa. Si la ruta activa fuera la raíz, navegaría "
        "a `/list`."
    ),
    ("NavigationExtras.md", "seg-f8264772"): (
        "Un valor `null` o `undefined` indica que los comandos de "
        "navegación deben aplicarse relativos a la raíz."
    ),
    ("NavigationExtras.md", "seg-c6e19361"): "Fija los query parameters en la URL.",
    ("NavigationExtras.md", "seg-fb4c53bc"): "Fija el fragmento hash de la URL.",
    ("NavigationExtras.md", "seg-56385deb"): (
        "Cómo se manejan los query parameters en el link del router "
        "para la siguiente navegación."
    ),
    ("NavigationExtras.md", "seg-9891f6a2"): (
        "La opción 'preserve' descarta los nuevos query params."
    ),
    ("NavigationExtras.md", "seg-fc67fea3"): (
        "La opción 'merge' añade los nuevos query params a los de la "
        "URL actual."
    ),
    ("NavigationExtras.md", "seg-38fed4d6"): (
        "En caso de colisión entre parámetros actuales y los del "
        "objeto `queryParams`, se usa el nuevo valor."
    ),
    ("NavigationExtras.md", "seg-f183674c"): "Si es `true`, preserva el fragmento de URL para la siguiente navegación.",
    ("NavigationExtras.md", "seg-14d23d23"): (
        "Cómo gestionar una petición de navegación a la URL actual. "
        "Este valor es un subconjunto de las opciones en "
        "[`OnSameUrlNavigation`](/api/router/OnSameUrlNavigation) y "
        "toma precedencia."
    ),
    ("NavigationExtras.md", "seg-591eb0de"): (
        "Si es `true`, navega sin añadir un nuevo estado al historial."
    ),
    ("NavigationExtras.md", "seg-72e177a8"): (
        "Si es `true`, navega reemplazando el estado actual en el "
        "historial."
    ),
    ("NavigationExtras.md", "seg-808816fd"): (
        "Estado definido por el desarrollador que se puede pasar a "
        "cualquier navegación. Accede a este valor a través del "
        "objeto [`Navigation.extras`](/api/router/Navigation#extras) "
        "devuelto por [`Router.currentNavigation`]"
        "(/api/router/Router#currentNavigation)."
    ),
    ("NavigationExtras.md", "seg-535ae2b3"): (
        "Úsalo para transportar información transitoria sobre esta "
        "navegación en particular, como por qué ocurrió. De esta "
        "manera, se diferencia del valor persistente `state` que se "
        "asigna a `history.state`."
    ),
    ("NavigationExtras.md", "seg-7fef3330"): (
        "Cada uno de estos quiere una animación distinta al momento "
        "de la navegación. Esta información no tendría sentido "
        "persistirla en la URL o en el estado del historial, pero sigue "
        "siendo importante para la animación."
    ),
    ("NavigationExtras.md", "seg-78f62e9c"): (
        "Cuando está fijado, el Router actualizará la barra de "
        "direcciones del navegador para coincidir con el "
        "[`UrlTree`](/api/router/UrlTree) dado, en vez del que se usa "
        "para hacer coincidir la ruta."
    ),
    ("NavigationExtras.md", "seg-74a0e534"): (
        "Configura cómo se gestiona el scroll para una navegación "
        "individual cuando la restauración de scroll está activada en "
        "el router."
    ),
    # ===============================================================
    # angular/api/router/RouterOutlet.md
    # ===============================================================
    ("RouterOutlet.md", "seg-b746195f"): (
        "Actúa como marcador que Angular rellena dinámicamente según "
        "el estado del router."
    ),
    ("RouterOutlet.md", "seg-ddd5a5ad"): "El nombre del outlet.",
    ("RouterOutlet.md", "seg-7c4cfbc9"): (
        "Emite un evento `deactivate` cuando un componente se destruye."
    ),
    ("RouterOutlet.md", "seg-72425293"): (
        "Emite una instancia del componente adjuntada cuando la "
        "[`RouteReuseStrategy`](/api/router/RouteReuseStrategy) pide "
        "readjuntar un subárbol antes separado."
    ),
    ("RouterOutlet.md", "seg-64b53801"): (
        "Emite una instancia del componente separada cuando la "
        "[`RouteReuseStrategy`](/api/router/RouteReuseStrategy) pide "
        "separar el subárbol."
    ),
    ("RouterOutlet.md", "seg-4764221d"): (
        "Datos que se proporcionan al injector hijo a través del "
        "token [`ROUTER_OUTLET_DATA`](/api/router/ROUTER_OUTLET_DATA). "
        "Cuando no se fija, el valor del token es `undefined` por defecto."
    ),
    ("RouterOutlet.md", "seg-2baf4875"): (
        "Llamada cuando la [`RouteReuseStrategy`]"
        "(/api/router/RouteReuseStrategy) pide separar el subárbol."
    ),
    ("RouterOutlet.md", "seg-4f7a577e"): (
        "Llamada cuando la [`RouteReuseStrategy`]"
        "(/api/router/RouteReuseStrategy) pide readjuntar un subárbol "
        "antes separado."
    ),
    ("RouterOutlet.md", "seg-8028a389"): (
        "Actúa como marcador que Angular rellena dinámicamente según "
        "el estado del router. Cada outlet puede tener un nombre único, "
        "determinado por el atributo opcional `name`. El nombre puede "
        "ser el destino de rutas secundarias."
    ),
    ("RouterOutlet.md", "seg-8ab3c768"): (
        "Los outlets con nombre pueden ser el destino de rutas "
        "secundarias. El objeto [`Route`](/api/router/Route) de una "
        "ruta secundaria tiene una propiedad `outlet` para identificar "
        "el outlet destino."
    ),
    # ===============================================================
    # angular/api/router/RouterOutletContract.md
    # ===============================================================
    ("RouterOutletContract.md", "seg-aacb447d"): (
        "Interfaz que define el contrato para desarrollar un outlet de "
        "componente para el [`Router`](/api/router/Router)."
    ),
    ("RouterOutletContract.md", "seg-ed09ade5"): (
        "Si el outlet dado está activado. Un outlet se considera "
        "\"activado\" si tiene un componente activo."
    ),
    ("RouterOutletContract.md", "seg-8d1b384a"): "La instancia del componente activado, o `null` si el outlet no está activado.",
    ("RouterOutletContract.md", "seg-2ffcf934"): (
        "El [`Data`](/api/router/Data) del snapshot "
        "[`ActivatedRoute`](/api/router/ActivatedRoute)."
    ),
    ("RouterOutletContract.md", "seg-ff499ea0"): (
        "El [`ActivatedRoute`](/api/router/ActivatedRoute) del outlet, "
        "o `null` si el outlet no está activado."
    ),
    ("RouterOutletContract.md", "seg-82eb16bc"): (
        "Llamada del [`Router`](/api/router/Router) cuando el outlet "
        "debe activarse (crear un componente)."
    ),
    ("RouterOutletContract.md", "seg-8e3c70b2"): (
        "Solicitud para destruir el componente activado actualmente. "
        "Cuando una [`RouteReuseStrategy`](/api/router/RouteReuseStrategy) "
        "indica que una [`ActivatedRoute`](/api/router/ActivatedRoute) "
        "debe almacenarse para reuso, no se llama a `destroy()`."
    ),
    ("RouterOutletContract.md", "seg-4c73ad10"): (
        "Llamada cuando la [`RouteReuseStrategy`]"
        "(/api/router/RouteReuseStrategy) pide separar el subárbol. "
        "Es similar a `deactivate`, pero el componente activado no debe "
        "destruirse; en su lugar, se almacena para reuso futuro."
    ),
    ("RouterOutletContract.md", "seg-b1799802"): (
        "Llamada cuando la [`RouteReuseStrategy`]"
        "(/api/router/RouteReuseStrategy) pide readjuntar un subárbol "
        "antes separado."
    ),
    ("RouterOutletContract.md", "seg-659fbb9d"): (
        "Emite un evento `activate` cuando se instancia un componente "
        "nuevo."
    ),
    ("RouterOutletContract.md", "seg-e7532ab7"): (
        "Emite un evento `deactivate` cuando se destruye un componente."
    ),
    ("RouterOutletContract.md", "seg-e21f4a3d"): (
        "Emite una instancia del componente adjuntada cuando la "
        "[`RouteReuseStrategy`](/api/router/RouteReuseStrategy) pide "
        "readjuntar un subárbol antes separado."
    ),
    ("RouterOutletContract.md", "seg-0ae22216"): (
        "Emite una instancia del componente separada cuando la "
        "[`RouteReuseStrategy`](/api/router/RouteReuseStrategy) pide "
        "separar el subárbol."
    ),
    ("RouterOutletContract.md", "seg-3489694b"): (
        "Se usa para indicar que el outlet puede enlazar datos del "
        "[`Router`](/api/router/Router) a las entradas del componente "
        "del outlet. Cuando es `undefined` o `false` y el "
        "desarrollador no ha activado "
        "`withComponentInputBinding()`, los datos del router no se "
        "enlazan."
    ),
    ("RouterOutletContract.md", "seg-1d1f9f01"): (
        "Interfaz que define el contrato para desarrollar un outlet de "
        "componente para el [`Router`](/api/router/Router). Un outlet "
        "actúa como marcador que Angular rellena dinámicamente."
    ),
    # ===============================================================
    # angular/api/router/Navigation.md
    # ===============================================================
    ("Navigation.md", "seg-1ed93572"): (
        "Clase que representa una navegación del router."
    ),
    ("Navigation.md", "seg-f8d05934"): (
        "Identificador único de la navegación actual."
    ),
    ("Navigation.md", "seg-74a0e534"): (
        "La URL fuente desde la que empezó esta navegación."
    ),
    ("Navigation.md", "seg-f8d05934ab"): (
        "Tipo de la operación que disparó la navegación (routerLink, "
        "imperativa, popstate, etc)."
    ),
    ("Navigation.md", "seg-bb6248b2"): (
        "El estado que se pasó con la navegación a través de la "
        "propiedad `state` de [`NavigationExtras`]"
        "(/api/router/NavigationExtras)."
    ),
    ("Navigation.md", "seg-33e5225e"): (
        "El árbol de URL objetivo de esta navegación cuando se "
        "completa con éxito."
    ),
    ("Navigation.md", "seg-1f7d0d2f"): (
        "El árbol de URL inicial al inicio de la navegación."
    ),
    ("Navigation.md", "seg-2e28979a"): (
        "El router state final después de la navegación."
    ),
    ("Navigation.md", "seg-bda95b3d"): (
        "Las opciones que pueden modificar la estrategia de "
        "navegación y otros comportamientos."
    ),
    # ===============================================================
    # angular/api/router/UrlTree.md
    # ===============================================================
    ("UrlTree.md", "seg-9c398dfb"): "Representa la URL analizada.",
    ("UrlTree.md", "seg-7f8fd0eb"): "El grupo segmento raíz del árbol de URL.",
    ("UrlTree.md", "seg-612b34c7"): "Los query params de la URL.",
    ("UrlTree.md", "seg-f709e4fe"): "El fragmento de la URL.",
    ("UrlTree.md", "seg-9d09cc4a"): (
        "Representa la URL analizada. Como el estado del router es un "
        "árbol y la URL no es sino un estado serializado, la URL es un "
        "árbol serializado. `UrlTree` es una estructura que da una "
        "representación intermedia."
    ),
    # ===============================================================
    # angular/api/router/RouteReuseStrategy.md
    # ===============================================================
    ("RouteReuseStrategy.md", "seg-102f089f"): (
        "Forma de personalizar cuándo se reusan las rutas activadas."
    ),
    ("RouteReuseStrategy.md", "seg-4ebc72f4"): (
        "Determina si esta ruta (y su subárbol) deben separarse para "
        "reusarse más tarde."
    ),
    ("RouteReuseStrategy.md", "seg-ab916583"): (
        "Almacena la ruta separada. Almacenar `null` debería borrar "
        "el valor previamente almacenado."
    ),
    ("RouteReuseStrategy.md", "seg-af2e9807"): (
        "Determina si esta ruta (y su subárbol) deben readjuntarse."
    ),
    ("RouteReuseStrategy.md", "seg-670454d0"): (
        "Recupera la ruta previamente almacenada."
    ),
    ("RouteReuseStrategy.md", "seg-77faedec"): (
        "Determina si una ruta debe reusarse. Nota: recrear un "
        "componente devolviendo `false` no vuelve a ejecutar guards ni "
        "resolvers automáticamente; el comportamiento de rerun para una "
        "ruta sin cambios depende del router."
    ),
    ("RouteReuseStrategy.md", "seg-0073f100"): (
        "Devuelve una lista de todos los "
        "[`DetachedRouteHandle`](/api/router/DetachedRouteHandle) "
        "actualmente almacenados."
    ),
    ("RouteReuseStrategy.md", "seg-d882955c"): (
        "Determina si el injector para la ruta dada debe destruirse. "
        "Si este método devuelve `true`, el router destruirá el "
        "injector de la ruta."
    ),
    # ===============================================================
    # angular/api/router/BaseRouteReuseStrategy.md
    # ===============================================================
    ("BaseRouteReuseStrategy.md", "seg-09775cca"): (
        "Esta estrategia de reutilización por defecto solo reusa rutas "
        "cuando las configuraciones del router que coinciden son "
        "idénticas. Evita que los componentes se destruyan y se "
        "recreen cuando solo cambian parámetros de la ruta, no la "
        "ruta en sí."
    ),
    ("BaseRouteReuseStrategy.md", "seg-3b68dbdd"): (
        "Sin operación; la ruta nunca se almacena porque esta "
        "estrategia nunca separa rutas para reuso."
    ),
    ("BaseRouteReuseStrategy.md", "seg-7b1f38ac"): (
        "Devuelve `false`, lo que significa que la ruta (y su "
        "subárbol) nunca se readjuntan."
    ),
    ("BaseRouteReuseStrategy.md", "seg-6dc7af68"): (
        "Devuelve `null` porque esta estrategia no almacena rutas para "
        "reuso."
    ),
    ("BaseRouteReuseStrategy.md", "seg-f593815e"): (
        "Determina si una ruta debe reusarse. Esta estrategia devuelve "
        "`true` cuando las configs de ruta futura y actual son "
        "idénticas."
    ),
    ("BaseRouteReuseStrategy.md", "seg-7b5dba07"): (
        "Determina si el injector de la ruta dada debe destruirse. "
        "Este método lo invoca el router tras las navegaciones."
    ),
    # ===============================================================
    # angular/api/router/RouteResolveFn.md
    # ===============================================================
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
            else:
                # sin override: identidad (los literals se preservan, la prosa es apparatus)
                if entry["translated_text"] and entry["translated_text"] != entry["original_text"]:
                    entry["translated_text"] = entry["original_text"]
                    changed = True
                    applied += 1
        if changed:
            data["generated_at"] = "2026-10-21T00:30:00Z"
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"entradas sobrescritas: {applied} / {total}, con override: {considered}")
    return 0


if __name__ == "__main__":
    main()