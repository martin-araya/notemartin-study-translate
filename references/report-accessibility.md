<!-- version: 1.0.0 -->

# Accesibilidad local del reporte (fase 128)

Esta política fija las condiciones mínimas que cualquier reporte
producido por `notemartin-study-translate` debe cumplir para poder
abrirse y revisarse **sin enviar documentación a terceros**.

## 1. Recursos locales

- Cero referencias externas (`http://` o `https://`) en los
  artefactos que la skill escribe en `reports/`.
- Cero `<script>`, cero `<link rel="stylesheet" href="http…">`,
  cero `<img src="http…">`.
- Si un reporte requiere hojas de estilo, deben ir en una carpeta local
  del propio reporte y enlazarse con ruta relativa. Hoy la skill no
  genera ninguna hoja de estilo: el reporte es Markdown sin recursos
  externos.
- Codificación UTF-8 verificable al leer el archivo.

## 2. Navegación

- Tabla de contenidos explícita con anclas Markdown (`# slug`)
  apuntando a encabezados del mismo documento.
- Cada `segment_id` se enlaza por ancla desde la fila y desde el
  TOC.
- Los enlaces deben ser estables: dos ejecuciones del mismo
  corpus producen anclas idénticas.

## 3. Contraste y tipografía

- Para los reportes que sí generen HTML: contraste mínimo 4.5:1
  entre texto y fondo en cualquier combinación de paleta.
- Tamaño mínimo de fuente 14 px para texto y 12 px para metadatos.
- No se exige a la versión Markdown, pero sí a cualquier vista
  opcional que el usuario final pueda abrir como HTML.

## 4. Datos personales

- Los reportes nunca imprimen nombres completos ni correos.
- Los alias de firmante son opt-in: si aparecen, están en el
  `manifest.json` y se redactan en `reports/bilingual/` y
  `reports/prioritized/`.

## 5. Relación con otras fases

| Fase | Relación |
|---|---|
| 121 | El informe bilingüe debe pasar el checklist. |
| 122 | La vista priorizada también: se reusa el mismo conjunto de fixtures. |
| 129 | Las pruebas de redacción de logs verifican que la salida no exponga textos sensibles. |
