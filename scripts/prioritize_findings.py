"""Vista estática con priorización de hallazgos (fase 122).

Consume un ``manifest.json`` y opcionalmente un
``semantic_pass.json`` y produce un Markdown en cuatro secciones
independientes:

1. **Gate pendiente**: cualquier archivo con ``current_state`` en
   {blocked, failed, gate_pending} o cualquier hallazgo
   ``severity == error`` con ``flags.gate_blocking == True``.
   Esta sección **nunca** se oculta, aunque la priorización de
   riesgos coloque un hallazgo en una sección posterior.
2. **Riesgo alto**: hallazgos con categoría que afecta a
   obligatoriedad, negación, cuantificadores, MUST/SHOULD/MAY o
   causalidad.
3. **Riesgo medio**: supresiones, omisiones parciales, listas
   reordenadas, versiones alteradas.
4. **Riesgo bajo**: typos, estilo, puntuación localizada.

Fórmula de prioridad (orden estable entre ejecuciones):

    score = (-severity_norm, evidence_strength, -scope_impact, segment_id)

severity_norm := {'error': 3, 'warning': 2, 'info': 1}[severity]
evidence_strength := número de hallazgos correlacionados (1 por defecto)
scope_impact := 1 si la ruta es global/sin ruta, 0.5 si afecta a una
ruta completa, 0.25 si afecta a un único segmento.

El script nunca modifica ni translations/ ni work_root/.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

HIGH_RISK_CATEGORIES = {
    "negation_invertida",
    "negation_dropped",
    "must_should_may_inversion",
    "obligation_softened",
    "quantifier_changed",
    "version_changed",
    "causalidade_alterada",
    "url_external_changed",
}

MEDIUM_RISK_CATEGORIES = {
    "list_reordered",
    "list_truncated",
    "code_literal_soft_rewrite",
    "adjacent_paragraph_merged",
    "heading_reorder",
    "subject_swapped",
    "version_reference_lost",
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="prioritize_findings.py")
    p.add_argument("--manifest", required=True, help="manifest.json de la ejecución.")
    p.add_argument("--semantic", help="semantic_pass.json (opcional).")
    p.add_argument("--out", required=True, help="Markdown de salida.")
    p.add_argument(
        "--mode",
        choices=["include_gate", "review"],
        default="include_gate",
        help="Modo de la vista. include_gate siempre expone el gate pendiente; review prioriza por riesgo.",
    )
    return p.parse_args(argv)


def _severity_norm(severity: str) -> int:
    return {"error": 3, "warning": 2, "info": 1, "critical": 3}.get(severity.lower(), 0)


def _classify_risk(category: str | None) -> str:
    if not category:
        return "low"
    if category in HIGH_RISK_CATEGORIES:
        return "high"
    if category in MEDIUM_RISK_CATEGORIES:
        return "medium"
    return "low"


def _scope_impact(item: dict) -> float:
    path = item.get("path")
    scope = item.get("scope")
    if scope == "global" or path is None:
        return 1.0
    if path.endswith(".md"):
        return 0.5
    return 0.25


def _is_gate_pending(file_record: dict) -> bool:
    state = (file_record.get("current_state") or "").lower()
    if state in {"blocked", "failed", "gate_pending"}:
        return True
    for issue in file_record.get("issues") or []:
        if (issue.get("severity") or "").lower() == "error":
            return True
    return False


def _collect_gate_pending(manifest: dict) -> list[dict]:
    items: list[dict] = []
    for f in manifest.get("files") or []:
        if not _is_gate_pending(f):
            continue
        state = (f.get("current_state") or "").lower()
        items.append(
            {
                "category": "gate_pending",
                "severity": "error",
                "path": f.get("path"),
                "segment_id": None,
                "state": state,
                "message": f"archivo en estado {state}" if state else "archivo en estado gate-pending",
                "score": (3, 1, 1.0, f.get("path") or ""),
            }
        )
    items.sort(key=lambda x: x["score"])
    return items


def _collect_semantic(manifest: dict, semantic: dict | None) -> list[dict]:
    rows: list[dict] = []
    for s in (semantic or {}).get("findings") or []:
        seg_id = s.get("segment_id") or ""
        path = s.get("path") or ""
        cat = s.get("category") or s.get("dimension") or "unknown"
        rows.append(
            {
                "category": cat,
                "severity": s.get("severity") or "info",
                "path": path,
                "segment_id": seg_id,
                "message": s.get("message") or "",
                "score": (
                    -(_severity_norm(s.get("severity") or "info")),
                    _scope_impact({"scope": "segment", "path": path}),
                    -1.0,
                    seg_id,
                ),
            }
        )
    return rows


def _collect_issues(manifest: dict) -> list[dict]:
    rows: list[dict] = []
    for f in manifest.get("files") or []:
        path = f.get("path")
        for issue in f.get("issues") or []:
            seg_id = issue.get("segment_id")
            rows.append(
                {
                    "category": issue.get("category") or "uncategorized",
                    "severity": issue.get("severity") or "info",
                    "path": path,
                    "segment_id": seg_id,
                    "message": issue.get("message") or "",
                    "score": (
                        -(_severity_norm(issue.get("severity") or "info")),
                        _scope_impact({"scope": "segment", "path": path}),
                        -1.0,
                        seg_id or "",
                    ),
                }
            )
    return rows


def _classify(items: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {"gate": [], "high": [], "medium": [], "low": []}
    for it in items:
        cat = it.get("category")
        if cat == "gate_pending":
            out["gate"].append(it)
            continue
        risk = _classify_risk(cat)
        out[risk].append(it)
    for k in out:
        out[k].sort(key=lambda x: (x["score"][0], x["score"][1], x["score"][2], x["score"][3]))
    return out


def _format_section(title: str, items: list[dict], footer: str) -> str:
    lines = [f"## {title}", ""]
    if not items:
        lines.append("_(sin hallazgos)_")
        lines.append("")
        return "\n".join(lines)
    lines.append("| # | categoría | severidad | path | segment_id | mensaje |")
    lines.append("|---|---|---|---|---|---|")
    for idx, it in enumerate(items, start=1):
        lines.append(
            f"| {idx} | {_cell(it.get('category'))} | {_cell(it.get('severity'))} | `{_cell(it.get('path') or '_')}` | {_cell(it.get('segment_id') or '_')} | {_cell(it.get('message'))} |"
        )
    lines.append("")
    lines.append(footer)
    lines.append("")
    return "\n".join(lines)


def _cell(text: str) -> str:
    if not text:
        return "_(vacío)_"
    return str(text).replace("\\", "\\\\").replace("|", "\\|").replace("\n", "<br>")


def render(manifest: dict, semantic: dict | None, mode: str = "include_gate") -> str:
    gate = _collect_gate_pending(manifest)
    semantic_items = _collect_semantic(manifest, semantic)
    issue_items = _collect_issues(manifest)
    all_items = gate + semantic_items + issue_items
    grouped = _classify(all_items)
    out: list[str] = []
    out.append("# Vista estática con priorización")
    out.append("")
    counts = Counter({k: len(v) for k, v in grouped.items()})
    out.append(f"Resumen: gate={counts['gate']} alto={counts['high']} medio={counts['medium']} bajo={counts['low']}.")
    out.append("")
    out.append(
        "Esta vista **nunca oculta** los hallazgos del gate obligatorio. La prioridad ordena el resto sin filtrarlos."
    )
    out.append("")
    out.append(_format_section(
        "Gate pendiente (bloqueante)",
        grouped["gate"],
        "Revisa primero esta sección: cualquier archivo listado bloquea la aprobación de su archivo o del corpus.",
    ))
    out.append(_format_section(
        "Riesgo alto (afecta obligatoriedad)",
        grouped["high"],
        "Resuelve antes de liberar el pase semántico.",
    ))
    out.append(_format_section(
        "Riesgo medio",
        grouped["medium"],
        "Agrupados por severidad. Corrige antes del export local.",
    ))
    out.append(_format_section(
        "Riesgo bajo",
        grouped["low"],
        "Estilo y consistencia. No bloquean el gate.",
    ))
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    semantic = None
    if args.semantic:
        semantic = json.loads(Path(args.semantic).read_text(encoding="utf-8"))
    body = render(manifest, semantic, args.mode)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(body, encoding="utf-8")
    print(
        f"ok: {len(body.splitlines())} lineas -> {out}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
