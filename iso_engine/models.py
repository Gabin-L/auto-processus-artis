"""Structures de données communes du moteur.

Les coordonnées de relevé (`Point3D`) sont en millimètres, dans un repère
local propre à la ligne (peu importe l'origine : seules les positions
relatives comptent pour tracer l'isométrique).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class JointType(str, Enum):
    """Type de jonction à un point du tracé, détermine si une soudure est comptée."""

    WELD = "weld"
    FLANGE = "flange"
    THREAD = "thread"
    END = "end"  # extrémité de ligne (piquage, équipement...) : pas de soudure


@dataclass(frozen=True)
class Point3D:
    x: float
    y: float
    z: float

    def as_tuple(self) -> tuple[float, float, float]:
        return (self.x, self.y, self.z)


@dataclass
class RoutePoint:
    """Un point relevé sur le tracé de la ligne (pliage, raccord, extrémité)."""

    seq: int
    position: Point3D
    joint_type: JointType = JointType.WELD
    fitting_type: str | None = None  # ex: "elbow90", "tee", "reducer", "valve_gate"
    fitting_ref: str | None = None  # référence catalogue / tag du composant
    nominal_size: str | None = None  # DN au point (si différent de la ligne, ex: réduction)
    note: str = ""


@dataclass
class LineHeader:
    """En-tête de ligne, reprise du BLE (bordereau de ligne)."""

    line_number: str
    project_code: str
    client: str = ""
    spec: str = ""
    nominal_size: str = ""
    schedule: str = ""
    material: str = ""
    fluid: str = ""
    insulation: str = ""
    pid_ref: str = ""
    drawing_number: str = ""
    revision: str = "A"
    author: str = ""
    date: str = ""


@dataclass
class IsoLine:
    """Une ligne complète : en-tête + tracé relevé, prête à être calculée."""

    header: LineHeader
    points: list[RoutePoint] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.points.sort(key=lambda p: p.seq)
