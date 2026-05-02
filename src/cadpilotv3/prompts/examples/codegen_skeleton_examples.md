## Agent 4 - Stage A Skeleton Few-Shots

### Example 1 - Static Single-Part Skeleton

INPUT:
```json
{
  "component": "square_bolt_pattern_adapter_plate",
  "parts": ["adapter_plate"],
  "parameters": ["PLATE_L", "PLATE_W", "PLATE_T", "OUTER_PATTERN", "INNER_PATTERN", "M4_CLEAR_D", "M3_CLEAR_D", "PILOT_D"],
  "output_format": "STEP"
}
```

OUTPUT:
```python
"""Square bolt pattern adapter plate.

Static single-part CadQuery 2.x model.
Exports one STEP file.
"""

import cadquery as cq
from cadquery import exporters

COMPONENT_NAME = "square_bolt_pattern_adapter_plate"

PLATE_L = 55.0  # overall plate length in mm
PLATE_W = 55.0  # overall plate width in mm
PLATE_T = 6.0  # plate thickness in mm
OUTER_PATTERN = 40.0  # M4 square bolt pattern spacing in mm
INNER_PATTERN = 30.0  # M3 square bolt pattern spacing in mm
M4_CLEAR_D = 4.5  # M4 clearance hole diameter in mm
M3_CLEAR_D = 3.4  # M3 clearance hole diameter in mm
PILOT_D = 12.0  # centered pilot hole diameter in mm


def make_square_bolt_pattern_adapter_plate() -> cq.Workplane:
    """Create the symmetric adapter plate.

    Returns:
        cq.Workplane: Adapter plate with rounded corners, pilot hole,
        outer M4 pattern, and inner M3 pattern.

    Geometric intent:
        Use a rounded rectangular plate profile, then cut all vertical
        through holes from the top-accessible face.

    Failure risks:
        - Chamfering after many hole cuts can fail if too large.
        - Hole patterns must remain inside rounded corners.
    """
    raise NotImplementedError("implement in Stage B")


def validate_geometry(model: cq.Workplane) -> dict:
    """Validate basic static geometry metadata."""
    raise NotImplementedError("implement in Stage B")


def export_all(model: cq.Workplane, output_dir: str) -> list[str]:
    """Export the adapter plate as STEP."""
    raise NotImplementedError("implement in Stage B")


if __name__ == "__main__":
    model = make_square_bolt_pattern_adapter_plate()
    validate_geometry(model)
    export_all(model, "./output")
```

### Example 2 - Static Assembly Skeleton

INPUT:
```json
{
  "component": "two_part_electronics_enclosure",
  "parts": ["base", "removable_lid"],
  "output_format": "STEP"
}
```

OUTPUT:
```python
"""Two-part electronics enclosure assembly.

Static CadQuery 2.x assembly with base and removable lid in closed position.
Exports one assembly STEP file.
"""

import cadquery as cq

COMPONENT_NAME = "two_part_electronics_enclosure"

OUTER_L = 100.0  # overall enclosure length in mm
OUTER_W = 60.0  # overall enclosure width in mm
BASE_H = 30.0  # base shell height in mm
LID_TOP_T = 5.0  # lid top thickness in mm
WALL_T = 2.0  # nominal FDM wall thickness in mm


def make_base() -> cq.Workplane:
    """Create the enclosure base shell.

    Returns:
        cq.Workplane: Open-top base shell with walls, standoffs, and cable opening.

    Geometric intent:
        Build from explicit bottom and wall boxes rather than using shell(),
        then add standoffs and cut cable openings.

    Failure risks:
        - Shell operations can fail on openings.
        - Standoffs must align to the lid screw pattern.
    """
    raise NotImplementedError("implement in Stage B")


def make_lid() -> cq.Workplane:
    """Create the removable screw-on lid.

    Returns:
        cq.Workplane: Separate lid with internal lip and countersunk screw holes.

    Geometric intent:
        Build the lid as a separate part, not unioned into the base.

    Failure risks:
        - Lid lip must fit inside base walls with clearance.
        - Countersunk holes must align to standoffs.
    """
    raise NotImplementedError("implement in Stage B")


def build_assembly() -> cq.Assembly:
    """Assemble the base and lid in the closed fixed position."""
    raise NotImplementedError("implement in Stage B")


if __name__ == "__main__":
    assembly = build_assembly()
    assembly.save(f"{COMPONENT_NAME}_assembly.step")
```