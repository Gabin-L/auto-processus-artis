"""Lecture des fichiers d'entrée (CSV) issus du BLE et du relevé terrain.

Deux fichiers par ligne :

- un CSV "en-tête" à deux colonnes (`key,value`) reprenant les champs du BLE
  (voir docs/data_schema.md pour la liste des clés reconnues) ;
- un CSV "points" listant les points relevés le long du tracé, un par ligne,
  dans l'ordre du parcours (colonnes : seq, x_mm, y_mm, z_mm, joint_type,
  fitting_type, fitting_ref, nominal_size, note).

Ce module ne fait aucune hypothèse sur l'outil de mesure (laser ou main) :
il attend des coordonnées déjà réduites à un repère local unique pour la
ligne (peu importe l'origine, seules les positions relatives comptent).
"""

from __future__ import annotations

import csv
from pathlib import Path

from .models import IsoLine, JointType, LineHeader, Point3D, RoutePoint

_REQUIRED_HEADER_KEYS = ("line_number", "project_code")
_HEADER_FIELDS = {f for f in LineHeader.__dataclass_fields__}


def parse_line_header(path: str | Path) -> LineHeader:
    values: dict[str, str] = {}
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        _require_columns(reader.fieldnames, {"key", "value"}, path)
        for row in reader:
            key = (row["key"] or "").strip()
            if not key:
                continue
            if key not in _HEADER_FIELDS:
                raise ValueError(
                    f"{path}: clé d'en-tête inconnue '{key}'. "
                    f"Clés valides : {sorted(_HEADER_FIELDS)}"
                )
            values[key] = (row["value"] or "").strip()

    missing = [k for k in _REQUIRED_HEADER_KEYS if not values.get(k)]
    if missing:
        raise ValueError(f"{path}: champ(s) d'en-tête obligatoire(s) manquant(s) : {missing}")

    return LineHeader(**values)


def parse_route_points(path: str | Path) -> list[RoutePoint]:
    points: list[RoutePoint] = []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        _require_columns(reader.fieldnames, {"seq", "x_mm", "y_mm", "z_mm"}, path)
        for row_num, row in enumerate(reader, start=2):  # ligne 1 = en-têtes
            points.append(_parse_point_row(row, path, row_num))

    if len(points) < 2:
        raise ValueError(f"{path}: au moins 2 points relevés sont nécessaires, {len(points)} trouvé(s)")
    return points


def _parse_point_row(row: dict[str, str], path: str | Path, row_num: int) -> RoutePoint:
    try:
        seq = int(row["seq"])
        x = float(row["x_mm"])
        y = float(row["y_mm"])
        z = float(row["z_mm"])
    except (KeyError, ValueError) as exc:
        raise ValueError(f"{path}, ligne {row_num}: seq/x_mm/y_mm/z_mm invalide(s) ({exc})") from exc

    joint_raw = (row.get("joint_type") or "").strip().lower() or JointType.WELD.value
    try:
        joint_type = JointType(joint_raw)
    except ValueError as exc:
        raise ValueError(
            f"{path}, ligne {row_num}: joint_type '{joint_raw}' invalide. "
            f"Valeurs possibles : {[j.value for j in JointType]}"
        ) from exc

    return RoutePoint(
        seq=seq,
        position=Point3D(x, y, z),
        joint_type=joint_type,
        fitting_type=(row.get("fitting_type") or "").strip() or None,
        fitting_ref=(row.get("fitting_ref") or "").strip() or None,
        nominal_size=(row.get("nominal_size") or "").strip() or None,
        note=(row.get("note") or "").strip(),
    )


def parse_iso_line(header_path: str | Path, points_path: str | Path) -> IsoLine:
    header = parse_line_header(header_path)
    points = parse_route_points(points_path)
    return IsoLine(header=header, points=points)


def _require_columns(fieldnames: list[str] | None, required: set[str], path: str | Path) -> None:
    present = set(fieldnames or [])
    missing = required - present
    if missing:
        raise ValueError(f"{path}: colonne(s) manquante(s) dans l'en-tête CSV : {sorted(missing)}")
