import json
from pathlib import Path

from iso_engine.export import compute_drawing, export_json
from iso_engine.input_parser import parse_iso_line

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"


def _sample_line():
    return parse_iso_line(EXAMPLES / "sample_header.csv", EXAMPLES / "sample_points.csv")


def test_compute_drawing_on_sample_line():
    drawing = compute_drawing(_sample_line())
    assert drawing["header"]["line_number"] == "AF145-L-014"
    assert len(drawing["vertices"]) == 6
    assert len(drawing["segments"]) == 5
    # 6 points, départ + fin exclus des soudures, une jonction est bridée (vanne) -> 3 soudures
    assert drawing["weld_count"] == 3
    assert {b["item_type"] for b in drawing["bom"]} == {"pipe", "fitting"}


def test_export_json_writes_valid_file(tmp_path):
    out = tmp_path / "drawing.json"
    export_json(_sample_line(), out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["header"]["project_code"] == "AF145"
    assert len(data["welds"]) == 3
