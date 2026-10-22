<!-- version: 1.0.0 -->

# Redacción de logs (fase 129)

Esta política fija qué se puede imprimir en logs técnicos sin
comprometer la privacidad del corpus, del revisor o de secretos.

## 1. Datos permitidos por defecto

- `segment_id` válidos (`seg-XXXXXXXX`).
- `document_id` válidos (`doc-XXXXXXXX`).
- `decision_id`, `approval_id` (formato `dec-…` y `app-…`).
- Rutas internas normalizadas, sin componentes que empiecen
  por `~` o `..`.
- Conteos y métricas agregadas.

## 2. Datos prohibidos

- Texto libre de un segmento (origen o candidato).
- Secretos plausibles: `api_key`, `token`, `password`, `secret`,
  `authorization`, `client_secret`, `private_key`,
  `refresh_token`, `access_token`.
- Rutas con directorios personales.
- Direcciones de correo, nombres completos, alias demasiado
  identificativos.
- Contenido de logs del sistema externo del proveedor.

## 3. Mecanismo de redacción

Los scripts del flujo ampliado de revisión deben importar y usar
`scripts/redact.py`:

```python
from redact import safe_segment_id, truncate_for_log, redact_secrets

log.info("decision %s sobre scope=%s reason=%s",
         safe_segment_id(decision.decision_id),
         truncate_for_log(reason, limit=40),
         truncate_for_log(motivo_completo, limit=80))
```

`redact_secrets(payload)` reemplaza claves sensibles en un
mapping por `***` y trunca textos largos.

`truncate_for_log(text, limit=40)` produce un resumen con
elipsis `…` y sin saltos de línea.

`safe_segment_id(value)` valida el patrón y devuelve
`"invalid"` en otro caso, **nunca el valor recibido**.

## 4. Lo que NO hace este módulo

- No aplica redacción automáticamente a otros scripts que no lo
  importen: cada script es responsable.
- No cifra logs: solo evita exposición accidental.
- No elimina logs antiguos; complementariamente,
  `references/workdir-retention.md` define la retención y
  `scripts/purge_workdir.py` la ejecuta (fase 148).

## 5. Cobertura de tests

`tests/test_log_redaction.py` valida:

- `redact.py` (funciones puras y CLI).
- `render_bilingual.py` y `prioritize_findings.py` producen
  salida estándar breve y no imprimen textos completos.
- `gate_review.py` no expone literales de secretos en su código.

## 6. Relación con otras fases

| Fase | Relación |
|---|---|
| 121 | El informe bilingüe muestra el texto de candidato; los logs **no**. |
| 122 | La vista priorizada imprime categorías y metadatos, no texto. |
| 124 | Las aprobaciones solo se loguean por id. |
| 126 | El detector de idioma residual emite alertas por id. |
| 127 | La retrotraducción opera por id y compara en memoria. |
| 130 | El gate globaliza esta política sobre todos los módulos del flujo ampliado. |
