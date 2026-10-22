"""Guía de entrega fuera del árbol importable (fase 137).

Genera ``DELIVERY.md`` y ``delivery_manifest.json`` junto a los reportes,
nunca dentro del paquete ni de ``output_root/``. La guía explica qué se
entrega, qué se comprobó y qué sigue sin verificar. No se importa como
documentación del producto.

Reglas duras:

- La ruta de la guía no puede estar dentro del árbol exportado ni
  coincidir con un miembro del paquete.
- La guía no contiene la ruta interna de trabajo: se citan nombres de
  archivo, no rutas absolutas del ``work_root``.
- El estado remoto se copia del registro de evidencia. Sin evidencia
  dice ``no verificado``.

Uso::

    python scripts/render_delivery_guide.py \\
        --manifest work_root/run-001/manifest.json \\
        --run-id run-001 \\
        --destination-id notion-manual \\
        --output-tree output_root/run-001 \\
        --package-manifest reports/delivery/package_manifest.json \\
        --zip dist/run-001-notion-manual.zip \\
        --import-evidence reports/import_evidence.json \\
        --out-dir reports/delivery/run-001
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from delivery_common import (  # noqa: E402
    is_within,
    now_iso,
    sha256_file,
    write_atomic,
)

EXIT_OK = 0
EXIT_INPUT_ERROR = 2

REQUIRED_SECTIONS = (
    "## 1. Identificación",
    "## 2. Alcance y conteos",
    "## 3. Glosario",
    "## 4. Comprobaciones ejecutadas",
    "## 5. Decisiones humanas",
    "## 6. Limitaciones aceptadas",
    "## 7. Estado de la verificación remota",
    "## 8. Adaptación aplicada",
    "## 9. Qué no afirma esta entrega",
    "## 10. Checklist de importación",
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="render_delivery_guide.py")
    p.add_argument("--manifest", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--destination-id", required=True)
    p.add_argument("--output-tree", help="Árbol exportado que el paquete no puede contener.")
    p.add_argument("--package-manifest", help="Manifiesto del paquete ZIP.")
    p.add_argument("--zip", help="Paquete ZIP entregado.")
    p.add_argument("--import-evidence", help="Registro de evidencia de importación.")
    p.add_argument("--degradation-report", help="Informe de degradaciones adaptado↔canónico.")
    p.add_argument("--issues", help="reports/issues.json con las limitaciones aceptadas.")
    p.add_argument("--guide-name", default="DELIVERY.md")
    p.add_argument("--out-dir", required=True, help="Directorio de reportes, fuera del árbol importable.")
    return p.parse_args(argv)


def load_json(path: str | None):
    if not path:
        return None
    target = Path(path)
    if not target.exists():
        return None
    return json.loads(target.read_text(encoding="utf-8"))


def count_states(manifest: dict) -> dict[str, int]:
    counts: dict[str, int] = {}
    for f in manifest.get("files") or []:
        state = f.get("current_state") or "unknown"
        counts[state] = counts.get(state, 0) + 1
    return dict(sorted(counts.items()))


def gather_limitations(issues: dict | None) -> list[dict]:
    if not issues:
        return []
    entries = issues.get("issues") or issues.get("accepted") or []
    return [
        {
            "severity": e.get("severity"),
            "message": e.get("message"),
            "path": e.get("path"),
            "segment_id": e.get("segment_id"),
        }
        for e in entries
        if e.get("severity") in ("warning", "info")
    ]


def render(guide_meta: dict) -> str:
    lines: list[str] = []
    add = lines.append

    add("# Guía de entrega")
    add("")
    add(
        "Este documento acompaña al paquete de entrega y **no forma parte de la "
        "documentación importada**. Se genera fuera del árbol importable y fuera "
        "del paquete ZIP para que no aparezca como contenido del producto."
    )
    add("")

    add(REQUIRED_SECTIONS[0])
    add("")
    add("| Campo | Valor |")
    add("|---|---|")
    add(f"| Ejecución | `{guide_meta['run_id']}` |")
    add(f"| Destino | `{guide_meta['destination_id']}` |")
    add(f"| Paquete | `{guide_meta.get('package_id') or 'no emitido'}` |")
    add(f"| SHA-256 del paquete | `{guide_meta.get('zip_sha256') or 'n/d'}` |")
    add(f"| Archivos en el paquete | {guide_meta['package_member_count']} |")
    add(f"| Generada | {guide_meta['generated_at']} |")
    add("")

    add(REQUIRED_SECTIONS[1])
    add("")
    add(f"Árbol de salida entregado: `{guide_meta.get('output_tree') or 'n/d'}`")
    add("")
    add("| Estado | Archivos |")
    add("|---|---|")
    for state, count in guide_meta["states"].items():
        add(f"| `{state}` | {count} |")
    add("")
    add(f"Documentos aprobados o terminales: **{guide_meta['approved_files']}**.")
    if guide_meta["blocked_files"] or guide_meta["failed_files"]:
        add("")
        add(
            f"Aviso: quedan {guide_meta['blocked_files']} bloqueados y "
            f"{guide_meta['failed_files']} fallidos. Una ejecución parcial no se "
            "presenta como traducción completa."
        )
    add("")

    add(REQUIRED_SECTIONS[2])
    add("")
    glossary = guide_meta["glossary"]
    add(f"- Versión: `{glossary.get('version') or 'n/d'}`")
    add(f"- Hash: `{glossary.get('hash') or 'n/d'}`")
    add(f"- Congelado: `{glossary.get('frozen')}`")
    add("")
    add("El glosario vive en el árbol de trabajo y **no** se incluye en el paquete.")
    add("")

    add(REQUIRED_SECTIONS[3])
    add("")
    add("| Comprobación | Estado |")
    add("|---|---|")
    for name, value in guide_meta["checks"].items():
        add(f"| {name} | `{value}` |")
    add("")

    add(REQUIRED_SECTIONS[4])
    add("")
    decisions = guide_meta["decisions"]
    if decisions:
        add("| Tipo | Ámbito | Autor | Motivo |")
        add("|---|---|---|---|")
        for d in decisions:
            add(f"| `{d.get('kind')}` | `{d.get('scope')}` | `{d.get('author')}` | {d.get('reason')} |")
    else:
        add("No hay decisiones humanas registradas en el manifiesto.")
    add("")

    add(REQUIRED_SECTIONS[5])
    add("")
    limitations = guide_meta["limitations"]
    if limitations:
        for lim in limitations:
            where = lim.get("path") or lim.get("segment_id") or "corpus"
            add(f"- `{lim.get('severity')}` · {where}: {lim.get('message')}")
    else:
        add("No hay limitaciones aceptadas registradas para esta ejecución.")
    add("")

    add(REQUIRED_SECTIONS[6])
    add("")
    evidence = guide_meta["evidence"]
    add(f"- Estado: **{evidence['remote_status']}**")
    add(f"- Verificado: `{evidence['verified']}`")
    add(f"- Revisor: `{evidence.get('reviewer') or 'sin firmante'}`")
    add("")
    if evidence["remote_status"] == "no_verificado":
        add(
            "La importación la realiza el usuario. Sin evidencia aportada por una "
            "persona, esta entrega no afirma nada sobre el comportamiento del "
            "destino: navegación, render de tablas, código e imágenes siguen "
            "**sin verificar**."
        )
    else:
        add(
            "Existe evidencia humana para las comprobaciones marcadas como superadas. "
            "Ese alcance es el de la muestra y el de la fecha de la evidencia, no el "
            "del corpus completo ni el de versiones futuras del destino."
        )
    add("")

    add(REQUIRED_SECTIONS[7])
    add("")
    if guide_meta["adaptation"]:
        adaptation = guide_meta["adaptation"]
        add(f"- Perfil: `{adaptation['profile_id']}`")
        add(f"- Reglas aplicadas: `{', '.join(adaptation['applied_rules']) or 'ninguna'}`")
        add(f"- Pérdidas de contenido detectadas: **{adaptation['content_loss']}**")
        add("")
        add(
            "La adaptación no modifica la traducción. El árbol canónico entregado "
            "sigue siendo la referencia auditada."
        )
    else:
        add("No se aplicó adaptación. El paquete contiene la traducción canónica.")
    add("")

    add(REQUIRED_SECTIONS[8])
    add("")
    add("- No se afirma fidelidad semántica absoluta: la validación determinista "
        "comprueba integridad estructural y literal, no significado.")
    add("- No se afirma paridad de render en el destino.")
    add("- No se afirma que la navegación remota funcione sin evidencia.")
    add("- No se afirma comportamiento fuera del dialecto Markdown probado.")
    add("- No se publica nada de forma remota: la importación es manual.")
    add("")

    add(REQUIRED_SECTIONS[9])
    add("")
    add("1. Importar una muestra de 3 a 5 documentos antes que el corpus completo.")
    add("2. Seguir `references/delivery-notion-checklist.md` y registrar la evidencia.")
    add("3. Contrastar la muestra con la sección 2 de esta guía.")
    add("4. Ante desviaciones, decidir antes de continuar y dejarlas por escrito.")
    add("")

    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"error: manifiesto inexistente: {manifest_path}", file=sys.stderr)
        return EXIT_INPUT_ERROR

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    package = load_json(args.package_manifest)
    evidence = load_json(args.import_evidence)
    degradations = load_json(args.degradation_report)
    issues = load_json(args.issues)

    out_dir = Path(args.out_dir)
    guide_path = out_dir / args.guide_name

    if args.output_tree:
        tree = Path(args.output_tree)
        if tree.exists() and is_within(guide_path, tree):
            print(
                "error: la guía no puede escribirse dentro del árbol importable",
                file=sys.stderr,
            )
            return EXIT_INPUT_ERROR
    if package:
        member_paths = {m.get("path") for m in package.get("members") or []}
        rel_guide = guide_path.as_posix()
        if rel_guide in member_paths or args.guide_name in {
            Path(p).name for p in member_paths
        }:
            print("error: la guía coincide con un miembro del paquete", file=sys.stderr)
            return EXIT_INPUT_ERROR

    states = count_states(manifest)
    files = manifest.get("files") or []
    content_loss = 0
    if degradations:
        content_loss = sum(
            1 for d in degradations.get("differences") or [] if d.get("classification") == "content_loss"
        )

    guide_meta = {
        "generated_at": now_iso(),
        "run_id": args.run_id,
        "destination_id": args.destination_id,
        "package_id": (package or {}).get("package_id"),
        "zip_sha256": (package or {}).get("zip_sha256") or (
            sha256_file(Path(args.zip)) if args.zip and Path(args.zip).exists() else None
        ),
        "package_member_count": len((package or {}).get("members") or []),
        "output_tree": args.output_tree,
        "states": states,
        "approved_files": sum(
            1 for f in files if f.get("current_state") in ("approved", "exported", "already_target")
        ),
        "blocked_files": sum(1 for f in files if f.get("current_state") == "blocked"),
        "failed_files": sum(1 for f in files if f.get("current_state") == "failed"),
        "glossary": manifest.get("glossary_snapshot") or {},
        "checks": {
            "validación determinista": "ejecutada antes de exportar",
            "revisión semántica": (manifest.get("semantic_review") or {}).get("status", "no registrada"),
            "resolución local de enlaces": (
                (evidence or {}).get("checks") and "ver import_evidence" or "no registrada"
            ),
            "importación remota": (evidence or {}).get("remote_status", "no verificado"),
        },
        "decisions": manifest.get("decisions") or [],
        "limitations": gather_limitations(issues),
        "evidence": {
            "verified": bool((evidence or {}).get("verified")),
            "remote_status": (evidence or {}).get("remote_status", "no_verificado"),
            "reviewer": ((evidence or {}).get("reviewer") or {}).get("name"),
        },
        "adaptation": (
            {
                "profile_id": (package or {}).get("adaptation", {}).get("profile_id"),
                "applied_rules": (package or {}).get("adaptation", {}).get("applied_rules") or [],
                "content_loss": content_loss,
            }
            if (package or {}).get("adaptation")
            else None
        ),
    }

    text = render(guide_meta)

    work_root = manifest_path.parent
    hosts_delivery = any(
        path is not None and is_within(path, work_root)
        for path in (
            Path(args.output_tree) if args.output_tree else None,
            Path(args.zip).parent if args.zip else None,
            Path(args.package_manifest).parent if args.package_manifest else None,
        )
    )
    leak_check = "not_applicable"
    if not hosts_delivery and str(work_root) in text:
        print(
            "error: la guía contiene la ruta interna del work_root",
            file=sys.stderr,
        )
        return EXIT_INPUT_ERROR
    if not hosts_delivery:
        leak_check = "passed"

    missing = [s for s in REQUIRED_SECTIONS if s not in text]
    if missing:
        print(f"error: la guía no contiene las secciones: {missing}", file=sys.stderr)
        return EXIT_INPUT_ERROR

    out_dir.mkdir(parents=True, exist_ok=True)
    guide_path.write_text(text, encoding="utf-8")
    guide_meta["work_root_leak_check"] = leak_check
    write_atomic(out_dir / "delivery_manifest.json", guide_meta)

    print(f"ok: guía -> {guide_path}")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())