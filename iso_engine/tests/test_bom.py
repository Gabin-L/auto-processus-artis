from iso_engine.bom import build_bom, build_fitting_lines, build_pipe_lines
from iso_engine.models import IsoLine, JointType, LineHeader, Point3D, RoutePoint


def _line(points, nominal_size="DN80"):
    header = LineHeader(line_number="L1", project_code="P1", nominal_size=nominal_size)
    return IsoLine(header=header, points=points)


def test_pipe_length_sums_segments_of_same_size():
    points = [
        RoutePoint(seq=1, position=Point3D(0, 0, 0), joint_type=JointType.END),
        RoutePoint(seq=2, position=Point3D(1000, 0, 0), joint_type=JointType.WELD),
        RoutePoint(seq=3, position=Point3D(1000, 0, 500), joint_type=JointType.END),
    ]
    lines = build_pipe_lines(_line(points))
    assert len(lines) == 1
    assert lines[0].nominal_size == "DN80"
    assert lines[0].quantity == 1500.0
    assert lines[0].unit == "mm"
    assert lines[0].description == "Tube DN80"  # pas de doublon "DN" (nominal_size l'inclut déjà)


def test_pipe_length_splits_by_size_after_reducer():
    points = [
        RoutePoint(seq=1, position=Point3D(0, 0, 0), joint_type=JointType.END),
        RoutePoint(
            seq=2,
            position=Point3D(1000, 0, 0),
            joint_type=JointType.WELD,
            fitting_type="reducer_concentric",
            nominal_size="DN50",
        ),
        RoutePoint(seq=3, position=Point3D(1600, 0, 0), joint_type=JointType.END),
    ]
    lines = {line.nominal_size: line for line in build_pipe_lines(_line(points))}
    assert lines["DN80"].quantity == 1000.0
    assert lines["DN50"].quantity == 600.0


def test_fitting_lines_count_by_type_size_and_ref():
    points = [
        RoutePoint(seq=1, position=Point3D(0, 0, 0), joint_type=JointType.END),
        RoutePoint(
            seq=2,
            position=Point3D(1000, 0, 0),
            joint_type=JointType.WELD,
            fitting_type="elbow90",
            fitting_ref="EL-01",
        ),
        RoutePoint(
            seq=3,
            position=Point3D(1000, 1000, 0),
            joint_type=JointType.WELD,
            fitting_type="elbow90",
            fitting_ref="EL-02",
        ),
    ]
    lines = build_fitting_lines(_line(points))
    assert len(lines) == 2
    assert {l.ref for l in lines} == {"EL-01", "EL-02"}
    assert all(l.quantity == 1 for l in lines)
    assert all(l.nominal_size == "DN80" for l in lines)


def test_build_bom_combines_pipe_and_fittings():
    points = [
        RoutePoint(seq=1, position=Point3D(0, 0, 0), joint_type=JointType.END),
        RoutePoint(
            seq=2,
            position=Point3D(1000, 0, 0),
            joint_type=JointType.WELD,
            fitting_type="elbow90",
            fitting_ref="EL-01",
        ),
        RoutePoint(seq=3, position=Point3D(1000, 0, 500), joint_type=JointType.END),
    ]
    bom = build_bom(_line(points))
    types = {line.item_type for line in bom}
    assert types == {"pipe", "fitting"}
