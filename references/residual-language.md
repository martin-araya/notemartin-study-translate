<!-- version: 1.0.0 -->

# Detector de idioma residual

> Regla canónica registrada en `references/rule-registry.json`.

## Qué detecta y qué no

`scripts/detect_residual_language.py` **solo señala**. Ninguna de sus
salidas es evidencia de que un segmento esté mal traducido: es una lista
para que la revisión semántica la confirme o la descarte.

## Evidencia a favor, no solo ausencia de evidencia en contra

La primera versión informaba de cualquier run de palabras que no fueran
funcionales españolas. Sobre el piloto autorizó 273 avisos que eran prosa
española corriente («tipo», «nodos, conexiones»), y su salida hubo que
descartarse como evidencia en `reports/pilot/summary.md` §5.2.

Ahora una run solo se informa si tiene **evidencia a favor**:

| Evidencia | Ejemplo |
|---|---|
| Palabra funcional inglesa | `the`, `and`, `of`, `is` |
| Terminación inglesa | `-tion`, `-ing`, `-ed`, `-ness`, `-ity` |
| Forma de identificador | `snake_case`, `kebab-case`, `CamelCase` |
| Lista cerrada de términos técnicos | `settings`, `templates`, `workers` |

La lista cerrada vive en el script (`DECLARED_ENGLISH_WORDS`) y es
revisable. No es un diccionario y no pretende serlo.

## Quedan exentos

- Contenido dentro de code fences y de código inline.
- Términos del glosario con `preservation_policy: keep-original`.
- Runs con marcadores en contra: acentos españoles o sufijos españoles en
  todas sus palabras.

## Severidad

`warning` a partir de 4 palabras consecutivas; `info` con menos.

## Límite declarado

Una frase inglesa corta sin palabras funcionales y sin terminación
inglesa se escapa del detector. Es un fallo aceptado: preferimos dejar
pasar un residuo raro a inundar el informe, porque el filtro humano de la
revisión semántica es el que decide. (fase 126)

`scripts/detect_residual_language.py` produce dos artefactos:

- `reports/residual_language.json` con la lista exacta de
  señales.
- `reports/residual_language.md` con un resumen legible.

Es una **alerta auxiliar**: nunca modifica `translations/` y no
demuestra equivalencia semántica, en línea con AGENTS.md §2 y la
fase 044.

## 1. Lo que marca

| Severidad | Criterio |
|---|---|
| `warning` | Cuatro o más palabras consecutivas de aspecto inglés. |
| `info` | Una a tres palabras consecutivas de aspecto inglés. |

Una palabra se considera "de aspecto inglés" si no está en la
lista de stopwords españolas, no tiene acentos españoles y
carece de sufijos típicamente españoles.

## 2. Exenciones (no se marcan)

- **Literales protegidos**: code fences ```…```, code inline
  `…`, y cualquier span entre backticks.
- **Términos del glosario con `preservation_policy: preserve`**:
  tanto su forma original como la `preferred.term` se excluyen.
- **Cadenas vacías**: 0 bytes.

## 3. Lo que NO hace

- **No modifica `translations/`** ni aplica correcciones.
- **No propone traducciones nuevas** para los segmentos
  afectados: emite una alerta y el revisor decide.
- **No acumula histórico**: cada ejecución escribe un nuevo
  archivo. No existe un seguimiento de incidencias
  automáticamente.
- **No compara embeddings ni modelos**: es una heurística
  basada en reglas, sin incorporación de dependencias externas.

## 4. Falsos positivos esperados

La heurística es deliberadamente blanda. Cualquier run ASCII sin
sufijos españoles marcados dispara `info`. La revisión semántica
o el rechazo humano eliminan los falsos positivos. Para
reducirlos:

- Mantener el glosario con `preservation_policy: preserve`
  para los términos que la fuente conserva en inglés
  deliberadamente (CSS, HTML, JSON, npm, etc.).
- Marcar las decisiones de bloqueo en `references/decision-protocol.md`.

## 5. Relación con otras fases

| Fase | Relación |
|---|---|
| 121 | El informe bilingüe muestra el texto íntegro; este detector lo complementa con alertas. |
| 124 | Si una alerta recurrente invalida aprobaciones, se re-firma con un nuevo `target_hash`. |
| 130 | El gate ampliado falla si hay `warning` sin decisión humana asociada. |
