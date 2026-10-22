# Caso HTML embebido (fases 071-080)

Estado: **material sintético declarado**. La evidencia está en
`reports/optional/html.json` y en la suite (`tests/test_html_*.py`, 11 ficheros).

Este caso existe para el criterio 1 de G-EXT. Su conclusión es incómoda y por
eso está escrita aquí: **el corpus autorizado no contiene HTML embebido de las
etiquetas que el contrato admite**. Encender el módulo sobre ese corpus sería
activarlo sin motivo, que es justo lo que el roadmap prohíbe para el adaptador
de entrega (`roadmap.md` G-EXT-N).

## 1. Medición sobre los corpus reales autorizados

| Corpus | Ruta | Etiquetas del contrato encontradas |
|---|---|---|
| Piloto | `tests/fixtures/pilot/` (9 archivos) | 0 |
| Beta | `/Users/martin/Desktop/projects/notemartin-beta/source` (2 682 Markdown) | 0 |

Etiquetas buscadas: `details`, `summary`, `a`, `img`, `table`, `thead`, `tbody`,
`tfoot`, `tr`, `th`, `td`, `code`, `kbd`, `br`, `span`.

Resultado: **0 ocurrencias** en ambos. `html_embebido` aparece 0 veces en
`reports/`.

Consecuencia honesta: los perfiles de las dos ejecuciones pasadas
(`reports/pilot/profile.json:27`, `reports/beta/profile.json:30`) activaron
`html.enabled: true` **sin corpus que lo justificara**. No se corrigen esos
archivos porque su hash está anclado en el manifiesto del piloto
(`reports/pilot/manifest.json:24`) y modificarlo invalidaría la aprobación de
G-PILOT. Queda declarado aquí como activación inmotivada, con su evidencia.

## 2. Corpus sintético que sí activa el módulo

| Campo | Valor |
|---|---|
| Ruta | `tests/fixtures/html/` |
| Naturaleza | **sintético**, declarado como tal en `references/html-contract.md` §1 |
| Archivos | 6 |
| Bytes | 2 189 |
| Árbol (prefijo) | `793f57061b193939` |

Cubre `details`/`summary` anidados, tablas con rowspan/colspan, `kbd`, código
inline y HTML dentro de un fence. El caso negativo es
`tests/test_html_gate.py::test_html_fuera_del_contrato_sigue_bloqueando_con_el_modulo_encendido`.

## 3. Estado de la activación

- `html.enabled` es **dormiente por defecto** y, con el perfil 1.1.0, exige
  `corpus_ref` y `justification` para activarse.
- Este caso es el `corpus_ref` declarado: `evals/cases/html.md` con
  `corpus_real: false`. El módulo queda registrado como disponible y probado,
  no como activado sobre material real.

## 4. Qué no afirma este caso

- **No** afirma que el importador de destino conserve el HTML. Esa
  comprobación es de la fase 079 y sigue en `design_only`
  (`references/html-compatibility.md`).
- **No** afirma paridad con HTML5: el contrato §2 es el límite.
- **No** corrige los perfiles históricos, por el motivo expuesto en §1.