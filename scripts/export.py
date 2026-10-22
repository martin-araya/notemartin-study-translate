"""Exportación local limpia y atómica (fase 047 + protección 056).

Orquesta las verificaciones previas y la exportación final:

1. ``validate.py`` sin errores.
2. ``check_integrity.py`` con ``integrity_ok: true``.
3. ``audit_terminology.py`` sin ``forbidden_use``.
4. ``copy_resources.py`` sin ``hash_mismatch`` ni ``missing_resource``.
5. ``assemble.py`` modo por defecto para cada archivo Markdown.
6. Árbol final en ``output_root/<run_id>/<mismas rutas relativas>``.

Ninguna reporte entra en ``output_root``. Si cualquier paso falla,
la exportación aborta sin escribir.

Si ``output_root/<run_id>/`` ya existe y no se pasa ``--force``, falla
sin escribir. La fase 056 añade detección de ediciones manuales
comparando el SHA-256 de cada archivo del destino previo contra el
catálogo ``output_hashes.json`` del run anterior.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
VALIDATE = SCRIPT_DIR / "validate.py"
CHECK_INTEGRITY = SCRIPT_DIR / "check_integrity.py"
AUDIT = SCRIPT_DIR / "audit_terminology.py"
COPY = SCRIPT_DIR / "copy_resources.py"
ASSEMBLE = SCRIPT_DIR / "assemble.py"

MERGE_STRATEGIES = ("new-destination", "preserve", "patch")
DEFAULT_MERGE_STRATEGY = "new-destination"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="export.py")
    p.add_argument("--source-root", required=True)
    p.add_argument("--translations", required=True)
    p.add_argument("--inventory", required=True)
    p.add_argument("--manifest", required=True)
    p.add_argument("--segments", required=True)
    p.add_argument("--packets", required=True)
    p.add_argument("--snapshots", required=True)
    p.add_argument("--anchors", required=True)
    p.add_argument("--glossary", required=True)
    p.add_argument("--output-root", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--force", action="store_true")
    p.add_argument("--merge-strategy", choices=MERGE_STRATEGIES, default=DEFAULT_MERGE_STRATEGY,
                   help="Comportamiento ante destino preexistente o editado.")
    p.add_argument("--report", required=True)
    return p.parse_args(argv)


def write_atomic(target: Path, payload) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    if isinstance(payload, bytes):
        tmp.write_bytes(payload)
    elif isinstance(payload, str):
        tmp.write_text(payload, encoding="utf-8")
    else:
        tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def run_step(cmd: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout, proc.stderr


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def output_hashes_path(output_root: Path, run_id: str) -> Path:
    return output_root / run_id / "output_hashes.json"


def load_prior_hashes(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return dict(payload.get("hashes", {}))


def compute_current_hashes(directory: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not directory.exists():
        return out
    for path in sorted(directory.rglob("*")):
        if path.is_file() and path.name != "output_hashes.json":
            out[path.relative_to(directory).as_posix()] = sha256_bytes(path.read_bytes())
    return out


def detect_conflicts(prior: dict[str, str], current: dict[str, str]) -> dict[str, list[str]]:
    """Compara hashes previos contra los actuales y devuelve tres
    listas: editados, añadidos al destino (foreign) y desaparecidos."""
    edited: list[str] = []
    foreign: list[str] = []
    missing = []
    for rel, current_hash in current.items():
        if rel not in prior:
            foreign.append(rel)
            continue
        if prior[rel] != current_hash:
            edited.append(rel)
    for rel in prior:
        if rel not in current:
            missing.append(rel)
    return {"edited": edited, "foreign": foreign, "missing": missing}


def backup_edited(target: Path, edited_paths: list[str]) -> Path:
    backup = target.parent / f"{target.name}_edited_backup"
    backup.mkdir(parents=True, exist_ok=True)
    for rel in edited_paths:
        src = target / rel
        if src.exists():
            dst = backup / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    return backup


def promote_manifest(manifest_path: Path, hashes: dict[str, str], run_id: str) -> tuple[list[str], list[dict]]:
    """Pasa a `exported` los archivos que estaban aprobados y tienen bytes.

    Solo se promueve lo que ya estaba `approved` y aparece en el árbol
    entregado con su hash: la promoción es consecuencia de la
    exportación, no un atajo para saltarse la aprobación. Un archivo en
    cualquier otro estado se queda como estaba y se reporta.
    """
    if not manifest_path.exists():
        return [], []
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    promoted: list[str] = []
    not_promoted: list[dict] = []

    for record in manifest.get("files", []):
        rel = record.get("path")
        current = record.get("current_state") or record.get("state")
        if current != "approved":
            not_promoted.append({"path": rel, "current_state": current, "reason": "no estaba aprobado"})
            continue
        digest = hashes.get(rel)
        if not digest:
            not_promoted.append({"path": rel, "current_state": current, "reason": "sin bytes entregados"})
            continue
        record["current_state"] = "exported"
        record["state"] = "exported"
        record["output_sha256"] = digest
        record["last_transition_at"] = now
        record.setdefault("state_history", []).append({
            "state": "exported",
            "timestamp": now,
            "reason": f"exportado en {run_id}",
        })
        promoted.append(rel)

    write_atomic(manifest_path, manifest)
    return promoted, not_promoted


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output_root = Path(args.output_root) / args.run_id

    strategy = args.merge_strategy

    catalog = output_hashes_path(Path(args.output_root), args.run_id)
    prior_hashes = load_prior_hashes(catalog)

    current_hashes = compute_current_hashes(output_root)
    conflicts = detect_conflicts(prior_hashes, current_hashes)
    edited_paths = conflicts["edited"]
    foreign_paths = conflicts["foreign"]

    if strategy == "preserve":
        if edited_paths or foreign_paths:
            backup = backup_edited(output_root, edited_paths + foreign_paths)
            print(
                f"warning: {len(edited_paths)} editados y {len(foreign_paths)} "
                f"ajenos respaldados en {backup}; no se sobrescriben",
                file=sys.stderr,
            )
        for rel in edited_paths + foreign_paths:
            target = output_root / rel
            if target.exists():
                if target.is_file():
                    target.unlink()
                else:
                    shutil.rmtree(target)
    elif strategy == "patch":
        if edited_paths:
            backup = backup_edited(output_root, edited_paths)
            print(
                f"warning: {len(edited_paths)} editados respaldados en {backup}",
                file=sys.stderr,
            )
    elif strategy == "new-destination":
        if (output_root.exists() and not args.force) and (edited_paths or foreign_paths or prior_hashes or current_hashes):
            if edited_paths or foreign_paths:
                print(
                    f"error: destino contiene ediciones manuales o archivos ajenos "
                    f"(edited={len(edited_paths)}, foreign={len(foreign_paths)}). "
                    f"Use --force para sobrescribir o --merge-strategy preserve|patch.",
                    file=sys.stderr,
                )
                return 1
            print(f"error: {output_root} existe; usa --force para sobrescribir", file=sys.stderr)
            return 1

    if output_root.exists() and not edited_paths and not foreign_paths:
        if not args.force and strategy != "preserve":
            for p in output_root.glob("**/*"):
                if p.is_file() and p.name != "output_hashes.json":
                    p.unlink()

    validate_report = Path(args.report).with_suffix(".validate.json")
    integrity_report = Path(args.report).with_suffix(".integrity.json")
    audit_report = Path(args.report).with_suffix(".audit.json")
    copy_report = Path(args.report).with_suffix(".copy.json")
    structure_report = Path(args.report).with_suffix(".structure.json")

    # El destino final aún no existe en este punto: la validación previa
    # comprueba protección, destinos, cobertura y deuda de origen, que no
    # dependen del árbol entregado. La paridad estructural se comprueba
    # después, contra el árbol real (ver más abajo).
    rc, _, stderr = run_step([
        sys.executable, str(VALIDATE),
        "--source", args.source_root,
        "--output-dir", str(output_root),
        "--packets", args.packets,
        "--segments", args.segments,
        "--translations", args.translations,
        "--snapshots", args.snapshots,
        "--anchors", args.anchors,
        "--manifest", args.manifest,
        "--out", str(validate_report),
    ])
    if rc != 0:
        print(f"error: validate.py falló: {stderr}", file=sys.stderr)
        return rc

    rc, _, stderr = run_step([
        sys.executable, str(CHECK_INTEGRITY),
        "--manifest", args.manifest,
        "--out", str(integrity_report),
    ])
    if rc != 0:
        print(f"error: check_integrity.py falló: {stderr}", file=sys.stderr)
        return rc

    rc, _, stderr = run_step([
        sys.executable, str(AUDIT),
        "--translations", args.translations,
        "--glossary", args.glossary,
        "--out", str(audit_report),
    ])
    if rc != 0:
        print(f"error: audit_terminology.py falló: {stderr}", file=sys.stderr)
        return rc

    rc, _, stderr = run_step([
        sys.executable, str(COPY),
        "--inventory", args.inventory,
        "--source-root", args.source_root,
        "--output-root", str(output_root),
        "--report", str(copy_report),
    ])
    if rc != 0:
        print(f"error: copy_resources.py falló: {stderr}", file=sys.stderr)
        return rc

    if output_root.exists():
        for p in output_root.glob("**/*"):
            if p.is_file() and p.name != "output_hashes.json":
                p.unlink()
    output_root.mkdir(parents=True, exist_ok=True)

    rc, _, stderr = run_step([
        sys.executable, str(COPY),
        "--inventory", args.inventory,
        "--source-root", args.source_root,
        "--output-root", str(output_root),
        "--report", str(copy_report),
    ])
    if rc != 0:
        print(f"error: copia final de recursos falló: {stderr}", file=sys.stderr)
        return rc

    segments_doc = json.loads(Path(args.segments).read_text(encoding="utf-8"))
    by_doc: dict[str, dict] = {}
    for f in segments_doc.get("files", []):
        by_doc[f["document_id"]] = f

    tmp_root = Path(args.output_root) / f".{args.run_id}.tmp"
    if tmp_root.exists():
        shutil.rmtree(tmp_root)
    tmp_root.mkdir(parents=True)

    assembled: list[dict] = []
    for f in segments_doc.get("files", []):
        doc_id = f["document_id"]
        rel_path = f["path"]
        source_path = Path(args.source_root) / rel_path
        if not source_path.exists():
            continue
        single = tmp_root / f"{doc_id}.json"
        write_atomic(single, f)
        out_path = tmp_root / rel_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        rc, _, stderr = run_step([
            sys.executable, str(ASSEMBLE),
            "--source", str(source_path),
            "--segments", str(single),
            "--out", str(out_path),
            "--translations", args.translations,
        ])
        if rc != 0:
            print(f"error: assemble.py falló para {rel_path}: {stderr}", file=sys.stderr)
            return rc
        assembled.append({"path": rel_path, "bytes": out_path.stat().st_size})

    final_target = Path(args.output_root) / args.run_id
    if final_target.exists():
        shutil.rmtree(final_target)
    os.rename(tmp_root, final_target)

    # Paridad estructural del árbol entregado contra la fuente (INV-06).
    # Sin esta comprobación `export.py` entregaba sin comparar nunca la
    # forma de lo entregado: el `validate.py` previo corría sobre el padre
    # del directorio del run, donde no hay ningún documento que comparar.
    rc, _, stderr = run_step([
        sys.executable, str(VALIDATE),
        "--source", args.source_root,
        "--output-dir", str(final_target),
        "--packets", args.packets,
        "--segments", args.segments,
        "--translations", args.translations,
        "--snapshots", args.snapshots,
        "--anchors", args.anchors,
        "--manifest", args.manifest,
        "--out", str(structure_report),
        "--checks", "structure",
        "--require-assembled",
    ])
    if rc != 0:
        shutil.rmtree(final_target)
        print(
            "error: la estructura del árbol entregado no coincide con la fuente; "
            "no se promueve nada",
            file=sys.stderr,
        )
        print(stderr, file=sys.stderr)
        return rc

    final_hashes = compute_current_hashes(final_target)
    write_atomic(catalog, {
        "run_id": args.run_id,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hashes": final_hashes,
    })

    promoted, not_promoted = promote_manifest(Path(args.manifest), final_hashes, args.run_id)

    write_atomic(Path(args.report), {
        "run_id": args.run_id,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "output_root": str(final_target),
        "merge_strategy": strategy,
        "conflicts": conflicts,
        "assembled_files": assembled,
        "structure_check": {
            "report": str(structure_report),
            "ok": True,
            "documents_compared": len(assembled),
        },
        "promoted_to_exported": promoted,
        "not_promoted": not_promoted,
    })
    print(f"ok: {len(assembled)} archivos ensamblados -> {final_target}")
    print(f"ok: estructura verificada en {len(assembled)} documentos entregados")
    print(f"ok: {len(promoted)} archivos promovidos a exported en el manifiesto")
    return 0


if __name__ == "__main__":
    sys.exit(main())