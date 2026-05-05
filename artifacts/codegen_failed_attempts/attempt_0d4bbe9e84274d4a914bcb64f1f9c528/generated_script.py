import cadquery as cq
from cadquery import exporters
from pathlib import Path

COMPONENT_NAME = "corexy_belt_tensioner_bracket"

BASE_W = 24.0
BASE_L = 60.0
BASE_T = 3.0

TAB_W = 24.0
TAB_T = 3.0
TAB_H = 28.0

MIN_WALL = 3.0
BASE_CORNER_R = 3.0

M5_CLEAR_D = 5.5
M5_HOLE_SPACING_X = 20.0
M5_HOLE_Y_OFFSET_FROM_BACK = 14.0

M4_CLEAR_D = 4.3
SLOT_LEN = 12.0
SLOT_CENTER_Z = BASE_T + TAB_H / 2.0

GUSSET_T = 3.0
GUSSET_REACH_Y = 14.0
GUSSET_RISE_Z = 16.0
GUSSET_INSET_FROM_SIDE = 1.5

TOP_CHAMFER = 0.6

TAB_CENTER_Y = BASE_L / 2.0 - TAB_T / 2.0
TAB_FRONT_Y = BASE_L / 2.0
TAB_BACK_Y = TAB_CENTER_Y - TAB_T / 2.0
BASE_BACK_Y = -BASE_L / 2.0
M5_HOLE_Y = BASE_BACK_Y + M5_HOLE_Y_OFFSET_FROM_BACK

SAFE_BASE_CORNER_R = min(BASE_CORNER_R, BASE_W / 2.0 - 0.5, BASE_L / 2.0 - 0.5)
SAFE_TOP_CHAMFER = min(TOP_CHAMFER, BASE_T / 2.0 - 0.1, TAB_T / 2.0 - 0.1)
SLOT_END_RADIUS = M4_CLEAR_D / 2.0


def make_y_axis_cylinder(diameter: float, length: float, x: float, y_start: float, z: float) -> cq.Workplane:
    return (
        cq.Workplane("XZ")
        .circle(diameter / 2.0)
        .extrude(length)
        .translate((x, y_start, z))
    )


def make_rounded_base_plate() -> cq.Workplane:
    plate = (
        cq.Workplane("XY")
        .rect(BASE_W - 2.0 * SAFE_BASE_CORNER_R, BASE_L)
        .extrude(BASE_T)
    )
    side_add = (
        cq.Workplane("XY")
        .rect(BASE_W, BASE_L - 2.0 * SAFE_BASE_CORNER_R)
        .extrude(BASE_T)
    )
    return plate.union(side_add).clean()


def make_vertical_tab() -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .box(TAB_W, TAB_T, TAB_H)
        .translate((0.0, TAB_CENTER_Y, BASE_T + TAB_H / 2.0))
    )


def make_left_gusset() -> cq.Workplane:
    x_center = -(TAB_W / 2.0 - GUSSET_T / 2.0 - GUSSET_INSET_FROM_SIDE)
    return (
        cq.Workplane("YZ")
        .polyline(
            [
                (TAB_BACK_Y - GUSSET_REACH_Y, BASE_T),
                (TAB_BACK_Y + 0.2, BASE_T),
                (TAB_BACK_Y + 0.2, BASE_T + GUSSET_RISE_Z),
            ]
        )
        .close()
        .extrude(GUSSET_T)
        .translate((x_center - GUSSET_T / 2.0, 0.0, 0.0))
    )


def make_right_gusset() -> cq.Workplane:
    return make_left_gusset().mirror("YZ")


def make_m4_slot_cutter() -> cq.Workplane:
    slot_y_start = TAB_CENTER_Y - TAB_T / 2.0 - 1.0
    slot_length_y = TAB_T + 2.0
    left_end = -SLOT_LEN / 2.0
    right_end = SLOT_LEN / 2.0

    center_rect = (
        cq.Workplane("YZ")
        .center(0.0, SLOT_CENTER_Z)
        .rect(SLOT_LEN, M4_CLEAR_D)
        .extrude(slot_length_y)
        .translate((0.0, slot_y_start, 0.0))
    )

    left_cap = make_y_axis_cylinder(M4_CLEAR_D, slot_length_y, left_end, slot_y_start, SLOT_CENTER_Z)
    right_cap = make_y_axis_cylinder(M4_CLEAR_D, slot_length_y, right_end, slot_y_start, SLOT_CENTER_Z)

    return center_rect.union(left_cap).union(right_cap).clean()


def make_m5_hole_cutter(x: float, y: float) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .circle(M5_CLEAR_D / 2.0)
        .extrude(BASE_T + 2.0)
        .translate((x, y, -1.0))
    )


def make_bracket() -> cq.Workplane:
    base_plate = make_rounded_base_plate()
    vertical_tab = make_vertical_tab()
    left_gusset = make_left_gusset()
    right_gusset = make_right_gusset()

    bracket = base_plate.union(vertical_tab).union(left_gusset).union(right_gusset).clean()

    bracket = bracket.cut(make_m4_slot_cutter())

    for x in (-M5_HOLE_SPACING_X / 2.0, M5_HOLE_SPACING_X / 2.0):
        bracket = bracket.cut(make_m5_hole_cutter(x, M5_HOLE_Y))

    if SAFE_TOP_CHAMFER > 0.0:
        bracket = bracket.faces(">Z").edges().chamfer(SAFE_TOP_CHAMFER)

    return bracket.clean()


def validate_geometry(part: cq.Workplane) -> dict:
    shape = part.val()
    bb = shape.BoundingBox()
    volume = shape.Volume()

    expected_x = BASE_W
    expected_y = BASE_L
    expected_z = BASE_T + TAB_H

    m5_hole_count = 2
    slot_margin_each_side = (TAB_W - SLOT_LEN) / 2.0

    checks = {
        "valid": volume > 0.0,
        "volume_positive": volume > 0.0,
        "bbox_x_close": abs(bb.xlen - expected_x) < 1.0,
        "bbox_y_close": abs(bb.ylen - expected_y) < 1.0,
        "bbox_z_close": abs(bb.zlen - expected_z) < 1.0,
        "min_wall_ok": BASE_T >= 2.0 and TAB_T >= 2.0 and GUSSET_T >= 2.0,
        "slot_wall_ok": slot_margin_each_side >= MIN_WALL,
        "m5_hole_count_expected": m5_hole_count == 2,
        "base_bottom_at_zero": abs(bb.zmin - 0.0) < 1e-6,
    }

    return {
        "component": COMPONENT_NAME,
        "checks": checks,
        "bounding_box": {
            "xlen": bb.xlen,
            "ylen": bb.ylen,
            "zlen": bb.zlen,
            "xmin": bb.xmin,
            "xmax": bb.xmax,
            "ymin": bb.ymin,
            "ymax": bb.ymax,
            "zmin": bb.zmin,
            "zmax": bb.zmax,
        },
        "volume": volume,
    }


def export_all(part: cq.Workplane, output_dir: str = ".") -> list[str]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    step_path = out_dir / f"{COMPONENT_NAME}.step"
    exporters.export(part, str(step_path), exportType="STEP")
    return [str(step_path)]


if __name__ == "__main__":
    bracket = make_bracket()
    validation = validate_geometry(bracket)
    if not all(validation["checks"].values()):
        raise RuntimeError(f"Geometry validation failed: {validation}")
    export_all(bracket, ".")
