"""Projection isométrique tuyauterie.

Convention standard utilisée en dessin isométrique de tuyauterie : l'axe
vertical (Z, altitude) reste vertical à l'écran, les deux axes horizontaux
(X, Y) sont projetés à 30° de part et d'autre de l'horizontale. C'est la
même convention que celle enseignée en dessin technique et utilisée par les
générateurs d'isométriques du marché (ISOGEN et équivalents) :

    screen_x = (X - Y) * cos(30°)
    screen_y = (X + Y) * sin(30°) + Z

Tant que chaque tronçon du relevé est aligné sur un des trois axes (ce qui
est le cas d'un tracé de tuyauterie orthogonal), cette transformation place
automatiquement chaque tronçon sur un des angles isométriques standard
(0°, 30°, 90°, 150°...) sans qu'il soit nécessaire de coder les directions
à la main.

Simplification connue : le tracé est ici projeté à l'échelle réelle (à un
facteur d'échelle près). Les outils professionnels type ISOGEN dessinent en
général les tronçons à une longueur schématique (non à l'échelle) pour la
lisibilité, la vraie longueur n'apparaissant que dans la cote. Ce
raffinement n'est pas implémenté ici (voir docs/workflow.md, phase 3).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .models import IsoLine, Point3D, RoutePoint

_COS_30 = math.cos(math.radians(30))
_SIN_30 = math.sin(math.radians(30))


@dataclass(frozen=True)
class Point2D:
    x: float
    y: float


@dataclass(frozen=True)
class ProjectedVertex:
    seq: int
    point3d: Point3D
    point2d: Point2D
    source: RoutePoint


@dataclass(frozen=True)
class ProjectedSegment:
    start: ProjectedVertex
    end: ProjectedVertex
    true_length_mm: float  # longueur réelle mesurée sur le terrain, à coter

    @property
    def is_degenerate(self) -> bool:
        """Deux points relevés confondus (ex: saisie en double)."""
        return self.true_length_mm < 1e-6


def project_point(p: Point3D, scale: float = 1.0) -> Point2D:
    x = (p.x - p.y) * _COS_30 * scale
    y = (p.x + p.y) * _SIN_30 * scale + p.z * scale
    return Point2D(x, y)


def true_length(a: Point3D, b: Point3D) -> float:
    return math.dist(a.as_tuple(), b.as_tuple())


def project_line(line: IsoLine, scale: float = 1.0) -> list[ProjectedSegment]:
    """Projette le tracé relevé d'une ligne en une suite de tronçons 2D.

    Retourne un tronçon par paire de points consécutifs du relevé, dans
    l'ordre de `seq`. Chaque tronçon porte sa longueur réelle (`true_length_mm`),
    indépendante de l'échelle de dessin, destinée à la cotation.
    """
    if len(line.points) < 2:
        raise ValueError(
            f"La ligne {line.header.line_number} a moins de 2 points relevés "
            "(un tracé nécessite au moins un point de départ et un point d'arrivée)"
        )

    vertices = [
        ProjectedVertex(seq=p.seq, point3d=p.position, point2d=project_point(p.position, scale), source=p)
        for p in line.points
    ]

    segments = []
    for start, end in zip(vertices, vertices[1:]):
        segments.append(
            ProjectedSegment(
                start=start,
                end=end,
                true_length_mm=true_length(start.point3d, end.point3d),
            )
        )
    return segments
