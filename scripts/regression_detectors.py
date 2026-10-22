"""Detectores del corpus permanente de regresión (fase 141).

Funciones puras. Cada una recibe las entradas compartidas de un fixture
(``case``) y una variante concreta (``positive`` o ``negative``) y devuelve
``{"detected": bool, "findings": [...]}``.

Ninguna función escribe en disco, ejecuta el corpus ni invoca al agente.
Cuando existe una implementación real en otro script del proyecto, el
detector **delega** en ella en lugar de reimplementarla:

- slugs de anclas: ``scripts/build_anchors.py::github_slug``
- vigencia de aprobaciones: ``scripts/approval_freshness.py::evaluate``
  (núcleo; ``check_approval_freshness.py`` es su interfaz de fase 124)
- rutas inseguras de un paquete: ``scripts/validate_zip_package.py::is_unsafe_path``
- pérdida de contenido en entrega: ``scripts/compare_delivery.py::compare_documents``
- clave compuesta de caché: ``scripts/translation_cache.py::key_short``

Las tres últimas delegan en un módulo opcional a propósito: el corpus
permanente de regresión cubre los fallos de todos los módulos y detector
debe ser la implementación de producción, no una copia. Esa delegación
está declarada en ``modules.json`` (``core_delegations``) y el gate G-EXT
la comprueba. No ocurre durante una ejecución de traducción.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from build_anchors import github_slug  # noqa: E402
from approval_freshness import evaluate as evaluate_approval_freshness  # noqa: E402
from compare_delivery import compare_documents  # noqa: E402
from delivery_common import iter_links  # noqa: E402
from translation_cache import key_short  # noqa: E402
from validate_zip_package import is_unsafe_path  # noqa: E402

FENCE_RE = re.compile(r"^\s*(```|~~~)")
LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\S")
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")
MARKER_RE = re.compile(r"§L(\d+)§")

ACTIVE_HTML_RE = re.compile(
    r"<\s*(script|iframe|object|embed)\b|\bon[a-z]+\s*=", re.IGNORECASE
)
UNSAFE_SCHEMES = ("javascript:", "data:", "file:", "vbscript:")

INJECTION_PATTERNS = (
    r"ignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions",
    r"disregard\s+(?:all\s+)?(?:previous|prior|above)",
    r"you\s+must\s+(?:run|execute|delete|ignore)",
    r"system\s+prompt",
    r"ignora\s+(?:todas\s+)?las\s+instrucciones",
    r"instrucciones\s+para\s+el\s+agente",
)

NEGATION_MARKERS = (
    "must not", "do not", "don't", "never", "cannot", "can't", "without",
    "no debe", "nunca", "jamás", "no se", "no puede", "sin ",
)


# --------------------------------------------------------------------------
# utilidades de extracción
# --------------------------------------------------------------------------

def _without_fenced(text: str) -> str:
    """Devuelve el texto con el contenido de los bloques de código vacío."""
    out: list[str] = []
    in_fence = False
    token = ""
    for line in text.splitlines():
        m = FENCE_RE.match(line)
        if m:
            if not in_fence:
                in_fence, token = True, m.group(1)
            elif m.group(1) == token:
                in_fence = False
            out.append("")
            continue
        out.append("" if in_fence else line)
    return "\n".join(out)


def _fenced_blocks(text: str) -> list[str]:
    """Contenido interior de cada bloque fenced."""
    blocks: list[str] = []
    current: list[str] | None = None
    token = ""
    for line in text.splitlines():
        m = FENCE_RE.match(line)
        if m:
            if current is None:
                current, token = [], m.group(1)
            elif m.group(1) == token:
                blocks.append("\n".join(current).strip("\n"))
                current = None
            continue
        if current is not None:
            current.append(line)
    if current is not None:
        blocks.append("\n".join(current).strip("\n"))
    return [b for b in blocks if b.strip()]


def _code_literals(text: str) -> list[str]:
    """Literales protegidos: bloques fenced y código inline."""
    literals = list(_fenced_blocks(text))
    prose = _without_fenced(text)
    literals.extend(m.group(0) for m in INLINE_CODE_RE.finditer(prose))
    return literals


def _list_items(text: str) -> int:
    return sum(1 for line in _without_fenced(text).splitlines() if LIST_ITEM_RE.match(line))


def _table_shape(text: str) -> list[tuple[int, int]]:
    """(filas, columnas) por cada bloque de tabla GFM, sin la fila separadora."""
    shapes: list[tuple[int, int]] = []
    rows: list[tuple[int, int]] = []
    for line in _without_fenced(text).splitlines():
        if TABLE_ROW_RE.match(line):
            cells = len([c for c in line.strip().strip("|").split("|")])
            is_separator = all(
                set(c.strip()) <= set("-: ") and c.strip() for c in line.strip().strip("|").split("|")
            )
            rows.append((cells, 1 if is_separator else 0))
            continue
        if rows:
            shapes.append(_finish_table(rows))
            rows = []
    if rows:
        shapes.append(_finish_table(rows))
    return shapes


def _finish_table(rows: list[tuple[int, int]]) -> tuple[int, int]:
    data_rows = [cells for cells, is_sep in rows if not is_sep]
    columns = max(data_rows, default=0)
    return (len(data_rows), columns)


def _negations(text: str) -> int:
    lowered = text.lower()
    return sum(lowered.count(marker) for marker in NEGATION_MARKERS)


def _result(findings: list[str]) -> dict:
    return {"detected": bool(findings), "findings": findings}


# --------------------------------------------------------------------------
# detectores
# --------------------------------------------------------------------------

def negation_preserved(case: dict, variant: dict) -> dict:
    source_count = _negations(case["source"])
    candidate_count = _negations(variant["text"])
    findings = []
    if candidate_count < source_count:
        findings.append(
            f"negación perdida: la fuente declara {source_count} y el candidato {candidate_count}"
        )
    return _result(findings)


def structure_preserved(case: dict, variant: dict) -> dict:
    source, text = case["source"], variant["text"]
    findings = []
    src_items, cand_items = _list_items(source), _list_items(text)
    if cand_items < src_items:
        findings.append(f"elementos de lista perdidos: {src_items} -> {cand_items}")
    src_headings = [m.group(2) for m in map(HEADING_RE.match, source.splitlines()) if m]
    cand_headings = [m.group(2) for m in map(HEADING_RE.match, text.splitlines()) if m]
    if len(cand_headings) < len(src_headings):
        findings.append(f"encabezados perdidos: {len(src_headings)} -> {len(cand_headings)}")
    src_tables, cand_tables = _table_shape(source), _table_shape(text)
    if cand_tables != src_tables:
        findings.append(f"tabla alterada: {src_tables} -> {cand_tables}")
    return _result(findings)


def literals_preserved(case: dict, variant: dict) -> dict:
    text = variant["text"]
    findings = [
        f"literal protegido ausente del candidato: {literal!r}"
        for literal in _code_literals(case["source"])
        if literal not in text
    ]
    return _result(findings)


def injected_instructions(case: dict, variant: dict) -> dict:
    prose = _without_fenced(variant["document"]).lower()
    findings = [
        f"instrucción incrustada detectada: {pattern}"
        for pattern in INJECTION_PATTERNS
        if re.search(pattern, prose)
    ]
    return _result(findings)


def unsafe_link_target(case: dict, variant: dict) -> dict:
    findings = [
        f"destino de enlace con esquema activo: {target}"
        for _is_image, _label, target in iter_links(variant["document"])
        if target.lower().startswith(UNSAFE_SCHEMES)
    ]
    return _result(findings)


def path_escapes_root(case: dict, variant: dict) -> dict:
    findings = []
    for path in variant["paths"]:
        pure = path.replace("\\", "/")
        if pure.startswith("/"):
            findings.append(f"ruta absoluta fuera de la raíz: {path}")
        elif ".." in pure.split("/"):
            findings.append(f"ruta que escapa de la raíz: {path}")
    return _result(findings)


def active_html_outside_code(case: dict, variant: dict) -> dict:
    prose = _without_fenced(variant["document"])
    findings = [match.group(0) for match in ACTIVE_HTML_RE.finditer(prose)]
    return _result(findings)


def slug_collision(case: dict, variant: dict) -> dict:
    seen: dict[str, str] = {}
    findings = []
    for heading in variant["headings"]:
        slug = github_slug(heading)
        if slug in seen:
            findings.append(f"slug duplicado {slug!r} en {seen[slug]!r} y {heading!r}")
        else:
            seen[slug] = heading
    return _result(findings)


def slug_truncated(case: dict, variant: dict) -> dict:
    limit = int(case.get("slug_limit", 256))
    slug = github_slug(variant["heading"])
    findings = []
    if len(slug) >= limit:
        findings.append(f"slug truncado al límite {limit}: longitud {len(slug)}")
    return _result(findings)


def fragment_resolution(case: dict, variant: dict) -> dict:
    fragment = variant["fragment"].lstrip("#")
    matches = [h for h in variant["headings"] if github_slug(h) == fragment]
    findings = []
    if len(matches) != 1:
        findings.append(
            f"el fragmento {variant['fragment']!r} resuelve contra {len(matches)} encabezados"
        )
    return _result(findings)


def segment_ids_known(case: dict, variant: dict) -> dict:
    known = set(case["segments"])
    findings = [
        f"segment_id ajeno al paquete: {sid}"
        for sid in sorted(set(variant["translations"]) - known)
    ]
    return _result(findings)


def markers_wellformed(case: dict, variant: dict) -> dict:
    expected = case["expected_markers"]
    found_markers = [f"§L{n}§" for n in MARKER_RE.findall(variant["text"])]
    findings = []
    missing = [m for m in expected if m not in found_markers]
    extra = [m for m in found_markers if m not in expected]
    duplicated = sorted({m for m in found_markers if found_markers.count(m) > 1})
    if missing:
        findings.append(f"marcadores ausentes: {missing}")
    if extra:
        findings.append(f"marcadores no declarados: {extra}")
    if duplicated:
        findings.append(f"marcadores duplicados: {duplicated}")
    return _result(findings)


def all_segments_present(case: dict, variant: dict) -> dict:
    expected = set(case["expected_segments"])
    present = set(variant["translations"])
    findings = [f"segmento ausente en la respuesta: {sid}" for sid in sorted(expected - present)]
    return _result(findings)


def cache_probe_compatible(case: dict, variant: dict) -> dict:
    probe = variant["probe"]
    findings = []
    for entry in case["entries"]:
        same_partial = all(
            entry.get(field) == probe.get(field)
            for field in ("segment_id", "source_hash", "locale_variant")
        )
        if same_partial and entry.get("glossary_hash") != probe.get("glossary_hash"):
            findings.append(
                "reutilización con glosario incompatible: "
                f"entrada {key_short(entry['segment_id'], entry['source_hash'], entry['glossary_hash'], entry['locale_variant'])} "
                f"frente a búsqueda {key_short(probe['segment_id'], probe['source_hash'], probe['glossary_hash'], probe['locale_variant'])}"
            )
    return _result(findings)


def cache_invalidated(case: dict, variant: dict) -> dict:
    current = case["current_glossary_hash"]
    findings = [
        f"entrada con glosario obsoleto: {entry['segment_id']} -> {entry['glossary_hash']}"
        for entry in variant["entries"]
        if entry.get("glossary_hash") != current
    ]
    return _result(findings)


def approval_fresh(case: dict, variant: dict) -> dict:
    manifest = dict(case["manifest"])
    manifest["approvals"] = [variant["approval"]]
    report = evaluate_approval_freshness(manifest, {})
    findings = [
        f"aprobación obsoleta {a['approval_id']}: {a['reasons']}"
        for a in report["approvals"]
        if a["status"] == "stale"
    ]
    return _result(findings)


def package_members_declared(case: dict, variant: dict) -> dict:
    declared = set(case["declared_members"])
    scope = set(case["manifest_scope"])
    findings = []
    for member in variant["members"]:
        if member not in declared:
            findings.append(f"miembro no declarado en el paquete: {member}")
        elif member not in scope:
            findings.append(f"miembro fuera del alcance aprobado: {member}")
    return _result(findings)


def package_member_safe(case: dict, variant: dict) -> dict:
    findings = []
    for member in variant["members"]:
        reason = is_unsafe_path(member)
        if reason:
            findings.append(f"miembro inseguro {member!r}: {reason}")
    return _result(findings)


def delivery_loss(case: dict, variant: dict) -> dict:
    differences = compare_documents(
        variant["canonical"], variant["adapted"], case.get("document", "docs/a.md")
    )
    findings = [
        f"pérdida de contenido en {d['aspect']}"
        for d in differences
        if d.get("classification") == "content_loss"
    ]
    return _result(findings)


def export_state_allowed(case: dict, variant: dict) -> dict:
    states = {f["path"]: f["current_state"] for f in case["manifest"]["files"]}
    findings = [
        f"exportado sin aprobación: {path} está en {states.get(path, 'desconocido')}"
        for path in variant["exported"]
        if states.get(path) != "approved"
    ]
    return _result(findings)


def case_insensitive_collision(case: dict, variant: dict) -> dict:
    seen: dict[str, str] = {}
    findings = []
    for path in variant["paths"]:
        lowered = path.lower()
        if lowered in seen:
            findings.append(f"colisión por mayúsculas: {seen[lowered]!r} y {path!r}")
        else:
            seen[lowered] = path
    return _result(findings)


DETECTORS: dict[str, Callable[[dict, dict], dict]] = {
    "negation_inverted": negation_preserved,
    "list_omission": structure_preserved,
    "command_altered": literals_preserved,
    "table_trimmed": structure_preserved,
    "prompt_injection": injected_instructions,
    "dangerous_links": unsafe_link_target,
    "path_traversal": path_escapes_root,
    "script_block": active_html_outside_code,
    "anchor_collision": slug_collision,
    "slug_truncation": slug_truncated,
    "ambiguous_link": fragment_resolution,
    "foreign_segment_id": segment_ids_known,
    "extra_marker": markers_wellformed,
    "truncated_response": all_segments_present,
    "cache_incompatible_reuse": cache_probe_compatible,
    "stale_cache_on_glossary_change": cache_invalidated,
    "stale_approval": approval_fresh,
    "package_member_not_declared": package_members_declared,
    "package_path_escape": package_member_safe,
    "delivery_content_loss": delivery_loss,
    "export_without_approval": export_state_allowed,
    "route_collision_case_only": case_insensitive_collision,
}


def detect(known_failure: str, case: dict, variant: dict) -> dict:
    """Ejecuta el detector de ``known_failure`` sobre una variante."""
    detector = DETECTORS.get(known_failure)
    if detector is None:
        return {"detected": True, "findings": [f"no hay detector para {known_failure}"]}
    return detector(case, variant)