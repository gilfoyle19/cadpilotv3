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
HOLE_1_X = -PLATE_L / 2.0 + HOLE_EDGE_OFFSET
HOLE_1_Y = -PLATE_W / 2.0 + HOLE_EDGE_OFFSET
HOLE_2_X = PLATE_L / 2.0 - HOLE_EDGE_OFFSET
HOLE_2_Y = -PLATE_W / 2.0 + HOLE_EDGE_OFFSET
HOLE_3_X = -PLATE_L / 2.0 + HOLE_EDGE_OFFSET
HOLE_3_Y = PLATE_W / 2.0 - HOLE_EDGE_OFFSET
HOLE_4_X = PLATE_L / 2.0 - HOLE_EDGE_OFFSET
HOLE_4_Y = PLATE_W / 2.0 - HOLE_EDGE_OFFSET
CHAMFER_W = 1.0
CHAMFER_ANGLE = 45.0
MIN_WALL_AFTER_HOLE = HOLE_EDGE_OFFSET - HOLE_D / 2.0

HOLE_POSITIONS = [
    (HOLE_1_X, HOLE_1_Y),
    (HOLE_2_X, HOLE_2_Y),
    (HOLE_3_X, HOLE_3_Y),
    (HOLE_4_X, HOLE_4_Y),
]


def make_z_axis_cutter(diameter: float, height: float, z_start: float, x: float, y: float) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .circle(diameter / 2.0)
        .extrude(height)
        .translate((x, y, z_start))
    )


def make_rectangular_mounting_plate() -> cq.Workplane:
    plate = (
        cq.Workplane("XY")
        .rect(PLATE_L, PLATE_W)
        .extrude(PLATE_T)
    )

    cutter_height = PLATE_T + 2.0
    cutter_z_start = -1.0

    for x, y in HOLE_POSITIONS:
        hole_cutter = make_z_axis_cutter(HOLE_D, cutter_height, cutter_z_start, x, y)
        plate = plate.cut(hole_cutter)

    chamfer_size = min(CHAMFER_W, (PLATE_T / 2.0) - 1e-3)
    if chamfer_size > 0:
        plate = plate.edges("|Z and >Z").chamfer(chamfer_size)

    return plate.clean()


def validate_geometry(part: cq.Workplane) -> dict:
    results = {
        "component_name": COMPONENT_NAME,
        "valid": True,
        "errors": [],
    }

    if PLATE_T < 2.0:
        results["valid"] = False
        results["errors"].append("PLATE_T violates minimum FDM thickness constraint.")

    if N_HOLES != 4:
        results["valid"] = False
        results["errors"].append("N_HOLES must be exactly 4.")

    if MIN_WALL_AFTER_HOLE < 2.0:
        results["valid"] = False
        results["errors"].append("Minimum wall after hole is below 2.0mm.")

    if CHAMFER_W >= PLATE_T / 2.0:
        results["valid"] = False
        results["errors"].append("Chamfer width must be less than half the plate thickness.")

    shape = part.val()
    bbox = shape.BoundingBox()

    expected_x = PLATE_L
    expected_y = PLATE_W
    expected_z = PLATE_T
    tol = 1e-3

    if abs(bbox.xlen - expected_x) > tol:
        results["valid"] = False
        results["errors"].append("Bounding box X length mismatch.")

    if abs(bbox.ylen - expected_y) > tol:
        results["valid"] = False
        results["errors"].append("Bounding box Y width mismatch.")

    if abs(bbox.zlen - expected_z) > tol:
        results["valid"] = False
        results["errors"].append("Bounding box Z thickness mismatch.")

    if abs(bbox.zmin - 0.0) > tol:
        results["valid"] = False
        results["errors"].append("Bottom face is not on z=0.")

    if shape.Volume() <= 0.0:
        results["valid"] = False
        results["errors"].append("Part volume must be positive.")

    return results


def export_all(part: cq.Workplane, output_dir: str = ".") -> list[str]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    step_path = output_path / f"{COMPONENT_NAME}.step"
    exporters.export(part, str(step_path), exportType="STEP")

    return [str(step_path)]


if __name__ == "__main__":
    part = make_rectangular_mounting_plate()
    validation = validate_geometry(part)
    if not validation["valid"]:
        raise ValueError(f"Geometry validation failed: {validation['errors']}")
    export_all(part, ".")
