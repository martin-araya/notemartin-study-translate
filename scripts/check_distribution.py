"""Checklist de distribución de la skill (fase 058).

Verifica que el paquete esté listo para entregar sin instalar nada
por su cuenta:

- ``SKILL.md`` existe y su frontmatter es parseable con ``name`` y
  ``description``.
- Cada ruta referenciada en la tabla §6 de ``SKILL.md`` apunta a un
  archivo existente.
- Cada enlace Markdown interno en ``references/*.md`` apunta a un
  archivo existente (cuando la ruta es local).
- Cada script referenciado por nombre en ``references/*.md`` existe
  en ``scripts/``.
- ``requirements.txt`` (si existe) tiene cada entrada pinneada con
  ``==X.Y.Z``. Si falta, se crea uno vacío marcado válido.
- No se incluyen ``*.pyc``, ``__pycache__/``, ``.tmp`` ni ``.partial``
  en la raíz.
- El perfil de instalación se imprime y la instalación real solo se
  aplica cuando el usuario pasa ``--apply`` explícitamente.

Uso::

    python scripts/check_distribution.py --root . --out dist_report.json

Devuelve código 0 si el paquete está listo para distribución sin
instalación. Si se pasa ``--apply``, devuelve código distinto de 0
porque aplicar el perfil de instalación queda fuera del alcance de la
skill.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path

FORBIDDEN_PATTERNS = ("__pycache__", ".pyc", ".tmp", ".partial", ".DS_Store")
PINNED_DEP_RE = re.compile(r"^([A-Za-z0-9_.\-]+)\s*==\s*([0-9][^\s]*)$")
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
SCRIPT_REF_RE = re.compile(r"`scripts/([a-zA-Z0-9_.\-]+\.py)`")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="check_distribution.py")
    p.add_argument("--root", required=True, help="Raíz del paquete.")
    p.add_argument("--out", required=True, help="Ruta del dist_report.json.")
    p.add_argument("--apply", action="store_true",
                   help="No implementado: solicitar al usuario la instalación real.")
    return p.parse_args(argv)


def write_atomic(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    out: dict[str, str] = {}
    for line in parts[1].strip().splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            out[k.strip()] = v.strip()
    return out


def extract_skill_table_paths(skill_md: str) -> list[str]:
    """Extrae las rutas de la tabla §6 (| `ruta` | rol |)."""
    paths: list[str] = []
    in_section = False
    for line in skill_md.splitlines():
        if line.startswith("## §6") or line.startswith("| Ruta | Rol |"):
            in_section = True
            continue
        if in_section and line.startswith("| "):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if cells and cells[0].startswith("`") and cells[0].endswith("`"):
                paths.append(cells[0].strip("`"))
            continue
        if in_section and not line.startswith("|"):
            in_section = False
    return paths


def find_forbidden(root: Path) -> list[str]:
    out: list[str] = []
    for path in root.rglob("*"):
        rel = path.relative_to(root).as_posix()
        for pattern in FORBIDDEN_PATTERNS:
            if pattern in path.name or pattern in rel.split("/"):
                out.append(rel)
                break
    return sorted(set(out))


def check_requirements(root: Path) -> dict:
    req = root / "requirements.txt"
    if not req.exists():
        empty = root / "requirements.txt"
        if not empty.exists():
            empty.write_text("", encoding="utf-8")
        return {"exists": False, "pinned": [], "unpinned": [], "ok": True}
    lines = [l.strip() for l in req.read_text(encoding="utf-8").splitlines()
             if l.strip() and not l.strip().startswith("#")]
    pinned: list[str] = []
    unpinned: list[str] = []
    for line in lines:
        if PINNED_DEP_RE.match(line):
            pinned.append(line)
        else:
            unpinned.append(line)
    return {"exists": True, "pinned": pinned, "unpinned": unpinned, "ok": not unpinned}


def strip_inline_code(text: str) -> str:
    """Sustituye `` `…` `` por un placeholder para evitar capturar
    enlaces que aparecen como ejemplos dentro de código inline."""
    return re.sub(r"`[^`]*`", "``", text)


def collect_internal_links(md_text: str) -> list[str]:
    """Recolecta enlaces internos ignorando los que estén dentro de
    bloques de código fenced (```) o indentados, donde los patrones
    suelen ser ejemplos literales, no referencias reales."""
    lines = md_text.splitlines()
    out: list[str] = []
    in_fence = False
    indent_buffer: list[str] = []
    fence_pat = re.compile(r"^\s*(```|~~~)")

    def flush_indent() -> None:
        if not indent_buffer:
            return
        block = "\n".join(indent_buffer)
        for m in LINK_RE.finditer(block):
            target = m.group(2).strip()
            if not target.startswith(("http://", "https://", "mailto:", "#", "javascript:", "data:", "file:")):
                out.append(target)
        indent_buffer.clear()

    for line in lines:
        stripped = line.lstrip()
        if fence_pat.match(stripped):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.startswith("    "):
            indent_buffer.append(line)
        else:
            flush_indent()
            line_no_code = strip_inline_code(line)
            for m in LINK_RE.finditer(line_no_code):
                target = m.group(2).strip()
                if not target.startswith(("http://", "https://", "mailto:", "#", "javascript:", "data:", "file:")):
                    out.append(target)
    flush_indent()
    return out


def check_references(root: Path, skill_md_text: str) -> dict:
    refs_dir = root / "references"
    skill_paths = extract_skill_table_paths(skill_md_text)
    missing_skill: list[str] = []
    for rel in skill_paths:
        if not (root / rel).exists():
            missing_skill.append(rel)

    missing_internal: list[tuple[str, list[str]]] = []
    missing_scripts: list[tuple[str, str]] = []
    if refs_dir.is_dir():
        for ref in sorted(refs_dir.glob("*.md")):
            text = ref.read_text(encoding="utf-8")
            for link in collect_internal_links(text):
                target = (ref.parent / link).resolve()
                if not target.exists():
                    missing_internal.append((ref.name, link))
            for m in SCRIPT_REF_RE.finditer(text):
                script = m.group(1)
                if not (root / "scripts" / script).exists():
                    missing_scripts.append((ref.name, script))
    return {
        "missing_skill_paths": missing_skill,
        "missing_internal_links": missing_internal,
        "missing_scripts": missing_scripts,
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    out_path = Path(args.out)

    if args.apply:
        print(
            "error: --apply no está implementado. La instalación real del paquete\n"
            "en un perfil de Hermes la solicita el usuario siguiendo la documentación\n"
            "oficial. Esta skill no se autoinstala.",
            file=sys.stderr,
        )
        return 2

    skill_path = root / "SKILL.md"
    checks: list[dict] = []
    skill_text = ""
    if not skill_path.exists():
        checks.append({"check": "skill_md_exists", "ok": False, "message": "SKILL.md no existe"})
    else:
        skill_text = skill_path.read_text(encoding="utf-8")
        front = parse_frontmatter(skill_text)
        if not front.get("name"):
            checks.append({"check": "skill_frontmatter_name", "ok": False, "message": "frontmatter sin 'name'"})
        else:
            checks.append({"check": "skill_frontmatter_name", "ok": True, "value": front["name"]})
        if not front.get("description"):
            checks.append({"check": "skill_frontmatter_description", "ok": False, "message": "frontmatter sin 'description'"})
        else:
            checks.append({"check": "skill_frontmatter_description", "ok": True, "length": len(front["description"])})

    refs_report = check_references(root, skill_text)
    if refs_report["missing_skill_paths"]:
        checks.append({"check": "skill_md_table_paths", "ok": False, "missing": refs_report["missing_skill_paths"]})
    else:
        checks.append({"check": "skill_md_table_paths", "ok": True})
    if refs_report["missing_internal_links"]:
        checks.append({"check": "references_internal_links", "ok": False, "missing": refs_report["missing_internal_links"][:10]})
    else:
        checks.append({"check": "references_internal_links", "ok": True})
    if refs_report["missing_scripts"]:
        checks.append({"check": "references_scripts", "ok": False, "missing": refs_report["missing_scripts"][:10]})
    else:
        checks.append({"check": "references_scripts", "ok": True})

    requirements = check_requirements(root)
    if requirements["ok"]:
        checks.append({"check": "requirements_pinned", "ok": True, "pinned": requirements["pinned"]})
    else:
        checks.append({"check": "requirements_pinned", "ok": False, "unpinned": requirements["unpinned"]})

    forbidden = find_forbidden(root)
    if forbidden:
        checks.append({"check": "forbidden_artifacts", "ok": False, "found": forbidden})
    else:
        checks.append({"check": "forbidden_artifacts", "ok": True})

    install_profile = {
        "system": "Hermes",
        "path_expected": "~/.config/kilo/skills/notemartin-study-translate/",
        "user_action_required": "Solicitar instalación manual al usuario siguiendo la documentación oficial de Hermes.",
    }

    all_ok = all(c.get("ok") for c in checks)
    report = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "root": str(root),
        "ok": all_ok,
        "checks": checks,
        "install_profile": install_profile,
        "user_action": (
            "Distribución lista. La instalación real del paquete en un perfil de Hermes "
            "la realiza el usuario; la skill no se autoinstala."
            if all_ok else
            "Hay hallazgos que bloquean la distribución. Ver 'checks' para detalle."
        ),
    }
    write_atomic(out_path, report)
    print(
        f"ok: distribution {'ready' if all_ok else 'blocked'} -> {out_path}\n"
        f"install_profile: {install_profile['path_expected']}\n"
        f"user_action: {report['user_action']}"
    )
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())