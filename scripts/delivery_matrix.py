"""Matriz de destinos de entrega (fase 139).

Emite ``delivery_matrix.json`` con los destinos que la skill sabe
preparar, sus casos, sus limitaciones y el estado real de su evidencia.

Reglas de honestidad del artefacto:

- ``notion-manual`` es el destino canónico. Su evidencia la aporta el
  usuario; sin ella la celda queda ``unverified``.
- ``plain-markdown-local`` es un **adaptador interno de la propia
  skill**, no una aplicación de escritorio. Declara
  ``real_app_evidence: false`` y su evidencia es ``local_fixture_only``.
- Ningún destino se activa por omisión: todos declaran
  ``activation: explicit``.

Uso::

    python scripts/delivery_matrix.py --out reports/delivery_matrix.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from delivery_common import now_iso, write_atomic  # noqa: E402

EXIT_OK = 0
EXIT_INPUT_ERROR = 2

DESTINATIONS = [
    {
        "destination_id": "notion-manual",
        "name": "Notion (importación manual)",
        "kind": "canonical",
        "delivery_profile": None,
        "import_method": "manual",
        "activation": "explicit",
        "evidence_kind": "user_reported",
        "real_app_evidence": False,
        "verified": False,
        "cases": [
            "tests/test_import_evidence.py::test_template_nace_sin_verificar",
            "tests/test_import_evidence.py::test_evidencia_con_revisor_humano_se_acepta",
            "tests/fixtures/delivery/canonical/",
        ],
        "limitations": [
            "La navegación remota, el render de tablas, código e imágenes no los verifica la skill.",
            "Un Markdown válido no demuestra que Notion conserve la construcción.",
            "El comportamiento puede cambiar entre versiones de Notion.",
        ],
        "notes": "Destino canónico del núcleo. El estado remoto vive en import_evidence.json.",
    },
    {
        "destination_id": "plain-markdown-local",
        "name": "Markdown plano local (adaptador interno)",
        "kind": "local_adapter",
        "delivery_profile": "references/delivery-profiles/plain-markdown-local.json",
        "import_method": "filesystem",
        "activation": "explicit",
        "evidence_kind": "local_fixture_only",
        "real_app_evidence": False,
        "verified": False,
        "cases": [
            "tests/test_adapt_delivery.py",
            "tests/test_compare_delivery.py",
            "tests/fixtures/delivery/canonical/",
        ],
        "limitations": [
            "No se ha probado en una aplicación de escritorio: la evidencia es de fixtures locales.",
            "Renombrar recursos rompe los enlaces externos que usen la ruta antigua.",
            "La adaptación solo cubre rutas y nombres; no resuelve destinos que no acepten Markdown.",
        ],
        "notes": "Existe porque no hay ningún importador local instalado en el entorno de desarrollo.",
    },
]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="delivery_matrix.py")
    p.add_argument("--out", required=True)
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    destinations = []
    for destination in DESTINATIONS:
        entry = dict(destination)
        profile_ref = entry.get("delivery_profile")
        if profile_ref:
            profile_path = ROOT / profile_ref
            if not profile_path.exists():
                print(f"error: perfil de entrega inexistente: {profile_ref}", file=sys.stderr)
                return EXIT_INPUT_ERROR
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            entry["profile_version"] = profile.get("version")
            entry["rules"] = [r.get("rule_id") for r in profile.get("rules") or []]
        destinations.append(entry)

    payload = {
        "generated_at": now_iso(),
        "skill": "notemartin-study-translate",
        "schema_version": "1",
        "destinations": destinations,
        "any_verified": any(d.get("verified") for d in destinations),
        "note": (
            "La matriz describe qué se puede preparar, no qué funciona en cada destino. "
            "Un destino solo pasa a verified con evidencia aportada por una persona."
        ),
    }
    write_atomic(Path(args.out), payload)
    print(f"ok: {len(destinations)} destinos -> {args.out}")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())