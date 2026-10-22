<!-- version: 1.0.0 -->

# Contrato de directivas de documentación (`notemartin-study-translate`)

Este contrato cubre las directivas estilo Sphinx/Numpydoc que
aparecen en bloques de documentación de funciones y clases:

```
:param x: Descripción del parámetro x.
:type x: int
:returns: Descripción del valor devuelto.
:raises ValueError: Cuando el valor es inválido.
:rtype: str
```

## 1. Estado del módulo

- **Activación:** opt-in por perfil (`profile.directives.enabled`).
- Por defecto **desactivado**.
- **Corpus de referencia:** `tests/fixtures/directives/`.

## 2. Lista cerrada de directivas

| Directiva | Argumento | Contenido traducible |
|---|---|---|
| `:param <name>:` | nombre del parámetro (literal) | descripción |
| `:type <name>:` | nombre (literal) | tipo (literal) |
| `:returns:` | — | descripción |
| `:rtype:` | — | tipo (literal) |
| `:raises <Exc>:` | clase de excepción (literal) | descripción |

Cualquier directiva fuera de esta lista se reporta como
`unsupported_directive` con severidad `critical` y bloquea el archivo.

## 3. Reglas

1. El **nombre de la directiva** (`param`, `type`, `returns`, etc.)
   es literal.
2. El **argumento** que sigue al nombre (`x`, `ValueError`, etc.)
   es literal.
3. El **contenido** (descripción o tipo) es traducible salvo en
   `:type:` y `:rtype:` cuyo contenido es **literal** (tipo
   técnico).
4. Las directivas adyacentes no se mezclan.

## 4. Lo que NO se hace

- No se traducen los nombres de directivas ni sus argumentos.
- No se cambia la posición de las directivas dentro del bloque.
- No se añaden directivas nuevas sin actualizar este contrato.