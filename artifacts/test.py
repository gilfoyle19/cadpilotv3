import cadquery as cq
from cadquery import exporters
import os

COMPONENT_NAME = "simple_wall_bracket"

BRACKET_W = 60.0
BRACKET_H = 20.0
BRACKET_D = 8.0
M5_CLEAR_D = 5.5
HOLE_SPACING = 40.0
EDGE_MARGIN = 10.0
HOLE_1_X_OFFSET = 20.0
HOLE_2_X_OFFSET = -20.0
HOLE_Y_OFFSET = 4.0
HOLE_AXIS_ANGLE = 0.0

CUT_EPS = 0.01


def validate_parameters() -> None:
    if BRACKET_W < HOLE_SPACING + 2.0 * EDGE_MARGIN:
        raise ValueError("BRACKET_W must be >= HOLE_SPACING + 2 * EDGE_MARGIN")
    if HOLE_SPACING > BRACKET_W - 2.0 * EDGE_MARGIN:
        raise ValueError("HOLE_SPACING must be <= BRACKET_W - 2 * EDGE_MARGIN")
    if abs(HOLE_1_X_OFFSET - HOLE_SPACING / 2.0) > 1e-9:
        raise ValueError("HOLE_1_X_OFFSET must equal HOLE_SPACING / 2")
    if abs(HOLE_2_X_OFFSET + HOLE_SPACING / 2.0) > 1e-9:
        raise ValueError("HOLE_2_X_OFFSET must equal -HOLE_SPACING / 2")
    if abs(HOLE_Y_OFFSET - BRACKET_D / 2.0) > 1e-9:
        raise ValueError("HOLE_Y_OFFSET must equal BRACKET_D / 2")
    if HOLE_AXIS_ANGLE != 0.0:
        raise ValueError("HOLE_AXIS_ANGLE must be 0.0 for holes normal to the mounting face")
    if BRACKET_D < M5_CLEAR_D + 2.0:
        raise ValueError("BRACKET_D must be >= M5_CLEAR_D + 2.0 for through hole strength")


def make_y_axis_cutter(diameter: float, length: float, x: float, y_start: float, z: float) -> cq.Workplane:
    return (
        cq.Workplane("XZ")
        .center(x, z)
        .circle(diameter / 2.0)
        .extrude(length)
        .translate((0.0, y_start, 0.0))
    )


def build_part() -> cq.Workplane:
    validate_parameters()

    bracket = (
        cq.Workplane("XY")
        .box(BRACKET_W, BRACKET_D, BRACKET_H, centered=(True, False, False))
    )

    hole_cut_1 = make_y_axis_cutter(
        diameter=M5_CLEAR_D,
        length=BRACKET_D + 2.0 * CUT_EPS,
        x=HOLE_1_X_OFFSET,
        y_start=-CUT_EPS,
        z=BRACKET_H / 2.0,
    )

    hole_cut_2 = make_y_axis_cutter(
        diameter=M5_CLEAR_D,
        length=BRACKET_D + 2.0 * CUT_EPS,
        x=HOLE_2_X_OFFSET,
        y_start=-CUT_EPS,
        z=BRACKET_H / 2.0,
    )

    bracket = bracket.cut(hole_cut_1).cut(hole_cut_2).clean()
    return bracket


def validate_geometry(part: cq.Workplane) -> dict:
    validate_parameters()

    shape = part.val()
    bbox = shape.BoundingBox()

    expected_xmin = -BRACKET_W / 2.0
    expected_xmax = BRACKET_W / 2.0
    expected_ymin = 0.0
    expected_ymax = BRACKET_D
    expected_zmin = 0.0
    expected_zmax = BRACKET_H
    tol = 1e-3

    return {
        "valid": bool(shape.Volume() > 0.0),
        "positive_volume": bool(shape.Volume() > 0.0),
        "bbox_xlen_ok": abs(bbox.xlen - BRACKET_W) < tol,
        "bbox_ylen_ok": abs(bbox.ylen - BRACKET_D) < tol,
        "bbox_zlen_ok": abs(bbox.zlen - BRACKET_H) < tol,
        "bbox_xmin_ok": abs(bbox.xmin - expected_xmin) < tol,
        "bbox_xmax_ok": abs(bbox.xmax - expected_xmax) < tol,
        "bbox_ymin_ok": abs(bbox.ymin - expected_ymin) < tol,
        "bbox_ymax_ok": abs(bbox.ymax - expected_ymax) < tol,
        "bbox_zmin_ok": abs(bbox.zmin - expected_zmin) < tol,
        "bbox_zmax_ok": abs(bbox.zmax - expected_zmax) < tol,
        "hole_spacing_ok": abs((HOLE_1_X_OFFSET - HOLE_2_X_OFFSET) - HOLE_SPACING) < 1e-9,
        "edge_margin_ok": (BRACKET_W / 2.0 - abs(HOLE_1_X_OFFSET)) >= EDGE_MARGIN - 1e-9,
    }


def export_all(part: cq.Workplane, output_dir: str = ".") -> list[str]:
    os.makedirs(output_dir, exist_ok=True)
    step_path = os.path.join(output_dir, f"{COMPONENT_NAME}.step")
    exporters.export(part, step_path, exportType="STEP")
    return [step_path]


if __name__ == "__main__":
    model = build_part()
    validation = validate_geometry(model)
    if not validation["valid"]:
        raise RuntimeError(f"Geometry validation failed: {validation}")
    export_all(model)
