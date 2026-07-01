"""Numérotation automatique des soudures le long d'un tracé.

Règle : chaque point relevé dont le `joint_type` est WELD reçoit un repère
séquentiel (W1, W2, ...) dans l'ordre du tracé. Le premier point de la ligne
(départ, seq minimal) n'est jamais une soudure : c'est une extrémité. Les
jonctions bridées (FLANGE), filetées (THREAD) ou les extrémités (END) ne
comptent pas comme soudures mais sont conservées dans le relevé des
jonctions pour la nomenclature.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import IsoLine, JointType, RoutePoint


@dataclass(frozen=True)
class WeldMark:
    weld_id: str
    point: RoutePoint


def assign_weld_numbers(line: IsoLine, prefix: str = "W") -> list[WeldMark]:
    """Attribue les repères de soudure dans l'ordre du tracé.

    Le point de départ de la ligne (le premier de la séquence) est toujours
    exclu : une ligne ne commence pas par une soudure.
    """
    points = sorted(line.points, key=lambda p: p.seq)
    marks: list[WeldMark] = []
    counter = 0
    for point in points[1:]:
        if point.joint_type is JointType.WELD:
            counter += 1
            marks.append(WeldMark(weld_id=f"{prefix}{counter}", point=point))
    return marks


def joint_summary(line: IsoLine) -> dict[JointType, list[RoutePoint]]:
    """Regroupe tous les points de jonction du tracé par type, pour vérification."""
    points = sorted(line.points, key=lambda p: p.seq)[1:]
    summary: dict[JointType, list[RoutePoint]] = {jt: [] for jt in JointType}
    for point in points:
        summary[point.joint_type].append(point)
    return summary
