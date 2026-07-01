"""Assemble le résultat calculé pour une ligne et le sérialise en JSON.

Le JSON produit est le seul contrat entre ce moteur (Python, testable) et la
macro de dessin MicroStation (VBA, voir /microstation/IsoBuilder.bas). Il ne
contient que des données déjà calculées : la macro n'a plus qu'à placer des
éléments, elle ne recalcule aucune géométrie.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .bom import build_bom
from .models import IsoLine
from .projection import project_line
from .weld_numbering import assign_weld_numbers, joint_summary


def compute_drawing(line: IsoLine, scale: float = 1.0) -> dict:
    segments = project_line(line, scale=scale)
    welds = assign_weld_numbers(line)
    joints = joint_summary(line)
    bom = build_bom(line)

    vertices = []
    seen_seq = set()
    for seg in (segments[0].start, *[s.end for s in segments]):
        if seg.seq in seen_seq:
            continue
        seen_seq.add(seg.seq)
        vertices.append(
            {
                "seq": seg.seq,
                "x2d": round(seg.point2d.x, 3),
                "y2d": round(seg.point2d.y, 3),
                "x3d": seg.point3d.x,
                "y3d": seg.point3d.y,
                "z3d": seg.point3d.z,
                "joint_type": seg.source.joint_type.value,
                "fitting_type": seg.source.fitting_type,
                "fitting_ref": seg.source.fitting_ref,
                "nominal_size": seg.source.nominal_size,
                "note": seg.source.note,
            }
        )

    weld_by_seq = {w.point.seq: w.weld_id for w in welds}

    return {
        "header": asdict(line.header),
        "vertices": vertices,
        "segments": [
            {
                "start_seq": seg.start.seq,
                "end_seq": seg.end.seq,
                "true_length_mm": round(seg.true_length_mm, 1),
            }
            for seg in segments
        ],
        "welds": [{"weld_id": w.weld_id, "seq": w.point.seq} for w in welds],
        "joints_summary": {jt.value: [p.seq for p in pts] for jt, pts in joints.items()},
        "bom": [asdict(line_item) for line_item in bom],
        "weld_count": len(welds),
        "_weld_by_seq": weld_by_seq,
    }


def export_json(line: IsoLine, path: str | Path, scale: float = 1.0, indent: int = 2) -> None:
    drawing = compute_drawing(line, scale=scale)
    Path(path).write_text(json.dumps(drawing, indent=indent, ensure_ascii=False), encoding="utf-8")
