# Documentation sample (English source)

This short technical document exercises the regional cache isolation
mechanism. The same source text is routed through three locale
profiles (`es-ES`, `es-MX`, `es-AR`) and the cache layer must keep
them apart.

## Login

When you sign in, the API issues a token. Refresh the token before
it expires. Logout invalidates it.

```yaml
endpoint: /api/v1/session
method: POST
```

## Errors

| Code | When it appears |
|---|---|
| `401` | Token missing or expired. |
| `403` | User lacks permission. |
| `429` | Too many requests, back off. |

> Technical literals above are preserved byte-by-byte.
