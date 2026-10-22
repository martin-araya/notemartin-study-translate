"""Redacción de logs: primitivas puras (núcleo).

La redacción de secretos y la truncatura de identificadores son una
necesidad de **seguridad**, no una capacidad opcional de revisión. Por eso
las primitivas viven en el núcleo: ``scripts/record_model_run.py``
(fase 145) las usa y no puede depender de la fase 129.

``scripts/redact.py`` es la interfaz de línea de comandos de la fase 129 y
reexporta estas mismas funciones. No hay dos implementaciones: si las
hubiera, una podría filtrar un secreto que la otra redacta.
"""

from __future__ import annotations

import re
from typing import Any

SEGMENT_ID_PATTERN = re.compile(r"^seg-[0-9a-f]{8}$")
DOCUMENT_ID_PATTERN = re.compile(r"^doc-[0-9a-f]{8}$")
DECISION_ID_PATTERN = re.compile(r"^dec-[0-9a-f]{8}$")
APPROVAL_ID_PATTERN = re.compile(r"^app-[0-9a-f]{8}$")

SECRET_KEYS = {
    "api_key",
    "apikey",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "password",
    "passwd",
    "secret",
    "client_secret",
    "private_key",
}

DEFAULT_TRUNCATE_LIMIT = 40

# Patrones de valores que parecen un secreto aunque la clave no lo diga.
# Sin esto, un `token` anidado bajo un nombre neutro se escribiría entero.
SECRET_VALUE_PATTERNS = (
    re.compile(r"\b(?:sk|pk|rk)-[A-Za-z0-9]{16,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{16,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{5,}\b"),
)


def safe_segment_id(value: Any) -> str:
    """Devuelve el identificador sin alterarlo, o ``invalid`` si no lo es."""
    if not isinstance(value, str):
        return "invalid"
    for pattern in (
        SEGMENT_ID_PATTERN,
        DOCUMENT_ID_PATTERN,
        DECISION_ID_PATTERN,
        APPROVAL_ID_PATTERN,
    ):
        if pattern.match(value):
            return value
    return "invalid"


def truncate_for_log(text: Any, limit: int = DEFAULT_TRUNCATE_LIMIT) -> str:
    """Una sola línea, sin saltos, recortada con elipsis."""
    if not isinstance(text, str):
        return "non-text"
    one_line = text.replace("\r\n", " ").replace("\n", " ").replace("\t", " ").strip()
    if len(one_line) <= limit:
        return one_line
    if limit <= 1:
        return "…"
    return one_line[: limit - 1] + "…"


def redact_secrets(payload: dict) -> dict:
    """Sustituye claves sensibles y valores con forma de secreto."""
    if not isinstance(payload, dict):
        return {"_error": "non-dict"}
    out: dict = {}
    for k, v in payload.items():
        if k.lower() in SECRET_KEYS:
            out[k] = "***"
        elif isinstance(v, dict):
            out[k] = redact_secrets(v)
        elif isinstance(v, str):
            out[k] = redact_value(v)
        else:
            out[k] = v
    return out


def redact_value(value: str) -> str:
    """Trunca y enmascara cualquier valor que parezca un secreto."""
    text = value
    for pattern in SECRET_VALUE_PATTERNS:
        text = pattern.sub("***", text)
    return truncate_for_log(text)


def safe_filename(value: Any) -> str:
    """Ruta relativa sin ``..``, sin ``~`` y recortada."""
    if not isinstance(value, str):
        return "invalid"
    cleaned = value.replace("\\", "/").strip("/")
    if not cleaned or cleaned.startswith(".."):
        return "invalid"
    parts = cleaned.split("/")
    if any(p.startswith("~") for p in parts):
        return "invalid"
    return cleaned[:160]