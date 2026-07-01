import math

from iso_engine.models import IsoLine, JointType, LineHeader, Point3D, RoutePoint
from iso_engine.projection import project_line, project_point, true_length


def _line(points):
    return IsoLine(header=LineHeader(line_number="L1", project_code="P1"), points=points)


def test_project_point_pure_x_gives_30_degrees_up_right():
    p = project_point(Point3D(100, 0, 0))
    angle = math.degrees(math.atan2(p.y, p.x))
    assert math.isclose(angle, 30, abs_tol=1e-6)


def test_project_point_pure_y_gives_150_degrees_up_left():
    p = project_point(Point3D(0, 100, 0))
    angle = math.degrees(math.atan2(p.y, p.x))
    assert math.isclose(angle, 150, abs_tol=1e-6)


def test_project_point_pure_z_is_vertical():
    p = project_point(Point3D(0, 0, 100))
    assert math.isclose(p.x, 0, abs_tol=1e-9)
    assert math.isclose(p.y, 100, abs_tol=1e-9)


def test_project_point_scale_factor_applied():
    p_full = project_point(Point3D(100, 0, 0), scale=1.0)
    p_half = project_point(Point3D(100, 0, 0), scale=0.5)
    assert math.isclose(p_half.x, p_full.x / 2)
    assert math.isclose(p_half.y, p_full.y / 2)


def test_true_length_is_euclidean_distance():
    assert true_length(Point3D(0, 0, 0), Point3D(3, 4, 0)) == 5.0


def test_project_line_produces_one_segment_per_pair_of_points():
    points = [
        RoutePoint(seq=1, position=Point3D(0, 0, 0), joint_type=JointType.END),
        RoutePoint(seq=2, position=Point3D(1000, 0, 0), joint_type=JointType.WELD),
        RoutePoint(seq=3, position=Point3D(1000, 0, 500), joint_type=JointType.END),
    ]
    segments = project_line(_line(points))
    assert len(segments) == 2
    assert segments[0].true_length_mm == 1000
    assert segments[1].true_length_mm == 500


def test_project_line_requires_at_least_two_points():
    points = [RoutePoint(seq=1, position=Point3D(0, 0, 0))]
    try:
        project_line(_line(points))
        assert False, "devrait lever une ValueError"
    except ValueError:
        pass
