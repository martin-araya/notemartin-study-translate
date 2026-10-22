<!-- version: 1.0.0 -->

# Configuración regional del español (fase 106)

Esta política decide qué variantes del español son válidas en una
ejecución y qué marcas regionales se aplican. Convive con
`references/translation-policy.md` (decisiones de prosa general) y
con `references/operation.md` (política de inferencia). Las marcas
que aparecen aquí son **las únicas** que el par `en → es-XX` puede
modificar; todo lo demás se trata como invariante del núcleo.

> El perfil regional debe auditarse por un nativo. Mientras el
> `manifest.json` no registre `evaluation_kind: human_approved`
> para el par correspondiente, los artefactos cumplen los gates
> deterministas pero **no demuestran equivalencia con el uso
> nativo**.

## 1. Variantes soportadas

| Variante | BCP-47 | Notas distintivas | Estado |
|---|---|---|---|
| Español de España | `es-ES` | « vosotros », leísmos eventuales, vocabulario peninsular | experimental, depende de firma. |
| Español de México | `es-MX` | « usted » generalizado, vocabulario norteño, **sin vosotros** | experimental, depende de firma. |
| Español de Argentina | `es-AR` | voseo, « ustedes », marcadores rioplatenses | experimental, depende de firma. |
| Español neutro | `es` | core; el resto se delega a `references/dialect-profiles.md` | estable (núcleo 0.1.0). |

Otras variantes (`es-CO`, `es-CL`, `es-PE`, `es-VE`, `es-UY`,
`es-419`) requieren fases posteriores.

## 2. Marcadores obligatorios por variante

| Marcador | es-ES | es-MX | es-AR |
|---|---|---|---|
| Tratamiento de « vosotros » | sí | no | no |
| Voseo (tratamiento de « vos ») | no | no | sí |
| « ustedes » para 2.ª plural | sí | sí | sí |
| Artículo ante nombre propio | sí | sí | varía |
| Plural « vosotros » obligatorio | sí | no (sustituir por ustedes) | no |

Las decisiones por variante se aplican en la prosa, no en el código
ni en los identificadores. Los únicos términos que la política
regional cubre de manera cerrada son los coloquialismos enumerados
en §3.

## 3. Coloquialismos (lista cerrada)

El siguiente vocabulario **se conserva tal cual** cuando aparece en
la fuente. Si la política `neutralize_colloquialisms` está activa, se
puede sustituir por un equivalente neutro, pero solo para los
términos listados:

| Término | Variante | Equivalente neutro | Notas |
|---|---|---|---|
| `vosotros` | es-ES | — | Solo en España. |
| `coche` | es-ES | `auto` / `carro` | Latinamérica prefiere « carro » / « auto ». |
| `ordenador` | es-ES | `computadora` / `computador` | Latinamérica usa « computadora ». |
| `vale` | es-ES | `de acuerdo` | Latinamérica no lo usa así. |
| `chido` | es-MX | `genial` | Uso coloquial. |
| `carnal` | es-MX | `amigo` / `compa` | Solo en registro informal. |
| `chela` | es-MX | `cerveza` | Caló. |
| `changarro` | es-MX | `tienda` / `negocio` | Útil solo en contexto de negocio. |
| `che` | es-AR | `oye` / `mira` | Interjección. |
| `boludo` / `boluda` | es-AR | — | **No traducir ni neutralizar por defecto**; carga semántica regional. |
| `pibe` / `piba` | es-AR | `chico` / `chica` | Connotación regional. |
| `re` (intensificador) | es-AR | `muy` | Es adverbio informal en rioplatense. |
| `afanar` | es-AR | `robar` / `hurtar` | Contexto informal. |
| `guay` | es-ES | `genial` | Coloquialismo peninsular. |
| `chaval` / `chavala` | es-ES | `chico` / `chica` | Registro coloquial. |
| `cacharro` | es-ES | `trasto` / `cosa` | Dispositivo cualquiera. |
| `botar` (lanzar) | es-AR / es-MX | — | Connotación opuesta a `botar` en otras latitudes. |

Términos no enumerados se traducen según el glosario general. La
lista **no** se amplía sin un test que justifique la entrada.

## 4. Lo que NO se localiza regionalmente

| Categoría | Política | Razón |
|---|---|---|
| API, nombres de funciones, clases, paquetes | preservar | `INV-05`. |
| Mensajes de error literales | preservar | Deben buscarse literalmente. |
| Comandos, flags, rutas | preservar | El lector los teclea como están. |
| Identificadores técnicos | preservar | Compatibilidad con código. |
| Fechas, horas, números, unidades | preservar | `AGENTS.md` §5.3. |
| URLs, paths | preservar | El destino no cambia. |
| Firmas, marcas, nombres propios | preservar salvo glosario | Visibilidad contractual. |
| SPDX, copyright, condiciones | preservar | `references/citations-policy.md` (fase 105). |

## 5. Política de procedimiento

1. Una ejecución declara **una y solo una** variante en
   `profile.locale.variant`.
2. Si `profile.locale.variant` se omite, la salida se trata como
   `es` neutro y se aplican las reglas del núcleo 0.1.0.
3. Cambiar la variante entre dos ejecuciones del mismo archivo
   invalida automáticamente la caché previa. Ver
   `scripts/check_cache_isolation.py` (fase 107).
4. La rúbrica `evals/rubric.md` mide el cumplimiento de §3.
5. Mezclar más de una variante en la **misma ejecución** es un
   error de configuración; `scripts/eval_regional.py` lo rechaza.

## 6. Limitaciones

- La lista de coloquialismos es **cerrada**; ampliarla exige
  revisión humana y un test que falle primero.
- Esta política **no** modifica cómo el navegador o Notion
  muestran la prosa; es decir, el render del importador puede
  añadir CSS propio que ignore las marcas regionales.
- Cobertura insuficiente de corpus regional: el piloto usa MDN
  es-ES real y corpus derivado CC0 para es-MX y es-AR. La
  sustitución se cierra cuando se incorporen corpus nativos
  auditados con firma humana.

## 7. Relación con el lote 101–105

- Las fases 102 y 105 son invariantes: la fuente francesa conserva
  sus modismos aunque se traduzca a es-MX; las citas contractuales
  siguen siendo contractuales.
- La fase 104 (perfil multilingüe) no se mezcla con esta política.
  Aquí solo cambia el **destino** del español; la fuente sigue
  siendo un único idioma declarado en el perfil.
