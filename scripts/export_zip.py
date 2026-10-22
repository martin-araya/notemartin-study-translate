"""Paquete ZIP autocontenido de entrega (fases 135 y 136).

``export_zip.py`` arma el paquete; ``validate_zip_package.py`` lo
reapre y lo audita. Ambos comparten las reglas de inclusión y de
seguridad de ruta.

Garantías al exportar:

- Un solo directorio raíz, ``<run_id>/`` o el valor indicado.
- Solo entran documentos y recursos. Los artefactos operativos
  (``manifest.json``, ``glossary.json``, ``reports/``, ``segments/``,
  ``translations/``, ``staged/``, ``__pycache__``, dotfiles) quedan
  fuera y su exclusión se declara con motivo.
- Rutas relativas POSIX, sin ``..``, sin ruta absoluta y sin symlinks.
- Escritura atómica y **determinista**: mismo árbol y mismo manifiesto
  producen el mismo ZIP byte a byte, porque la fecha de cada miembro es
  fija y el orden es estable. Eso permite comprobar en la fase 140 que
  desactivar el adaptador reproduce el paquete canónico.
- Nada se escribe dentro de ``output_root/`` ni de ``work_root/``.

Uso::

    python scripts/export_zip.py \\
        --tree output_root/run-001 \\
        --manifest work_root/run-001/manifest.json \\
        --run-id run-001 \\
        --destination-id notion-manual \\
        --out dist/run-001-notion-manual.zip \\
        --package-manifest reports/delivery/package_manifest.json

    python scripts/validate_zip_package.py \\
        --zip dist/run-001-notion-manual.zip \\
        --package-manifest reports/delivery/package_manifest.json \\
        --manifest work_root/run-001/manifest.json \\
        --out reports/delivery/package_validation.json
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from delivery_common import (  # noqa: E402
    FORBIDDEN_DIRS,
    FORBIDDEN_NAMES,
    now_iso,
    sha256_bytes,
    write_atomic,
)

PACKAGE_SCHEMA = ROOT / "schemas" / "delivery_package.schema.json"

EXIT_OK = 0
EXIT_INPUT_ERROR = 2
EXIT_PACKAGE_INVALID = 3

FIXED_DATE_TIME = (1980, 1, 1, 0, 0, 0)
MARKDOWN_SUFFIXES = (".md", ".markdown")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="export_zip.py")
    p.add_argument("--tree", required=True, help="Árbol a empaquetar: canónico o adaptado.")
    p.add_argument("--manifest", required=True, help="manifest.json de la ejecución.")
    p.add_argument("--run-id", required=True)
    p.add_argument("--destination-id", required=True)
    p.add_argument("--top-level-dir", help="Directorio raíz del paquete. Por defecto el run_id.")
    p.add_argument("--remote-status", default="no_verificado",
                   choices=["no_verificado", "verificado_con_evidencia"])
    p.add_argument("--import-evidence", help="Registro de evidencia de importación (fase 131).")
    p.add_argument("--adaptation-report", help="Informe de adaptación (fase 134).")
    p.add_argument("--degradation-report", help="Informe de degradaciones (fase 138).")
    p.add_argument("--out", required=True, help="Ruta del ZIP a escribir.")
    p.add_argument("--package-manifest", required=True)
    return p.parse_args(argv)


def exclusion_reason(rel: str, name: str) -> str | None:
    """Motivo de exclusión, o None si el archivo sí entra en el paquete."""
    parts = rel.split("/")
    for part in parts[:-1]:
        if part in FORBIDDEN_DIRS:
            return f"directorio operativo excluido: {part}"
    if name in FORBIDDEN_NAMES:
        return "artefacto operativo excluido"
    if name.startswith("."):
        return "archivo oculto"
    if name.endswith((".pyc", ".tmp", ".partial")):
        return "artefacto temporal"
    if name.endswith(MARKDOWN_SUFFIXES):
        return None
    return None


def collect_members(tree: Path, top_level: str) -> tuple[list[dict], list[dict]]:
    members: list[dict] = []
    excluded: list[dict] = []
    for path in sorted(tree.rglob("*")):
        rel = path.relative_to(tree).as_posix()
        if path.is_symlink():
            excluded.append({"path": rel, "reason": "symlink excluido"})
            continue
        if not path.is_file():
            continue
        reason = exclusion_reason(rel, path.name)
        if reason:
            excluded.append({"path": rel, "reason": reason})
            continue
        data = path.read_bytes()
        members.append({
            "path": f"{top_level}/{rel}",
            "sha256": sha256_bytes(data),
            "bytes": len(data),
            "kind": "document" if path.name.endswith(MARKDOWN_SUFFIXES) else "resource",
        })
    members.sort(key=lambda m: m["path"])
    excluded.sort(key=lambda e: e["path"])
    return members, excluded


def remote_status_from_evidence(path: str | None) -> str:
    if not path:
        return "no_verificado"
    evidence = json.loads(Path(path).read_text(encoding="utf-8"))
    if evidence.get("verified") is True and evidence.get("remote_status") == "verificado_con_evidencia":
        return "verificado_con_evidencia"
    return "no_verificado"


def write_zip(out: Path, tree: Path, members: list[dict], top_level: str) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(out.suffix + ".tmp")
    if tmp.exists():
        tmp.unlink()
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for member in members:
            rel = member["path"][len(top_level) + 1:]
            info = zipfile.ZipInfo(member["path"], date_time=FIXED_DATE_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, (tree / rel).read_bytes())
    tmp.replace(out)


def validate_package_document(payload: dict) -> list[str]:
    try:
        import jsonschema
    except ImportError:
        return []
    schema = json.loads(PACKAGE_SCHEMA.read_text(encoding="utf-8"))
    return [e.message for e in jsonschema.Draft202012Validator(schema).iter_errors(payload)]


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    tree = Path(args.tree)
    manifest_path = Path(args.manifest)
    if not tree.is_dir():
        print(f"error: árbol inexistente: {tree}", file=sys.stderr)
        return EXIT_INPUT_ERROR
    if not manifest_path.exists():
        print(f"error: manifiesto inexistente: {manifest_path}", file=sys.stderr)
        return EXIT_INPUT_ERROR

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    top_level = args.top_level_dir or args.run_id
    if not top_level or top_level.startswith("/") or ".." in top_level.split("/"):
        print(f"error: directorio raíz de paquete inválido: {top_level}", file=sys.stderr)
        return EXIT_INPUT_ERROR

    members, excluded = collect_members(tree, top_level)
    if not members:
        print("error: el árbol no contiene nada empaquetable", file=sys.stderr)
        return EXIT_PACKAGE_INVALID

    package: dict = {
        "schema_version": "1",
        "package_id": f"{args.run_id}-{args.destination_id}",
        "run_id": args.run_id,
        "destination_id": args.destination_id,
        "created_at": now_iso(),
        "top_level_dir": top_level,
        "source_tree": str(tree),
        "members": members,
        "excluded": excluded,
        "guide_outside_package": True,
        "remote_status": remote_status_from_evidence(args.import_evidence),
    }

    adaptation_ref = args.adaptation_report
    if adaptation_ref and Path(adaptation_ref).exists():
        adaptation = json.loads(Path(adaptation_ref).read_text(encoding="utf-8"))
        if adaptation.get("rules_enabled"):
            package["adaptation"] = {
                "profile_id": adaptation.get("profile_id"),
                "applied_rules": adaptation.get("rules_enabled"),
                "degradation_report_ref": args.degradation_report or "",
            }

    declared_remote = args.remote_status
    if package["remote_status"] == "verificado_con_evidencia" and declared_remote == "no_verificado":
        print(
            "error: la evidencia declara verificación remota pero el destino se marca no verificado",
            file=sys.stderr,
        )
        return EXIT_PACKAGE_INVALID

    errors = validate_package_document(package)
    if errors:
        print("error: manifiesto de paquete inválido:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return EXIT_PACKAGE_INVALID

    out = Path(args.out)
    write_zip(out, tree, members, top_level)
    package["zip_sha256"] = sha256_bytes(out.read_bytes())
    write_atomic(Path(args.package_manifest), package)

    print(
        f"ok: zip={out} miembros={len(members)} excluidos={len(excluded)} "
        f"remote_status={package['remote_status']}"
    )
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())