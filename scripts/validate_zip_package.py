"""Validación del contenido de un paquete ZIP (fase 136).

Reabre el paquete y lo audita contra el manifiesto de paquete y contra
el manifiesto de la ejecución. Comprueba:

- que el conjunto de miembros coincida exactamente con el declarado;
- que ningún miembro se repita;
- que el SHA-256 de cada miembro coincida con el declarado;
- que toda ruta sea relativa, POSIX, sin ``..`` y sin prefijo de
  unidad o de sistema;
- que ningún miembro sea un symlink;
- que ningún miembro caiga en un directorio operativo excluido;
- que todo documento del paquete esté en el alcance aprobado del
  manifiesto de la ejecución;
- que el orden de miembros sea el estable, que es lo que permite
  reproducir el paquete byte a byte.

El validador solo lee. No escribe dentro del paquete ni de ``output_root``.

Uso::

    python scripts/validate_zip_package.py \\
        --zip dist/run-001-notion-manual.zip \\
        --package-manifest reports/delivery/package_manifest.json \\
        --manifest work_root/run-001/manifest.json \\
        --out reports/delivery/package_validation.json
"""

from __future__ import annotations

import argparse
import json
import posixpath
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
MARKDOWN_SUFFIXES = (".md", ".markdown")
IMPORTABLE_STATES = ("approved", "exported", "already_target")

EXIT_OK = 0
EXIT_INPUT_ERROR = 2
EXIT_PACKAGE_INVALID = 3


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="validate_zip_package.py")
    p.add_argument("--zip", required=True)
    p.add_argument("--package-manifest", required=True)
    p.add_argument("--manifest", required=True, help="manifest.json de la ejecución.")
    p.add_argument("--out", required=True)
    return p.parse_args(argv)


def is_unsafe_path(name: str) -> str | None:
    if name.startswith("/") or name.startswith("\\"):
        return "ruta absoluta"
    if len(name) > 1 and name[1] == ":":
        return "ruta con unidad"
    if "\\" in name:
        return "separador no POSIX"
    normalized = posixpath.normpath(name)
    if normalized.startswith("../") or normalized == "..":
        return "escape de ruta"
    parts = name.split("/")
    if ".." in parts:
        return "escape de ruta"
    return None


def is_symlink(info: zipfile.ZipInfo) -> bool:
    return (info.external_attr >> 16) & 0o170000 == 0o120000


def audit(zip_path: Path, package: dict, manifest: dict) -> dict:
    declared = package.get("members") or []
    declared_by_path = {m["path"]: m for m in declared}
    top_level = package.get("top_level_dir") or ""
    scope = {
        f.get("path")
        for f in manifest.get("files") or []
        if f.get("current_state") in IMPORTABLE_STATES
    }

    violations: list[dict] = []
    seen: set[str] = set()
    members_seen: list[dict] = []

    with zipfile.ZipFile(zip_path, "r") as zf:
        infos = zf.infolist()
        for info in infos:
            name = info.filename
            if name in seen:
                violations.append({"check": "duplicate_member", "path": name})
                continue
            seen.add(name)

            reason = is_unsafe_path(name)
            if reason:
                violations.append({"check": "unsafe_path", "path": name, "detail": reason})
                continue
            if is_symlink(info):
                violations.append({"check": "symlink_member", "path": name})
                continue
            if name.endswith("/"):
                violations.append({"check": "directory_member", "path": name})
                continue
            if top_level and not name.startswith(f"{top_level}/"):
                violations.append({"check": "outside_top_level", "path": name})
            parts = name.split("/")
            for part in parts[:-1]:
                if part in FORBIDDEN_DIRS:
                    violations.append({"check": "operational_dir_member", "path": name})
                    break
            base = parts[-1]
            if base in FORBIDDEN_NAMES:
                violations.append({"check": "operational_file_member", "path": name})

            declared_member = declared_by_path.get(name)
            if declared_member is None:
                violations.append({"check": "undeclared_member", "path": name})
                continue
            data = zf.read(name)
            actual = sha256_bytes(data)
            if actual != declared_member.get("sha256"):
                violations.append({
                    "check": "hash_mismatch",
                    "path": name,
                    "expected": declared_member.get("sha256"),
                    "actual": actual,
                })
            if len(data) != declared_member.get("bytes"):
                violations.append({"check": "size_mismatch", "path": name})
            members_seen.append({"path": name, "sha256": actual})

    for path in declared_by_path:
        if path not in seen:
            violations.append({"check": "missing_member", "path": path})

    ordered = sorted(declared_by_path)
    declared_order = [m["path"] for m in declared]
    if declared_order != ordered:
        violations.append({"check": "member_order_not_stable", "path": ""})

    if top_level:
        for path in declared_by_path:
            if not path.startswith(f"{top_level}/"):
                violations.append({"check": "outside_top_level", "path": path})

    for path, member in declared_by_path.items():
        rel = path[len(top_level) + 1:] if top_level and path.startswith(f"{top_level}/") else path
        if member.get("kind") == "document" and rel not in scope:
            violations.append({"check": "document_outside_scope", "path": path, "detail": rel})

    zip_hash = sha256_bytes(zip_path.read_bytes())
    if package.get("zip_sha256") and package["zip_sha256"] != zip_hash:
        violations.append({"check": "zip_hash_mismatch", "path": str(zip_path)})

    return {
        "zip": str(zip_path),
        "checked_at": now_iso(),
        "declared_members": len(declared_by_path),
        "observed_members": len(seen),
        "zip_sha256": zip_hash,
        "violations": violations,
        "ok": not violations,
    }


def validate_schema(package: dict) -> list[str]:
    try:
        import jsonschema
    except ImportError:
        return []
    schema = json.loads(PACKAGE_SCHEMA.read_text(encoding="utf-8"))
    return [e.message for e in jsonschema.Draft202012Validator(schema).iter_errors(package)]


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    zip_path = Path(args.zip)
    package_path = Path(args.package_manifest)
    manifest_path = Path(args.manifest)
    for path in (zip_path, package_path, manifest_path):
        if not path.exists():
            print(f"error: fichero inexistente: {path}", file=sys.stderr)
            return EXIT_INPUT_ERROR

    package = json.loads(package_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    schema_errors = validate_schema(package)
    if schema_errors:
        print("error: manifiesto de paquete inválido:", file=sys.stderr)
        for e in schema_errors:
            print(f"  - {e}", file=sys.stderr)
        return EXIT_PACKAGE_INVALID

    result = audit(zip_path, package, manifest)
    result["schema_errors"] = schema_errors
    write_atomic(Path(args.out), result)

    if not result["ok"]:
        print(f"error: {len(result['violations'])} violaciones en el paquete", file=sys.stderr)
        for v in result["violations"][:10]:
            print(f"  - {v}", file=sys.stderr)
        return EXIT_PACKAGE_INVALID
    print(
        f"ok: {result['observed_members']} miembros validados contra "
        f"{result['declared_members']} declarados -> {args.out}"
    )
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())