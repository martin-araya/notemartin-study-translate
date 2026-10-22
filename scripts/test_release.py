"""Verifica el paquete beta del núcleo (fase 050) y emite el reporte
de release (fase 059).

Ejecuta las verificaciones finales sobre el alcance del piloto:

- ``validate.py`` sin errores.
- ``audit_terminology.py`` sin ``forbidden_use``.
- ``check_integrity.py`` con ``integrity_ok: true``.
- ``raise_issues.py`` ejecutado y conteo por severidad registrado.
- Manifiesto declara ``pilot_approved: true``.

Genera ``evals/release/RELEASE_NOTES.md`` con secciones explícitas
(fase 059):

- ``## Pruebas automáticas`` — conteos de pytest y scripts ejecutados.
- ``## Revisión asistida`` — ``raise_issues.py`` + ``audit_terminology.py``.
- ``## Revisión humana`` — segmentos revisados manualmente (lista
  explícita o "ninguna registrada").
- ``## Notion`` — "no verificado: la importación la realiza el
  usuario siguiendo ``references/notion-handoff.md``".
- ``## Limitaciones aceptadas`` — issues no bloqueantes con motivo.

Devuelve código 0 si la beta está lista y no hay issues críticos.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="test_release.py")
    p.add_argument("--source-root", required=True)
    p.add_argument("--translations", required=True)
    p.add_argument("--inventory", required=True)
    p.add_argument("--manifest", required=True)
    p.add_argument("--segments", required=True)
    p.add_argument("--packets", required=True)
    p.add_argument("--snapshots", required=True)
    p.add_argument("--glossary", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--release-notes", required=True)
    p.add_argument("--human-reviewed", default=None,
                   help="JSON con la lista de segment_id revisados por humanos.")
    p.add_argument("--pytest-summary", default=None,
                   help="JSON con resumen de pytest (passed/failed/skipped).")
    return p.parse_args(argv)


def run_step(args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(args, capture_output=True, text=True, check=False)
    return proc.returncode, proc.stdout, proc.stderr


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def load_json_or_default(path: str | None, default: dict) -> dict:
    if not path:
        return default
    p = Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return default


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    issues: list[dict] = []
    accepted_limitations: list[dict] = []

    validate_report = Path(args.output_dir) / "validate.json"
    rc, _, stderr = run_step([
        sys.executable, str(ROOT / "scripts" / "validate.py"),
        "--source", args.source_root,
        "--output-dir", args.output_dir,
        "--packets", args.packets,
        "--segments", args.segments,
        "--translations", args.translations,
        "--snapshots", args.snapshots,
        "--anchors", str(Path(args.output_dir) / "anchors"),
        "--manifest", args.manifest,
        "--out", str(validate_report),
    ])
    if rc != 0:
        issues.append({"check": "validate", "severity": "critical", "message": f"validate.py falló: {stderr}"})

    integrity_out = Path(args.output_dir) / "integrity.json"
    rc, _, stderr = run_step([
        sys.executable, str(ROOT / "scripts" / "check_integrity.py"),
        "--manifest", args.manifest,
        "--out", str(integrity_out),
    ])
    if rc != 0:
        issues.append({"check": "check_integrity", "severity": "critical", "message": f"check_integrity.py falló: {stderr}"})

    audit_report = Path(args.output_dir) / "audit.json"
    rc, _, stderr = run_step([
        sys.executable, str(ROOT / "scripts" / "audit_terminology.py"),
        "--translations", args.translations,
        "--glossary", args.glossary,
        "--out", str(audit_report),
    ])
    if rc != 0:
        issues.append({"check": "audit_terminology", "severity": "critical", "message": "audit_terminology.py reportó forbidden_use"})
    if audit_report.exists():
        audit = json.loads(audit_report.read_text(encoding="utf-8"))
        if audit.get("summary", {}).get("forbidden_uses", 0) > 0:
            issues.append({"check": "forbidden_uses", "severity": "critical", "message": f"forbidden_uses: {audit['summary']['forbidden_uses']}"})

    issues_path = Path(args.output_dir) / "issues.json"
    rc, _, stderr = run_step([
        sys.executable, str(ROOT / "scripts" / "raise_issues.py"),
        "--translations", args.translations,
        "--segments", args.segments,
        "--issues-out", str(issues_path),
    ])
    if rc != 0:
        issues.append({"check": "issues_critical", "severity": "critical", "message": "issues.json contiene issues críticos"})

    issues_payload = json.loads(issues_path.read_text(encoding="utf-8")) if issues_path.exists() else {"by_severity": {}, "issues": []}
    for issue in issues_payload.get("issues", []):
        if issue.get("severity") in ("info", "warning"):
            accepted_limitations.append({
                "category": issue.get("category"),
                "severity": issue.get("severity"),
                "message": issue.get("message"),
                "path": issue.get("path"),
                "segment_id": issue.get("segment_id"),
            })

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    pilot_approved = bool(manifest.get("pilot_approved"))
    coverage = manifest.get("coverage", {})

    if not pilot_approved:
        issues.append({"check": "pilot_approved", "severity": "critical", "message": "manifiesto no declara pilot_approved: true"})
    if coverage.get("blocked", 0) > 0:
        issues.append({"check": "coverage_blocked", "severity": "critical", "message": f"cobertura con archivos bloqueados: {coverage.get('blocked', 0)}"})
    if not manifest.get("integrity_ok", False):
        issues.append({"check": "integrity_ok", "severity": "critical", "message": "integrity_ok: false"})

    html_dir = Path(SCRIPT_DIR).parent / "tests" / "fixtures" / "html"
    html_fixtures_count = len(list(html_dir.glob("*.md"))) if html_dir.is_dir() else 0
    html_tests_count = sum(
        1 for p in (Path(SCRIPT_DIR).parent / "tests").glob("test_html_*.py")
    )

    release_dir = Path(args.release_notes).parent
    release_dir.mkdir(parents=True, exist_ok=True)

    artifact_paths = [
        Path(args.manifest),
        Path(args.glossary),
        validate_report,
        integrity_out,
        audit_report,
        issues_path,
    ]
    artifacts: list[dict] = []
    for path in artifact_paths:
        if path.exists():
            artifacts.append({"path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size})

    pytest_summary = load_json_or_default(args.pytest_summary, {"passed": 0, "failed": 0, "skipped": 0})
    human_review = load_json_or_default(args.human_reviewed, {"segments": []})
    human_segments = human_review.get("segments", []) or []
    if not isinstance(human_segments, list):
        human_segments = []

    generated_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        f"# Notas de release — {generated_at}",
        "",
        "## Pruebas automáticas",
        "",
        f"- `validate.py`: {'ok' if not any(i['check'] == 'validate' for i in issues) else 'falló'}",
        f"- `check_integrity.py`: {'ok' if not any(i['check'] == 'check_integrity' for i in issues) else 'falló'}",
        f"- `audit_terminology.py`: {'ok' if not any(i['check'] == 'audit_terminology' for i in issues) else 'falló'}",
        f"- `pytest` totales: passed={pytest_summary.get('passed', '?')} "
        f"failed={pytest_summary.get('failed', '?')} skipped={pytest_summary.get('skipped', '?')}",
        f"- Scripts ejecutados en este gate: validate, check_integrity, audit_terminology, raise_issues.",
        "",
        "## Revisión asistida",
        "",
        f"- `raise_issues.py` total: {issues_payload.get('total_issues', 0)}",
        f"- Por severidad: critical={issues_payload.get('by_severity', {}).get('critical', 0)}, "
        f"major={issues_payload.get('by_severity', {}).get('major', 0)}, "
        f"info={issues_payload.get('by_severity', {}).get('info', 0)}",
        "- `audit_terminology.py` revisa coherencia de glosario y prohíbe usos no permitidos.",
        "",
        "## Revisión humana",
        "",
    ]
    if human_segments:
        lines.append(f"- {len(human_segments)} segmentos revisados manualmente.")
        lines.append(f"- Lista: {', '.join(str(s) for s in human_segments[:20])}{'…' if len(human_segments) > 20 else ''}")
    else:
        lines.append("- Ninguna registrada en esta ejecución. Pasa `--human-reviewed=<path>` con un JSON `{segments: [...]}` para incluir la lista explícita.")
    lines.extend([
        "",
        "## Notion",
        "",
        "- No verificado. La importación a Notion la realiza el usuario siguiendo `references/notion-handoff.md`.",
        "- La entrega local es Markdown en disco. Esta skill no publica por API en Notion ni en otros servicios remotos.",
        "",
        "## Estado del beta",
        "",
        f"- `pilot_approved`: {'true' if pilot_approved else 'false'}",
        f"- `integrity_ok`: {'true' if manifest.get('integrity_ok') else 'false'}",
        f"- `coverage.integrated`: {coverage.get('integrated', '?')}/{coverage.get('total', '?')}",
        "",
        "## Artefactos verificados",
        "",
        "| Ruta | SHA-256 | Bytes |",
        "|---|---|---|",
    ])
    for a in artifacts:
        lines.append(f"| `{a['path']}` | `{a['sha256'][:16]}…` | {a['bytes']} |")
    lines.extend([
        "",
        "## Extensión HTML",
        "",
        f"- Fixtures sintéticos en `tests/fixtures/html/`: {html_fixtures_count}.",
        f"- Tests del módulo HTML: {html_tests_count} archivos `test_html_*.py`.",
        "- Gate `profile.html.enabled`: opt-in. Por defecto desactivado.",
        "- Cubre tablas complejas, clasificación código vs contenido, HTML malformado y matriz de compatibilidad local.",
        "- Importación a Notion no verificada (ver `references/notion-handoff.md`).",
        "",
        "## Issues críticos detectados",
        "",
    ])
    critical_issues = [i for i in issues if i["severity"] == "critical"]
    if not critical_issues:
        lines.append("- Ninguno. La beta está lista para entrega local.")
    else:
        for i in critical_issues:
            lines.append(f"- {i['check']}: {i['message']}")
    lines.extend([
        "",
        "## Limitaciones aceptadas",
        "",
    ])
    if not accepted_limitations:
        lines.append("- Ninguna registrada como issue no crítico en esta ejecución.")
    else:
        for lim in accepted_limitations:
            scope = lim.get("segment_id") or lim.get("path") or "global"
            lines.append(f"- {lim['severity'].upper()} ({lim.get('category', '?')}) {scope}: {lim['message']}")
    Path(args.release_notes).write_text("\n".join(lines), encoding="utf-8")

    critical = len(critical_issues)
    print(f"ok: critical={critical} issues={len(issues)} -> {args.release_notes}")
    return 0 if critical == 0 else 1


if __name__ == "__main__":
    sys.exit(main())