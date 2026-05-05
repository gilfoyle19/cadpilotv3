import cadquery as cq
from cadquery import exporters
from pathlib import Path

COMPONENT_NAME = "two_part_electronics_enclosure"

BASE_L = 100.0
BASE_W = 60.0
BASE_H = 30.0
WALL_T = 2.0
BASE_PLATE_T = 2.0
SIDE_WALL_H = 28.0
LID_T = 2.0
N_STANDOFFS = 4
STANDOFF_OD = 6.0
STANDOFF_H = 28.0
STANDOFF_HOLE_D = 3.4
STANDOFF_X_OFFSET = 38.0
STANDOFF_Y_OFFSET = 18.0
LID_HOLE_X_OFFSET = 38.0
LID_HOLE_Y_OFFSET = 18.0
CABLE_OPENING_W = 15.0
CABLE_OPENING_H = 8.0
CABLE_OPENING_Z_OFFSET = 5.0
CABLE_OPENING_Y_POS = 30.0
CABLE_OPENING_X_POS = 0.0
CABLE_OPENING_Z_POS = 7.0
ALIGNMENT_PIN_D = 2.0
ALIGNMENT_PIN_H = 2.0
ALIGNMENT_PIN_X_OFFSET = 32.0
ALIGNMENT_PIN_Y_OFFSET = 12.0
ALIGNMENT_PIN_CLEAR = 0.2
FILLET_R = 1.0

EPS = 0.01
CUT_EXTRA = 2.0


def pin_positions():
    return [
        (-ALIGNMENT_PIN_X_OFFSET, -ALIGNMENT_PIN_Y_OFFSET),
        (-ALIGNMENT_PIN_X_OFFSET, ALIGNMENT_PIN_Y_OFFSET),
        (ALIGNMENT_PIN_X_OFFSET, -ALIGNMENT_PIN_Y_OFFSET),
        (ALIGNMENT_PIN_X_OFFSET, ALIGNMENT_PIN_Y_OFFSET),
    ]


def standoff_positions():
    return [
        (-STANDOFF_X_OFFSET, -STANDOFF_Y_OFFSET),
        (-STANDOFF_X_OFFSET, STANDOFF_Y_OFFSET),
        (STANDOFF_X_OFFSET, -STANDOFF_Y_OFFSET),
        (STANDOFF_X_OFFSET, STANDOFF_Y_OFFSET),
    ]


def safe_fillet_radius() -> float:
    return max(0.0, min(FILLET_R, WALL_T / 2.0 - EPS))


def make_z_cylinder(diameter: float, height: float, center_z: float, x: float, y: float) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .circle(diameter / 2.0)
        .extrude(height)
        .translate((x, y, center_z - height / 2.0))
    )


def make_base() -> cq.Workplane:
    bottom = (
        cq.Workplane("XY")
        .box(BASE_L, BASE_W, BASE_PLATE_T)
        .translate((0.0, 0.0, BASE_PLATE_T / 2.0))
    )

    front_wall = (
        cq.Workplane("XY")
        .box(BASE_L, WALL_T, SIDE_WALL_H)
        .translate((0.0, BASE_W / 2.0 - WALL_T / 2.0, BASE_PLATE_T + SIDE_WALL_H / 2.0))
    )

    back_wall = (
        cq.Workplane("XY")
        .box(BASE_L, WALL_T, SIDE_WALL_H)
        .translate((0.0, -BASE_W / 2.0 + WALL_T / 2.0, BASE_PLATE_T + SIDE_WALL_H / 2.0))
    )

    left_wall = (
        cq.Workplane("XY")
        .box(WALL_T, BASE_W - 2.0 * WALL_T, SIDE_WALL_H)
        .translate((-BASE_L / 2.0 + WALL_T / 2.0, 0.0, BASE_PLATE_T + SIDE_WALL_H / 2.0))
    )

    right_wall = (
        cq.Workplane("XY")
        .box(WALL_T, BASE_W - 2.0 * WALL_T, SIDE_WALL_H)
        .translate((BASE_L / 2.0 - WALL_T / 2.0, 0.0, BASE_PLATE_T + SIDE_WALL_H / 2.0))
    )

    base = bottom.union(front_wall).union(back_wall).union(left_wall).union(right_wall)

    for x, y in standoff_positions():
        standoff = make_z_cylinder(
            diameter=STANDOFF_OD,
            height=STANDOFF_H,
            center_z=BASE_PLATE_T + STANDOFF_H / 2.0,
            x=x,
            y=y,
        )
        through_hole = make_z_cylinder(
            diameter=STANDOFF_HOLE_D,
            height=BASE_H + CUT_EXTRA,
            center_z=(BASE_H + CUT_EXTRA) / 2.0,
            x=x,
            y=y,
        )
        base = base.union(standoff).cut(through_hole)

    recess_d = ALIGNMENT_PIN_D + 2.0 * ALIGNMENT_PIN_CLEAR
    recess_h = ALIGNMENT_PIN_H
    for x, y in pin_positions():
        recess = make_z_cylinder(
            diameter=recess_d,
            height=recess_h + EPS,
            center_z=BASE_H - recess_h / 2.0,
            x=x,
            y=y,
        )
        base = base.cut(recess)

    cable_cutter = (
        cq.Workplane("XZ")
        .rect(CABLE_OPENING_W, CABLE_OPENING_H)
        .extrude(WALL_T + CUT_EXTRA)
        .translate(
            (
                CABLE_OPENING_X_POS,
                BASE_W / 2.0 - WALL_T / 2.0 - CUT_EXTRA / 2.0,
                CABLE_OPENING_Z_POS,
            )
        )
    )
    base = base.cut(cable_cutter)

    fillet_r = safe_fillet_radius()
    if fillet_r > 0.0:
        base = base.edges("|Z").fillet(fillet_r)

    return base.clean()


def make_lid() -> cq.Workplane:
    lid = (
        cq.Workplane("XY")
        .box(BASE_L, BASE_W, LID_T)
        .translate((0.0, 0.0, BASE_H + LID_T / 2.0))
    )

    for x, y in standoff_positions():
        hole = make_z_cylinder(
            diameter=STANDOFF_HOLE_D,
            height=LID_T + CUT_EXTRA,
            center_z=BASE_H + LID_T / 2.0,
            x=x,
            y=y,
        )
        lid = lid.cut(hole)

    for x, y in pin_positions():
        pin = make_z_cylinder(
            diameter=ALIGNMENT_PIN_D,
            height=ALIGNMENT_PIN_H,
            center_z=BASE_H - ALIGNMENT_PIN_H / 2.0,
            x=x,
            y=y,
        )
        lid = lid.union(pin)

    fillet_r = safe_fillet_radius()
    if fillet_r > 0.0:
        lid = lid.edges("|Z").fillet(fillet_r)

    return lid.clean()


def build_assembly() -> cq.Assembly:
    base = make_base()
    lid = make_lid()

    assembly = cq.Assembly(name=COMPONENT_NAME)
    assembly.add(base, name="base_shell", loc=cq.Location(cq.Vector(0.0, 0.0, 0.0)))
    assembly.add(lid, name="removable_lid", loc=cq.Location(cq.Vector(0.0, 0.0, 0.0)))
    return assembly


def validate_geometry() -> dict:
    checks = {
        "parameters_valid": True,
        "base_positive_volume": False,
        "lid_positive_volume": False,
        "assembly_child_count_ok": False,
        "bbox_base_ok": False,
        "bbox_lid_ok": False,
        "standoff_count_ok": N_STANDOFFS == 4,
    }

    if BASE_PLATE_T <= 0 or WALL_T <= 0 or LID_T <= 0:
        checks["parameters_valid"] = False
    if SIDE_WALL_H != BASE_H - BASE_PLATE_T:
        checks["parameters_valid"] = False
    if STANDOFF_H != SIDE_WALL_H:
        checks["parameters_valid"] = False
    if FILLET_R > WALL_T / 2.0:
        checks["parameters_valid"] = False
    if STANDOFF_OD <= STANDOFF_HOLE_D:
        checks["parameters_valid"] = False
    if CABLE_OPENING_H >= SIDE_WALL_H - CABLE_OPENING_Z_OFFSET:
        checks["parameters_valid"] = False

    base = make_base()
    lid = make_lid()
    asm = build_assembly()

    base_shape = base.val()
    lid_shape = lid.val()

    checks["base_positive_volume"] = base_shape.Volume() > 0.0
    checks["lid_positive_volume"] = lid_shape.Volume() > 0.0

    base_bb = base_shape.BoundingBox()
    lid_bb = lid_shape.BoundingBox()

    checks["bbox_base_ok"] = (
        abs(base_bb.xlen - BASE_L) < 0.5
        and abs(base_bb.ylen - BASE_W) < 0.5
        and abs(base_bb.zlen - BASE_H) < 0.5
    )
    checks["bbox_lid_ok"] = (
        abs(lid_bb.xlen - BASE_L) < 0.5
        and abs(lid_bb.ylen - BASE_W) < 0.5
        and abs(lid_bb.zlen - (LID_T + ALIGNMENT_PIN_H)) < 0.5
    )

    try:
        child_count = len(asm.children)
    except Exception:
        child_count = 0
    checks["assembly_child_count_ok"] = child_count == 2

    checks["valid"] = all(checks.values())
    return checks


def export_all(output_dir: str = ".") -> list[str]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    assembly = build_assembly()
    step_path = output_path / f"{COMPONENT_NAME}_assembly.step"
    assembly.save(str(step_path))
    return [str(step_path)]


if __name__ == "__main__":
    results = validate_geometry()
    if not results["valid"]:
        raise ValueError(f"Geometry validation failed: {results}")
    build_assembly()
    export_all(".")
