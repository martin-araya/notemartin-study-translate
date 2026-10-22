"""Utilidades de redacción para logs (fase 129).

Interfaz de línea de comandos de la fase 129. Las funciones puras viven en
``scripts/redaction.py``, que pertenece al núcleo: la redacción de secretos
no puede depender de un módulo opcional. Aquí solo se interpretan los
subcomandos y se imprime el resultado.

- ``safe_segment_id(segment_id)``: valida y devuelve el
  ``segment_id`` sin alterarlo. Si el id no coincide con el
  patrón conocido, devuelve ``invalid`` (sin exponer el valor).
- ``truncate_for_log(text, limit=40)``: trunca texto libre con
  elipsis ``…`` y eliminador de saltos de línea.
- ``redact_secrets(payload)``: substituye claves sensibles por
  ``***`` en un mapping arbitrario.
"""

from __future__ import annotations

import json
import sys

from redaction import (  # noqa: F401  (reexportado para el contrato de la fase 129)
    APPROVAL_ID_PATTERN,
    DECISION_ID_PATTERN,
    DOCUMENT_ID_PATTERN,
    SECRET_KEYS,
    SEGMENT_ID_PATTERN,
    redact_secrets,
    redact_value,
    safe_filename,
    safe_segment_id,
    truncate_for_log,
)

__all__ = [
    "APPROVAL_ID_PATTERN",
    "DECISION_ID_PATTERN",
    "DOCUMENT_ID_PATTERN",
    "SECRET_KEYS",
    "SEGMENT_ID_PATTERN",
    "redact_secrets",
    "redact_value",
    "safe_filename",
    "safe_segment_id",
    "truncate_for_log",
]


def _main(argv: list[str]) -> int:
    if not argv:
        print("usage: redact.py {check|truncate|dict} ...", file=sys.stderr)
        return 2
    cmd = argv[0]
    rest = argv[1:]
    if cmd == "check":
        if not rest:
            return 2
        result = safe_segment_id(rest[0])
        print(result)
        return 0 if result != "invalid" else 1
    if cmd == "truncate":
        if not rest:
            return 2
        text = rest[0]
        limit = 40
        if "--limit" in rest:
            i = rest.index("--limit")
            if i + 1 < len(rest):
                try:
                    limit = int(rest[i + 1])
                except ValueError:
                    return 2
        print(truncate_for_log(text, limit))
        return 0
    if cmd == "dict":
        if not rest:
            return 2
        try:
            payload = json.loads(rest[0])
        except Exception:
            return 2
        out = redact_secrets(payload) if isinstance(payload, dict) else {"_error": "non-dict"}
        print(json.dumps(out, ensure_ascii=False))
        return 0
    if cmd == "--help" or cmd == "-h":
        print(__doc__)
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))