"""Inventario de un corpus Markdown para notemartin-study-translate.

Recorre ``--source``, calcula hash SHA-256, detecta codificación y saltos de
línea, clasifica por tipo (markdown, resource, other) y detecta la marca
``flag_mdx`` para alimentar la fase de preparación.

No sigue symlinks por defecto. Rechaza ``source_root`` que solape con
``--work`` o ``--out`` tras resolver a absolutas.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import sys
import unicodedata
from pathlib import Path

MARKDOWN_EXT = {".md", ".markdown", ".mdx"}
RESOURCE_EXT = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".pdf", ".zip",
}


class InventoryError(Exception):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def detect_encoding(data: bytes) -> tuple[str, str | None]:
    if not data:
        return ("utf-8", None)
    try:
        data.decode("utf-8", errors="strict")
        return ("utf-8", None)
    except UnicodeDecodeError as e:
        return ("binary", f"utf-8 decode failed at byte {e.start}")


def detect_line_ending(data: bytes) -> str:
    total_lf = data.count(b"\n")
    total_cr = data.count(b"\r")
    crlf = data.count(b"\r\n")
    lone_lf = max(total_lf - crlf, 0)
    lone_cr = max(total_cr - crlf, 0)
    has_crlf = crlf > 0
    if has_crlf and (lone_lf > 0 or lone_cr > 0):
        return "mixed"
    if has_crlf:
        return "crlf"
    if lone_cr > 0 and lone_lf == 0:
        return "cr"
    return "lf"


def classify(path: Path) -> tuple[str, bool]:
    ext = path.suffix.lower()
    if ext in MARKDOWN_EXT:
        return ("markdown", ext == ".mdx")
    if ext in RESOURCE_EXT:
        return ("resource", False)
    return ("other", False)


def normalize_for_collision(p: str) -> str:
    return unicodedata.normalize("NFC", unicodedata.normalize("NFD", p)).casefold()


def check_collisions(entries: list[dict]) -> list[tuple[str, str]]:
    seen: dict[str, str] = {}
    collisions: list[tuple[str, str]] = []
    for entry in entries:
        key = normalize_for_collision(entry["path"])
        if key in seen and seen[key] != entry["path"]:
            collisions.append((seen[key], entry["path"]))
        else:
            seen[key] = entry["path"]
    return collisions


def check_overlap(source_root: str, work: str | None, out: str | None) -> str | None:
    src = os.path.realpath(source_root)
    if work:
        if os.path.realpath(work) == src:
            return f"source_root solapa con work_root ({work})"
    if out:
        if os.path.realpath(out) == src:
            return f"source_root solapa con output_root ({out})"
    if work and out:
        if os.path.realpath(work) == os.path.realpath(out):
            return f"work_root solapa con output_root ({work} == {out})"
    return None


def walk_source(
    source_root: Path,
) -> list[dict]:
    out: list[dict] = []
    for dirpath, dirnames, filenames in os.walk(source_root, followlinks=False):
        for filename in filenames:
            abs_path = Path(dirpath) / filename
            try:
                lstat = abs_path.lstat()
            except OSError as e:
                raise InventoryError(f"no se pudo lstat {abs_path}: {e}")
            if lstat.st_mode & 0o170000 == 0o120000:
                raise InventoryError(
                    f"symlink detectado, no se sigue por defecto: {abs_path}"
                )
            data = abs_path.read_bytes()
            sha = sha256_bytes(data)
            enc, enc_err = detect_encoding(data)
            le = detect_line_ending(data)
            ftype, flag_mdx = classify(abs_path)
            rel = abs_path.relative_to(source_root).as_posix()
            entry = {
                "path": rel,
                "bytes": len(data),
                "sha256": sha,
                "encoding": enc,
                "line_ending": le,
                "type": ftype,
                "flag_mdx": flag_mdx,
            }
            if enc_err:
                entry["encoding_error"] = enc_err
            out.append(entry)
    out.sort(key=lambda e: e["path"])
    return out


def write_atomic(target: Path, payload: dict) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="inventory.py")
    p.add_argument("--source", required=True, help="Raíz del corpus a inventariar.")
    p.add_argument("--out", required=True, help="Ruta del JSON de salida.")
    p.add_argument("--work", default=None, help="Raíz de trabajo, para validar disyunción.")
    p.add_argument("--output-root", dest="output_root", default=None, help="Raíz de salida, para validar disyunción.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source_root = Path(args.source).resolve()
    if not source_root.is_dir():
        print(f"error: source_root no es directorio: {source_root}", file=sys.stderr)
        return 2

    overlap = check_overlap(str(source_root), args.work, args.output_root)
    if overlap:
        print(f"error: {overlap}", file=sys.stderr)
        return 3

    try:
        entries = walk_source(source_root)
    except InventoryError as e:
        print(f"error: {e}", file=sys.stderr)
        return 4

    collisions = check_collisions(entries)
    if collisions:
        for a, b in collisions:
            print(f"error: colisión de rutas tras normalización: {a} == {b}", file=sys.stderr)
        return 5

    payload = {
        "source_root": str(source_root),
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_files": len(entries),
        "total_bytes": sum(e["bytes"] for e in entries),
        "files": entries,
    }
    write_atomic(Path(args.out), payload)
    print(f"ok: {len(entries)} archivos, {payload['total_bytes']} bytes -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())