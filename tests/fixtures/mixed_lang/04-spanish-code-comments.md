# Spanish code comment fixture

Este archivo existe **únicamente** para verificar que los segmentos
marcados como `es` no se vuelven a traducir. La prosa exterior está
en español; **los comentarios de código están también en español**
y deben preservarse tal cual.

> Bloque no traducible: ver
> [`references/citations-policy.md`](../../references/citations-policy.md).

```bash
# Comentario en español dentro de un bloque de código.
echo "No traducir este comentario."
```

```yaml
# Comentario YAML en español.
clave: valor
```

La prosa que rodea los bloques sí es traducible; vive en español y se
mantiene como `already_target`. El clasificador debe respetarlo: la
doble traducción no procede.
