<!-- version: 1.0.0 -->

# Política de texto bidireccional RTL (fase 108)

Esta política decide cómo la skill `notemartin-study-translate`
procesa texto con caracteres de derecha a izquierda (RTL). Convive
con `references/locale-policy.md` (variante del español de destino)
y con `references/operation.md` (política de inferencia). Lo que
esta política **no** modifica es responsabilidad del importador
(Notion, navegador, etc.).

> La fase 108 mide el soporte, **no** el render. No se afirma
> que la salida se vea igual en todos los destinos. La verificación
> se hace por preservación **byte-a-byte** del texto origen y por
> registro de la dirección por segmento.

## 1. Detección por carácter

| Bloque Unicode | Idioma(s) habitual(es) | Dirección |
|---|---|---|
| `U+0590..U+05FF` | Hebreo, yidis | RTL |
| `U+0600..U+06FF` | Árabe, farsi, urdu | RTL |
| `U+0700..U+074F` | Siríaco | RTL |
| `U+0750..U+077F` | Árabe suplementario | RTL |
| `U+0780..U+07BF` | Thaana (divehi) | RTL |
| `U+07C0..U+07FF` | NKo | RTL |
| `U+0800..U+083F` | Samaritano | RTL |
| `U+0840..U+085F` | Mandaico | RTL |
| `U+FB50..U+FDFF`, `U+FE70..U+FEFF` | Presentaciones árabes | RTL |
| `U+200F` | RLM (right-to-left mark) | marca |
| `U+200E` | LRM (left-to-right mark) | marca |

El algoritmo de detección cuenta cuántos caracteres de cada bloque
Unicode aparecen en el `translatable_text` de un segmento y asigna
una `text_direction` ∈ {`ltr`, `rtl`, `mixed`}.

## 2. Reglas de preservación

- **Orden lógico**: la secuencia Unicode del `translatable_text` se
  conserva tal cual. La traducción no reordena caracteres.
- **Bytes**: cada `byte_range` cubre exactamente los bytes de la
  fuente; no se inserta ni se quita nada entre medio sin un marcador
  de protección explícito.
- **Pares de control bidi**: si la fuente contiene RLM/LRM, se
  conservan. Si el destino requiere añadir, eso se documenta como
  `bidi_control_added: true` en el segmento; por defecto la
  política NO añade controles (`add_bidi_controls: false`).

## 3. Numerales

| Sistema | Bloque Unicode | Comportamiento |
|---|---|---|
| ASCII | `0`-`9`, `U+0030..U+0039` | Se conservan. |
| Árabe-índico | `٠`-`٩`, `U+0660..U+0669` | Se conservan. |
| Árabe-oriental | `۰`-`۹`, `U+06F0..U+06F9` | Se conservan. |

La política `rtl.preserve_digits` es `true` por defecto: **no se
localizan** los numerales. Si un corredor pide localización
(`preserve_digits: false`), esa ejecución queda bloqueada por
incompatibilidad con AGENTS.md §5.3. Esta política **no** debe
utilizarse.

## 4. Lo que NO se modifica

- Caracteres: cualquier carácter Unicode presente en la fuente
  permanece idéntico.
- Orden de bytes: el ensamblado produce los mismos bytes que la
  fuente para el contenido del rango traducible, salvo la
  sustitución del `translatable_text` por la traducción.
- Glifos: esta política **no** aplica glifos ni ligaduras. El
  render es responsabilidad del destino.

## 5. Mezcla LTR/RTL

Es habitual encontrar párrafos con segmentos predominantemente LTR
y frases en RTL insertadas, o viceversa. Para cada segmento:

- Si todos los caracteres no-espacio son RTL → `text_direction: rtl`.
- Si todos son LTR → `text_direction: ltr`.
- Si ambos aparecen → `text_direction: mixed`.

Esta clasificación vive en el campo `segment.text_direction` del
esquema. No afecta al contenido, solo al reporte.

## 6. Procedimiento por fase

1. `prepare.py` extrae rangos.
2. `scripts/detect_text_direction.py` (fase 108, interno) clasifica
   cada segmento en `ltr`, `rtl` o `mixed`.
3. La traducción se hace preservando orden Unicode.
4. El ensamblador vuelve a montar el documento comprobando que los
   segmentos RTL no han sido alterados más allá del rango declarado.
5. `scripts/eval_rtl.py` vuelca los artefactos con métricas y
   disclaimers de render.

## 7. Riesgos y limitaciones

- **Render no comprobado**: el aspecto real depende del importador
  y del navegador. Si Notion renderiza mal la mezcla, ese no es
  falla de esta política.
- **Comparación de longitud**: las palabras RTL ocupan menos
  espacio en una cuenta glifo-a-glifo que en bytes; los reportes
  usan bytes, no glifos.
- **Selección**: en contextos como « (مرحبا) » con texto LTR fuera
  y RTL dentro, el clasificador devuelve `mixed`. El caso sigue
  siendo traducible segmento a segmento.

## 8. Lo que NO hace

- No renderiza.
- No convierte texto RTL a LTR.
- No añade RLM/LRM sin opción explícita del perfil.
- No reordena la salida.
- No localiza numerales.
