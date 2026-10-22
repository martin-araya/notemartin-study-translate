# Caso beta (fase 050, gate G-BETA)

Estado: **autorizado** por el usuario el 2026-10-20 tras el cierre de
`G-BETA` como fase. Criterio de selección, exclusiones y recursos
aprobados en la misma tanda. Evidencia de la ejecución en
`reports/beta/`.

Este caso **no sustituye** a `evals/cases/pilot.md`: el piloto sigue siendo
la muestra de 9 documentos con constructions representativas y su
evidencia no se toca. La beta amplía el alcance a los tres directorios
que el piloto excluyó por tamaño más la rebanada de Oracle, y es la que
sostiene el gate G-BETA.

## 1. Origen autorizado

| Campo | Valor |
|---|---|
| Corpus de origen | `/Users/martin/Desktop/documentacion` (solo lectura) |
| `source_root` de la corrida | `/Users/martin/Desktop/projects/notemartin-beta/source` |
| Copia inmutable | sí, con `cp` byte a byte. La fuente nunca se modifica (INV-01) |
| Fecha de copia | 2026-10-20 |
| Documentos Markdown | 2 682 |
| Bytes totales | 61 055 709 |
| Recursos locales | 66 archivos, 45,35 MB |

La suma de bytes se recalculó el 2026-10-21 contra los archivos reales:
la tabla por directorio de §1.1 y sus cuatro hashes de árbol coinciden,
y el total correcto es 61 055 709. La cifra anterior, 61 075 709, era
un error de suma en este documento; el árbol de la fuente nunca cambió,
como confirma el hash `283c5a07…`.

### 1.1.Hash de árbol por directorio

El hash de árbol es el SHA-256 de la concatenación ordenada de
`<ruta relativa> <sha256 del archivo>\n` para todos los archivos del
directorio. Es determinista y se recalcula con un script, no a mano:

```bash
python3 - <<'PY'
import hashlib, sys
from pathlib import Path
dst = Path("/Users/martin/Desktop/projects/notemartin-beta/source")
root = Path(sys.argv[1] if len(sys.argv) > 1 else dst)
h = hashlib.sha256()
for p in sorted(x for x in root.rglob("*") if x.is_file()):
    h.update(f"{p.relative_to(dst).as_posix()} {hashlib.sha256(p.read_bytes()).hexdigest()}\n".encode())
print(h.hexdigest())
PY
```

| Directorio | Archivos | Bytes | SHA-256 de árbol |
|---|---|---|---|
| `angular/` | 1 531 | 6 444 212 | `454e2e2cf7c7a954dfe186b401f751e7fe70787f3799ac171bd456138840d012` |
| `nextjs/` | 908 | 7 278 946 | `c4dbd30859173a133b388665b0c8269b906bac39d8247bee376747a1f6cbec18` |
| `tailwindcss/` | 226 | 51 062 | `48a792be4fb1b019f96a8416d0fed9291417dc1fb1db6c39fb90bb73edc3ee3e` |
| `oracle/` | 83 | 47 281 489 | `23110f91e44af7a26423df2defec17239e6ed9a6b7b42675ad3c8744f9f67027` |
| **total** | **2 748** | **61 055 709** | `283c5a073dc8fe01127abb6e884d59546284827a879d66585c12492c338f8214` |

Los hashes por archivo quedan en `work/<run_id>/inventory.json`. Este
documento no los lista uno a uno: son 2 748 líneas que se consultan en el
inventario, que es donde deben estar.

## 2. Alcance y exclusiones

| Ruta | Motivo de exclusión | Aprobado por |
|---|---|---|
| `crawl.log`, `crawl.ndjson`, `summary.json` (3 directorios) | Telemetría del scraper, no documentación | usuario |
| `plan.md`, `summary.md` (3 directorios) | Artefactos de planificación del scraper, no documentación | usuario |
| `.DS_Store` (25 archivos) | Basura del sistema de archivos | usuario |
| `angular.zip`, `nextjs.zip`, PDFs de `oracle/` | Fuera del alcance de la beta: el scraper no los produce como Markdown | usuario |
| `tailwindcss/*.md` con tamaño 0 | El scraper perdió la prosa de las páginas de referencia de cada utilidad (cada archivo es la página individual de una clase Tailwind, `accent-color.md`, `align-content.md`, etc.). 175 archivos de las 226 en `tailwindcss/` están vacíos. Representan fragmentos de documentación que el scraper no descargó; no aportan prosa traducible | usuario |

Ninguna exclusión es documentación del producto. Aun así, una exclusión
no cuenta como traducción: se declara aquí y en el informe final con su
motivo y su aprobador, y nunca se reduce el denominador para mejorar una
métrica.

## 3. Qué ejercita cada directorio

| Directorio | Lo que aporta a la beta |
|---|---|
| `angular/` | Referencia de API extensa (1 143 páginas), guías, errores, tutoriales, `ecosystem`. Tablas de parámetros con valores por defecto: el lugar donde se concentran las regresiones de cifras y unidades. |
| `nextjs/` | Rutas por versión (`15/`, `app/`, `pages/`, `messages/`). `messages/*.md` son guías de error en inglés, no catálogos i18n. Encabezados que se autolinkean: `## Título[](#slug) <a id="slug"></a>`. Rutas escapadas: `pages/\_app.js`. |
| `tailwindcss/` | Referencia corta y muy densa en tablas de utilidades. Aporta `custom property`, que quedó fuera del glosario del piloto por no tener ejemplo real. |
| `oracle/resúmenes/` | **Recursos locales reales**: 66 imágenes (45 MB) referenciadas con rutas relativas. Es lo que permite cerrar la casilla de recursos del gate. El texto ya está en español: sale como `already_target` y se verifica, no se reescribe. |

## 4. Deuda del origen que se hereda sin reparar

Los resúmenes de Oracle apuntan a sus imágenes con
`resúmenes/assets/...` desde archivos que ya están dentro de
`resúmenes/`, así que la ruta no resuelve desde el propio documento.
Es deuda del scraper, no un defecto de traducción: se registra como
`source_debt_missing_target` y **no se repara**. Reparar rutas del
scraper está fuera del alcance de esta skill.

Las imágenes de `angular/`, `nextjs/` y `tailwindcss/` son rutas
absolutas del sitio (`/docs/user-guide/editor.png`). No se pueden
comprobar contra el corpus y no son deuda: se declaran como
`source_debt_external`.

## 5. Construcciones que el alcance contiene

| Construcción | Dónde | Nota |
|---|---|---|
| Encabezados ATX | los cuatro directorios | |
| `<a id="...">` explícito | `nextjs/messages/`, `angular/`, `tailwindcss/` | El scraper lo emite en casi todos los encabezados: por eso la reescritura de fragmentos **no debe dispararse** en ellos (INV-09) |
| Encabezado que se autolinkea | `nextjs/messages/app-container-deprecated.md:5` | `## Título[](#slug) <a id="slug"></a>` |
| Enlaces con fragmento local | `nextjs/messages/app-container-deprecated.md:5` | |
| Rutas absolutas del sitio | los tres directorios | imágenes y enlaces `/docs/...` |
| Tablas GFM | `angular/api/`, `tailwindcss/` | columnas y alineación |
| Bloques de código | los cuatro | `text`, `html`, `css`, `tsx`, `ts`, `bash`, `yaml`, `mermaid`, `sql` |
| Mermaid en fence | según detección | se conserva literal |
| YAML escapado | `nextjs/messages/` | `pages/\_app.js` |
| Frontmatter YAML | según detección | se preserva literal |
| Recursos locales | `oracle/resumenes/assets/` | 66 archivos |
| Prosa ya en español | `oracle/resumenes/` | `already_target` |

## 6. Lo que este caso NO afirma

- No afirma que el corpus completo de 4 832 archivos esté cubierto: el
  alcance son tres directorios más una rebanada de Oracle.
- No afirma equivalencia semántica: la revisión es asistida por agente.
- No afirma verificación remota en Notion: `remote_status` queda en
  `no_verificado`.
- No afirma que los módulos opt-in 061–150 estén probados por este caso.