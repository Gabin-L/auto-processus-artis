"""Moteur de calcul pour la génération automatique de mises en plan isométriques.

Ce package ne dessine rien lui-même : il prend les données de relevé terrain
(BLE + mesures) et calcule tout ce qu'un dessinateur ferait à la main avant de
tracer l'isométrique (projection isométrique, longueurs réelles à coter,
nomenclature, numérotation des soudures). Le résultat est exporté en JSON,
consommé ensuite par la macro MicroStation (voir /microstation) qui se charge
du dessin dans le .dgn.
"""
