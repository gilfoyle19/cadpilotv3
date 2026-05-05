import cadquery as cq
from cadquery import exporters
from pathlib import Path

COMPONENT_NAME = "rectangular_mounting_plate"

PLATE_LENGTH = 80.0
PLATE_WIDTH = 50.0
PLATE_THICKNESS = 6.0

M4_CLEARANCE_DIAMETER = 4.5

HOLE_EDGE_MARGIN_X = 10.0
HOLE_EDGE_MARGIN_Y = 10.0

TOP_EDGE_CHAMFER = 1.5

CUTTER_EXTRA = 2.0
VALIDATION_TOL = 1e-6


def clamp_top_chamfer() -> float:
    max_from_x = HOLE_EDGE_MARGIN_X - M4_CLEARANCE_DIAMETER / 2.0
    max_from_y = HOLE_EDGE_MARGIN_Y - M4_CLEARANCE_DIAMETER / 2.0
    max_from_thickness = PLATE_THICKNESS / 2.0 - VALIDATION_TOL
    safe_max = min(max_from_x, max_from_y, max_from_thickness)
    return max(0.0, min(TOP_EDGE_CHAMFER, safe_max))


def hole_positions() -> list[tuple[float, float]]:
    x = PLATE_LENGTH / 2.0 - HOLE_EDGE_MARGIN_X
    y = PLATE_WIDTH / 2.0 - HOLE_EDGE_MARGIN_Y
    return [
        (-x, -y),
        (x, -y),
        (-x, y),
        (x, y),
    ]


def make_z_axis_cutter(diameter: float, height: float, x: float, y: float, z_start: float) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .circle(diameter / 2.0)
        .extrude(height)
        .translate((x, y, z_start))
    )


def build_part() -> cq.Workplane:
    plate = (
        cq.Workplane("XY")
        .rect(PLATE_LENGTH, PLATE_WIDTH)
        .extrude(PLATE_THICKNESS)
    )

    cutter_height = PLATE_THICKNESS + 2.0 * CUTTER_EXTRA
    cutter_z_start = -CUTTER_EXTRA

    for x, y in hole_positions():
        hole_cutter = make_z_axis_cutter(
            M4_CLEARANCE_DIAMETER,
            cutter_height,
            x,
            y,
            cutter_z_start,
        )
        plate = plate.cut(hole_cutter)

    chamfer_size = clamp_top_chamfer()
    if chamfer_size > 0.0:
        plate = plate.faces(">Z").edges().chamfer(chamfer_size)

    return plate.clean()


def validate_geometry(part: cq.Workplane) -> dict:
    shape = part.val()
    bb = shape.BoundingBox()

    expected_hole_count = 4
    actual_volume = shape.Volume()

    expected_plate_volume = PLATE_LENGTH * PLATE_WIDTH * PLATE_THICKNESS
    expected_hole_volume = expected_hole_count * (
        3.141592653589793 * (M4_CLEARANCE_DIAMETER / 2.0) * (M4_CLEARANCE_DIAMETER / 2.0) * PLATE_THICKNESS
    )
    expected_final_volume_upper_bound = expected_plate_volume - expected_hole_volume

    min_edge_distance_x = HOLE_EDGE_MARGIN_X - M4_CLEARANCE_DIAMETER / 2.0
    min_edge_distance_y = HOLE_EDGE_MARGIN_Y - M4_CLEARANCE_DIAMETER / 2.0

    result = {
        "valid": True,
        "component": COMPONENT_NAME,
        "volume_positive": actual_volume > 0.0,
        "bbox_length_ok": abs(bb.xlen - PLATE_LENGTH) < 1e-3,
        "bbox_width_ok": abs(bb.ylen - PLATE_WIDTH) < 1e-3,
        "bbox_thickness_ok": abs(bb.zlen - PLATE_THICKNESS) < 1e-3,
        "bottom_at_z0_ok": abs(bb.zmin - 0.0) < 1e-3,
        "edge_distance_x_ok": min_edge_distance_x >= 2.0,
        "edge_distance_y_ok": min_edge_distance_y >= 2.0,
        "chamfer_safe_ok": clamp_top_chamfer() <= min(min_edge_distance_x, min_edge_distance_y) + 1e-9,
        "volume_reduced_by_holes": actual_volume < expected_plate_volume,
        "volume_reasonable": actual_volume < expected_final_volume_upper_bound + expected_plate_volume * 0.05,
    }

    result["valid"] = all(
        value for key, value in result.items() if key not in ("valid", "component")
    )
    return result


def export_all(part: cq.Workplane, output_dir: str | Path = ".") -> list[str]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    step_path = output_path / f"{COMPONENT_NAME}.step"
    exporters.export(part, str(step_path), exportType="STEP")
    return [str(step_path)]


if __name__ == "__main__":
    model = build_part()
    validation = validate_geometry(model)
    if not validation["valid"]:
        raise ValueError(f"Geometry validation failed: {validation}")
    export_all(model, ".")
