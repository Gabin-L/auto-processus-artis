"""Génération de la nomenclature (BOM) à partir du tracé relevé.

Deux familles de lignes de nomenclature :
- tuyau droit : longueur cumulée par diamètre (déduite des tronçons projetés,
  donc de la vraie longueur mesurée sur le terrain) ;
- raccords/robinetterie : comptage par (type de raccord, diamètre, référence).

Simplification connue : la longueur de tuyau droit n'est pas diminuée des
longueurs hors-tout (lay length) des raccords, faute de table de référence
des composants dans ce module. À affiner une fois la bibliothèque de
composants standard branchée (voir docs/workflow.md).
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass

from .models import IsoLine, RoutePoint
from .projection import project_line


@dataclass(frozen=True)
class BomLine:
    item_type: str  # "pipe" ou "fitting"
    description: str
    nominal_size: str
    quantity: float
    unit: str  # "mm" pour le tuyau, "u" (unité) pour les raccords
    spec: str = ""
    ref: str = ""


def _active_size_by_seq(line: IsoLine) -> dict[int, str]:
    """Diamètre nominal actif juste après chaque point (gère les réductions)."""
    points = sorted(line.points, key=lambda p: p.seq)
    current = line.header.nominal_size
    sizes: dict[int, str] = {}
    for point in points:
        if point.nominal_size:
            current = point.nominal_size
        sizes[point.seq] = current
    return sizes


def build_pipe_lines(line: IsoLine) -> list[BomLine]:
    """Longueur de tuyau droit cumulée, groupée par diamètre."""
    segments = project_line(line)
    sizes = _active_size_by_seq(line)

    totals: "OrderedDict[str, float]" = OrderedDict()
    for segment in segments:
        # le diamètre d'un tronçon est celui en vigueur à son point de départ
        size = sizes[segment.start.seq]
        totals[size] = totals.get(size, 0.0) + segment.true_length_mm

    return [
        BomLine(
            item_type="pipe",
            description=f"Tube {size}",
            nominal_size=size,
            quantity=round(length_mm, 1),
            unit="mm",
            spec=line.header.spec,
        )
        for size, length_mm in totals.items()
    ]


def build_fitting_lines(line: IsoLine) -> list[BomLine]:
    """Comptage des raccords/robinetterie, groupés par (type, diamètre, référence)."""
    sizes = _active_size_by_seq(line)
    counts: "OrderedDict[tuple[str, str, str], int]" = OrderedDict()

    for point in line.points:
        if not point.fitting_type:
            continue
        size = point.nominal_size or sizes[point.seq]
        key = (point.fitting_type, size, point.fitting_ref or "")
        counts[key] = counts.get(key, 0) + 1

    return [
        BomLine(
            item_type="fitting",
            description=fitting_type,
            nominal_size=size,
            quantity=qty,
            unit="u",
            spec=line.header.spec,
            ref=ref,
        )
        for (fitting_type, size, ref), qty in counts.items()
    ]


def build_bom(line: IsoLine) -> list[BomLine]:
    return build_pipe_lines(line) + build_fitting_lines(line)
