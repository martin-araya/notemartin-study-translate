<!-- version: 1.0.0 -->

# Política lingüística del idioma de origen — francés

Esta política recoge las convenciones que la skill
`notemartin-study-translate` aplica cuando traduce **del francés
hacia el español**. Complementa a `references/translation-policy.md`,
que rige el lado español y los invariantes del núcleo. Lo que un
dominio técnico no decida se delega al glosario global; esta política
no duplica las decisiones por dominio.

> El par fr→es está **experimental**. La fase 103 del roadmap exige
> un revisor humano nativo en francés; mientras no se designe, las
> decisiones aquí recogidas pasan por la rejilla de la revisión
> asistida, nunca por una auditoría humana formal.

## 1. Modalidad y registro

- **Vouvoiement sistemático.** La documentación técnica francesa usa
  `vous`; el agente no tutea (`tu`) ni neutraliza.
- **Voz pasiva y tercera persona** se prefieren para describir
  configuraciones y estados del sistema.
- No se traducen los actos de habla contractual: « Vous devez » se
  traduce como **« debe »** (preservación de obligación), « Vous
  pouvez » como **« puede »** (permiso). Conservar la fuerza
  normativa es una invariante; los matices de cortesía se pierden.

## 2. Puntuación

- **Espacios insécables antes de** `:` `;` `?` `!`. Esta es la regla
  tipográfica francesa por defecto.
- **Comillas tipográficas**: « … » (con espacios). La salida las
  preserva por defecto. Se puede neutralizar a comillas rectas si
  `profile.punctuation_preference` lo establece; por defecto, se
  mantienen.
- **Puntos suspensivos**: tres puntos separados, o carácter
  `…` (U+2026). Lo que diga la fuente.
- **Guiones y rayas**: `-` (signo menos), `–` (en-dash),
  `—` (em-dash). Preservar.
- Las comas y los puntos del español **no** se cambian retroactivamente
  sobre código, URLs, YAML ni literales protegidos.

## 3. Acentos y mayúsculas

| Característica | Comportamiento | Nota |
|---|---|---|
| Agudo (`é`, `è`, `ê`, `ë`) | Se preserva. | Cualquier pérdida es regresión. |
| Grave (`à`, `ù`) | Se preserva. | `où` ≠ `ou`. |
| Circonflexo (`â`, `î`, `ô`, `û`) | Se preserva. | `sur` ≠ `sûr`. |
| Diéresis (`ï`, `ë`, `ü`, `ÿ`) | Se preserva. | `aïe`, `ciguë`. |
| Cedilla (`ç`) | Se preserva. | `garçon`, `leçon`. |
| Mayúsculas lexicales (`la Configuration`, `l'État`) | Preservadas en la fuente. | No se eliminan en español. |
| `Æ æ Œ œ` | Se preservan. | `cœur`, `œuvre`. |

## 4. Falsos amigos prioritarios

Tabla de falsos amigos que el agente debe tratar con cuidado.
Cuando un caso presente ambigüedad se escala a glosario por dominio.

| Francés | Calco a evitar | Español correcto | Notas de uso |
|---|---|---|---|
| actuellement | actualmente (literal) | actualmente / en realidad / hoy por hoy | « actualmente » en español se acerca a `presently`; conviene verificar el matiz. |
| éventuellement | eventualmente | posiblemente / llegado el caso / si llega el caso | `eventuellement` ≈ « possibly / should it happen ». |
| assister à | asistir a (siempre) | asistir (a una sesión) / presenciar (un evento) | Distinguir `attend` (ponente) vs `witness` (espectador). |
| librairie | librería (siempre) | librería (tienda) / bibliothèque (edificio) | Para `library` (programación), conservar en inglés. |
| blesser | bendecir | herir / dañar | No mezclar con sentido religioso. |
| figure | figura (gráfico) | figura / ilustración / diagrama (según contexto) | Distinguir del sentido « figura pública ». |
| autorité | autoridad (poder) | autoridad / organismo competente (según contexto) | En legal, suele ser « autoridad ». |
| journée | jornado (calco) | día / jornada (laborable) | Distinguir `day` y `working day`. |
| chair | chair (calco del inglés) | carne (alimento) / piel / carne (literario) | Conflicto ortográfico con `chair` inglés. |
| coin | coin / esquina | moneda / esquina (según contexto) | Distinguir `coin of currency` vs `corner`. |
| rester | restar (siempre) | quedarse / permanecer / seguir | `rester` ≈ `stay / remain`. |
| tirer | tirar (siempre) | tirar / disparar / arrastrar | `tirer` polysémique. |
| sympatique | simpático (siempre) | agradable / afable | En registro neutro, evitar `simpático` con matiz frívolo. |
| fastidieux | fastidioso (siempre) | tedioso / aburrido / largo | « fastidieux » ≈ `tedious`, no `disgusting`. |
| grossier | grosero (siempre) | grosero / aproximado / basto | Distinguir `rude` de `rough`. |
| préserver | preservar (siempre) | preservar / proteger / conservar | A veces `proteger` es más natural. |
| réaliser | realizar (siempre) | darse cuenta / llevar a cabo | `realiser` ≈ `realize / carry out`. |
| supporter | soportar (siempre) | soportar / sostener / ser hincha de | En deporte, mejor « ser aficionado ». |

> Esta tabla es **mínima** y extensible. Cada entrada adicional
> debe registrarse en la rúbrica antes de ampliarse.

## 5. Tratamiento de números y unidades

- **NO** se localizan separadores decimales. La coma francesa
  decimal y el punto anglosajón se conservan tal cual figuren en la
  fuente. Esto es invariante (`AGENTS.md` §5.3).
- **NO** se traducen unidades (`Mo`, `Go`, `ko`, `Hz`, `°C`,
  `kg`). Lo que diga la fuente.
- **NO** se localizan formatos de fecha ni de hora. ISO 8601 se
  preserva.
- **NO** se cambian porcentajes, ratios ni cuantificadores.

## 6. Términos cuyo tratamiento se delega al glosario

Las decisiones sobre « state », « lock », « render », « thread » y
demás términos cuya equivalencia depende del dominio técnico se
gestionan en `evals/cases/pilot-fr.md` (sección 6) y en
`schemas/glossary.schema.json`. Esta política **no** las duplica.

## 7. Limitaciones

- No regula variantes regionales del español (fase 106 del roadmap).
- No aborda direccionalidad RTL (fase 108). El par fr→es es
  estrictamente LTR.
- No es exhaustiva para todos los falsos amigos; es un conjunto
  inicial ampliable.
- No se aplica a la inversa (es→fr), que requeriría una política
  espejada.
