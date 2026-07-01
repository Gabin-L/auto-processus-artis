from iso_engine.models import IsoLine, JointType, LineHeader, Point3D, RoutePoint
from iso_engine.weld_numbering import assign_weld_numbers, joint_summary


def _line(points):
    return IsoLine(header=LineHeader(line_number="L1", project_code="P1"), points=points)


def test_start_point_never_gets_a_weld_number_even_if_marked_weld():
    points = [
        RoutePoint(seq=1, position=Point3D(0, 0, 0), joint_type=JointType.WELD),
        RoutePoint(seq=2, position=Point3D(1000, 0, 0), joint_type=JointType.WELD),
    ]
    marks = assign_weld_numbers(_line(points))
    assert len(marks) == 1
    assert marks[0].weld_id == "W1"
    assert marks[0].point.seq == 2


def test_non_weld_joints_are_skipped_and_numbering_stays_sequential():
    points = [
        RoutePoint(seq=1, position=Point3D(0, 0, 0), joint_type=JointType.END),
        RoutePoint(seq=2, position=Point3D(1000, 0, 0), joint_type=JointType.WELD),
        RoutePoint(seq=3, position=Point3D(2000, 0, 0), joint_type=JointType.FLANGE),
        RoutePoint(seq=4, position=Point3D(3000, 0, 0), joint_type=JointType.WELD),
        RoutePoint(seq=5, position=Point3D(4000, 0, 0), joint_type=JointType.END),
    ]
    marks = assign_weld_numbers(_line(points))
    assert [m.weld_id for m in marks] == ["W1", "W2"]
    assert [m.point.seq for m in marks] == [2, 4]


def test_numbering_follows_seq_order_not_input_order():
    points = [
        RoutePoint(seq=1, position=Point3D(0, 0, 0), joint_type=JointType.END),
        RoutePoint(seq=3, position=Point3D(2000, 0, 0), joint_type=JointType.WELD),
        RoutePoint(seq=2, position=Point3D(1000, 0, 0), joint_type=JointType.WELD),
    ]
    marks = assign_weld_numbers(_line(points))
    assert [m.point.seq for m in marks] == [2, 3]


def test_joint_summary_groups_by_type_excluding_start_point():
    points = [
        RoutePoint(seq=1, position=Point3D(0, 0, 0), joint_type=JointType.WELD),  # départ, ignoré
        RoutePoint(seq=2, position=Point3D(1000, 0, 0), joint_type=JointType.WELD),
        RoutePoint(seq=3, position=Point3D(2000, 0, 0), joint_type=JointType.FLANGE),
    ]
    summary = joint_summary(_line(points))
    assert [p.seq for p in summary[JointType.WELD]] == [2]
    assert [p.seq for p in summary[JointType.FLANGE]] == [3]
    assert summary[JointType.END] == []
