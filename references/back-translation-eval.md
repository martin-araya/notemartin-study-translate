<!-- version: 1.0.0 -->

# Retrotraducción como señal (fase 127)

La retrotraducción se evalúa **solo** como una señal auxiliar.
Su valor real está en medir dónde falla — falsos positivos y
negativos — sobre casos conocidos, **no** en decidir aprobaciones.

## 1. Modos

- `dry-run` (por defecto): aplica un comparador local,
  determinista y reproducible, sobre `tests/fixtures/back_translation/`.
- `live` (sólo fuera de CI): invoca al agente disponible para
  retrotraducir. Exige `NOTE_BACK_TRANSLATION_LIVE=1` en el
  entorno. Nunca se ejecuta accidentalmente durante CI.

## 2. Fixtures

Cada fixture es un objeto JSON con:

- `case_id`: identificador estable.
- `source_text`: original en idioma origen.
- `translated_text`: candidato en español.
- `expected_outcome`: `agree_match`, `agree_diverging`, o
  `comp_should_disagree`.
- `expected_should_be_caught`: `true` si es un caso que expone
  un fallo conocido del comparador (falso positivo o negativo).
- `category`: `equivalent`, `false_positive`, `false_negative`,
  `true_match`.
- `notes`: contexto opcional.

Las fixtures cubren, como mínimo:

1. equivalencia semántica esperada (acierto real).
2. cognados falsos positivos (`application`, `state`).
3. negación perdida (falso negativo).
4. cuantificador preservado (acierto).
5. causalidad invertida (falso negativo).

## 3. Métricas

El script vuelca `reports/back_translation.json` con:

- `total`: número total de casos.
- `true_match`: casos cuyo veredicto del comparador coincide con
  el resultado esperado.
- `false_positives`: casos donde el comparador dijo `match` sobre
  una diferencia semántica real.
- `false_negatives`: casos donde el comparador dijo `diverging`
  sobre una equivalencia semántica real.
- `details`: una entrada por caso con su veredicto, su
  retrotraducción de muestra y la categoría.

## 4. Lo que NO hace

- **No demuestra equivalencia semántica**: una métrica favorable
  no acredita la calidad global de la traducción. Solo expone los
  límites del comparador.
- **No influye en el gate** directamente (fase 130): sólo emite
  métricas y, si el umbral cae, el gate falla.
- **No publica los textos** al comparar: la salida trunca a 120
  caracteres.

## 5. Política de privacidad

- En modo `live`, el texto completo del candidato se envía al
  proveedor del agente. Esto exige confirmación del proveedor
  autorizado (AGENTS.md §4).
- En modo `dry-run`, no se invoca ningún servicio externo.

## 6. Relación con otras fases

| Fase | Relación |
|---|---|
| 044 | Las decisiones humanas registradas aquí alimentan `decisions[]`. |
| 121 | El reporte bilingüe sigue siendo la entrada principal de revisión. |
| 130 | El gate ampliado exige métricas dentro de tolerancia configurable. |
