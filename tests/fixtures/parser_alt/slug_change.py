"""Adaptador de prueba: cambia un slug de encabezado (fase 144).

Simula una versión del parser o un algoritmo de anclas que produce un slug
distinto para el mismo encabezado. Debe bloquear la promoción.
"""


def transform(features: dict) -> dict:
    for document in features.values():
        if document["slugs"]:
            document["slugs"][0] = document["slugs"][0] + "-alterado"
    return features