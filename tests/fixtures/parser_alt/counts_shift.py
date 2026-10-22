"""Adaptador de prueba: cambia un recuento sin tocar rangos ni slugs (144).

Un cambio de recuento significa que la candidata interpreta el documento de
otra forma. También bloquea la promoción: rangos iguales no bastan.
"""


def transform(features: dict) -> dict:
    for document in features.values():
        document["tokens"] = document["tokens"] + 3
    return features