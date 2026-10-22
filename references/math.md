<!-- version: 1.1.0 -->

# Contrato de Math (`notemartin-study-translate`)

Este contrato cubre cómo se traduce el contenido en presencia de
expresiones matemáticas LaTeX. LaTeX **no** se traduce ni se valida.
La prosa entre expresiones sí es traducible.

## 1. Estado del módulo

- **Activación:** sin interruptor propio. El núcleo detecta los límites de
  bloque y de línea y preserva LaTeX literal.
- **Contradicción declarada:** `scripts/dialect_matrix.py` lista `math`
  entre lo que el perfil `commonmark-basic` no soporta, mientras este
  documento decía que la matemática estaba «siempre activa». Ambas
  describen la misma realidad desde distinto sitio: la construcción se
  detecta y se preserva, pero no se traduce. Declarado así, sin
  contradicción.
- **Sin render real.** El parser no compila ni renderiza LaTeX.
  Solo detecta límites de bloque y línea.

## 2. Reglas

1. **Display math** `$$...$$` es **literal**. No se traduce.
2. **Inline math** `$...$` es **literal**. No se traduce.
3. La **prosa** entre expresiones (párrafos, listas, citas) sí se
   traduce.
4. Los **entornos** `\begin{aligned} ... \end{aligned}` dentro
   de `$$...$$` permanecen literales.
5. Los caracteres `$` fuera de estas construcciones se tratan como
   prosa normal.

## 3. Lo que NO se hace

- No se valida sintaxis LaTeX.
- No se renombran comandos LaTeX.
- No se traducen los entornos ni las ecuaciones.

## 4. Procedimiento para añadir un patrón

1. Aportar corpus en `tests/fixtures/math/`.
2. Si el patrón excede este contrato, dividir en código LaTeX
   (literal) y prosa explicativa (traducible).
3. Actualizar `manifest.json` con `policy_decisions` si cambia la
   política.