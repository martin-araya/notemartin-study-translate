<!-- version: 1.1.0 -->

# Contrato del adaptador Mermaid opcional (`notemartin-study-translate`)

Este contrato cubre el modo **opt-in** para traducir etiquetas
visibles de diagramas Mermaid. En el **modo núcleo**, Mermaid
siempre se preserva literal (fase 030).

## 1. Estado del módulo

- **Activación:** opt-in por perfil (`profile.mermaid.enabled`
  con `profile.mermaid.labels: "allow"`). Default: `labels: "deny"`.
- **Sin render real.** El adaptador no compila ni renderiza Mermaid.
  Solo reconoce sintaxis estática.
- **Sin dependencias nuevas.** Sin puppeteer, sin headless browsers.
- **Corpus de referencia:** `tests/fixtures/mermaid/`.

## 2. Activación

El adaptador se aplica **solo** si el perfil declara:

```json
{
  "mermaid": {
    "enabled": true,
    "labels": "allow"
  }
}
```

Si `enabled: false` o `labels: "deny"`, Mermaid permanece como en el
modo núcleo (preservado literal, sin cambios).

## 3. Sintaxis reconocida

- ```` ```mermaid ```` fences: el contenido se trata como código
  Mermaid; el adaptador solo traduce las etiquetas visibles.
- Etiquetas en nodos: `A["Texto visible"]`, `B("Otro")`, `C{Tercero}`,
  `D[(Cuarto)]`, `E>Quinto]`, `F((Sexto))`.
- Clases con texto: `classDef clase fill:#fff` no se traduce;
  `class "nodo" "Clase traducida"` no se soporta en esta versión.
- Edges con etiquetas: `A -->|Texto| B` traduce `Texto`.

## 4. Lo que NO se modifica

- Los **IDs de nodo** (`A`, `B`, etc.) son literales.
- Los **tipos de nodo** (`[]`, `()`, `{}`, `[]`, `>]`, `(())`).
- Las **flechas y direcciones** (`-->`, `---`, `TD`, `LR`, etc.).
- El **contenido de los fences** fuera de las etiquetas visibles.

## 5. Sintaxis inválida

Si el parser no reconoce el contenido Mermaid o detecta un patrón
malformado, emite un hallazgo `mermaid_unsupported` con severidad
`info`. **No** se repara.

Esa severidad `info` y no `bloqueante`, porque el núcleo preserva el fence
literal y un diagrama que no se va a traducir no puede quedar mal escrito
por haberlo leído. El diagrama se copia byte a byte, como cualquier bloque
de código.

Pasa a `bloqueante` en un solo caso: cuando el perfil activa la
traducción de etiquetas (`mermaid.enabled: true` **y**
`mermaid.labels: allow`). Ahí el texto del diagrama va a cambiar y una
sintaxis que no se reconoce impediría traducirla sin inventar, así que
bloquea. `references/markdown-contract.md` decía antes que cualquier
Mermaid malformado bloqueaba siempre; se ha corregido para que diga lo que
el código hace.

## 7. Procedimiento para añadir un patrón

1. Aportar el corpus en `tests/fixtures/mermaid/`.
2. Extender el parser con el nuevo patrón.
3. Añadir prueba positiva en `tests/test_mermaid_labels.py`.
4. Registrar la decisión en `manifest.json` bajo
   `policy_decisions` con `kind: mermaid_pattern`, `motivo`,
   `corpus_path`.