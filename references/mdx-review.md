<!-- version: 1.0.0 -->

# Revisión semántica de la extensión MDX (fase 069)

Este documento extiende `evals/rubric.md` con reglas específicas
para segmentos MDX. La auditoría semántica se ejecuta sobre los
segmentos que `scripts/mdx_selector.py` produce.

## 1. Reglas por componente

### 1.1 `<Info>`

- **Modalidad preservada.** Una frase "MUST NOT" debe seguir siendo
  prohibición en español, no recomendación. Verbos como "puedes",
  "es recomendable" rebajan la fuerza normativa.
- **No añadir explicaciones pedagógicas.** "Info" es admonition
  neutra; no se transforma en nota de estudio.
- **Identidad sospechosa.** `translated_text == original_text`
  cuando el segmento es traducible produce issue `ambiguous` con
  severidad `info`.

### 1.2 `<Note>`

- **Compatibilidad técnica.** Frases como "requires version X or
  later" deben mantener la condición explícita. Quitar la
  condición cambia el significado técnico.

### 1.3 `<Warning>`

- **Negación obligatoria.** "MUST NOT delete" no puede traducirse
  como "delete". La negación es parte de la fuerza normativa.
- **Severidad.** El atributo `severity` (literal) preserva el nivel
  de urgencia. La traducción no debe añadir rebajas ni alarmas
  nuevas.

### 1.4 `<TabItem>`

- **Identificador `value` literal.** Ver `references/mdx-contract.md`
  sección 5.
- **`label` traducible.** Conserva la palabra o frase corta que el
  lector ve en la pestaña.

### 1.5 `<Card>`, `<CardGroup>`

- **Lista compacta.** El contenido de un `<Card>` es texto plano;
  mantenerlo conciso. No expandir.

## 2. Hallazgos generados

| Tipo | Severidad | Origen |
|---|---|---|
| `clarification_needed` | major | negación invertida en `<Warning>` |
| `ambiguous` | info | traducción idéntica al original |
| `flag_loss` | critical | literales protegidos desaparecidos |
| `unsupported_component` | critical | componente fuera del contrato |

Los segmentos cuyo `kind` es `expression` o `jsx_element` se
ignoran en la auditoría semántica: el traductor no debe tocar
literales ni atributos funcionales.

## 3. Procedimiento

1. Construir el catálogo de segmentos con `scripts/mdx_selector.py`.
2. Cargar las traducciones de `translations/<doc_id>.json` o del
   paquete de revisión.
3. Comparar `original_text` y `translated_text` por segmento.
4. Emitir hallazgos en `reports/issues.json` con `category`,
   `severity`, `path`, `segment_id`, `parent` (componente MDX).
5. Aplicar el gate global: si hay `critical`, el archivo no pasa a
   `approved`.