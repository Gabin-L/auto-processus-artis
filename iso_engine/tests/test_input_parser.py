from pathlib import Path

import pytest

from iso_engine.input_parser import parse_iso_line, parse_line_header, parse_route_points
from iso_engine.models import JointType

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"


def test_parse_sample_header():
    header = parse_line_header(EXAMPLES / "sample_header.csv")
    assert header.line_number == "AF145-L-014"
    assert header.project_code == "AF145"
    assert header.nominal_size == "DN80"


def test_parse_sample_points():
    points = parse_route_points(EXAMPLES / "sample_points.csv")
    assert len(points) == 6
    assert points[0].joint_type == JointType.END
    assert points[3].fitting_type == "valve_gate"
    assert points[3].joint_type == JointType.FLANGE
    assert points[4].nominal_size == "DN50"


def test_parse_iso_line_combines_both_files():
    line = parse_iso_line(EXAMPLES / "sample_header.csv", EXAMPLES / "sample_points.csv")
    assert line.header.line_number == "AF145-L-014"
    assert len(line.points) == 6


def test_missing_required_header_field_raises(tmp_path):
    bad = tmp_path / "header.csv"
    bad.write_text("key,value\nline_number,L1\n", encoding="utf-8")  # project_code manquant
    with pytest.raises(ValueError, match="project_code"):
        parse_line_header(bad)


def test_unknown_joint_type_raises(tmp_path):
    bad = tmp_path / "points.csv"
    bad.write_text(
        "seq,x_mm,y_mm,z_mm,joint_type\n1,0,0,0,end\n2,100,0,0,soudure_bizarre\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="joint_type"):
        parse_route_points(bad)


def test_too_few_points_raises(tmp_path):
    bad = tmp_path / "points.csv"
    bad.write_text("seq,x_mm,y_mm,z_mm\n1,0,0,0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="au moins 2 points"):
        parse_route_points(bad)
