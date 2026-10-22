"""Comprobación de la política de versionado (fase 142).

Verifica que cada cosa que el proyecto versionadeclare su versión y que un
cambio incompatible tenga migración:

    1 = la versión de la skill no tiene entrada propia en CHANGELOG.md
    2 = un esquema no declara `x-schema-version` o su `$id` no coincide con
        su nombre de archivo, o el contrato lista un esquema inexistente
    3 = una referencia no lleva la marca `<!-- version: X.Y.Z -->`, o el
        contrato lista una referencia inexistente
    4 = un cambio incompatible no tiene migración declarada y existente
    5 = el contrato es incoherente con el CHANGELOG, con los contratos
        `translate/vN` o con la versión de parser fijada en el contrato
        Markdown
    6 = `requirements.txt` falta, está vacío o tiene dependencias sin
        pinear con `==`

Uso::

    python scripts/check_versioning.py --root . \\
        --out reports/maintenance/versioning.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from delivery_common import now_iso, write_atomic  # noqa: E402

VERSION_MARKER_RE = re.compile(r"<!--\s*version:\s*(\d+\.\d+\.\d+)\s*-->")
CHANGELOG_HEADING_RE = re.compile(r"^###\s+(\d+\.\d+\.\d+)\b", re.MULTILINE)
PINNED_RE = re.compile(r"^([A-Za-z0-9_.\-]+)\s*==\s*([0-9][^\s#]*)$")

CODES = {
    "1": "changelog_entry",
    "2": "schema_versions",
    "3": "doc_versions",
    "4": "breaking_change_migration",
    "5": "contract_consistency",
    "6": "requirements_pinned",
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="check_versioning.py")
    p.add_argument("--root", default=str(ROOT))
    p.add_argument("--contract", default=None,
                   help="Ruta del contrato de versiones. Por defecto release_contract.json.")
    p.add_argument("--out", required=True)
    return p.parse_args(argv)


def _semver_key(version: str) -> tuple[int, int, int]:
    parts = (version.split(".") + ["0", "0"])[:3]
    try:
        return (int(parts[0]), int(parts[1]), int(parts[2]))
    except ValueError:
        return (0, 0, 0)


def check_versioning(root: Path, contract_path: Path | None = None) -> dict:
    """Audita el versionado de un árbol. Devuelve informe con ``failures``."""
    root = Path(root)
    contract_path = Path(contract_path) if contract_path else root / "release_contract.json"
    failures: dict[str, list[str]] = {code: [] for code in CODES}

    if not contract_path.exists():
        failures["5"].append(f"no existe el contrato de versiones: {contract_path}")
        return _report(root, contract_path, failures, {})
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures["5"].append(f"el contrato no es JSON válido: {exc}")
        return _report(root, contract_path, failures, {})

    changelog_path = root / "CHANGELOG.md"
    changelog = changelog_path.read_text(encoding="utf-8") if changelog_path.exists() else ""
    skill_version = contract.get("skill_version") or ""

    # 1 · entrada de changelog
    if not skill_version or f"### {skill_version}" not in changelog:
        failures["1"].append(
            f"la versión {skill_version or '(sin declarar)'} no tiene entrada propia en CHANGELOG.md"
        )

    # 2 · esquemas
    declared_schemas = {entry.get("path"): entry for entry in contract.get("schemas") or []}
    for path in sorted((root / "schemas").glob("*.schema.json")):
        rel = path.relative_to(root).as_posix()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            failures["2"].append(f"{rel}: no es JSON válido ({exc})")
            continue
        version = data.get("x-schema-version")
        if not version:
            failures["2"].append(f"{rel}: no declara x-schema-version")
        elif rel in declared_schemas and declared_schemas[rel].get("version") != version:
            failures["2"].append(
                f"{rel}: el contrato declara {declared_schemas[rel].get('version')} "
                f"y el esquema declara {version}"
            )
        schema_id = data.get("$id") or ""
        if not schema_id.endswith(path.name):
            failures["2"].append(f"{rel}: su $id ({schema_id}) no termina en el nombre del archivo")
    for rel, entry in sorted(declared_schemas.items()):
        if not (root / rel).exists():
            failures["2"].append(f"{rel}: el contrato lista un esquema inexistente")

    # 3 · referencias
    declared_docs = {entry.get("path"): entry for entry in contract.get("docs") or []}
    for path in sorted((root / "references").rglob("*.md")):
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        match = VERSION_MARKER_RE.search(text)
        if not match:
            failures["3"].append(f"{rel}: sin marca '<!-- version: X.Y.Z -->'")
        elif rel in declared_docs and declared_docs[rel].get("version") != match.group(1):
            failures["3"].append(
                f"{rel}: el contrato declara {declared_docs[rel].get('version')} "
                f"y el documento {match.group(1)}"
            )
    for rel in sorted(declared_docs):
        if not (root / rel).exists():
            failures["3"].append(f"{rel}: el contrato lista una referencia inexistente")

    # 4 · cambios incompatibles
    migrations = {(m.get("from"), m.get("to")) for m in contract.get("migrations") or []}
    for change in contract.get("breaking_changes") or []:
        tool = change.get("migration") or ""
        if not (root / tool).exists():
            failures["4"].append(
                f"cambio incompatible {change.get('id')}: la migración {tool} no existe"
            )
        if not any(to for _frm, to in migrations):
            failures["4"].append(
                f"cambio incompatible {change.get('id')}: no hay entrada en migrations[]"
            )

    # 5 · coherencia del contrato
    changelog_versions = CHANGELOG_HEADING_RE.findall(changelog)
    if changelog_versions and skill_version:
        newest = max(changelog_versions, key=_semver_key)
        if _semver_key(skill_version) < _semver_key(newest):
            failures["5"].append(
                f"el CHANGELOG declara {newest} y el contrato una versión anterior ({skill_version})"
            )
    for entry in contract.get("contracts") or []:
        if not re.match(r"^translate/v\d+$", entry.get("version") or ""):
            failures["5"].append(f"contrato {entry.get('id')} con versión no canónica")
        doc = entry.get("doc") or ""
        if doc.endswith(".md") and not (root / doc).exists():
            failures["5"].append(f"contrato {entry.get('id')} apunta a una doc inexistente: {doc}")
    parser = contract.get("parser") or {}
    policy = parser.get("policy") or ""
    if policy and not (root / policy).exists():
        failures["5"].append(f"la política de parser no existe: {policy}")
    markdown_contract = root / "references" / "markdown-contract.md"
    if markdown_contract.exists() and parser.get("pinned"):
        match = re.search(
            r"\*\*Versión fijada\*\*:\s*`([^`]+)`",
            markdown_contract.read_text(encoding="utf-8"),
        )
        if match and match.group(1) != parser["pinned"]:
            failures["5"].append(
                f"el contrato fija el parser {parser['pinned']} y markdown-contract.md fija {match.group(1)}"
            )

    # 6 · requisitos pinneados
    requirements = root / "requirements.txt"
    if not requirements.exists():
        failures["6"].append("requirements.txt no existe")
    else:
        entries = [
            line.strip() for line in requirements.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        if not entries:
            failures["6"].append("requirements.txt está vacío")
        unpinned = [line for line in entries if not PINNED_RE.match(line)]
        if unpinned:
            failures["6"].append(f"dependencias sin pinear: {unpinned}")

    return _report(root, contract_path, failures, {
        "skill_version": skill_version,
        "schemas": len(list((root / "schemas").glob("*.schema.json"))),
        "docs": len(list((root / "references").rglob("*.md"))),
        "breaking_changes": len(contract.get("breaking_changes") or []),
        "migrations": len(contract.get("migrations") or []),
    })


def _report(root: Path, contract_path: Path, failures: dict[str, list[str]], counts: dict) -> dict:
    populated = {code: messages for code, messages in failures.items() if messages}
    return {
        "generated_at": now_iso(),
        "root": str(root),
        "contract": str(contract_path),
        "ok": not populated,
        "failures": populated,
        "codes": CODES,
        "counts": counts,
    }


def exit_code_for(report: dict) -> int:
    codes = sorted(int(code) for code in (report.get("failures") or {}))
    return codes[0] if codes else 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = check_versioning(Path(args.root), args.contract)
    write_atomic(Path(args.out), report)
    code = exit_code_for(report)
    if code:
        print(f"fail: {json.dumps(report['failures'], ensure_ascii=False)}", file=sys.stderr)
        return code
    print(
        f"ok: versionado coherente (skill {report['counts'].get('skill_version')}, "
        f"{report['counts'].get('schemas')} esquemas, {report['counts'].get('docs')} referencias)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())