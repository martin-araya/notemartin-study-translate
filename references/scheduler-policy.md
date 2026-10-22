<!-- version: 1.0.0 -->

# Política del planificador de paquetes (fase 112)

El planificador de paquetes ordena los `packet_id` de una ejecución
**antes** de entregarlos a workers (fase 113) o al modo serie
(fallback, fase 117). El orden no decide _quién_ traduce, sino
_qué_ se traduce **antes**. Esa diferencia es importante: en
paralelo o en serie, liberar las dependencias en el orden correcto
evita que un paquete referencie un encabezado todavía no traducido
de otro documento, o un término todavía no congelado del glosario.

> La fase 112 mide la **planificación**, no la ejecución. Las
> traducciones reales son trabajo del agente; este documento solo
> decide qué paquete recibe primero.

## 1. Reglas de dependencia

1. **Dependencia de glosario**: si un paquete menciona un término
   presente en `glossary.json` (detectado por reglas simples:
   palabra completa, normalizada a minúsculas, ignorando
   acentuación), ese paquete se considera
   `glossary_dependent`. La planificación no asume que el
   término esté aprobado; solo verifica que exista en el glosario
   congelado. Si falta, se reporta en
   `missing_terms[]`.
2. **Dependencia de anclas**: si un paquete contiene un enlace
   interno `(#anchor)` cuyo destino apunta a otro `document_id`,
   ese paquete depende del paquete del documento de destino. La
   dependencia es por ancla: se conserva la lista de anclas a
   reescribir (fase 039).
3. **Sin dependencia**: el resto. Estos paquetes pueden
   ejecutarse en cualquier orden al final del lote.

## 2. Orden topológico

Se construye un grafo dirigido de dependencias. La salida es la
lista de IDs en orden topológico:

```
A depende de B  →  B antes que A
A depende de B y C  →  B y C antes que A
```

Si el grafo contiene un ciclo, la planificación **falla**: el lote
no se libera. El script `scripts/schedule_packets.py` devuelve
código no cero y vuelca el plan con `cycles` poblado.

## 3. Congelación del glosario

El planificador exige que `glossary.json` esté congelado. El hash
del glosario va en `glossary_hash`. Si la ejecución declara un
`expected_glossary_hash` distinto del actual, el plan se publica
igual pero registra la divergencia.

## 4. Fases del plan

| Fase | Descripción | Orden |
|---|---|---|
| `glossary_dependent` | Paquetes que requieren un término del glosario congelado. | Antes de los demás del mismo `document_id`. |
| `anchor_dependent` | Paquetes cuyo destino de ancla apunta a otro documento. | Orden por `document_id` destino; suborden por aparición. |
| `free` | Resto. | Cualquier orden estable. |

Si un paquete cumple dos fases (p. ej. glosario + ancla), va en
`glossary_dependent`.

## 5. Lo que esta política **NO** hace

- No ejecuta traducción. Eso corresponde a workers o al modo
  serie.
- No reescribe anclas; eso es la fase 039.
- No propone nuevo glosario; eso es el flujo del agente
  (fase 024). Esta política **lee** el congelado.
- No tolera ciclos. Si los hay, el lote no avanza.
