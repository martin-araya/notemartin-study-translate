# Caso piloto — francés → español (`pilot-fr`)

Estado: **experimental, sin revisor humano nativo en fr**.
Aceptación parcial de la fase 101: corpus inventariado y atribuido.
La fase 103 sigue pendiente hasta que un nativo en fr firme la
revisión.

> ⚠ **Disclaimer de competencia.** Este caso piloto **no** se
> presenta como soporte estable del par fr→es. La fase 103 del
> roadmap exige « revisión competente en el idioma de origen » para
> cerrar con `✅`; mientras esa firma no exista, la fila 103 del
> roadmap lleva el aviso `revisión asistida registrada, pendiente
> de revisión humana`. El resto de las filas (101, 102, 104, 105)
> se cierran con artefactos verificables.

## 1. Origen autorizado

| Campo | Valor |
|---|---|
| Fuente prevista | Nextcloud user manual fr (`docs.nextcloud.com/server/latest/user_manual/fr/`) |
| Fuente efectivamente integrada | corpus derivado CC0 (ver §3) |
| Licencia original del corpus | CC0 1.0 Universal (de mi autoría para este piloto) |
| Licencia prevista si se sustituye por la fuente real | CC-BY-SA 3.0 (Nextcloud documentation) |
| Fecha de inventario | 2026-10-20 |
| Codificación detectada | UTF-8 en los 6 archivos |
| Saltos de línea | LF en los 6 archivos |

## 2. Por qué el corpus es derivado

Los manuales de Nextcloud se distribuyen en HTML / reStructuredText,
no en Markdown. La fase 101 mide el soporte del par fr→es; el
contrato soportado es CommonMark + GFM. La conversión HTML → Markdown
pertenece a otra fase (HTML embebido, 071–080) y no se aborda aquí.

Por tanto, este piloto usa **corpus derivado CC0**, escrito en
francés técnico, que reproduce la variedad de construcciones
observada en manuales de administración (tablas, código, listas,
advertencias, citas contractuales) sin reproducir la prosa original
de Nextcloud. Cuando se active el flujo HTML→MD (fases 071–080) con
un parser que respete los rangos, se sustituirá este directorio por
un volcado Markdown real con la atribución correspondiente.

## 3. Archivos seleccionados

Cada archivo conserva su ruta relativa exacta dentro de
`tests/fixtures/pilot-fr/`. Hash y tamaño se calculan sobre los
bytes originales.

| Ruta relativa | Hash SHA-256 (prefijo 16) | Bytes | Codificación |
|---|---|---|---|
| `01-prelude-et-licence.md` | `06b2cead15159ee1` | 1982 | utf-8 |
| `02-fichiers-et-synchronisation.md` | `f02b3b3f43bed1d3` | 2198 | utf-8 |
| `03-authentification.md` | `5c64eaaf682e01d1` | 2193 | utf-8 |
| `04-configuration-2fa.md` | `0fcaf443713b06be` | 2109 | utf-8 |
| `05-client-bureau.md` | `dfd907470cc074a3` | 1948 | utf-8 |
| `06-preferences-utilisateur.md` | `96c7001e89902612` | 2329 | utf-8 |

Los hashes completos se conservan en `manifest.json` cuando exista.

## 4. Criterios cubiertos por el piloto fr

| # | Criterio | Estado | Evidencia |
|---|---|---|---|
| 1 | Tabla GFM con alineación por columna | cumplido | `02-fichiers...md` (alineación por defecto), `03-authentification.md` (alineación mixta). |
| 2 | Bloques fenced e indentados | cumplido parcial | Fenced en `03-authentification.md` (` ```bash `), `04-configuration-2fa.md`. Indentados no incluidos; se documentan como limitación. |
| 3 | Código con comentarios en francés | cumplido | `03-authentification.md` contiene commentaires tras comandos. |
| 4 | Enlace entre archivos distintos | cumplido | `02-fichiers...md`, `03-authentification.md`, `04-configuration-2fa.md`, `05-client-bureau.md`, `06-preferences-utilisateur.md` se enlazan entre sí con anclas `(#section)`. |
| 5 | Variantes de encabezado (tilde, código inline, duplicado) | cumplido parcial | Acentos: « Authentification et connexion », « Configuration de l'authentification à deux facteurs ». Código inline: no se observa. Duplicados entre archivos no incluidos (se documentan como limitación). |
| 6 | Enlace externo (no se reescribe) | cumplido | `05-client-bureau.md` contiene `https://example.org/client-desktop/`. |
| 7 | Región en idioma de origen distinto del inglés | cumplido | Los seis documentos están redactados en francés. |
| 8 | Bloque de cita contractual + cita literaria | cumplido | `01-prelude-et-licence.md` y `06-preferences-utilisateur.md` contienen bloques `> **Note de licence**` y `> **Important**`. |
| 9 | Frontmatter | cumplido | `01-prelude-et-licence.md` inicia con `---` y bloque YAML. |
| 10 | Recurso local referenciado | cumplido | `02-fichiers...md` referencia `/uploads/illustration.png`. |
| 11 | Admonition (`> [!NOTE]`, `> [!TIP]`, etc.) | cumplido | `02`, `03`, `04`, `05` y `06` contienen admonitions declaradas. |

## 5. Limitaciones aceptadas

- **Corpus derivado CC0**, no volcado real de Nextcloud. La
  sustitución se realizará cuando se activen las fases 071–080 con
  un conversor HTML→MD auditado.
- Sin **revisor humano nativo en francés** (fase 103).
- **Acentos y circonflexos** presentes pero no exhaustivos.
- **Falsos amigos**: el corpus contiene casos puntuales
  (« actuellement », « éventuellement ») que la política lingüística
  cubre. El eval asistida puede ampliar la tabla si encuentra más.

## 6. Glosario tentativo extraído

| Término origen | Dominio | Sentido observado | Equivalente propuesto |
|---|---|---|---|
| `authentification` | seguridad | proceso de verificar identidad | autenticación |
| `autorisation` | seguridad | proceso de verificar permisos | autorización |
| `facteur` | seguridad | segundo factor 2FA | factor |
| `quota` | ui | límite de almacenamiento | cuota |
| `épingle` | ui | indicador fijo | indicador fijo |
| `téléchargement` | red | transferencia servidor → cliente | descarga |
| `synchronisation` | red | puesta al día entre cliente y servidor | sincronización |
| `sécurisé` | general | protegido por dispositif de sécurité | seguro |
| `sur` | general | seguro (qualificatif) ≠ `sur` (sobre) | seguro |

## 7. Aprobaciones pendientes

- [ ] Aceptación de la sustitución HTML→MD (fase 101).
- [ ] Revisor humano nativo en fr para la fase 103.
- [ ] Confirmación del subconjunto glosario de la sección 6.

Sin estos tres puntos, la fila 103 del roadmap no se cierra con
`✅` aunque el resto (101, 102, 104, 105) sí queden marcadas.
