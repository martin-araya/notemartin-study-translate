# Rúbrica de fidelidad y criticidad

Esta rúbrica guía la revisión semántica separada del paso 6 del flujo operativo. Distingue dos niveles de severidad:

- **Crítico**: bloquea la aprobación del archivo. Cambia el significado obligatorio de una instrucción, invierte una negación, convierte una obligación en recomendación, omite un elemento numerado o rompe un rango cuantitativo.
- **Mayor**: debe corregirse antes de la exportación. Cambia fuerza normativa sin invertir obligación, suaviza una condición, pierde un cuantificador total o equivoca una causalidad simple.

Los hallazgos `menores` no se registran como tales: saturan la revisión sin ayudar al gate. Si un hallazgo no es crítico ni mayor, no se eleva.

## 1. Dimensiones evaluadas

1. Negación
2. Modalidad
3. Condiciones
4. Omisiones
5. Causalidad
7. Sujetos
8. Versiones y rangos
9. Referencias cruzadas
10. Numeración cerrada

## 2. Definiciones operativas

| Dimensión | Marcadores en inglés | Marcadores en español |
|---|---|---|
| Negación | `not`, `no`, `never`, `without`, `must not`, `don't`, `nope` | `no`, `nunca`, `sin`, `jamás` |
| Modalidad | `MUST`, `MUST NOT`, `REQUIRED`, `SHALL`, `SHOULD`, `MAY` | `debe`, `no debe`, `obligatorio`, `recomendado`, `opcional` |
| Condiciones | `if`, `unless`, `when`, `provided that`, `as long as` | `si`, `a menos que`, `cuando`, `siempre que`, `con tal de que` |
| Omisiones | truncamientos, `etc.`, `and so on`, `among others` | `etc.`, `entre otros`, `varios`, `diversos` |
| Causalidad | `because`, `causes`, `results in`, `leads to` | `porque`, `provoca`, `da lugar a`, `debido a` |
| Cuantificadores | `all`, `every`, `each`, `some`, `any`, `none` | `todos`, `cada`, `ninguno`, `alguno`, `ningún` |
| Sujetos | agente de la acción, pasivas, impersonales | agente de la acción, pasivas, impersonales |
| Versiones | `>=2.1`, `<3`, `1.x`, `since v2` | `>=2.1`, `<3`, `1.x`, `a partir de la 2.1` |
| Referencias | enlaces, anclas, identificadores cruzados | enlaces, anclas, identificadores cruzados |
| Numeración | pasos numerados, viñetas cerradas | pasos numerados, viñetas cerradas |

## 3. Ejemplos evaluables

Cada ejemplo declara su severidad y la regla violada o preservada.

### 3.1 Negación

- **Original.** "Do not delete the database before backing it up."
- **Aceptable.** "No elimine la base de datos antes de hacer una copia de seguridad."
- **Crítico.** "Elimine la base de datos antes de hacer una copia de seguridad."
  - Regla violada: la negación `not` desaparece. Severidad: crítico.
- **Mayor.** "No debería eliminar la base de datos antes de hacer una copia de seguridad."
  - Regla violada: la obligación `do not` se convierte en recomendación `no debería`. Severidad: mayor.

### 3.2 Modalidad

- **Original.** "You MUST call `commit()` before exiting."
- **Aceptable.** "Debe llamar a `commit()` antes de salir."
- **Crítico.** "Puede llamar a `commit()` antes de salir."
  - Regla violada: `MUST` se convierte en `puede` (permiso). Severidad: crítico.
- **Crítico.** "You SHOULD call `commit()` before exiting." → "Debe llamar a `commit()` antes de salir."
  - Regla violada: `SHOULD` se convierte en `debe` (obligación). Severidad: crítico.

### 3.3 Condiciones

- **Original.** "The cache is invalidated when the token expires."
- **Aceptable.** "La caché se invalida cuando el token expira."
- **Crítico.** "La caché se invalida si el token no expira."
  - Regla violada: la condición se invierte. Severidad: crítico.
- **Mayor.** "La caché puede invalidarse cuando el token expira."
  - Regla violada: la condición se convierte en posibilidad sin cambiar el verbo principal. Severidad: mayor.

### 3.4 Omisiones

- **Original.** "The list contains `a`, `b`, `c`, and `d`."
- **Aceptable.** "La lista contiene `a`, `b`, `c` y `d`."
- **Crítico.** "La lista contiene `a`, `b`, etc."
  - Regla: enumeración cerrada `a, b, c, d` se trunca a `a, b, etc.`. Severidad: crítico.
- **Crítico.** "La lista contiene varios elementos."
  - Regla: enumeración cerrada reemplazada por cuantificador vago. Severidad: crítico.

### 3.5 Causalidad

- **Original.** "The query fails because the index is missing."
- **Aceptable.** "La consulta falla porque falta el índice."
- **Crítico.** "La consulta falla aunque el índice esté presente."
  - Regla: la causalidad se invierte con `because → although`. Severidad: crítico.
- **Mayor.** "La consulta falla; el índice falta."
  - Regla: causalidad sustituida por yuxtaposición sin nexo. Severidad: mayor.

### 3.6 Cuantificadores

- **Original.** "All requests require authentication."
- **Aceptable.** "Todas las solicitudes requieren autenticación."
- **Crítico.** "Algunas solicitudes requieren autenticación."
  - Regla: `all → some` cambia el alcance. Severidad: crítico.
- **Crítico.** "Ninguna solicitud requiere autenticación."
  - Regla: `all → none` invierte el alcance. Severidad: crítico.

### 3.7 Sujetos

- **Original.** "The server returns the token to the client."
- **Aceptable.** "El servidor devuelve el token al cliente."
- **Crítico.** "El cliente devuelve el token al servidor."
  - Regla: sujeto y objeto se intercambian. Severidad: crítico.
- **Mayor.** "Se devuelve el token al cliente."
  - Regla: el sujeto se vuelve impersonal sin conservar el actor. Severidad: mayor.

### 3.8 Versiones y rangos

- **Original.** "This API is stable since v2.1 and not available before v3.0."
- **Aceptable.** "Esta API es estable a partir de la 2.1 y no está disponible antes de la 3.0."
- **Crítico.** "Esta API es estable a partir de la 3.0 y no está disponible antes de la 2.1."
  - Regla: los rangos inferior y superior se intercambian. Severidad: crítico.
- **Crítico.** "Esta API es estable desde la versión 3.0."
  - Regla: `since v2.1 → desde la 3.0` cambia el rango mínimo. Severidad: crítico.

### 3.9 Referencias cruzadas

- **Original.** "See the [Authentication](#authentication) section for details."
- **Aceptable.** "Consulte la sección [Autenticación](#autenticación) para más detalles."
- **Mayor.** "Consulte la sección Autenticación para más detalles."
  - Regla: el enlace con fragmento local desaparece. Severidad: mayor (porque la navegación se rompe aunque el texto conserve el sentido).
- **Crítico.** "Consulte la sección [Autenticación](#autenticacion) para más detalles."
  - Regla: el fragmento local pierde la tilde tras la traducción. Severidad: crítico (porque la navegación queda inválida aunque la prosa sea fiel).

### 3.10 Numeración cerrada

- **Original.** "Follow these three steps: 1. Configure, 2. Build, 3. Deploy."
- **Aceptable.** "Siga estos tres pasos: 1. configurar, 2. compilar, 3. implementar."
- **Crítico.** "Siga estos pasos: 1. configurar, 2. compilar."
  - Regla: enumeración cerrada de tres se trunca a dos. Severidad: crítico.
- **Crítico.** "Siga estos cuatro pasos: 1. configurar, 2. compilar, 3. implementar."
  - Regla: el conteo declarado cambia de tres a cuatro. Severidad: crítico.

## 4. Aplicación

La rúbrica se aplica por inspección directa sobre cada segmento traducible. Cada hallazgo registra:

- Archivo.
- `segment_id` o rango.
- Dimensión (sección 1).
- Severidad (crítico o mayor).
- Original.
- Candidato.
- Regla violada (sección 3).
- Resolución.

La fase de corrección modifica únicamente los segmentos con hallazgos críticos o mayores y vuelve a aplicar la rúbrica sobre ellos antes de promover la aprobación.