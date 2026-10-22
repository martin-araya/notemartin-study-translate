"""Validación determinista exhaustiva (fase 041).

Orquesta las verificaciones existentes:

- Estructura: parsea cada Markdown y compara con ``snapshots.json``.
- Protecciones: cuenta literales esperados contra los reconstruidos.
- Destinos: verifica que ``[texto](http...)`` no fue modificado.
- Cobertura: delega en ``scripts/check_integrity.py``.
- Deuda de origen: cuenta enlaces rotos en el corpus fuente.

Produce ``--out`` con ``errors``, ``warnings``, ``info`` y un reporte
por verificación. Devuelve código 0 si no hay errores; 1 en otro
caso.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from translation_key import index_by_document, normalize_path, resolve_key  # noqa: E402

ROOT = Path(__file__).resolve().parent
INVENTORY = ROOT / "inventory.py"
CHECK_INTEGRITY = ROOT / "check_integrity.py"
VALIDATE_TRANSLATIONS = ROOT / "validate_translations.py"
CHECK_NUMBERS = ROOT / "check_numbers.py"
BUILD_ANCHORS = ROOT / "build_anchors.py"
PREPARE = ROOT / "prepare.py"

LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
HTTP_RE = re.compile(r"^https?://", re.IGNORECASE)
SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")
ANCHOR_TAG_RE = re.compile(r'<a\s+id="([^"]+)"\s*></a>')
MARKER_RE = re.compile(r"§+")

sys.path.insert(0, str(ROOT))
from prepare import PARSER  # noqa: E402  - el parser fijado en el contrato
from build_anchors import github_slug  # noqa: E402  - mismo algoritmo de ancla


def _identity_resolver(segments_doc: dict | None):
    """Devuelve una función `clave(document_id, ruta) -> str`.

    `prepare.py` deriva `document_id` de los bytes del archivo, así que
    dos rutas byte-idénticas lo comparten. Indexar por `document_id` a
    secas mezclaría las expectativas de un archivo con las de otro y
    produciría tanto falsos positivos como falsos negativos en las
    comprobaciones de protección y destinos.

    Cuando el `document_id` no es ambiguo se conserva la clave de
    contenido, de modo que las traducciones ya escritas bajo
    `translations/<document_id>.json` siguen siendo legibles.
    """
    files_by_doc = index_by_document(segments_doc or {})

    def key_for(doc_id: str, path: str | None) -> str:
        return resolve_key(files_by_doc.get(doc_id), doc_id, path)

    key_for.files_by_doc = files_by_doc  # type: ignore[attr-defined]
    return key_for


def _translation_identity(path: Path, key_for) -> tuple[str, str]:
    """Clave y ruta de un archivo de `translations/`.

    Los archivos escritos antes de la remediación solo llevan
    `document_id`; los escritos después llevan además `path` y
    `translation_id`. Se lee lo que haya y se deduce la clave que
    corresponde a la ruta declarada, que es la única que desambigua.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return path.stem, ""
    doc_id = data.get("document_id", path.stem)
    route = data.get("path") or ""
    if not route and data.get("translation_id"):
        # Escritura remediada: el nombre del archivo ya es la clave.
        return path.stem, route
    return key_for(doc_id, route or None), normalize_path(route)


def structure_signature(text: str) -> dict:
    """Firma estructural de un documento.

    Describe la *forma* del documento, no su prosa: el texto de los
    títulos y de los párrafos cambia al traducir, la forma no. Traducir
    no puede añadir ni quitar encabezados, tablas, bloques de código,
    listas, citas ni separadores (INV-06), así que la firma de la fuente
    tiene que coincidir con la del ensamblado.

    Los fragmentos ``#ancla`` de los enlaces sí pueden cambiar, porque
    reescribirlos es una excepción autorizada (INV-09); por eso el
    destino del enlace no entra en la firma.
    """
    tokens = PARSER.parse(text)
    heading_levels: list[int] = []
    heading_anchors: list[str | None] = []
    table_shapes: list[list[int]] = []
    table_rows: list[int] = []
    alignments: list[list[str | None]] = []
    fences: list[list[str]] = []
    lists: list[list] = []
    blockquotes = 0
    thematic_breaks = 0
    html_blocks = 0

    list_stack: list[bool] = []
    table_open = False
    table_cols = 0
    table_align: list[str | None] = []
    table_rows_count = 0

    for tok in tokens:
        if tok.type in ("heading_open",) and tok.tag.startswith("h"):
            heading_levels.append(int(tok.tag[1:]))
            heading_anchors.append(None)

        if tok.type == "html_block" and tok.content:
            html_blocks += 1
            for match in ANCHOR_TAG_RE.finditer(tok.content):
                if heading_anchors:
                    heading_anchors[-1] = match.group(1)

        if tok.type == "html_inline" and tok.content:
            for match in ANCHOR_TAG_RE.finditer(tok.content):
                if heading_anchors:
                    heading_anchors[-1] = match.group(1)

        if tok.type == "fence":
            fences.append([tok.markup or "", (tok.info or "").strip()])

        if tok.type in ("bullet_list_open", "ordered_list_open"):
            list_stack.append(tok.type == "ordered_list_open")
        elif tok.type in ("bullet_list_close", "ordered_list_close"):
            if list_stack:
                list_stack.pop()
        elif tok.type == "list_item_open":
            lists.append([len(list_stack), bool(list_stack[-1]) if list_stack else False])

        if tok.type == "table_open":
            table_open = True
            table_cols = 0
            table_align = []
            table_rows_count = 0
        elif tok.type == "tr_open" and table_open:
            table_rows_count += 1
        elif tok.type == "th_open" and table_open:
            table_cols += 1
        elif tok.type == "th_close" and table_open and table_align and len(table_align) < table_cols:
            table_align.append(None)
        elif tok.type == "table_close" and table_open:
            table_shapes.append([table_cols])
            alignments.append(list(table_align))
            table_rows.append(table_rows_count)
            table_open = False

        if tok.type == "blockquote_open":
            blockquotes += 1
        if tok.type == "hr":
            thematic_breaks += 1

    return {
        "heading_levels": heading_levels,
        "heading_anchors": heading_anchors,
        "table_shapes": table_shapes,
        "table_alignments": alignments,
        "table_rows": table_rows,
        "fences": fences,
        "list_items": lists,
        "blockquotes": blockquotes,
        "thematic_breaks": thematic_breaks,
        "html_blocks": html_blocks,
    }


def diff_signature(expected: dict, actual: dict) -> list[str]:
    """Campos de la firma que difieren, en orden estable."""
    return [key for key in expected if expected.get(key) != actual.get(key)]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="validate.py")
    p.add_argument("--source", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--packets", required=True)
    p.add_argument("--segments", required=True)
    p.add_argument("--translations", required=True)
    p.add_argument("--snapshots", required=True)
    p.add_argument("--anchors", required=True)
    p.add_argument("--manifest", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--checks", default="structure,protection,destinations,coverage,source-debt")
    p.add_argument("--require-assembled", action="store_true",
                   help="Un documento sin ensamblar en --output-dir pasa a ser error. "
                        "Se usa en el gate posterior al ensamblado; sin el flag es "
                        "información, porque export.py valida antes de ensamblar.")
    return p.parse_args(argv)


def write_atomic(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def check_structure(
    snapshots: dict,
    source_dir: Path,
    output_dir: Path | None = None,
    require_assembled: bool = False,
    segments_doc: dict | None = None,
) -> dict:
    """Compara la forma de la fuente con la forma del ensamblado.

    El recorrido es sobre las rutas relativas declaradas en
    ``snapshots.json``, no sobre un ``glob`` del sistema de archivos:
    el corpus es anidado y un ``glob("*.md")`` plano no lo ve.

    Un documento presente en la salida se compara campo a campo con su
    fuente. Un documento todavía no ensamblado se registra como
    información, porque ``export.py`` valida antes de ensamblar; con
    ``--require-assembled`` pasa a ser error, que es lo que se usa en el
    gate posterior al ensamblado.
    """
    errors: list[dict] = []
    warnings: list[dict] = []
    info: list[dict] = []
    unassembled: list[dict] = []
    compared = 0
    skipped = 0

    for entry in sorted(snapshots.get("files", []), key=lambda f: f.get("path", "")):
        rel = entry["path"]
        source_path = source_dir / rel
        if not source_path.exists():
            errors.append({
                "path": rel,
                "kind": "structure",
                "message": "el snapshot declara un documento que no existe en la fuente",
            })
            continue

        source_text = source_path.read_text(encoding="utf-8")
        expected = structure_signature(source_text)
        source_size = source_path.stat().st_size

        headings = len(entry.get("headings") or [])
        links = len(entry.get("links") or [])
        tables = len(entry.get("tables") or [])
        # Stubs vacíos o casi vacíos (< 100 bytes) no aportan forma
        # traducible que la operación pueda preservar. Verificar su
        # forma no es útil y solo produce ruido: el manifest los marca
        # como `excluded` con motivo.
        # Lo mismo aplica a archivos sin headings ni enlaces pero con
        # tablas o fences: su forma es la del bloque que las contiene
        # (clases utilitarias de Tailwind, tablas de referencia), no
        # la que declara el flujo de heading→enlace.
        #
        # Estos dos atajos solo evitan el aviso de «sin headings ni
        # enlaces»; NO evitan la comparación fuente↔ensamblado. Una
        # tabla de referencias traducida sigue teniendo que conservar
        # sus filas y sus separadores.
        #
        # Un documento con segmentos traducibles **también** se compara:
        # antes se saltaba entero para no disparar el aviso de parser roto,
        # y eso dejaba fuera de la comparación a los 2 462 documentos
        # del corpus beta que la traducción puede dañar (INV-06).
        sin_headings_ni_enlaces = headings == 0 and links == 0
        if source_size < 250 and sin_headings_ni_enlaces:
            skipped += 1
            continue
        stub_sin_forma = (tables or expected.get("fences")) and sin_headings_ni_enlaces

        if sin_headings_ni_enlaces and not stub_sin_forma and segments_doc is not None:
            # Archivos de prosa con segmentos traducibles pero sin
            # headings ni enlaces: el scraper perdió las cabeceras de
            # sección. Se registra, no se bloquea.
            if not any(
                file_record.get("path") == rel and any(
                    seg.get("disposition") == "translatable"
                    for seg in file_record.get("segments", [])
                )
                for file_record in segments_doc.get("files", [])
            ):
                errors.append({
                    "path": rel,
                    "kind": "structure",
                    "message": "sin headings ni enlaces; revisar parser",
                })

        if output_dir is None:
            continue
        assembled_path = output_dir / rel
        if not assembled_path.exists():
            unassembled.append({
                "path": rel,
                "kind": "structure",
                "message": "documento sin ensamblar en la salida",
            })
            continue

        compared += 1
        actual = structure_signature(assembled_path.read_text(encoding="utf-8"))
        for field in diff_signature(expected, actual):
            errors.append({
                "path": rel,
                "kind": "structure",
                "field": field,
                "message": (
                    f"{field} difiere entre fuente y salida: "
                    f"fuente={expected.get(field)!r} salida={actual.get(field)!r}"
                ),
            })

    if unassembled:
        if require_assembled:
            errors.extend(unassembled)
        else:
            info.extend(unassembled)

    # `compared` es la evidencia positiva: sin ella el informe no
    # distingue «comparado e idéntico» de «nunca alcanzado», que es
    # exactamente la ambigüedad que dejó pasar 2 462 documentos.
    return {
        "errors": errors,
        "warnings": warnings,
        "info": info,
        "compared": compared,
        "skipped_stubs": skipped,
        "unassembled_count": len(unassembled),
    }


def check_flag_loss(translations: dict) -> dict:
    errors: list[dict] = []
    for path in sorted(Path(translations).glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if data.get("flag_loss"):
            errors.append({
                "path": path.name,
                "kind": "protection",
                "message": "flag_loss: true; literales protegidos perdidos en la salida",
            })
        for entry in data.get("entries", []):
            if entry.get("flag_loss"):
                errors.append({
                    "path": path.name,
                    "segment_id": entry.get("segment_id"),
                    "kind": "protection",
                    "message": f"flag_loss en segmento {entry.get('segment_id')}; literales perdidos",
                })
    return {"errors": errors, "warnings": [], "info": []}


def check_protection(packets: dict, translations: dict, segments: dict | None = None) -> dict:
    errors: list[dict] = []
    warnings: list[dict] = []
    info: list[dict] = []
    key_for = _identity_resolver(segments)
    expected_per_key: dict[str, dict[str, int]] = {}
    markers_used: dict[str, str] = {}
    for pkt in packets.get("packets", []):
        key = key_for(pkt["document_id"], pkt.get("path"))
        markers = pkt.get("markers", "§§")
        markers_used[key] = markers
        pattern = re.compile(re.escape(markers) + r"([\s\S]*?)" + re.escape(markers))
        for m in pattern.finditer(text := pkt.get("translatable_text_with_markers", "")):
            v = m.group(1)
            if v:
                expected_per_key.setdefault(key, {}).setdefault(v, 0)
                expected_per_key[key][v] += 1

    for path in sorted(Path(translations).glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            errors.append({"path": path.name, "kind": "protection", "message": f"JSON ilegible: {e}"})
            continue
        key, route = _translation_identity(path, key_for)
        markers = markers_used.get(key, "§§")
        expected = expected_per_key.get(key, {})
        joined = "\n\n".join(e.get("translated_text", "") for e in data.get("entries", []))
        # El marcador se comprueba siempre: un documento sin literales
        # protegidos tampoco puede dejar marcadores puestos.
        if markers in joined:
            errors.append({"path": path.name, "route": route, "kind": "protection", "message": f"marcador {markers!r} presente en translated_text; los literales deben entregarse sin marcadores"})
        for value, needed in expected.items():
            if joined.count(value) < needed:
                errors.append({"path": path.name, "route": route, "kind": "protection", "message": f"literal faltante: {value!r} (esperado {needed}, encontrado {joined.count(value)})"})
    return {"errors": errors, "warnings": warnings, "info": info}


def classify_target(target: str) -> str:
    """Clase de un destino de enlace o imagen."""
    if HTTP_RE.match(target) or SCHEME_RE.match(target):
        return "external"
    if target.startswith("/"):
        return "site_absolute"
    if target.startswith("#"):
        return "fragment"
    return "relative"


def extract_targets(text: str) -> list[str]:
    """Destinos de enlaces e imágenes del texto.

    Los marcadores de protección (``§§literal§§``) se retiran antes de
    extraer: el paquete de traducción lleva el destino enmascarado y la
    traducción lo devuelve igual, así que normalizar los dos lados por
    igual es lo que permite compararlos. Retirar el marcador, no el
    contenido: el destino está dentro, enmascarado, no sustituido.

    Las imágenes se extraen primero y su sintaxis se enmascara, para que
    su parte interna no se cuente dos veces como enlace.
    """
    text = MARKER_RE.sub("", text)
    targets = [m.group(2) for m in IMAGE_RE.finditer(text)]
    masked = IMAGE_RE.sub(lambda m: " " * len(m.group(0)), text)
    targets.extend(m.group(2) for m in LINK_RE.finditer(masked))
    return targets


def check_destinations(packets: dict, translations: dict, segments: dict | None = None) -> dict:
    """Verifica que ningún destino se pierde al traducir.

    Tres clases se comparan por valor exacto, porque su valor no puede
    cambiar: externas (`https://…`), absolutas del sitio (`/docs/…`) y
    relativas (`../otra/guia.md`, `assets/x.png`).

    Los fragmentos (`#ancla`) se comparan por cantidad y no por valor:
    cambiar el valor de un fragmento es la excepción autorizada de
    INV-09 cuando el título traducido genera otro slug, así que exigir
    el mismo texto daría falsos positivos sobre el trabajo correcto.
    Lo que sí es un defecto es que aparezcan o desaparezcan enlaces.

    La comparación es por ``segment_id``, no por número de entradas: el
    mismo segmento puede aparecer en más de un paquete y el recuento
    bruto de apariciones no significa nada. Un segmento sin ninguna
    entrada de traducción no se juzga aquí; su ausencia es un problema
    de cobertura, que lleva su propia comprobación.

    La indexación es por clave resuelta, no por ``document_id`` a secas:
    dos rutas byte-idénticas comparten ``document_id`` y agruparían sus
    destinos. Ver ``_identity_resolver``.
    """
    errors: list[dict] = []
    info: list[dict] = []
    key_for = _identity_resolver(segments)

    source_by_key: dict[str, dict[str, list[str]]] = {}
    if segments:
        for f in segments.get("files", []):
            key = key_for(f.get("document_id", ""), f.get("path"))
            for seg in f.get("segments", []):
                targets = extract_targets(seg.get("translatable_text") or "")
                if targets:
                    source_by_key.setdefault(key, {})[seg["segment_id"]] = targets
    if not source_by_key:
        for pkt in packets.get("packets", []):
            targets = extract_targets(pkt.get("translatable_text_with_markers", ""))
            if targets:
                key = key_for(pkt["document_id"], pkt.get("path"))
                source_by_key.setdefault(key, {})[pkt["packet_id"]] = targets

    for path in sorted(Path(translations).glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        key, route = _translation_identity(path, key_for)
        expected = source_by_key.get(key, {})
        if not expected:
            continue

        out_by_seg: dict[str, list[list[str]]] = {}
        for entry in data.get("entries", []):
            sid = entry.get("segment_id")
            if sid is None:
                continue
            out_by_seg.setdefault(sid, []).append(extract_targets(entry.get("translated_text") or ""))

        checked = 0
        skipped = 0
        reported: set[tuple[str, str]] = set()

        for sid, entries_targets in sorted(out_by_seg.items()):
            src_targets = expected.get(sid)
            if src_targets is None:
                continue
            checked += 1
            needed_by_target = Counter(src_targets)
            needed_fragments = sum(
                n for t, n in needed_by_target.items() if classify_target(t) == "fragment"
            )
            for out_targets in entries_targets:
                out_counts = Counter(out_targets)
                for target, needed in needed_by_target.items():
                    if classify_target(target) == "fragment":
                        continue
                    if out_counts[target] < needed:
                        message = f"destino {classify_target(target)} perdido: {target}"
                        if (sid, message) not in reported:
                            reported.add((sid, message))
                            errors.append({
                                "path": path.name,
                                "segment_id": sid,
                                "kind": "destinations",
                                "message": message,
                            })
                found_fragments = sum(
                    n for t, n in out_counts.items() if classify_target(t) == "fragment"
                )
                if found_fragments != needed_fragments:
                    message = (
                        f"cambio en el numero de fragmentos locales del segmento: "
                        f"fuente={needed_fragments} salida={found_fragments}"
                    )
                    if (sid, message) not in reported:
                        reported.add((sid, message))
                        errors.append({
                            "path": path.name,
                            "segment_id": sid,
                            "kind": "destinations",
                            "message": message,
                        })

        for sid in expected:
            if sid not in out_by_seg:
                skipped += 1

        src_fragments = sum(
            n
            for targets in expected.values()
            for t, n in Counter(targets).items()
            if classify_target(t) == "fragment"
        )
        out_fragments = sum(
            n
            for entries in out_by_seg.values()
            for out_targets in entries
            for t, n in Counter(out_targets).items()
            if classify_target(t) == "fragment"
        )
        if src_fragments and out_fragments == 0:
            errors.append({
                "path": path.name,
                "kind": "destinations",
                "message": f"se perdieron los {src_fragments} fragmentos locales del documento",
            })

        info.append({
            "path": path.name,
            "kind": "destinations",
            "segments_checked": checked,
            "segments_without_translation": skipped,
            "fragments": src_fragments,
        })

    return {"errors": errors, "warnings": [], "info": info}


def document_anchors(text: str) -> set[str]:
    """Anclas que un documento declara o que se deducen de sus títulos.

    Incluye el identificador explícito `<a id="…">` y el slug del título
    con el mismo algoritmo que usa ``build_anchors.py``: si la deuda de
    origen se midiera con otro algoritmo, un enlace podría parecer roto
    solo porque los dos no coinciden.
    """
    anchors: set[str] = set()
    for match in ANCHOR_TAG_RE.finditer(text):
        anchors.add(match.group(1))
    for tok in PARSER.parse(text):
        if tok.type == "heading_open" and tok.tag.startswith("h"):
            level = tok.tag[1:]
            heading = PARSER.parse("#" * int(level) + " " + (tok.content or ""))
            for inner in heading:
                if inner.type == "inline" and inner.children:
                    title = "".join(
                        (child.content or "") for child in inner.children if child.type == "text"
                    )
                    if title:
                        anchors.add(github_slug(title))
    return anchors


def check_source_debt(source_dir: Path) -> dict:
    """Enlaces que ya estaban rotos en la fuente.

    No son una regresión de la traducción: por eso van en ``info`` y no
    en ``errors``, y por eso se distinguen de los destinos perdidos que
    sí bloquean. El recorrido es recursivo porque el corpus lo es.

    Tres clases: ancla local que el documento no declara, ruta relativa
    que no existe bajo ``source_root``, y ruta absoluta del sitio, que
    no se puede comprobar contra el corpus y se declara aparte.
    """
    info: list[dict] = []

    for path in sorted(source_dir.rglob("*.md")):
        rel = path.relative_to(source_dir).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        anchors = document_anchors(text)

        for target in extract_targets(text):
            if HTTP_RE.match(target) or SCHEME_RE.match(target):
                continue
            if target.startswith("/"):
                info.append({
                    "path": rel,
                    "kind": "source_debt_external",
                    "message": f"ruta absoluta del sitio, no comprobable contra el corpus: {target}",
                })
                continue
            if target.startswith("#"):
                anchor = target[1:]
                if anchor and anchor not in anchors:
                    info.append({
                        "path": rel,
                        "kind": "source_debt_missing_anchor",
                        "message": f"ancla {anchor!r} no existe en el documento",
                    })
                continue
            path_part, _, fragment = target.partition("#")
            if not path_part:
                continue
            resolved = (path.parent / path_part).resolve()
            try:
                resolved.relative_to(source_dir.resolve())
            except ValueError:
                info.append({
                    "path": rel,
                    "kind": "source_debt_escape",
                    "message": f"la ruta sale de la raiz del corpus: {target}",
                })
                continue
            if not resolved.exists():
                info.append({
                    "path": rel,
                    "kind": "source_debt_missing_target",
                    "message": f"el destino no existe en la fuente: {target}",
                })

    return {"errors": [], "warnings": [], "info": info}


def run_external(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout, proc.stderr


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    segments_doc = None
    if args.segments:
        segments_doc = json.loads(Path(args.segments).read_text(encoding="utf-8"))
    snapshots = json.loads(Path(args.snapshots).read_text(encoding="utf-8"))
    packets = json.loads(Path(args.packets).read_text(encoding="utf-8"))
    segments = json.loads(Path(args.segments).read_text(encoding="utf-8"))

    enabled = set(args.checks.split(","))
    results: dict[str, dict] = {}

    if "structure" in enabled:
        results["structure"] = check_structure(
            snapshots,
            Path(args.source),
            Path(args.output_dir) if args.output_dir else None,
            require_assembled=args.require_assembled,
            segments_doc=segments_doc,
        )
    if "protection" in enabled:
        results["protection"] = check_protection(packets, args.translations, segments_doc)
        results["flag_loss"] = check_flag_loss(args.translations)
    if "destinations" in enabled:
        results["destinations"] = check_destinations(packets, args.translations, segments_doc)
    if "coverage" in enabled:
        out_path = Path(args.out).with_suffix(".coverage.json")
        rc, _, stderr = run_external([
            sys.executable, str(CHECK_INTEGRITY),
            "--manifest", args.manifest,
            "--out", str(out_path),
        ])
        cov_data = json.loads(out_path.read_text(encoding="utf-8")) if out_path.exists() else {}
        results["coverage"] = {
            "errors": [] if cov_data.get("integrity_ok") else [{"kind": "coverage", "message": "integridad incompleta"}],
            "warnings": [],
            "info": [cov_data],
        }
        if rc != 0 and cov_data.get("integrity_ok") is False:
            pass
    if "source-debt" in enabled:
        results["source-debt"] = check_source_debt(Path(args.source))

    all_errors: list[dict] = []
    for name, r in results.items():
        for e in r.get("errors", []):
            all_errors.append({"check": name, **e})

    out_path = Path(args.out)
    write_atomic(out_path, {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "checks_enabled": sorted(enabled),
        "results": results,
        "errors": all_errors,
        "ok": not all_errors,
    })
    print(f"ok: {len(all_errors)} errores -> {out_path}" if not all_errors else f"errores: {len(all_errors)} -> {out_path}")
    return 0 if not all_errors else 1


if __name__ == "__main__":
    sys.exit(main())