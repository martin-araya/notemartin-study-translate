"""Adaptador de prueba: desplaza una línea de cada rango (fase 144).

Simula una versión del parser que declara los rangos desplazados en una
línea. Sirve para comprobar que `compare_parser.py` bloquea la promoción
cuando cambian los rangos, sin instalar nada.
"""


def transform(features: dict) -> dict:
    for document in features.values():
        for entry in document["ranges"]:
            entry["lines"] = [entry["lines"][0] + 1, entry["lines"][1] + 1]
    return features