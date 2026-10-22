"""Sonda de portabilidad del entorno (fase 147).

No comprueba que el paquete funcione: comprueba qué **supuestos** del
entorno se cumplen aquí y ahora, para que la matriz de portabilidad pueda
separar lo diseñado de lo ejecutado.

Cada comprobación escribe su resultado en el informe, no solo un booleano,
para que un fallo en otro sistema se pueda diagnosticar.

Uso::

    python scripts/probe_platform.py --out reports/maintenance/platform_probe.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from delivery_common import now_iso, write_atomic  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="probe_platform.py")
    p.add_argument("--out", required=True)
    return p.parse_args(argv)


def _probe_fcntl(work: Path) -> dict:
    if not hasattr(os, "fork") or os.name == "nt":
        return {"available": False, "reason": "fcntl no existe en esta plataforma"}
    try:
        import fcntl
    except ImportError as exc:  # pragma: no cover - depende del SO
        return {"available": False, "reason": str(exc)}
    target = work / "lock.txt"
    try:
        target.write_text("x", encoding="utf-8")
        with open(target, "r+", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        return {"available": True, "detail": "flock exclusivo y liberación verificados"}
    except OSError as exc:
        return {"available": False, "reason": str(exc)}


def _probe_atomic_replace(work: Path) -> dict:
    target = work / "atomic.txt"
    tmp = work / "atomic.tmp"
    try:
        target.write_text("nuevo", encoding="utf-8")
        tmp.write_text("temporal", encoding="utf-8")
        os.replace(tmp, target)
        return {
            "available": True,
            "detail": target.read_text(encoding="utf-8"),
        }
    except OSError as exc:
        return {"available": False, "reason": str(exc)}


def _probe_case_insensitive(work: Path) -> dict:
    folder = work / "case"
    folder.mkdir(exist_ok=True)
    (folder / "Guia.md").write_text("a", encoding="utf-8")
    try:
        (folder / "guia.md").write_text("b", encoding="utf-8")
    except OSError as exc:
        return {"sensitive": True, "detail": f"el segundo nombre falla: {exc}"}
    names = sorted(p.name for p in folder.iterdir())
    collided = len(names) == 1
    for path in folder.iterdir():
        path.unlink()
    folder.rmdir()
    return {"sensitive": not collided,
            "detail": "nombres que solo difieren en mayúsculas se solapan"
                      if collided else "el sistema conserva ambos nombres"}


def _probe_unicode_names(work: Path) -> dict:
    names = ("acentuado-ñ.md", "emoji-📄.md", "espacio en el nombre.md")
    created = []
    for name in names:
        target = work / name
        try:
            target.write_text("ok", encoding="utf-8")
            created.append(target)
        except OSError as exc:
            return {"available": False, "failed": name, "reason": str(exc)}
    for target in created:
        target.unlink()
    return {"available": True, "detail": f"{len(names)} nombres no ASCII creados y leídos"}


def _probe_long_names(work: Path) -> dict:
    name = "n" * 200
    target = work / f"{name}.md"
    try:
        target.write_text("ok", encoding="utf-8")
        size = len(target.name.encode("utf-8"))
        target.unlink()
        return {"available": True, "detail": f"componente de {size} bytes"}
    except OSError as exc:
        return {"available": False, "reason": str(exc)}


def probe() -> dict:
    with tempfile.TemporaryDirectory(prefix="nst-probe-") as raw:
        work = Path(raw)
        report = {
            "generated_at": now_iso(),
            "python_version": sys.version.split()[0],
            "python_implementation": sys.implementation.name,
            "os_name": os.name,
            "platform": sys.platform,
            "filesystem_encoding": sys.getfilesystemencoding(),
            "filesystem_errors": sys.getfilesystemencodeerrors(),
            "default_newline": repr(os.linesep),
            "hash_algorithms": sorted(
                name for name in ("sha256", "blake2b") if name in hashlib.algorithms_available
            ),
            "fcntl": _probe_fcntl(work),
            "atomic_replace": _probe_atomic_replace(work),
            "case_insensitive_fs": _probe_case_insensitive(work),
            "unicode_names": _probe_unicode_names(work),
            "long_names": _probe_long_names(work),
            "zoneinfo": _probe_zoneinfo(),
        }
    return report


def _probe_zoneinfo() -> dict:
    try:
        from zoneinfo import ZoneInfo

        ZoneInfo("Europe/Madrid")
        return {"available": True, "detail": "ZoneInfo('Europe/Madrid') resuelto"}
    except Exception as exc:  # pragma: no cover - depende del SO
        return {"available": False, "reason": str(exc)}


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = probe()
    write_atomic(Path(args.out), report)
    print(
        f"ok: sonda de portabilidad escrita -> {args.out} "
        f"({report['os_name']}/{report['platform']}, python {report['python_version']})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())