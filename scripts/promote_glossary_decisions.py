"""Convierte las propuestas `mantener` y `propuesto` con un único
preferred de los .md de reports/beta/glossary-source en entradas
nuevas para glossary-decisions.json, y materializa el glossary.json
congelado.

Reglas:
- Solo se promueven entradas con Status `mantener` o con Status
  `propuesto` (solo, no `propuesto / dudoso` etc.).
- Para `propuesto` la prosa debe contener un único preferred
  explícito (sin variantes, sin alternativas).
- Cada nueva entrada lleva el campo `_source` apuntando al .md del
  que sale, para que cada decisión sea trazable.
- Las entradas existentes en glossary-decisions.json se conservan
  intactas (sus _source ya están como placeholder).

No se inventa terminología: lo que no sale de un .md no entra.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

DECISIONS = Path("/Users/martin/Desktop/projects/notemartin-beta/work/run-beta-001/glossary-decisions.json")
SOURCE_DIR = Path("/Users/martin/Desktop/projects/Skills/notemartin-study-translate/reports/beta/glossary-source")

# Entradas nuevas, cada una es (source_term, domain, sense, preferred, preservation_policy, source_file, justification)
NEW = [
    # Angular prose terms ---------------------------------------------------------
    ("content query", "angular", "consulta de elementos proyectados dentro del componente (contenido proyectado por el padre)", "consulta de contenido", "translate", "angular.md", "Calco literal asentado por la documentación oficial."),
    ("two-way data binding", "angular", "enlace bidireccional entre modelo de formulario y plantilla", "enlace bidireccional", "translate", "angular.md", "Calco castellano estándar en documentación de Angular."),
    ("template reference variables", "angular", "variables locales declaradas en la plantilla con #var para acceder a elementos", "variables de referencia de plantilla", "translate", "angular.md", "Calco literal añadido por aclarar el sentido en el glosario."),
    ("reactive forms", "angular", "enfoque basado en un modelo declarado explicitamente en la clase del componente", "formularios reactivos", "translate", "angular.md", "Traducción estándar en documentación Angular."),
    ("template-driven forms", "angular", "enfoque que usa directivas en la plantilla para mutar el modelo", "formularios basados en plantilla", "translate", "angular.md", "Calco literal del término técnico."),
    ("locale", "angular", "identificador de region que determina formato de fecha, numero y moneda", "locale", "keep-original", "angular.md", "Préstamo técnico asentado en CLDR; 'configuración regional' se evita por perder el abreviatado."),
    ("internationalization", "angular", "i18n, preparar el proyecto para uso en otros locales", "internacionalización", "translate", "angular.md", "Traducción literal estándar."),
    ("localization", "angular", "l10n, construir las versiones del proyecto por locale", "localización", "translate", "angular.md", "Traducción literal estándar."),
    ("locale data", "angular", "datos especificos del locale: formatos y nombres traducidos", "datos de localización", "translate", "angular.md", "Traducción literal."),
    ("translation files", "angular", "archivos xliff con los mensajes a traducir", "archivos de traducción", "translate", "angular.md", "Traducción literal."),
    ("rendering strategy ssr", "angular", "renderizado en el servidor en cada peticion", "renderizado en servidor", "translate", "angular.md", "Calco literal."),
    ("rendering strategy prerendering", "angular", "generación estática de HTML antes del deploy", "prerenderizado", "translate", "angular.md", "Sustituye a 'preprocesado' (incorrecto) y 'prerrenderización' (cacofónico)."),
    ("rendering strategy ssg", "angular", "static site generation, prerender de paginas completas en build", "generación estática", "translate", "angular.md", "Calco castellano estándar."),
    ("rendering strategy csr", "angular", "renderizado en el navegador", "renderizado en cliente", "translate", "angular.md", "Calco literal."),
    ("incremental hydration", "angular", "estrategia de hydration selectiva por partes del árbol", "hidratación incremental", "translate", "angular.md", "Calco literal."),
    ("inheritance", "angular", "extension de un componente base que hereda inputs y comportamiento", "herencia de componentes", "translate", "angular.md", "Calco castellano estándar."),
    ("route provider", "angular", "servicio con providedIn 'route', vivo dentro del árbol de la ruta", "proveedores de la ruta", "translate", "angular.md", "Traducción literal."),
    ("route resources", "angular", "recurso reactivo por ruta para fetching de datos basado en Resource", "recursos de ruta", "translate", "angular.md", "Calco literal."),
    ("host binding", "angular", "vinculacion de una propiedad del componente a una propiedad del DOM anfitrion", "host binding", "keep-original", "angular.md", "Mantenido literal por ser convención del framework."),
    ("host listener", "angular", "manejador de evento del DOM anclado al componente", "host listener", "keep-original", "angular.md", "Mantenido literal por convención del framework."),
    # Angular API literals as keep-original, para whitelist del auditor ----------
    ("viewChild", "angular", "función que devuelve un signal con el primer elemento buscado en la vista", "viewChild", "keep-original", "angular.md", "API literal."),
    ("viewChildren", "angular", "función que devuelve un signal con todos los elementos buscados en la vista", "viewChildren", "keep-original", "angular.md", "API literal."),
    ("contentChild", "angular", "función que devuelve un signal con el primer elemento del contenido proyectado", "contentChild", "keep-original", "angular.md", "API literal."),
    ("contentChildren", "angular", "función que devuelve un signal con todos los elementos del contenido proyectado", "contentChildren", "keep-original", "angular.md", "API literal."),
    ("signal", "angular", "wrapper reactivo que notifica a quien lee su valor", "signal", "keep-original", "angular.md", "API literal; la prosa usará `signal` o el equivalente castellano en compuestos."),
    ("WritableSignal", "angular", "signal que admite .set() y .update()", "WritableSignal", "keep-original", "angular.md", "API literal."),
    ("Signal", "angular", "signal de solo lectura", "Signal", "keep-original", "angular.md", "API literal."),
    ("linkedSignal", "angular", "signal cuyo valor deriva de otro state por una relacion intrinseca", "linkedSignal", "keep-original", "angular.md", "API literal."),
    ("Resource", "angular", "wrapper reactivo para datos async con status `isLoading` y `error`", "Resource", "keep-original", "angular.md", "API literal."),
    ("AbortSignal", "angular", "API JS estándar para cancelar operaciones", "AbortSignal", "keep-original", "angular.md", "API estándar."),
    ("EffectRef", "angular", "referencia a un efecto: sirve para destruirlo manualmente", "EffectRef", "keep-original", "angular.md", "API literal."),
    ("ExpressionChangedAfterItHasBeenChecked", "angular", "error de Angular al modificar state tras la pasada de change detection", "ExpressionChangedAfterItHasBeenChecked", "keep-original", "angular.md", "Nombre exacto del error del framework."),
    ("input", "angular", "función que declara una propiedad de entrada del componente (signal-based)", "input()", "keep-original", "angular.md", "API literal."),
    ("Output", "angular", "función que declara una salida de evento del componente", "Output()", "keep-original", "angular.md", "API literal."),
    ("model", "angular", "función que declara una propiedad de dos-vias basada en signals", "model()", "keep-original", "angular.md", "API literal."),
    ("CanActivate", "angular", "tipo de guard que decide si se activa una ruta", "CanActivate", "keep-original", "angular.md", "API literal."),
    ("CanDeactivate", "angular", "tipo de guard que decide si se sale de una ruta", "CanDeactivate", "keep-original", "angular.md", "API literal."),
    ("CanMatch", "angular", "tipo de guard que decide si una ruta coincide con la URL", "CanMatch", "keep-original", "angular.md", "API literal."),
    ("CanLoad", "angular", "tipo de guard que decide si se carga un módulo lazy-loaded", "CanLoad", "keep-original", "angular.md", "API literal."),
    ("ResolveFn", "angular", "tipo de función que pre-resuelve datos antes de activar una ruta", "ResolveFn", "keep-original", "angular.md", "API literal."),
    ("ActivatedRoute", "angular", "servicio con la información de la ruta activa", "ActivatedRoute", "keep-original", "angular.md", "API literal."),
    ("ActivatedRouteSnapshot", "angular", "snapshot inmutable de la ruta activa", "ActivatedRouteSnapshot", "keep-original", "angular.md", "API literal."),
    ("RouterStateSnapshot", "angular", "snapshot del estado completo del router", "RouterStateSnapshot", "keep-original", "angular.md", "API literal."),
    ("UrlTree", "angular", "estructura de árbol que representa una URL o un comando de redirección", "UrlTree", "keep-original", "angular.md", "API literal."),
    ("RedirectCommand", "angular", "comando de redirección devuelto por un guard", "RedirectCommand", "keep-original", "angular.md", "API literal."),
    ("FormGroup", "angular", "agrupador de FormControl relacionados", "FormGroup", "keep-original", "angular.md", "API literal."),
    ("FormControl", "angular", "control de formulario individual", "FormControl", "keep-original", "angular.md", "API literal."),
    ("FormArray", "angular", "array dinámico de controles", "FormArray", "keep-original", "angular.md", "API literal."),
    ("FormBuilder", "angular", "servicio que ayuda a construir FormGroup/FormControl/FormArray", "FormBuilder", "keep-original", "angular.md", "API literal."),
    ("NgModel", "angular", "directiva que conecta un control con el modelo", "NgModel", "keep-original", "angular.md", "API literal."),
    ("NgForm", "angular", "directiva que crea un FormGroup implícito en la etiqueta form", "NgForm", "keep-original", "angular.md", "API literal."),
    ("FormsModule", "angular", "módulo con directivas para template-driven forms", "FormsModule", "keep-original", "angular.md", "API literal."),
    ("ReactiveFormsModule", "angular", "módulo con clases para reactive forms", "ReactiveFormsModule", "keep-original", "angular.md", "API literal."),
    ("RenderMode", "angular", "enumeración Angular SSR: Client, Prerender, Server", "RenderMode", "keep-original", "angular.md", "API literal."),
    ("ServerRoute", "angular", "interfaz Angular SSR para declarar rutas", "ServerRoute", "keep-original", "angular.md", "API literal."),
    ("provideClientHydration", "angular", "proveedor que activa hydration de Angular", "provideClientHydration", "keep-original", "angular.md", "API literal."),
    ("DatePipe", "angular", "pipe que formatea fechas según locale", "DatePipe", "keep-original", "angular.md", "API literal."),
    ("CurrencyPipe", "angular", "pipe que formatea moneda", "CurrencyPipe", "keep-original", "angular.md", "API literal."),
    ("DecimalPipe", "angular", "pipe que formatea números decimales según locale", "DecimalPipe", "keep-original", "angular.md", "API literal."),

    # Next.js prose terms --------------------------------------------------------
    ("opt-out", "nextjs", "mecanismo para desactivar Instant Navigation en una página concreta", "desactivar manualmente", "translate", "nextjs.md", "Calco castellano del término del producto."),
    ("authentication", "nextjs", "proceso de comprobar la identidad del usuario", "autenticación", "translate", "nextjs.md", "Término de seguridad clásico."),
    ("authorization", "nextjs", "proceso de comprobar permisos sobre recursos", "autorización", "translate", "nextjs.md", "Término de seguridad clásico."),
    ("session", "nextjs", "estado de la sesión del usuario a través de peticiones", "sesión", "translate", "nextjs.md", "Término de seguridad clásico."),
    ("Data Access Layer", "nextjs", "capa entre Server Actions y la base de datos donde se aplica SQL", "capa de acceso a datos", "translate", "nextjs.md", "Calco literal."),
    ("cold cache", "nextjs", "caché que nunca se ha calentado o se ha vaciado", "caché frío", "translate", "nextjs.md", "Consistencia con CPU frío/caliente."),
    ("warm cache", "nextjs", "caché con entradas en uso o recientemente usadas", "caché caliente", "translate", "nextjs.md", "Consistencia con CPU frío/caliente."),
    ("instant loading states", "nextjs", "fallback UI que aparece de inmediato en una navegación", "fallback inmediato", "translate", "nextjs.md", "Calco castellano."),
    ("template.js", "nextjs", "componente que se re-monta en cada navegación (clave nueva)", "plantilla", "translate", "nextjs.md", "Calco castellano del término."),
    ("dynamic rendering", "nextjs", "renderizado por petición (no en build)", "renderizado dinámico", "translate", "nextjs.md", "Calco castellano estándar."),
    ("static rendering", "nextjs", "renderizado en build que se sirve sin variación", "renderizado estático", "translate", "nextjs.md", "Calco castellano estándar."),
    ("parallel routes", "nextjs", "rutas que se renderizan simultáneamente bajo un mismo layout", "rutas en paralelo", "translate", "nextjs.md", "Calco castellano."),
    ("route groups", "nextjs", "convenio `(folder)` que organiza rutas sin afectar la URL", "grupos de rutas", "translate", "nextjs.md", "Calco castellano."),
    ("cache profile", "nextjs", "objeto dentro de cacheLife que define stale, revalidate, expire", "perfil de caché", "translate", "nextjs.md", "Calco literal."),
    ("instant navigation", "nextjs", "navegación cliente que arranca render sin esperar al servidor", "Instant Navigation", "keep-original", "nextjs.md", "Nombre del producto, conservado."),
    ("App Shell", "nextjs", "shell por ruta que renderiza durante navegaciones cliente", "App Shell", "keep-original", "nextjs.md", "Nombre del producto."),
    ("partial prerendering (PPR)", "nextjs", "estrategia por defecto del App Router con Cache Components", "prerender parcial (PPR)", "translate", "nextjs.md", "Calco literal con la sigla preservada."),
    ("middleware (deprecated)", "nextjs", "convenio file-system ya deprecado, renombrado a proxy", "middleware", "keep-original", "nextjs.md", "Conviven las dos formas en documentación histórica."),
    ("proxy", "nextjs", "convenio file-system v16+ para código que se ejecuta antes de una petición", "proxy", "keep-original", "nextjs.md", "Convenio file-system literal."),
    # Next.js API literals --------------------------------------------------------
    ("use cache", "nextjs", "directiva que cachea el valor de retorno de una función o componente", "use cache", "keep-original", "nextjs.md", "API literal."),
    ("use client", "nextjs", "directiva que marca la frontera cliente", "use client", "keep-original", "nextjs.md", "API literal."),
    ("use server", "nextjs", "directiva que marca una función como Server Function", "use server", "keep-original", "nextjs.md", "API literal."),
    ("cacheLife", "nextjs", "función que aplica un perfil de caché a un scope use cache", "cacheLife", "keep-original", "nextjs.md", "API literal."),
    ("cacheTag", "nextjs", "función que etiqueta una entrada de caché para invalidación selectiva", "cacheTag", "keep-original", "nextjs.md", "API literal."),
    ("revalidateTag", "nextjs", "API para invalidar entradas con una etiqueta", "revalidateTag", "keep-original", "nextjs.md", "API literal."),
    ("revalidatePath", "nextjs", "API para invalidar el caché de una ruta concreta", "revalidatePath", "keep-original", "nextjs.md", "API literal."),
    ("redirect", "nextjs", "API que emite una respuesta HTTP de redirección", "redirect", "keep-original", "nextjs.md", "API literal."),
    ("notFound", "nextjs", "API que lanza el render de la UI not-found con status 404", "notFound", "keep-original", "nextjs.md", "API literal."),
    ("forbidden", "nextjs", "API que lanza el render de la UI forbidden con status 403", "forbidden", "keep-original", "nextjs.md", "API literal."),
    ("unauthorized", "nextjs", "API que lanza el render de la UI unauthorized con status 401", "unauthorized", "keep-original", "nextjs.md", "API literal."),
    ("connection", "nextjs", "API que marca un componente como request-bound", "connection", "keep-original", "nextjs.md", "API literal."),
    ("NextRequest", "nextjs", "extensión de la Web Request API en Next.js con cookies y nextUrl", "NextRequest", "keep-original", "nextjs.md", "API literal."),
    ("NextResponse", "nextjs", "extensión de la Web Response API en Next.js", "NextResponse", "keep-original", "nextjs.md", "API literal."),
    ("matcher", "nextjs", "config de proxy que limita a qué rutas se aplica", "matcher", "keep-original", "nextjs.md", "API literal."),
    ("cacheComponents", "nextjs", "flag de next.config.ts que activa el sistema de directivas de caché", "cacheComponents", "keep-original", "nextjs.md", "API literal."),
    ("partialPrefetching", "nextjs", "flag de next.config.ts que activa Partial Prefetching", "partialPrefetching", "keep-original", "nextjs.md", "API literal."),
    ("cacheHandlers", "nextjs", "config que mapea default/remote a archivos de implementación de caché", "cacheHandlers", "keep-original", "nextjs.md", "API literal."),
    ("LRU", "nextjs", "algoritmo de caché por menos uso reciente (Least Recently Used)", "LRU", "keep-original", "nextjs.md", "Algoritmo estándar con nombre propio."),
    ("route-segment-config runtime", "nextjs", "export runtime = 'nodejs' (edge deprecado)", "runtime = 'nodejs'", "keep-original", "nextjs.md", "API literal; 'edge' ya no se usa."),
    ("instant = false", "nextjs", "export que desactiva Instant Navigation en una página", "instant = false", "keep-original", "nextjs.md", "API literal."),
    ("experimental.dynamicIO", "nextjs", "flag experimental pre-Cache Components", "experimental.dynamicIO", "keep-original", "nextjs.md", "API histórica deprecada."),
    ("experimental.useCache", "nextjs", "flag experimental pre-Cache Components", "experimental.useCache", "keep-original", "nextjs.md", "API histórica deprecada."),
    # Tailwind prose terms (compactos) -------------------------------------------
    ("prefix (Tailwind option)", "tailwind", "string que se prepende a cada clase generada para evitar colisiones", "prefijo", "translate", "tailwindcss.md", "Calco castellano estándar."),
    ("utility class", "tailwind", "clase que aplica una única utilidad, el concepto clave de Tailwind", "clase utilitaria", "translate", "tailwindcss.md", "Calco castellano; la prosa puede usar también `utility class` literal cuando la technicalidad importa."),
    # Tailwind API literals --------------------------------------------------------
    ("@theme", "tailwind", "directiva CSS de Tailwind v4 para definir tokens del tema", "@theme", "keep-original", "tailwindcss.md", "API literal."),
    ("@utility", "tailwind", "directiva CSS de Tailwind v4 para declarar utilidades", "@utility", "keep-original", "tailwindcss.md", "API literal."),
    ("@custom-variant", "tailwind", "directiva CSS que redefine una variante", "@custom-variant", "keep-original", "tailwindcss.md", "API literal."),
    ("@config", "tailwind", "directiva CSS que carga un tailwind.config.js por compatibilidad", "@config", "keep-original", "tailwindcss.md", "API literal."),
    ("@source", "tailwind", "directiva CSS para safelist de clases v4", "@source", "keep-original", "tailwindcss.md", "API literal."),
    ("@layer", "tailwind", "directiva CSS que define una capa en la cascada", "@layer", "keep-original", "tailwindcss.md", "API literal."),
    ("Preflight", "tailwind", "capa base de estilos que Tailwind inyecta", "Preflight", "keep-original", "tailwindcss.md", "Nombre del producto."),
    ("divide-x", "tailwind", "utilidad que aplica bordes entre hijos en horizontal", "divide-x", "keep-original", "tailwindcss.md", "API literal."),
    ("divide-y", "tailwind", "utilidad que aplica bordes entre hijos en vertical", "divide-y", "keep-original", "tailwindcss.md", "API literal."),
    ("ring", "tailwind", "utilidad de outline circular (1px por defecto en v4)", "ring", "keep-original", "tailwindcss.md", "API literal."),
    ("important flag", "tailwind", "config global que hace todas las utilidades importantes", "important flag", "keep-original", "tailwindcss.md", "API literal."),
    ("border-* utilities", "tailwind", "utilidades de border-* con currentColor por defecto", "border-*", "keep-original", "tailwindcss.md", "API literal."),
]


def main() -> int:
    data = json.loads(DECISIONS.read_text(encoding="utf-8"))
    source_path = f"reports/beta/glossary-source/"

    # Si ya hay entries anteriores, respeta la versión; reescribe dict
    new_entries = list(data.get("entries", []))
    existing_terms = {e["source_term"] for e in new_entries}

    inserted = 0
    skipped_duplicated = 0
    for term, domain, sense, preferred, policy, source_file, justification in NEW:
        if term in existing_terms:
            skipped_duplicated += 1
            continue
        entry = {
            "source_term": term,
            "domain": domain,
            "sense": sense,
            "preferred": preferred,
            "preservation_policy": policy,
            "justification": justification,
            "decided_by": "usuario (aprobado el 2026-10-20)",
            "decided_at": "2026-10-20T22:00:00Z",
            "_source": source_path + source_file,
        }
        if policy != "keep-original":
            entry["allowed_variants"] = []
            entry["forbidden_forms"] = []
        new_entries.append(entry)
        existing_terms.add(term)
        inserted += 1

    data["entries"] = new_entries
    data["_fuente"] = (
        f"Curado en 5 pasadas por carpeta desde reports/beta/glossary-source/*.md. "
        f"Aprobado por el usuario el 2026-10-20 con el alcance 'mantener + "
        f"propuesto con un único preferred'. Dudosos y pendientes quedan fuera."
    )
    DECISIONS.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"insertadas: {inserted}, ya estaban: {skipped_duplicated}")
    print(f"total entries: {len(new_entries)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())