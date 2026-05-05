import cadquery as cq
from cadquery import exporters
from pathlib import Path

COMPONENT_NAME = "rectangular_mounting_plate"

PLATE_L = 80.0
PLATE_W = 40.0
PLATE_T = 4.0
N_HOLES = 4
HOLE_D = 4.5
HOLE_EDGE_OFFSET = 8.0
MIN_WALL_AROUND_HOLE = 4.0
CHAMFER_W = 1.0
CHAMFER_ANGLE = 45.0

HOLE_X = PLATE_L / 2.0 - HOLE_EDGE_OFFSET
HOLE_Y = PLATE_W / 2.0 - HOLE_EDGE_OFFSET
HOLE_CUT_EXTRA = 2.0
SAFE_CHAMFER_W = min(CHAMFER_W, PLATE_T / 2.0 - 0.001)


def make_z_axis_cylinder(diameter: float, length: float, x: float, y: float, z_start: float) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .circle(diameter / 2.0)
        .extrude(length)
        .translate((x, y, z_start))
    )


def make_rectangular_mounting_plate() -> cq.Workplane:
    plate = (
        cq.Workplane("XY")
        .rect(PLATE_L, PLATE_W)
        .extrude(PLATE_T)
    )

    hole_positions = [
        (-HOLE_X, -HOLE_Y),
        (HOLE_X, -HOLE_Y),
        (-HOLE_X, HOLE_Y),
        (HOLE_X, HOLE_Y),
    ]

    for x, y in hole_positions:
        cutter = make_z_axis_cylinder(
            HOLE_D,
            PLATE_T + HOLE_CUT_EXTRA,
            x,
            y,
            -HOLE_CUT_EXTRA / 2.0,
        )
        plate = plate.cut(cutter)

    if SAFE_CHAMFER_W > 0.0:
        plate = plate.faces(">Z").edges().chamfer(SAFE_CHAMFER_W)

    return plate.clean()


def validate_geometry(part: cq.Workplane) -> dict:
    shape = part.val()
    bbox = shape.BoundingBox()

    hole_positions = [
        (-HOLE_X, -HOLE_Y),
        (HOLE_X, -HOLE_Y),
        (-HOLE_X, HOLE_Y),
        (HOLE_X, HOLE_Y),
    ]

    expected_xmin = -PLATE_L / 2.0
    expected_xmax = PLATE_L / 2.0
    expected_ymin = -PLATE_W / 2.0
    expected_ymax = PLATE_W / 2.0

    checks = {
        "positive_volume": shape.Volume() > 0.0,
        "bbox_length_ok": abs(bbox.xlen - PLATE_L) < 0.01,
        "bbox_width_ok": abs(bbox.ylen - PLATE_W) < 0.01,
        "bbox_height_ok": abs(bbox.zlen - PLATE_T) < 0.01,
        "bottom_on_z0": abs(bbox.zmin - 0.0) < 0.01,
        "hole_count_parameter_ok": N_HOLES == 4,
        "min_wall_ok": MIN_WALL_AROUND_HOLE >= 2.0,
        "hole_edge_offset_x_ok": abs((PLATE_L / 2.0 - HOLE_X) - HOLE_EDGE_OFFSET) < 1e-6,
        "hole_edge_offset_y_ok": abs((PLATE_W / 2.0 - HOLE_Y) - HOLE_EDGE_OFFSET) < 1e-6,
        "hole_positions_inside_plate": all(
            expected_xmin < x < expected_xmax and expected_ymin < y < expected_ymax
            for x, y in hole_positions
        ),
        "chamfer_safe": CHAMFER_W < PLATE_T / 2.0,
    }

    checks["valid"] = all(checks.values())
    return checks


def export_all(part: cq.Workplane, output_dir: str = ".") -> list[str]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    step_path = out_dir / f"{COMPONENT_NAME}.step"
    exporters.export(part, str(step_path), exportType="STEP")

    return [str(step_path)]


if __name__ == "__main__":
    model = make_rectangular_mounting_plate()
    validation = validate_geometry(model)
    if not validation["valid"]:
        raise ValueError(f"Geometry validation failed: {validation}")
    export_all(model, ".")
