"""Clave de persistencia de traducciones cuando `document_id` colisiona.

`prepare.py` deriva `document_id` de los **bytes** del archivo:

    document_id = "doc-" + sha256(source_bytes)[:8]

Eso hace que dos rutas con contenido byte a byte idéntico compartan
`document_id`. En el corpus real medido eso ocurre en 15 identificadores
y 214 rutas (páginas stub de `tailwindcss/installation/`, FAQ repetidas
de `angular/`). Como la traducción se persiste en
`translations/<clave>.json`, dos archivos distintos escribían sobre la
misma clave: el segundo pisaba al primero y el parche de `assemble.py`
se aplicaba sobre el documento equivocado, sin que ningún validador por
paquete lo notara.

Este módulo resuelve el conflicto **sin regenerar identificadores**.
`document_id` conserva su significado real — la clase de equivalencia de
contenido, que es valuable para agrupar y para la trazabilidad — y se
introduce una clave de persistencia que sí distingue la ruta:

    translation_id = "trl-" + sha256(document_id + "|" + ruta)[:12]

**Por qué no se renombran todos los archivos.** Solo colisionan los
documentos ambigüos. Renombrar los 2 682 invalidaría el manifiesto, los
hashes de procedencia y la traducción ya entregada de `doc-f0342fb5`
(43 segmentos) sin ganar nada: el 99,3 % de las claves no ambigüas ya
es correcta. `resolve_key` usa por tanto la clave de contenido cuando
no hay ambigüedad, y la clave con ruta cuando la hay. Un archivo tocado
por la remediación conserva su nombre; los demás no se mueven.
"""

from __future__ import annotations

import hashlib
from pathlib import PurePosixPath


def normalize_path(relative_path: str) -> str:
    """Ruta relativa normalizada con separadores `/` y sin prefijos superfluos.

    `inventory.py` y `prepare.py` ya emiten rutas con `/`, pero un path
    ajeno (`./a.md`, `a/../a.md`, separadores del sistema) no debe
    producir dos claves distintas para el mismo archivo. La clave de
    persistencia identifica un archivo, no una forma de escribir su
    nombre.
    """
    text = str(relative_path).replace("\\", "/").strip()
    parts = [p for p in PurePosixPath(text).parts if p not in ("", ".", "..")]
    return "/".join(parts)


def translation_id(document_id: str, relative_path: str) -> str:
    """Clave de persistencia que distingue rutas con el mismo `document_id`."""
    payload = f"{document_id}|{normalize_path(relative_path)}"
    return "trl-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def index_by_document(segments_doc: dict) -> dict[str, list[dict]]:
    """Agrupa `segments_doc["files"]` por `document_id`.

    El valor es una **lista**: una lista de un solo elemento significa
    que el `document_id` no colisiona y basta como clave de
    persistencia. Más de un elemento significa ambigüedad real, y obliga
    a incorporar la ruta.
    """
    index: dict[str, list[dict]] = {}
    for f in segments_doc.get("files", []):
        doc_id = f.get("document_id")
        if not doc_id:
            continue
        index.setdefault(doc_id, []).append(f)
    return index


def ambiguous_documents(segments_doc: dict) -> dict[str, list[str]]:
    """Mapa `document_id -> rutas` de los documentos que colisionan."""
    out: dict[str, list[str]] = {}
    for doc_id, files in index_by_document(segments_doc).items():
        if len(files) > 1:
            out[doc_id] = [normalize_path(f.get("path", "")) for f in files]
    return dict(sorted(out.items()))


def resolve_file(files: list[dict] | None, doc_id: str, path: str | None) -> dict | None:
    """Localiza la entrada de `segments_doc["files"]` que corresponde al paquete.

    Un paquete declara `document_id` y `path`. Cuando el `document_id`
    no es ambiguo basta con él. Cuando lo es, la ruta es lo que
    desambigua: dos archivos byte-idénticos siguen siendo dos archivos.
    """
    candidates = files or []
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]
    wanted = normalize_path(path or "")
    for f in candidates:
        if normalize_path(f.get("path", "")) == wanted:
            return f
    return None


def resolve_key(files: list[dict] | None, doc_id: str, path: str | None) -> str:
    """Clave de persistencia para un paquete o documento.

    Sin ambigüedad devuelve `document_id` (comportamiento previo, sin
    movimiento de archivos ya escritos). Con ambigüedad devuelve
    `translation_id(document_id, path)`.
    """
    candidates = files or []
    if len(candidates) > 1:
        return translation_id(doc_id, path or "")
    return doc_id


def key_for_segments_doc(segments_doc: dict, doc_id: str, path: str | None) -> str:
    """Atajo: resuelve la clave usando un `segments_doc` completo."""
    return resolve_key(index_by_document(segments_doc).get(doc_id), doc_id, path)


def collision_report(segments_doc: dict) -> dict:
    """Informe medido de las colisiones de `document_id`.

    Devuelve, por `document_id` ambiguo, las rutas implicadas y una
    estimación del tamaño del problema: cuántas rutas quedan separadas
    por la remediación y cuántas siguen compartiendo clave de contenido.
    """
    groups = ambiguous_documents(segments_doc)
    ambiguous_paths = sorted({p for paths in groups.values() for p in paths})
    total_files = len(segments_doc.get("files", []))
    return {
        "ambiguous_document_ids": len(groups),
        "paths_affected": len(ambiguous_paths),
        "files_total": total_files,
        "files_unambiguous": total_files - len(ambiguous_paths),
        "collisions": groups,
    }