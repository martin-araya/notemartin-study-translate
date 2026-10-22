"""Aplica la secuencia de estados del contrato C-RUN (cierre de G-BETA).

El contrato fija el recorrido

    inventoried -> prepared -> translated -> deterministic_pass
                -> semantic_pass -> approved -> exported

y ninguna herramienta de la skill lo recorria entero: `approve_pilot.py`
saltaba de `translated` a `approved` y `export.py` no tocaba el
manifiesto, de modo que `deterministic_pass`, `semantic_pass` y `exported`
no se escribian nunca y el estado final era inalcanzable.

Este script es el unico que hace esas transiciones. No las inventa: solo
avanza archivos que estan en un estado cuyo sucesor legal es el pedido, y
deja constancia en `state_history` con su motivo.

    python3 scripts/advance_state.py \\
        --manifest manifest.json --to deterministic_pass \\
        --reason "validate.py sin errores" --out reports/state.json
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
from pathlib import Path


SEQUENCE = [
    "inventoried",
    "prepared",
    "translated",
    "deterministic_pass",
    "semantic_pass",
    "approved",
    "exported",
]

TERMINAL = {"exported", "blocked", "failed", "excluded", "already_target"}

LEGAL_NEXT = {
    "inventoried": {"prepared", "blocked", "failed", "excluded"},
    "prepared": {"translated", "blocked", "failed", "excluded"},
    "translated": {"deterministic_pass", "blocked", "failed"},
    "deterministic_pass": {"semantic_pass", "blocked", "failed"},
    "semantic_pass": {"approved", "blocked", "failed"},
    "approved": {"exported", "blocked", "failed"},
    "exported": set(),
    "blocked": set(),
    "failed": set(),
    "excluded": set(),
    "already_target": set(),
}

# Estados que afirman que alguien leyó el documento: exigen evidencia de
# revisión, y `approved` exige además una firma humana.
REVIEW_STATES = {"semantic_pass", "approved"}
SIGNOFF_STATES = {"approved"}

ACCEPTING_VERDICTS = {"accept"}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="advance_state.py")
    p.add_argument("--manifest", required=True)
    p.add_argument("--to", dest="to_state", required=True, choices=SEQUENCE + ["blocked", "failed", "excluded"])
    p.add_argument("--from", dest="from_state", default=None,
                   help="Estado que deben tener los archivos. Por defecto, cualquiera "
                        "cuyo sucesor legal sea el estado pedido.")
    p.add_argument("--reason", required=True)
    p.add_argument("--out", help="Reporte JSON de la transicion (opcional).")
    p.add_argument("--translations",
                   help="Directorio translations/<doc_id>.json. Cuando se pasa, solo "
                        "avanza a un estado de trabajo los documentos que tienen "
                        "traduccion persistida. Sin este flag no se comprueba evidencia.")
    p.add_argument("--segments",
                   help="segments.json del run. Da el denominador real de segmentos "
                        "traducibles por documento; sin el, la revision no se puede "
                        "medir.")
    p.add_argument("--review",
                   help="Ledger JSON de revision con una entrada por documento "
                        "(path, verdict, segments_reviewed, reviewed_at). Exigido para "
                        "avanzar a semantic_pass y approved.")
    p.add_argument("--apply", action="store_true",
                   help="Escribir el manifiesto. Sin este flag solo se informa.")
    return p.parse_args(argv)


def write_atomic(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def load_translatable_counts(segments_path: str | None) -> dict[str, int] | None:
    """Segmentos traducibles por ruta, leídos del archivo de segmentos.

    El denominador de la revisión sale de aquí y no del ledger: si el
    ledger declarara su propio total, un ledger vacío declararía cobertura
    completa y el gate dejaría de medir nada. `None` significa «no se
    comprobó».
    """
    if not segments_path:
        return None
    base = Path(segments_path)
    if not base.is_file():
        return {}
    try:
        payload = json.loads(base.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    counts: dict[str, int] = {}
    for record in payload.get("files", []):
        path = record.get("path")
        if not path:
            continue
        counts[path] = sum(
            1 for seg in record.get("segments", [])
            if seg.get("disposition") == "translatable"
        )
    return counts


def load_review_evidence(review_path: str | None) -> dict[str, dict]:
    """Entradas del ledger de revisión indexadas por ruta.

    Formato del ledger (fase 042, ``reviewer_role.py`` deja los veredictos
    vacíos y quien revisa los rellena)::

        {"reviews": [{"path": ..., "verdict": ...,
                      "segments_reviewed": N, "reviewed_at": ...}]}
    """
    if not review_path:
        return {}
    base = Path(review_path)
    if base.is_dir():
        payloads = []
        for candidate in sorted(base.glob("*.json")):
            try:
                payloads.append(json.loads(candidate.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError):
                continue
    elif base.is_file():
        try:
            payloads = [json.loads(base.read_text(encoding="utf-8"))]
        except (OSError, json.JSONDecodeError):
            payloads = []
    else:
        return {}

    evidence: dict[str, dict] = {}
    for payload in payloads:
        for entry in payload.get("reviews", []) or []:
            path = entry.get("path")
            if path:
                evidence[path] = entry
    return evidence


def review_covers(path: str, entry: dict | None, required: int) -> str | None:
    """Motivo por el que la revisión no cubre el documento, o ``None``."""
    if entry is None:
        return "sin entrada de revision"
    verdict = entry.get("verdict")
    if verdict not in ACCEPTING_VERDICTS:
        return f"verdict de revision {verdict!r} no acepta"
    if not entry.get("reviewed_at"):
        return "revision sin reviewed_at"
    reviewed = entry.get("segments_reviewed")
    if not isinstance(reviewed, int):
        return "segments_reviewed ausente o no entero"
    if reviewed < required:
        return f"revisados {reviewed} de {required} segmentos traducibles"
    return None


def scope_covers(scope, path: str) -> bool:
    """``global`` cubre todo; una lista cubre solo lo que nombra."""
    if scope == "global":
        return True
    return isinstance(scope, list) and path in scope


def human_signoff(manifest: dict, path: str) -> str | None:
    """Motivo por el que falta la firma humana, o ``None`` si existe.

    Exige las dos mitades del contrato de ``references/reviewer-policy.md``:
    una decisión ``approve`` con hashes revisados y un firmante
    ``kind: human``. Una revisión asistida (``kind: assisted``) cubre el
    pase de revisión, no la aprobación.
    """
    approved = None
    for decision in manifest.get("decisions", []) or []:
        if decision.get("kind") != "approve":
            continue
        if not decision.get("reviewed_hashes"):
            continue
        if scope_covers(decision.get("scope"), path):
            approved = decision
            break
    if approved is None:
        return "sin decision humana de tipo approve con reviewed_hashes que cubra la ruta"

    for signer in manifest.get("reviewers", []) or []:
        if signer.get("kind") == "human" and scope_covers(signer.get("scope"), path):
            return None
    return "sin firmante humano (reviewers[].kind == human) que cubra la ruta"


def select_files(manifest: dict, from_state: str | None, to_state: str,
                 evidence: set[str] | None = None,
                 review: dict[str, dict] | None = None,
                 counts: dict[str, int] | None = None,
                 signoff: dict[str, str | None] | None = None) -> tuple[list[dict], list[dict]]:
    selected: list[dict] = []
    rejected: list[dict] = []
    for record in manifest.get("files", []):
        current = record.get("current_state") or record.get("state") or "unknown"
        if from_state is not None:
            ok = current == from_state
        else:
            ok = to_state in LEGAL_NEXT.get(current, set())
        if ok and evidence is not None:
            # Un estado de la secuencia C-RUN afirma trabajo hecho. Sin
            # evidencia de que ese trabajo existe, avanzar es fabricar
            # progreso (INV-12). Se puede avanzar a un estado terminal
            # de descarte, que no afirma trabajo, sin evidencia.
            if to_state not in {"blocked", "failed", "excluded"}:
                doc_id = record.get("document_id")
                path = record.get("path")
                # Cualquiera de los tres identificadores basta: el de
                # contenido (``document_id``), el de persistencia
                # (``translation_id`` o stem) o la ruta. Los archivos
                # ambiguos persisten bajo ``trl-XYZ``, no bajo su
                # ``document_id``.
                if not any(key in evidence for key in (doc_id, path) if key):
                    ok = False
                    rejected.append({
                        "path": record.get("path"),
                        "document_id": doc_id,
                        "current_state": current,
                        "reason": f"sin evidencia para {to_state}",
                    })
                    continue
        if ok and to_state in REVIEW_STATES and review is not None:
            path = record.get("path")
            required = (counts or {}).get(path, 0)
            motivo = review_covers(path, (review or {}).get(path), required)
            if motivo is None and to_state in SIGNOFF_STATES and signoff is not None:
                motivo = signoff.get(path)
            if motivo is not None:
                ok = False
                rejected.append({
                    "path": path,
                    "document_id": record.get("document_id"),
                    "current_state": current,
                    "reason": motivo,
                })
                continue
        if ok:
            selected.append(record)
        else:
            rejected.append({
                "path": record.get("path"),
                "document_id": record.get("document_id"),
                "current_state": current,
            })
    return selected, rejected


def load_translation_evidence(translations_dir: str | None) -> set[str] | None:
    """Identificadores de archivos con traducción persistida en disco.

    Devuelve el **conjunto de claves** que representan un archivo con
    traducción: el nombre del archivo (``trl-XYZ`` o ``doc-XXX``), el
    ``document_id`` declarado en el payload, el ``translation_id`` y la
    ruta relativa. Cualquiera de ellos basta para considerar al
    documento como «con evidencia».

    El manifest ``file_record`` solo conoce ``document_id`` y ``path``.
    Antes este script buscaba por ``document_id`` y, para los archivos
    ambiguos cuya clave de persistencia es ``trl-XYZ``, no encontraba
    la evidencia sin motivo: el archivo de traducción existía y tenía
    entradas, pero ``advance_state`` lo declaraba «sin evidencia» y
    rechazaba avanzar. El bug estaba tapado por el hecho de que la
    única traducción entregada hasta ahora (``doc-f0342fb5``) no era
    ambigua.

    ``None`` significa «no se comprobó»: el script se comporta como
    antes, sin exigir evidencia.
    """
    if not translations_dir:
        return None
    base = Path(translations_dir)
    if not base.is_dir():
        # Quien invoca con ``--translations`` está afirmando que hay un
        # directorio de traducciones: si no existe, devolvemos vacío,
        # no «sin comprobar», para que el gate no avance sin evidencia.
        return set()
    evidence: set[str] = set()
    for path in base.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        entries = data.get("entries") or []
        if not entries:
            # Un archivo con ``entries: []`` no contiene traducción: el
            # nombre del archivo no es evidencia. Eso preserva el
            # contrato de «sin evidencia falsa»: declarar traducido
            # algo que sigue vacío sería fabricar progreso (INV-12).
            continue
        for key in (
            path.stem,
            data.get("document_id"),
            data.get("translation_id"),
            data.get("path"),
        ):
            if key:
                evidence.add(str(key))
    return evidence


def apply_transition(manifest: dict, records: list[dict], to_state: str, reason: str, now: str) -> None:
    for record in records:
        record["current_state"] = to_state
        record["state"] = to_state
        record["last_transition_at"] = now
        history = record.setdefault("state_history", [])
        history.append({"state": to_state, "timestamp": now, "reason": reason})


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest_path = Path(args.manifest)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if args.to_state in REVIEW_STATES:
        missing = []
        if not args.review:
            missing.append("--review")
        if not args.segments:
            missing.append("--segments")
        if missing:
            print(
                f"error: avanzar a {args.to_state} afirma que alguien leyo el documento; "
                f"hacen falta {', '.join(missing)}",
                file=sys.stderr,
            )
            print(
                "  --review: ledger con una entrada por documento (path, verdict, "
                "segments_reviewed, reviewed_at)",
                file=sys.stderr,
            )
            print(
                "  --segments: denominador real de segmentos traducibles; sin el, "
                "el ledger se declararia a si mismo completo",
                file=sys.stderr,
            )
            return 1
        if not Path(args.segments).is_file():
            print(f"error: --segments no existe: {args.segments}", file=sys.stderr)
            return 1

    evidence = load_translation_evidence(args.translations)
    counts = load_translatable_counts(args.segments) if args.to_state in REVIEW_STATES else None
    review = load_review_evidence(args.review) if args.to_state in REVIEW_STATES else None

    signoff = None
    if args.to_state in SIGNOFF_STATES:
        signoff = {
            record.get("path"): human_signoff(manifest, record.get("path"))
            for record in manifest.get("files", [])
        }

    selected, rejected = select_files(
        manifest, args.from_state, args.to_state, evidence,
        review=review, counts=counts, signoff=signoff,
    )
    if not selected:
        print(
            f"error: ningun archivo puede pasar a {args.to_state} desde "
            f"{args.from_state or 'cualquier estado'}",
            file=sys.stderr,
        )
        for entry in rejected[:10]:
            detail = f": {entry['reason']}" if entry.get("reason") else ""
            print(f"  {entry['path']}: {entry['current_state']}{detail}", file=sys.stderr)
        if len(rejected) > 10:
            print(f"  ... y {len(rejected) - 10} mas", file=sys.stderr)
        return 1

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    report = {
        "manifest": str(manifest_path),
        "from_state": args.from_state,
        "to_state": args.to_state,
        "reason": args.reason,
        "applied_at": now,
        "applied": args.apply,
        "transitioned": len(selected),
        "not_eligible": rejected,
        "paths": [r.get("path") for r in selected],
        "review_evidence": {
            "review_ledger": args.review,
            "segments": args.segments,
            "documents_reviewed": len(review or {}) if review is not None else None,
            "human_signoff_required": args.to_state in SIGNOFF_STATES,
        },
    }

    if args.apply:
        apply_transition(manifest, selected, args.to_state, args.reason, now)
        write_atomic(manifest_path, manifest)

    if args.out:
        write_atomic(Path(args.out), report)

    print(
        f"ok: {len(selected)} archivos -> {args.to_state}"
        f"{'' if args.apply else ' (sin escribir: falta --apply)'}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())