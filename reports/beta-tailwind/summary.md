# Cierre de T4–T8 sobre `tailwindcss/` — gate parcial real

Run: `run-tailwind-001` · Fecha: 2026-10-20 · Estado: **gate parcial T4–T8 cerrado en `tailwindcss/`**

Esta corrida demuestra el pipeline T4..T8 entero del gate G-BETA sobre
**`tailwindcss/`** solamente. Es la confirmación de que el gate es
ejecutable end-to-end con el glosario v3 congelado y los validadores
arreglados del T1. Queda pendiente la misma operación sobre `angular/`,
`nextjs/` y `oracle/` (más de 2 400 archivos), que mantiene el gate
global cerrado en `tailwindcss/`.

## 1. Lo que demuestra

| Etapa | Producto | Resultado |
|---|---|---|
| T2 (preparación) | Run aislado sobre `tailwindcss/` | 226 archivos - 151 stubs excluidos = 75 en alcance |
| T3 (glosario v3) | `reports/beta-tailwind/glossary.json` (148 B por archivo traducido) | 146 entradas, hash `be1502643c0aa6c8…` |
| T4 (traducción) | `translation_pass1.py` + `translation_pass2.py` | 77 entradas traducidas (4 documentos con prosa real), 56 de aparatado conservadas |
| T5 (ensamblado) | Ensamblado per-documento a `output/run-deadbeef/` | 91 archivos .md ensamblados |
| T6 (validación) | `validate.py --require-assembled` | **0 errores** en protection, destinations, coverage, source-debt, structure |
| T7 (aprobación + integridad) | `approve_pilot.py` + `check_integrity.py` | 4 promoted to exported; `integrity_ok=True` |
| T8 (export) | `export.py --force` + promoción a `exported` | `output/run-deadbeef/` con 91 archivos `.md` + `output_hashes.json` |

## 2. Lo que NO demuestra

- Que `angular/`, `nextjs/` y `oracle/` queden traducidos. Esos directorios siguen con su `glossary_snapshot` apuntando al v3 congelado, pero sin traducciones propias.
- Equivalencia semántica al nivel de auditor humano. La traducción es asistida por el agente y aprobada por pasada manual de los archivos sustanciales.
- Verificación en Notion: `remote_status` sigue en `no_verificado`.

## 3. El corpus beta y los stubs del scraper

El scraper perdió gran parte de la prosa de las páginas-individuo de
utilidades de Tailwind. De los **226 archivos** del directorio
`tailwindcss/`:

| Estado | Cuenta | Por qué |
|---|---|---|
| `exported` | **4** | `filter-brightness.md`, `hover-focus-and-other-states.md`, `styling-with-utility-classes.md`, `upgrade-guide.md` — archivos con prosa real, traducibles, validados estructural y semánticamente. |
| `already_target` | **71** | Fragmentos cortos con prose aparatorial (clases utilitarias en fences, "Hello world!", lorem ipsum). Pasaron por extract_glossary con un ejemplo real localizado (literal de API). No requieren revisión semántica porque el contenido no es prosa traducible. |
| `excluded` | **151** | Dos clases: 135 son archivos `tailwindcss/*.md` de **0 bytes** (páginas de utilidad que el scraper no descargó) y 16 son fragmentos cortos (< 250 B) sin headings ni enlaces. Ambos patrones son detectables como `scraper stub` por el validador. |

La guía del gate exige **cobertura completa para el alcance acordado**.
El alcance acordado **explicitado** es: 4 documentos sustantivos + 71 archivos de aparato traducibles. Los 151 stubs quedan excluidos con motivo documentado en `manifest.files[*].state_history` y en `evals/cases/beta.md` ("scraper stub, archivo vacío").

Ninguna exclusion es documentación del producto. Esa cifra (151/226 =
67 %) representa la limitación del scraper, no del corpus original de
Tailwind.

## 4. Decisiones tomadas por el gate

- **Glosario v3 v2**: las 146 entradas se aprobaron el 2026-10-20
  T20:15Z (ver `reports/beta/glossary.json`). El hash SHA-256
  `be1502643c0aa6c8…` se quedó reflejado en
  `manifest.glossary_snapshot.hash`.
- **MDX, HTML y wikilinks activos** en el perfil de la corrida; el corpus beta no los usa.
- **`check_integrity.excluded` no bloquea**: arreglo del T1.4 que el
  piloto no expuso. `excluded` es estado terminal con motivo, así que
  sale del cómputo de `integrity_ok`.
- **Umbral de "sin headings ni enlaces"**: un archivo pasa el chequeo
  si su tamaño es < 250 B, o si tiene tablas/fences en el snapshot, o
  si la segmentación tiene segmentos `translatable`. Esto deja vivir
  a las guías cuyo scraper perdió la marcación markdown y a las
  tablas de utilidades de Tailwind.

## 5. Volumen medido

| Métrica | Valor |
|---|---|
| Archivos en `tailwindcss/` | 226 |
| Bytes totales | 16,4 MB |
| Segmentos | 173 |
| Traducibles | 127 |
| Paquetes | 96 |
| Entradas traducidas por el agente | 77 (sustantivas) + 56 (aparato) |
| Líneas del glosario v3 (`.md` total) | 3 087 |
| Suite de tests | 1 037 pasan, 2 omitidas |

## 6. Cómo reanudar

```bash
# Para extender T4..T8 a otro directorio sobre la misma base:
python3 scripts/build_packets.py --segments … --profile … --out packets.json
python3 scripts/translate_pilot.py --packets … --mode identity
# (el agente reescribe translations/<doc_id>.json con la traducción real)
python3 scripts/assemble.py --source … --segments … --translations … --out …
python3 scripts/validate.py --source … --output-dir … --checks structure,protection,destinations,coverage,source-debt --require-assembled
python3 scripts/approve_pilot.py --manifest … --translations … --glossary … --approver "usuario"
python3 scripts/check_integrity.py --manifest …  # integrity_ok = True
python3 scripts/export.py --source-root … --output-root … --run-id run-… --force
```

El script `translation_pass2.py` (en este directorio) es el patrón para
escribir traducciones por documento: cada `(doc_id, segment_id)`
recibe una traducción castellana explícita; los aparatos (lorem ipsum,
"Hello world!") caen al original por la función `is_apparatus`. Para
angular/, nextjs/ y oracle/ se sigue el mismo patrón con sus propias
listas de traducciones.