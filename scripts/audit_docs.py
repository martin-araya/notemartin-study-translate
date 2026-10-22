"""Auditoría del contenido de la skill (fase 146).

`scripts/check_distribution.py` (fase 058) comprueba que el paquete esté
listo para entregar. Esta auditoría va más allá del empaque y comprueba que
lo que la skill **dice** exista y no se contradiga:

    1 = una ruta citada no existe
    2 = un comando documentado no existe o usa un flag que no existe
    3 = una regla canónica aparece con un valor distinto al del registro
    4 = un documento afirma una verificación remota que no existe
    5 = una referencia no lleva marca de versión
    6 = una referencia no es alcanzable desde ningún documento

Reutiliza las funciones de `check_distribution.py` en lugar de repetirlas.

Uso::

    python scripts/audit_docs.py --root . \\
        --out reports/maintenance/docs_audit.json
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from check_distribution import (  # noqa: E402
    collect_internal_links,
    extract_skill_table_paths,
)
from delivery_common import now_iso, write_atomic  # noqa: E402

COMMAND_RE = re.compile(
    r"python3?\s+(?:[^\s`]*\/)?scripts/([A-Za-z0-9_\-]+\.py)((?:\s+--?[A-Za-z0-9_\-]+)*)"
)
VERSION_MARKER_RE = re.compile(r"<!--\s*version:\s*\d+\.\d+\.\d+\s*-->")
FENCE_RE = re.compile(r"^\s*(```|~~~)")

DOC_NAMES = ("SKILL.md", "RELEASE.md", "CHANGELOG.md", "roadmap.md", "AGENTS.md")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="audit_docs.py")
    p.add_argument("--root", default=str(ROOT))
    p.add_argument("--registry", default="references/rule-registry.json")
    p.add_argument("--out", required=True)
    return p.parse_args(argv)


def _documents(root: Path) -> list[Path]:
    docs = [root / name for name in DOC_NAMES]
    docs += sorted((root / "references").rglob("*.md"))
    docs += sorted((root / "templates").glob("*.md"))
    docs += sorted((root / "evals").rglob("*.md"))
    return [path for path in docs if path.is_file()]


def _strip_fenced(text: str) -> str:
    """Quita el contenido de los bloques fenced, que son ejemplos, no
    afirmaciones sobre el proyecto."""
    out: list[str] = []
    in_fence = False
    token = ""
    for line in text.splitlines():
        m = FENCE_RE.match(line)
        if m:
            in_fence = in_fence is False
            if not in_fence:
                token = m.group(1)
            out.append("")
            continue
        out.append("" if in_fence else line)
    return "\n".join(out)


# --------------------------------------------------------------------------
# 1 · rutas
# --------------------------------------------------------------------------

PATH_MENTION_RE = re.compile(
    r"`((?:references|scripts|schemas|templates|evals)/[A-Za-z0-9_./\-]+)`"
)


def check_paths(root: Path) -> list[str]:
    findings: list[str] = []
    skill_text = (root / "SKILL.md").read_text(encoding="utf-8")
    for rel in extract_skill_table_paths(skill_text):
        if not (root / rel).exists():
            findings.append(f"SKILL.md §6 cita una ruta inexistente: {rel}")
    for path in sorted((root / "references").rglob("*.md")):
        for link in collect_internal_links(path.read_text(encoding="utf-8")):
            if link.startswith(("http://", "https://", "#")):
                continue
            target = (path.parent / link.split("#")[0]).resolve()
            if not target.exists():
                findings.append(f"{path.name} enlaza a una ruta inexistente: {link}")
    for path in _documents(root):
        for rel in set(PATH_MENTION_RE.findall(path.read_text(encoding="utf-8"))):
            if not (root / rel).exists():
                findings.append(f"{path.name} cita una ruta inexistente: `{rel}`")
    return findings


# --------------------------------------------------------------------------
# 2 · comandos
# --------------------------------------------------------------------------

def _script_flags(script: Path) -> set[str] | None:
    if not script.is_file():
        return None
    proc = subprocess.run(
        [sys.executable, str(script), "--help"],
        capture_output=True, text=True, check=False,
    )
    output = proc.stdout + proc.stderr
    if not output.strip():
        return None
    return set(re.findall(r"--?[A-Za-z0-9_\-]+", output))


def check_commands(root: Path) -> list[str]:
    findings: list[str] = []
    cache: dict[str, set[str] | None] = {}
    for path in _documents(root):
        text = _strip_fenced(path.read_text(encoding="utf-8")) + "\n"
        # los comandos se documentan sobre todo dentro de bloques fenced:
        # se recuperan del original, no de la versión recortada.
        raw = path.read_text(encoding="utf-8")
        for name, flag_blob in COMMAND_RE.findall(raw):
            script = root / "scripts" / name
            if not script.exists():
                findings.append(f"{path.name} cita un script inexistente: scripts/{name}")
                continue
            if name not in cache:
                cache[name] = _script_flags(script)
            available = cache[name]
            if available is None:
                findings.append(
                    f"scripts/{name} no expone --help: el comando documentado no es verificable"
                )
                continue
            for flag in re.findall(r"--?[A-Za-z0-9_\-]+", flag_blob):
                if flag not in available:
                    findings.append(
                        f"{path.name} documenta {flag} y scripts/{name} no lo expone"
                    )
        del text
    return findings


# --------------------------------------------------------------------------
# 3 · reglas contradictorias
# --------------------------------------------------------------------------

def check_rules(root: Path, registry: dict) -> list[str]:
    findings: list[str] = []
    for rule in registry.get("rules") or []:
        pattern = re.compile(rule["pattern"])
        declared: dict[str, set[str]] = {}
        for path in _documents(root):
            text = path.read_text(encoding="utf-8")
            for match in pattern.finditer(text):
                value = match.group(1) if match.groups() else match.group(0)
                declared.setdefault(value, set()).add(path.name)
        if rule.get("kind") == "enum":
            for value, where in sorted(declared.items()):
                if value not in (rule.get("values") or []):
                    findings.append(
                        f"regla {rule['key']}: valor {value!r} no permitido "
                        f"({sorted(where)}); fuente de verdad: {rule.get('source_of_truth')}"
                    )
        else:
            expected = rule.get("value")
            for value, where in sorted(declared.items()):
                if value != expected:
                    findings.append(
                        f"regla {rule['key']}: {value!r} contradice el valor canónico "
                        f"{expected!r} ({sorted(where)}); fuente de verdad: "
                        f"{rule.get('source_of_truth')}"
                    )
    return findings


# --------------------------------------------------------------------------
# 4 · afirmaciones remotas
# --------------------------------------------------------------------------

NEGATION_MARKERS = (
    " no ", "no significa", "nunca", "sin ", "not ", "neither", "todavía no",
    "no está", "no se", "queda ", "until",
)


def check_remote_claims(root: Path, forbidden: list[str]) -> list[str]:
    """Una afirmación remota prohibida solo es un hallazgo si no está negada.

    ``no significa publicado ni verificado en Notion`` es una prohibición,
    no una afirmación. Solo se marca la frase que el documento sostiene.
    """
    findings: list[str] = []
    for path in _documents(root):
        text = path.read_text(encoding="utf-8")
        for sentence in re.split(r"(?<=[.;:\n])", text):
            lowered = sentence.lower()
            for phrase in forbidden:
                needle = phrase.lower()
                if needle in lowered and not any(
                    marker in lowered for marker in NEGATION_MARKERS
                ):
                    findings.append(
                        f"{path.name} afirma {phrase!r} sin evidencia registrada"
                    )
    return findings


# --------------------------------------------------------------------------
# 5 y 6 · versión y alcanzabilidad
# --------------------------------------------------------------------------

def check_doc_versions(root: Path) -> list[str]:
    findings: list[str] = []
    for path in sorted((root / "references").rglob("*.md")):
        if not VERSION_MARKER_RE.search(path.read_text(encoding="utf-8")):
            findings.append(f"{path.relative_to(root).as_posix()}: sin marca de versión")
    return findings


def check_reachability(root: Path) -> list[str]:
    references = sorted((root / "references").rglob("*.md"))
    corpus = "\n".join(path.read_text(encoding="utf-8") for path in _documents(root))
    return [
        f"{path.relative_to(root).as_posix()} no se menciona en ningún documento"
        for path in references
        if path.name not in corpus
    ]


def audit(root: Path, registry_path: Path) -> dict:
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "generated_at": now_iso(),
            "root": str(root),
            "ok": False,
            "failures": {"3": [f"el registro de reglas no es legible: {exc}"]},
            "counts": {},
        }

    findings = {
        "1": check_paths(root),
        "2": check_commands(root),
        "3": check_rules(root, registry),
        "4": check_remote_claims(root, registry.get("forbidden_remote_claims") or []),
        "5": check_doc_versions(root),
        "6": check_reachability(root),
    }
    populated = {code: items for code, items in findings.items() if items}
    return {
        "generated_at": now_iso(),
        "root": str(root),
        "registry": str(registry_path),
        "ok": not populated,
        "failures": populated,
        "counts": {
            "documents": len(_documents(root)),
            "references": len(list((root / "references").rglob("*.md"))),
            "rules": len(registry.get("rules") or []),
        },
    }


def exit_code_for(report: dict) -> int:
    codes = sorted(int(code) for code in (report.get("failures") or {}))
    return codes[0] if codes else 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.root).resolve()
    report = audit(root, root / args.registry if not Path(args.registry).is_absolute()
                   else Path(args.registry))
    write_atomic(Path(args.out), report)
    code = exit_code_for(report)
    if code:
        print(f"fail: {json.dumps(report['failures'], ensure_ascii=False)}", file=sys.stderr)
        return code
    print(
        f"ok: auditoría documental limpia ({report['counts']['documents']} documentos, "
        f"{report['counts']['references']} referencias, {report['counts']['rules']} reglas)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())