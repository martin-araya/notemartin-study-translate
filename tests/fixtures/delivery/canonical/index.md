---
title: Guía de instalación
lang: es
---

# Guía de instalación

Este documento es la entrega canónica usada por las pruebas de entrega local.

## Requisitos previos

| Requisito | Versión mínima | Nota |
|---|---|---|
| Node.js | 18 | Sin soporte para versiones anteriores |
| Puerto | 8080 \| 9090 | Dos puertos disponibles |

> **Advertencia.** La instalación no admite el modo `--legacy`. Ejecutar
> ese flag deja el servicio sin soporte.

## Pasos

1. Ejecutar `npm install --save-exact`.
2. Copiar el archivo de configuración sin renombrarlo.
3. Arrancar el servicio con `npm start`.

- [ ] Verificar la conectividad
- [x] Revisar los registros

1. Instalar dependencias
   1. Verificar versiones
      1. Confirmar el motor
         1. Registrar el resultado

```bash
npm ci --omit=dev
# la salida de este comando se conserva literal
```

Continuar en [configuración avanzada](guias/instalacion.md#configuracion-avanzada).

![Diagrama de flujo](imagenes/diagrama.png)