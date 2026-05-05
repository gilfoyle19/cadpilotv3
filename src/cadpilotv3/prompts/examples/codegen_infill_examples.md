## Agent 4 - Stage B Complete-Script Few-Shots

### Static Example 1 - Micro Servo Extrusion Mount

INPUT:
```json
{
  "generation_mode": "complete script",
  "intent": "Create a single-piece FDM-printable micro servo bracket for mounting a standard micro servo to a 20x20 aluminum extrusion. Use mm units and export as STEP. The part should be a rigid fixed L-bracket with matching-width horizontal and vertical plates. Include a horizontal base plate with two M5 through holes spaced 20mm apart for the extrusion slot pattern. Include a vertical servo face plate with four M2 through holes in a rectangular servo mounting pattern. Add two triangular side gusset ribs between the base and face plate for stiffness, placed near the outer edges so they do not interfere with any mounting holes. Keep the design lightweight but structurally stiff, with minimum 2mm walls, a flat print base, and no moving joints."
}
```

OUTPUT:
```python
import cadquery as cq
from cadquery import exporters

COMPONENT_NAME = "micro_servo_extrusion_mount"

PLATE_W = 42.0

BASE_L = 58.0
BASE_W = PLATE_W
BASE_T = 5.0

SERVO_PLATE_W = PLATE_W
SERVO_PLATE_T = 5.0
SERVO_PLATE_H = 46.0

GUSSET_T = 4.0
GUSSET_REACH_Y = 18.0
GUSSET_RISE_Z = 24.0
GUSSET_X_OFFSET = 18.0

M2_CLEAR_D = 2.4
M5_CLEAR_D = 5.5

SERVO_HOLE_X_SPACING = 27.0
SERVO_HOLE_Z_SPACING = 32.0
SERVO_HOLE_Z_CENTER = BASE_T + 23.0

EXTRUSION_SLOT_PATTERN_SPACING = 20.0
EXTRUSION_HOLE_Y = 10.0


def make_y_axis_cylinder(diameter: float, length: float, x: float, y: float, z: float) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .cylinder(length, diameter / 2)
        .rotate((0, 0, 0), (1, 0, 0), 90)
        .translate((x, y, z))
    )


def make_z_axis_cylinder(diameter: float, length: float, x: float, y: float, z: float) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .cylinder(length, diameter / 2)
        .translate((x, y, z))
    )


def build_part() -> cq.Workplane:
    plate_y = -BASE_W / 2 + SERVO_PLATE_T / 2
    plate_front_y = plate_y + SERVO_PLATE_T / 2

    base = (
        cq.Workplane("XY")
        .box(BASE_L, BASE_W, BASE_T)
        .translate((0, 0, BASE_T / 2))
    )

    vertical_plate = (
        cq.Workplane("XY")
        .box(SERVO_PLATE_W, SERVO_PLATE_T, SERVO_PLATE_H)
        .translate((0, plate_y, BASE_T + SERVO_PLATE_H / 2))
    )

    for x in (-SERVO_HOLE_X_SPACING / 2, SERVO_HOLE_X_SPACING / 2):
        for z in (
            SERVO_HOLE_Z_CENTER - SERVO_HOLE_Z_SPACING / 2,
            SERVO_HOLE_Z_CENTER + SERVO_HOLE_Z_SPACING / 2,
        ):
            cutter = make_y_axis_cylinder(
                M2_CLEAR_D,
                SERVO_PLATE_T + 8.0,
                x,
                plate_y,
                z,
            )
            vertical_plate = vertical_plate.cut(cutter)

    mount = base.union(vertical_plate)

    for x_center in (-GUSSET_X_OFFSET, GUSSET_X_OFFSET):
        gusset = (
            cq.Workplane("YZ")
            .polyline(
                [
                    (plate_front_y, BASE_T),
                    (plate_front_y + GUSSET_REACH_Y, BASE_T),
                    (plate_front_y, BASE_T + GUSSET_RISE_Z),
                ]
            )
            .close()
            .extrude(GUSSET_T)
            .translate((x_center - GUSSET_T / 2, 0, 0))
        )
        mount = mount.union(gusset)

    for x in (-EXTRUSION_SLOT_PATTERN_SPACING / 2, EXTRUSION_SLOT_PATTERN_SPACING / 2):
        cutter = make_z_axis_cylinder(
            M5_CLEAR_D,
            BASE_T + 8.0,
            x,
            EXTRUSION_HOLE_Y,
            BASE_T / 2,
        )
        mount = mount.cut(cutter)

    return mount.clean()


if __name__ == "__main__":
    model = build_part()
    exporters.export(model, f"{COMPONENT_NAME}.step")
```

### Static Example 2 - 608 Bearing Pillow Block

INPUT:
```json
{
  "generation_mode": "complete script",
  "intent": "Design a single-piece bearing pillow block for a 608 bearing. Use mm units and export as STEP. The part will be CNC machined from aluminum. Include a rectangular base with two M6 through holes, a raised central bearing boss, and a circular bearing seat sized for a press-fit 608 bearing. Avoid internal undercuts, keep all holes through-drilled from accessible faces, and include small chamfers on external edges. The design should be a solid structural block, approximately 80mm long, 35mm wide, and 35mm tall."
}
```

OUTPUT:
```python
import cadquery as cq
from cadquery import exporters

COMPONENT_NAME = "bearing_pillow_block_608"

BASE_L = 80.0
BASE_W = 35.0
BASE_T = 6.0

PEDESTAL_L = 36.0
PEDESTAL_W = 24.0
PEDESTAL_H = 14.0

BOSS_OD = 28.0
BOSS_W = 24.0
BOSS_CENTER_Z = 20.0

BEARING_SEAT_D = 21.9
BEARING_SEAT_W = 8.0
SHAFT_CLEAR_D = 8.5

M6_CLEAR_D = 6.6
BASE_HOLE_SPACING = 58.0

CHAMFER_W = 0.6


def make_y_axis_cylinder(diameter: float, length: float, x: float, y: float, z: float) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .cylinder(length, diameter / 2)
        .rotate((0, 0, 0), (1, 0, 0), 90)
        .translate((x, y, z))
    )


def build_part() -> cq.Workplane:
    base = (
        cq.Workplane("XY")
        .box(BASE_L, BASE_W, BASE_T)
        .translate((0, 0, BASE_T / 2))
    )

    pedestal = (
        cq.Workplane("XY")
        .box(PEDESTAL_L, PEDESTAL_W, PEDESTAL_H)
        .translate((0, 0, BASE_T + PEDESTAL_H / 2))
    )

    boss = make_y_axis_cylinder(BOSS_OD, BOSS_W, 0, 0, BOSS_CENTER_Z)

    block = base.union(pedestal).union(boss)

    for x in (-BASE_HOLE_SPACING / 2, BASE_HOLE_SPACING / 2):
        m6_cutter = (
            cq.Workplane("XY")
            .cylinder(BASE_T + 4.0, M6_CLEAR_D / 2)
            .translate((x, 0, BASE_T / 2))
        )
        block = block.cut(m6_cutter)

    bearing_seat = make_y_axis_cylinder(BEARING_SEAT_D, BEARING_SEAT_W, 0, 0, BOSS_CENTER_Z)
    shaft_clearance = make_y_axis_cylinder(SHAFT_CLEAR_D, BASE_W + 4.0, 0, 0, BOSS_CENTER_Z)

    block = block.cut(bearing_seat).cut(shaft_clearance)

    block = block.edges("|Z").chamfer(CHAMFER_W)

    return block.clean()


if __name__ == "__main__":
    model = build_part()
    exporters.export(model, f"{COMPONENT_NAME}.step")
```

### Static Example 3 - Snap-On Electronics Enclosure Lid

INPUT:
```json
{
  "generation_mode": "complete script",
  "intent": "Create a single-piece snap-on lid for a small electronics enclosure. Use mm units, export as STEP, and make it suitable for FDM printing. The lid should be about 90mm x 55mm x 8mm overall, with a thin-wall shell form, a shallow underside lip that fits inside a matching box, four small snap tabs on the long sides, and two cable relief notches on one short edge. Use 2mm nominal wall thickness, rounded corners, and no overhangs beyond 45 degrees where possible."
}
```

OUTPUT:
```python
import cadquery as cq
from cadquery import exporters

COMPONENT_NAME = "snap_on_electronics_enclosure_lid"

LID_L = 90.0
LID_W = 55.0
OVERALL_H = 8.0

TOP_T = 2.0
LIP_H = OVERALL_H - TOP_T
WALL_T = 2.0

CORNER_R = 4.0

LIP_OUTER_L = 82.0
LIP_OUTER_W = 47.0
LIP_INNER_L = LIP_OUTER_L - 2.0 * WALL_T
LIP_INNER_W = LIP_OUTER_W - 2.0 * WALL_T

TAB_L = 10.0
TAB_PROJ = 2.0
TAB_H = 3.0
TAB_Z = 2.2
TAB_X_OFFSET = 24.0

NOTCH_W = 7.0
NOTCH_D = 8.0
NOTCH_Z_CLEAR = 6.0
NOTCH_Y_OFFSET = 10.0


def make_rounded_box(length: float, width: float, height: float, radius: float) -> cq.Workplane:
    safe_radius = min(radius, length / 2.0 - 0.5, width / 2.0 - 0.5)
    box = cq.Workplane("XY").box(length, width, height)
    if safe_radius > 0.5:
        box = box.edges("|Z").fillet(safe_radius)
    return box


def build_part() -> cq.Workplane:
    top = make_rounded_box(LID_L, LID_W, TOP_T, CORNER_R).translate(
        (0, 0, LIP_H + TOP_T / 2.0)
    )

    front_lip = (
        cq.Workplane("XY")
        .box(LIP_OUTER_L, WALL_T, LIP_H)
        .translate((0, LIP_OUTER_W / 2.0 - WALL_T / 2.0, LIP_H / 2.0))
    )

    rear_lip = (
        cq.Workplane("XY")
        .box(LIP_OUTER_L, WALL_T, LIP_H)
        .translate((0, -LIP_OUTER_W / 2.0 + WALL_T / 2.0, LIP_H / 2.0))
    )

    left_lip = (
        cq.Workplane("XY")
        .box(WALL_T, LIP_INNER_W, LIP_H)
        .translate((-LIP_OUTER_L / 2.0 + WALL_T / 2.0, 0, LIP_H / 2.0))
    )

    right_lip = (
        cq.Workplane("XY")
        .box(WALL_T, LIP_INNER_W, LIP_H)
        .translate((LIP_OUTER_L / 2.0 - WALL_T / 2.0, 0, LIP_H / 2.0))
    )

    lid = top.union(front_lip).union(rear_lip).union(left_lip).union(right_lip)

    for y_side in (-1.0, 1.0):
        y = y_side * (LIP_OUTER_W / 2.0 + TAB_PROJ / 2.0)
        for x in (-TAB_X_OFFSET, TAB_X_OFFSET):
            tab = (
                cq.Workplane("XY")
                .box(TAB_L, TAB_PROJ, TAB_H)
                .translate((x, y, TAB_Z + TAB_H / 2.0))
            )
            lead_chamfer = (
                cq.Workplane("YZ")
                .polyline(
                    [
                        (
                            y_side * (LIP_OUTER_W / 2.0),
                            TAB_Z,
                        ),
                        (
                            y_side * (LIP_OUTER_W / 2.0 + TAB_PROJ),
                            TAB_Z,
                        ),
                        (
                            y_side * (LIP_OUTER_W / 2.0),
                            TAB_Z + TAB_H,
                        ),
                    ]
                )
                .close()
                .extrude(TAB_L)
                .translate((x - TAB_L / 2.0, 0, 0))
            )
            lid = lid.union(tab).union(lead_chamfer)

    for y in (-NOTCH_Y_OFFSET, NOTCH_Y_OFFSET):
        notch = (
            cq.Workplane("XY")
            .box(NOTCH_D, NOTCH_W, NOTCH_Z_CLEAR + 2.0)
            .translate((LID_L / 2.0 - NOTCH_D / 2.0, y, NOTCH_Z_CLEAR / 2.0))
        )
        lid = lid.cut(notch)

    return lid.clean()


if __name__ == "__main__":
    model = build_part()
    exporters.export(model, f"{COMPONENT_NAME}.step")
```

### Static Example 4 - Square Bolt Pattern Adapter Plate

INPUT:
```json
{
  "generation_mode": "complete script",
  "intent": "Create a single-piece adapter plate that converts a 40mm square bolt pattern to a 30mm square bolt pattern. Use mm units and export as STEP. The part should be CNC machinable or FDM printable, about 55mm x 55mm x 6mm, with four M4 clearance holes on the outer 40mm pattern and four M3 clearance holes on the inner 30mm pattern. Add a centered circular pilot hole of 12mm diameter, lightly chamfer all top edges, and keep the shape symmetric with rounded outside corners."
}
```

OUTPUT:
```python
import cadquery as cq
from cadquery import exporters

COMPONENT_NAME = "square_bolt_pattern_adapter_plate"

PLATE_L = 55.0
PLATE_W = 55.0
PLATE_T = 6.0

CORNER_R = 4.0
TOP_CHAMFER = 0.5

OUTER_PATTERN = 40.0
INNER_PATTERN = 30.0

M4_CLEAR_D = 4.5
M3_CLEAR_D = 3.4
PILOT_D = 12.0


def build_part() -> cq.Workplane:
    plate = (
        cq.Workplane("XY")
        .rect(PLATE_L - 2.0 * CORNER_R, PLATE_W)
        .rect(PLATE_L, PLATE_W - 2.0 * CORNER_R)
        .circle(CORNER_R)
        .pushPoints(
            [
                (-PLATE_L / 2.0 + CORNER_R, -PLATE_W / 2.0 + CORNER_R),
                (PLATE_L / 2.0 - CORNER_R, -PLATE_W / 2.0 + CORNER_R),
                (-PLATE_L / 2.0 + CORNER_R, PLATE_W / 2.0 - CORNER_R),
                (PLATE_L / 2.0 - CORNER_R, PLATE_W / 2.0 - CORNER_R),
            ]
        )
        .circle(CORNER_R)
        .extrude(PLATE_T)
    )

    pilot_cut = (
        cq.Workplane("XY")
        .circle(PILOT_D / 2.0)
        .extrude(PLATE_T + 2.0)
        .translate((0.0, 0.0, -1.0))
    )
    plate = plate.cut(pilot_cut)

    outer_points = [
        (-OUTER_PATTERN / 2.0, -OUTER_PATTERN / 2.0),
        (OUTER_PATTERN / 2.0, -OUTER_PATTERN / 2.0),
        (-OUTER_PATTERN / 2.0, OUTER_PATTERN / 2.0),
        (OUTER_PATTERN / 2.0, OUTER_PATTERN / 2.0),
    ]
    outer_holes = (
        cq.Workplane("XY")
        .pushPoints(outer_points)
        .circle(M4_CLEAR_D / 2.0)
        .extrude(PLATE_T + 2.0)
        .translate((0.0, 0.0, -1.0))
    )
    plate = plate.cut(outer_holes)

    inner_points = [
        (-INNER_PATTERN / 2.0, -INNER_PATTERN / 2.0),
        (INNER_PATTERN / 2.0, -INNER_PATTERN / 2.0),
        (-INNER_PATTERN / 2.0, INNER_PATTERN / 2.0),
        (INNER_PATTERN / 2.0, INNER_PATTERN / 2.0),
    ]
    inner_holes = (
        cq.Workplane("XY")
        .pushPoints(inner_points)
        .circle(M3_CLEAR_D / 2.0)
        .extrude(PLATE_T + 2.0)
        .translate((0.0, 0.0, -1.0))
    )
    plate = plate.cut(inner_holes)

    plate = plate.faces(">Z").edges().chamfer(TOP_CHAMFER)

    return plate.clean()


if __name__ == "__main__":
    model = build_part()
    exporters.export(model, f"{COMPONENT_NAME}.step")
```

### Static Assembly Example 1 - Two-Part Electronics Enclosure

INPUT:
```json
{
  "generation_mode": "complete script",
  "intent": "Create a static two-part FDM-printable electronics enclosure assembly with a base and a removable screw-on lid. Use mm units and export as STEP. The enclosure should be about 100mm x 60mm x 35mm overall, with no moving joints. The base should be an open-top thin-wall box with a flat bottom, 2mm walls, and four internal cylindrical standoffs for M3 screws. Add a cable opening on one short side of the base. The lid should sit on top of the base, overlap it with a shallow internal lip, and include four M3 countersunk through holes aligned with the base standoffs. Assemble the base and lid in the closed position as separate components in a CadQuery assembly."
}
```

OUTPUT:
```python
import cadquery as cq

COMPONENT_NAME = "two_part_electronics_enclosure"

OUTER_L = 100.0
OUTER_W = 60.0
OVERALL_H = 35.0

BASE_H = 30.0
LID_TOP_T = 5.0
BOTTOM_T = 3.0
WALL_T = 2.0

LID_LIP_H = 4.0
LID_LIP_T = 1.6
LID_CLEARANCE = 0.4

M3_CLEAR_D = 3.4
M3_PILOT_D = 2.7
M3_COUNTERSINK_D = 7.0

STANDOFF_OD = 8.0
STANDOFF_H = 22.0

SCREW_X_SPACING = 78.0
SCREW_Y_SPACING = 42.0

CABLE_OPENING_W = 16.0
CABLE_OPENING_H = 9.0
CABLE_OPENING_Z = BOTTOM_T + CABLE_OPENING_H / 2.0

SMALL_CHAMFER = 0.5


def make_z_axis_cylinder(diameter: float, height: float, x: float, y: float, z: float) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .cylinder(height, diameter / 2.0)
        .translate((x, y, z))
    )


def make_base() -> cq.Workplane:
    bottom = (
        cq.Workplane("XY")
        .box(OUTER_L, OUTER_W, BOTTOM_T)
        .translate((0.0, 0.0, BOTTOM_T / 2.0))
    )

    front_wall = (
        cq.Workplane("XY")
        .box(OUTER_L, WALL_T, BASE_H)
        .translate((0.0, OUTER_W / 2.0 - WALL_T / 2.0, BASE_H / 2.0))
    )

    back_wall = (
        cq.Workplane("XY")
        .box(OUTER_L, WALL_T, BASE_H)
        .translate((0.0, -OUTER_W / 2.0 + WALL_T / 2.0, BASE_H / 2.0))
    )

    left_wall = (
        cq.Workplane("XY")
        .box(WALL_T, OUTER_W - 2.0 * WALL_T, BASE_H)
        .translate((-OUTER_L / 2.0 + WALL_T / 2.0, 0.0, BASE_H / 2.0))
    )

    right_wall = (
        cq.Workplane("XY")
        .box(WALL_T, OUTER_W - 2.0 * WALL_T, BASE_H)
        .translate((OUTER_L / 2.0 - WALL_T / 2.0, 0.0, BASE_H / 2.0))
    )

    base = bottom.union(front_wall).union(back_wall).union(left_wall).union(right_wall)

    for x in (-SCREW_X_SPACING / 2.0, SCREW_X_SPACING / 2.0):
        for y in (-SCREW_Y_SPACING / 2.0, SCREW_Y_SPACING / 2.0):
            standoff = make_z_axis_cylinder(
                STANDOFF_OD,
                STANDOFF_H,
                x,
                y,
                BOTTOM_T + STANDOFF_H / 2.0,
            )
            pilot_hole = make_z_axis_cylinder(
                M3_PILOT_D,
                STANDOFF_H + 2.0,
                x,
                y,
                BOTTOM_T + STANDOFF_H / 2.0,
            )
            base = base.union(standoff).cut(pilot_hole)

    cable_opening = (
        cq.Workplane("XY")
        .box(WALL_T + 4.0, CABLE_OPENING_W, CABLE_OPENING_H)
        .translate((OUTER_L / 2.0 - WALL_T / 2.0, 0.0, CABLE_OPENING_Z))
    )
    base = base.cut(cable_opening)

    base = base.edges("|Z").chamfer(SMALL_CHAMFER)

    return base.clean()


def make_lid() -> cq.Workplane:
    lid_top = (
        cq.Workplane("XY")
        .box(OUTER_L, OUTER_W, LID_TOP_T)
        .translate((0.0, 0.0, BASE_H + LID_TOP_T / 2.0))
    )

    lip_outer_l = OUTER_L - 2.0 * WALL_T - LID_CLEARANCE
    lip_outer_w = OUTER_W - 2.0 * WALL_T - LID_CLEARANCE
    lip_z = BASE_H - LID_LIP_H / 2.0

    lip_front = (
        cq.Workplane("XY")
        .box(lip_outer_l, LID_LIP_T, LID_LIP_H)
        .translate((0.0, lip_outer_w / 2.0 - LID_LIP_T / 2.0, lip_z))
    )

    lip_back = (
        cq.Workplane("XY")
        .box(lip_outer_l, LID_LIP_T, LID_LIP_H)
        .translate((0.0, -lip_outer_w / 2.0 + LID_LIP_T / 2.0, lip_z))
    )

    lip_left = (
        cq.Workplane("XY")
        .box(LID_LIP_T, lip_outer_w - 2.0 * LID_LIP_T, LID_LIP_H)
        .translate((-lip_outer_l / 2.0 + LID_LIP_T / 2.0, 0.0, lip_z))
    )

    lip_right = (
        cq.Workplane("XY")
        .box(LID_LIP_T, lip_outer_w - 2.0 * LID_LIP_T, LID_LIP_H)
        .translate((lip_outer_l / 2.0 - LID_LIP_T / 2.0, 0.0, lip_z))
    )

    lid = lid_top.union(lip_front).union(lip_back).union(lip_left).union(lip_right)

    for x in (-SCREW_X_SPACING / 2.0, SCREW_X_SPACING / 2.0):
        for y in (-SCREW_Y_SPACING / 2.0, SCREW_Y_SPACING / 2.0):
            clearance = make_z_axis_cylinder(
                M3_CLEAR_D,
                LID_TOP_T + 4.0,
                x,
                y,
                BASE_H + LID_TOP_T / 2.0,
            )
            countersink_recess = make_z_axis_cylinder(
                M3_COUNTERSINK_D,
                1.6,
                x,
                y,
                BASE_H + LID_TOP_T - 0.8,
            )
            lid = lid.cut(clearance).cut(countersink_recess)

    lid = lid.edges("|Z").chamfer(SMALL_CHAMFER)

    return lid.clean()


def build_assembly() -> cq.Assembly:
    base = make_base()
    lid = make_lid()

    assembly = cq.Assembly(name=COMPONENT_NAME)
    assembly.add(base, name="base", loc=cq.Location(cq.Vector(0.0, 0.0, 0.0)))
    assembly.add(lid, name="removable_lid", loc=cq.Location(cq.Vector(0.0, 0.0, 0.0)))
    return assembly


if __name__ == "__main__":
    assembly = build_assembly()
    assembly.save(f"{COMPONENT_NAME}_assembly.step")
```

### Static Assembly Example 2 - Split Tube Clamp Block

INPUT:
```json
{
  "generation_mode": "complete script",
  "intent": "Design a static split clamp block assembly for fastening a 12mm round tube to a flat mounting plate. Use mm units and export as STEP. The assembly should be suitable for CNC machining or FDM printing and should include separate lower and upper clamp halves plus two M5 socket-head cap screws. Use a compact rectangular clamp body with robust wall thickness. The lower block should have a flat mounting base, a centered half-round saddle for the 12mm tube, and two vertical M5 clearance holes placed on either side of the tube bore. Add two countersunk or counterbored mounting holes in the lower block so it can bolt down to a flat plate. The upper cap should have the matching half-round tube saddle, flat mating face, two vertical M5 clearance holes aligned with the lower block, and counterbores for the M5 screw heads. When assembled, the two halves should form a continuous circular tube bore with slight clearance around the 12mm tube. Keep screw holes outside the tube bore, maintain enough material around all holes, chamfer external edges, and avoid moving joints or hinged features."
}
```

OUTPUT:
```python
import cadquery as cq

COMPONENT_NAME = "static_split_tube_clamp_block"

CLAMP_L = 56.0
CLAMP_W = 42.0
LOWER_H = 16.0
UPPER_H = 14.0

TUBE_D = 12.6
TUBE_AXIS_Z = LOWER_H
TUBE_AXIS_Y = 0.0

CLAMP_SCREW_D = 5.5
CLAMP_SCREW_HEAD_D = 10.0
CLAMP_SCREW_HEAD_H = 4.2
CLAMP_SCREW_Y_OFFSET = 14.0

MOUNT_HOLE_D = 5.5
MOUNT_COUNTERBORE_D = 10.0
MOUNT_COUNTERBORE_H = 3.5
MOUNT_HOLE_X_OFFSET = 18.0
MOUNT_HOLE_Y_OFFSET = 14.0

SCREW_SHAFT_D = 5.0
SCREW_HEAD_D = 9.5
SCREW_HEAD_H = 4.0

EDGE_CHAMFER = 0.5


def make_x_axis_cylinder(diameter: float, length: float, x: float, y: float, z: float) -> cq.Workplane:
    return (
        cq.Workplane("YZ")
        .circle(diameter / 2.0)
        .extrude(length)
        .translate((x - length / 2.0, y, z))
    )


def make_z_axis_cylinder(diameter: float, height: float, x: float, y: float, z: float) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .cylinder(height, diameter / 2.0)
        .translate((x, y, z))
    )


def make_lower_saddle_block() -> cq.Workplane:
    lower = (
        cq.Workplane("XY")
        .box(CLAMP_L, CLAMP_W, LOWER_H)
        .translate((0.0, 0.0, LOWER_H / 2.0))
    )

    tube_saddle_cut = make_x_axis_cylinder(
        TUBE_D,
        CLAMP_L + 4.0,
        0.0,
        TUBE_AXIS_Y,
        TUBE_AXIS_Z,
    )
    lower = lower.cut(tube_saddle_cut)

    for y in (-CLAMP_SCREW_Y_OFFSET, CLAMP_SCREW_Y_OFFSET):
        screw_clearance = make_z_axis_cylinder(
            CLAMP_SCREW_D,
            LOWER_H + 4.0,
            0.0,
            y,
            LOWER_H / 2.0,
        )
        lower = lower.cut(screw_clearance)

    for x in (-MOUNT_HOLE_X_OFFSET, MOUNT_HOLE_X_OFFSET):
        for y in (-MOUNT_HOLE_Y_OFFSET, MOUNT_HOLE_Y_OFFSET):
            mounting_clearance = make_z_axis_cylinder(
                MOUNT_HOLE_D,
                LOWER_H + 4.0,
                x,
                y,
                LOWER_H / 2.0,
            )
            bottom_counterbore = make_z_axis_cylinder(
                MOUNT_COUNTERBORE_D,
                MOUNT_COUNTERBORE_H,
                x,
                y,
                MOUNT_COUNTERBORE_H / 2.0,
            )
            lower = lower.cut(mounting_clearance).cut(bottom_counterbore)

    lower = lower.edges("|Z").chamfer(EDGE_CHAMFER)
    return lower.clean()


def make_upper_clamp_cap() -> cq.Workplane:
    upper = (
        cq.Workplane("XY")
        .box(CLAMP_L, CLAMP_W, UPPER_H)
        .translate((0.0, 0.0, LOWER_H + UPPER_H / 2.0))
    )

    tube_saddle_cut = make_x_axis_cylinder(
        TUBE_D,
        CLAMP_L + 4.0,
        0.0,
        TUBE_AXIS_Y,
        TUBE_AXIS_Z,
    )
    upper = upper.cut(tube_saddle_cut)

    for y in (-CLAMP_SCREW_Y_OFFSET, CLAMP_SCREW_Y_OFFSET):
        screw_clearance = make_z_axis_cylinder(
            CLAMP_SCREW_D,
            UPPER_H + 4.0,
            0.0,
            y,
            LOWER_H + UPPER_H / 2.0,
        )
        head_counterbore = make_z_axis_cylinder(
            CLAMP_SCREW_HEAD_D,
            CLAMP_SCREW_HEAD_H,
            0.0,
            y,
            LOWER_H + UPPER_H - CLAMP_SCREW_HEAD_H / 2.0,
        )
        upper = upper.cut(screw_clearance).cut(head_counterbore)

    upper = upper.edges("|Z").chamfer(EDGE_CHAMFER)
    return upper.clean()


def make_m5_socket_head_cap_screw(y: float) -> cq.Workplane:
    shaft = make_z_axis_cylinder(
        SCREW_SHAFT_D,
        LOWER_H + UPPER_H - 2.0,
        0.0,
        y,
        (LOWER_H + UPPER_H - 2.0) / 2.0,
    )

    head = make_z_axis_cylinder(
        SCREW_HEAD_D,
        SCREW_HEAD_H,
        0.0,
        y,
        LOWER_H + UPPER_H - SCREW_HEAD_H / 2.0,
    )

    socket = make_z_axis_cylinder(
        4.0,
        1.8,
        0.0,
        y,
        LOWER_H + UPPER_H - 0.9,
    )

    return shaft.union(head).cut(socket).clean()


def build_assembly() -> cq.Assembly:
    lower = make_lower_saddle_block()
    upper = make_upper_clamp_cap()
    screw_a = make_m5_socket_head_cap_screw(-CLAMP_SCREW_Y_OFFSET)
    screw_b = make_m5_socket_head_cap_screw(CLAMP_SCREW_Y_OFFSET)

    assembly = cq.Assembly(name=COMPONENT_NAME)
    assembly.add(lower, name="lower_saddle_block", loc=cq.Location(cq.Vector(0.0, 0.0, 0.0)))
    assembly.add(upper, name="upper_clamp_cap", loc=cq.Location(cq.Vector(0.0, 0.0, 0.0)))
    assembly.add(screw_a, name="m5_socket_head_screw_left", loc=cq.Location(cq.Vector(0.0, 0.0, 0.0)))
    assembly.add(screw_b, name="m5_socket_head_screw_right", loc=cq.Location(cq.Vector(0.0, 0.0, 0.0)))
    return assembly


if __name__ == "__main__":
    assembly = build_assembly()
    assembly.save(f"{COMPONENT_NAME}.step")
```

### Static Assembly Example 3 - Camera Mount Assembly

INPUT:
```json
{
  "generation_mode": "complete script",
  "intent": "Create a static camera mount assembly for attaching a small rectangular camera module to a vertical extrusion. Use mm units and export as STEP. The assembly should include a back plate that bolts to 20x20 aluminum extrusion, a front camera plate with four M2 mounting holes, and two spacer posts between the plates. Use M3 screws to connect the spacer posts to both plates. The design should be lightweight structural, FDM printable, and have alignment features so the camera plate stays parallel to the extrusion face. This is a fixed assembly, not an adjustable joint."
}
```

OUTPUT:
```python
import cadquery as cq

COMPONENT_NAME = "static_camera_mount_assembly"

BACK_PLATE_W = 48.0
BACK_PLATE_H = 60.0
BACK_PLATE_T = 4.0

CAMERA_PLATE_W = 42.0
CAMERA_PLATE_H = 38.0
CAMERA_PLATE_T = 4.0

PLATE_GAP = 30.0
BACK_PLATE_Y = 0.0
FRONT_PLATE_Y = BACK_PLATE_Y + BACK_PLATE_T / 2.0 + PLATE_GAP + CAMERA_PLATE_T / 2.0

SPACER_D = 8.0
SPACER_BORE_D = 3.3
SPACER_LENGTH = PLATE_GAP
SPACER_X_SPACING = 28.0
SPACER_Z = 0.0

M3_CLEAR_D = 3.4
M3_HEAD_D = 6.2
M3_HEAD_H = 2.5

M2_CLEAR_D = 2.4
CAMERA_HOLE_X_SPACING = 28.0
CAMERA_HOLE_Z_SPACING = 28.0

EXTRUSION_M5_D = 5.5
EXTRUSION_HOLE_Z_SPACING = 20.0

ALIGN_RAIL_W = 3.0
ALIGN_RAIL_H = 28.0
ALIGN_RAIL_T = 1.2
ALIGN_RAIL_X_OFFSET = 17.0


def make_y_axis_cylinder(
    diameter: float,
    length: float,
    x: float,
    y_start: float,
    z: float,
) -> cq.Workplane:
    return (
        cq.Workplane("XZ")
        .circle(diameter / 2.0)
        .extrude(length)
        .translate((x, y_start, z))
    )


def make_back_plate() -> cq.Workplane:
    back = (
        cq.Workplane("XY")
        .box(BACK_PLATE_W, BACK_PLATE_T, BACK_PLATE_H)
        .translate((0.0, BACK_PLATE_Y, 0.0))
    )

    for z in (-EXTRUSION_HOLE_Z_SPACING / 2.0, EXTRUSION_HOLE_Z_SPACING / 2.0):
        extrusion_hole = make_y_axis_cylinder(
            EXTRUSION_M5_D,
            BACK_PLATE_T + 4.0,
            0.0,
            BACK_PLATE_Y - BACK_PLATE_T / 2.0 - 2.0,
            z,
        )
        back = back.cut(extrusion_hole)

    for x in (-SPACER_X_SPACING / 2.0, SPACER_X_SPACING / 2.0):
        spacer_screw_hole = make_y_axis_cylinder(
            M3_CLEAR_D,
            BACK_PLATE_T + 4.0,
            x,
            BACK_PLATE_Y - BACK_PLATE_T / 2.0 - 2.0,
            SPACER_Z,
        )
        back = back.cut(spacer_screw_hole)

    for x in (-ALIGN_RAIL_X_OFFSET, ALIGN_RAIL_X_OFFSET):
        rail = (
            cq.Workplane("XY")
            .box(ALIGN_RAIL_W, ALIGN_RAIL_T, ALIGN_RAIL_H)
            .translate(
                (
                    x,
                    BACK_PLATE_Y + BACK_PLATE_T / 2.0 + ALIGN_RAIL_T / 2.0,
                    SPACER_Z,
                )
            )
        )
        back = back.union(rail)

    return back.clean()


def make_front_camera_plate() -> cq.Workplane:
    front = (
        cq.Workplane("XY")
        .box(CAMERA_PLATE_W, CAMERA_PLATE_T, CAMERA_PLATE_H)
        .translate((0.0, FRONT_PLATE_Y, 0.0))
    )

    for x in (-CAMERA_HOLE_X_SPACING / 2.0, CAMERA_HOLE_X_SPACING / 2.0):
        for z in (-CAMERA_HOLE_Z_SPACING / 2.0, CAMERA_HOLE_Z_SPACING / 2.0):
            camera_hole = make_y_axis_cylinder(
                M2_CLEAR_D,
                CAMERA_PLATE_T + 4.0,
                x,
                FRONT_PLATE_Y - CAMERA_PLATE_T / 2.0 - 2.0,
                z,
            )
            front = front.cut(camera_hole)

    for x in (-SPACER_X_SPACING / 2.0, SPACER_X_SPACING / 2.0):
        spacer_screw_hole = make_y_axis_cylinder(
            M3_CLEAR_D,
            CAMERA_PLATE_T + 4.0,
            x,
            FRONT_PLATE_Y - CAMERA_PLATE_T / 2.0 - 2.0,
            SPACER_Z,
        )
        head_recess = make_y_axis_cylinder(
            M3_HEAD_D,
            M3_HEAD_H,
            x,
            FRONT_PLATE_Y + CAMERA_PLATE_T / 2.0 - M3_HEAD_H,
            SPACER_Z,
        )
        front = front.cut(spacer_screw_hole).cut(head_recess)

    for x in (-ALIGN_RAIL_X_OFFSET, ALIGN_RAIL_X_OFFSET):
        alignment_pocket = (
            cq.Workplane("XY")
            .box(ALIGN_RAIL_W + 0.4, ALIGN_RAIL_T + 0.4, ALIGN_RAIL_H + 0.4)
            .translate(
                (
                    x,
                    FRONT_PLATE_Y - CAMERA_PLATE_T / 2.0 + ALIGN_RAIL_T / 2.0,
                    SPACER_Z,
                )
            )
        )
        front = front.cut(alignment_pocket)

    return front.clean()


def make_spacer_post(x: float) -> cq.Workplane:
    y_start = BACK_PLATE_Y + BACK_PLATE_T / 2.0
    spacer = make_y_axis_cylinder(
        SPACER_D,
        SPACER_LENGTH,
        x,
        y_start,
        SPACER_Z,
    )

    bore = make_y_axis_cylinder(
        SPACER_BORE_D,
        SPACER_LENGTH + 4.0,
        x,
        y_start - 2.0,
        SPACER_Z,
    )

    return spacer.cut(bore).clean()


def make_m3_screw(x: float) -> cq.Workplane:
    screw_start = BACK_PLATE_Y - BACK_PLATE_T / 2.0
    screw_length = BACK_PLATE_T + PLATE_GAP + CAMERA_PLATE_T

    shaft = make_y_axis_cylinder(
        3.0,
        screw_length,
        x,
        screw_start,
        SPACER_Z,
    )

    head = make_y_axis_cylinder(
        M3_HEAD_D,
        M3_HEAD_H,
        x,
        FRONT_PLATE_Y + CAMERA_PLATE_T / 2.0 - M3_HEAD_H,
        SPACER_Z,
    )

    socket = make_y_axis_cylinder(
        2.4,
        1.4,
        x,
        FRONT_PLATE_Y + CAMERA_PLATE_T / 2.0 - 1.4,
        SPACER_Z,
    )

    return shaft.union(head).cut(socket).clean()


def build_assembly() -> cq.Assembly:
    back_plate = make_back_plate()
    front_plate = make_front_camera_plate()
    spacer_left = make_spacer_post(-SPACER_X_SPACING / 2.0)
    spacer_right = make_spacer_post(SPACER_X_SPACING / 2.0)
    screw_left = make_m3_screw(-SPACER_X_SPACING / 2.0)
    screw_right = make_m3_screw(SPACER_X_SPACING / 2.0)

    assembly = cq.Assembly(name=COMPONENT_NAME)
    assembly.add(back_plate, name="back_plate", loc=cq.Location(cq.Vector(0.0, 0.0, 0.0)))
    assembly.add(front_plate, name="front_camera_plate", loc=cq.Location(cq.Vector(0.0, 0.0, 0.0)))
    assembly.add(spacer_left, name="left_spacer_post", loc=cq.Location(cq.Vector(0.0, 0.0, 0.0)))
    assembly.add(spacer_right, name="right_spacer_post", loc=cq.Location(cq.Vector(0.0, 0.0, 0.0)))
    assembly.add(screw_left, name="left_m3_screw", loc=cq.Location(cq.Vector(0.0, 0.0, 0.0)))
    assembly.add(screw_right, name="right_m3_screw", loc=cq.Location(cq.Vector(0.0, 0.0, 0.0)))
    return assembly


if __name__ == "__main__":
    assembly = build_assembly()
    assembly.save(f"{COMPONENT_NAME}.step")
```

### Static Assembly Example 4 - NEMA 17 Motor Mount Assembly

INPUT:
```json
{
  "generation_mode": "complete script",
  "intent": "Create a static FDM-printable NEMA 17 stepper motor mounting assembly. Use mm units and export as STEP. The assembly should include one rigid L-bracket body and four M3 motor mounting screws represented as simple cylinders. The bracket should have a horizontal base plate, a vertical motor face plate, and two triangular side gussets for stiffness. This is a fixed assembly with no joints or motion degrees of freedom. Make the motor face plate large enough for a NEMA 17 mounting pattern. Include a centered shaft clearance hole on the motor face and four M3 clearance holes on the standard 31mm square NEMA 17 bolt pattern. Place the triangular gussets outboard near the left and right edges of the face plate so they do not interfere with the shaft hole or M3 mounting holes. Make the base plate broad and rigid, with four M5 vertical mounting holes positioned clear of the gussets. Keep the design structurally stiff, FDM printable, and assembled in the final mounted position."
}
```

OUTPUT:
```python
import cadquery as cq

COMPONENT_NAME = "static_nema17_motor_mount_assembly"

BASE_L = 86.0
BASE_D = 72.0
BASE_T = 6.0

FACE_W = 78.0
FACE_H = 74.0
FACE_T = 6.0

FACE_Y = 3.0
FACE_FRONT_Y = FACE_Y + FACE_T / 2.0
MOTOR_CENTER_Z = BASE_T + 36.0

SHAFT_CLEAR_D = 24.0
NEMA17_BOLT_PATTERN = 31.0
M3_CLEAR_D = 3.4

BASE_M5_CLEAR_D = 5.5
BASE_M5_X_SPACING = 56.0
BASE_M5_Y_SPACING = 40.0
BASE_M5_Y_CENTER = 38.0

GUSSET_T = 6.0
GUSSET_REACH_Y = 36.0
GUSSET_RISE_Z = 52.0
GUSSET_X_OFFSET = 34.0

M3_SCREW_D = 3.0
M3_SCREW_HEAD_D = 6.0
M3_SCREW_HEAD_T = 2.5
M3_SCREW_LENGTH = FACE_T + 10.0


def make_y_axis_cylinder(diameter: float, length: float, x: float, y_start: float, z: float) -> cq.Workplane:
    return (
        cq.Workplane("XZ")
        .circle(diameter / 2.0)
        .extrude(length)
        .translate((x, y_start, z))
    )


def make_z_axis_cylinder(diameter: float, height: float, x: float, y: float, z: float) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .cylinder(height, diameter / 2.0)
        .translate((x, y, z))
    )


def make_motor_mount_bracket() -> cq.Workplane:
    base_plate = (
        cq.Workplane("XY")
        .box(BASE_L, BASE_D, BASE_T)
        .translate((0.0, BASE_D / 2.0, BASE_T / 2.0))
    )

    motor_face_plate = (
        cq.Workplane("XY")
        .box(FACE_W, FACE_T, FACE_H)
        .translate((0.0, FACE_Y, BASE_T + FACE_H / 2.0))
    )

    bracket = base_plate.union(motor_face_plate)

    for x_center in (-GUSSET_X_OFFSET, GUSSET_X_OFFSET):
        gusset = (
            cq.Workplane("YZ")
            .polyline(
                [
                    (FACE_FRONT_Y, BASE_T),
                    (FACE_FRONT_Y + GUSSET_REACH_Y, BASE_T),
                    (FACE_FRONT_Y, BASE_T + GUSSET_RISE_Z),
                ]
            )
            .close()
            .extrude(GUSSET_T)
            .translate((x_center - GUSSET_T / 2.0, 0.0, 0.0))
        )
        bracket = bracket.union(gusset)

    shaft_clearance = make_y_axis_cylinder(
        SHAFT_CLEAR_D,
        FACE_T + 8.0,
        0.0,
        FACE_Y - FACE_T / 2.0 - 4.0,
        MOTOR_CENTER_Z,
    )
    bracket = bracket.cut(shaft_clearance)

    for x in (-NEMA17_BOLT_PATTERN / 2.0, NEMA17_BOLT_PATTERN / 2.0):
        for z in (
            MOTOR_CENTER_Z - NEMA17_BOLT_PATTERN / 2.0,
            MOTOR_CENTER_Z + NEMA17_BOLT_PATTERN / 2.0,
        ):
            motor_mount_hole = make_y_axis_cylinder(
                M3_CLEAR_D,
                FACE_T + 8.0,
                x,
                FACE_Y - FACE_T / 2.0 - 4.0,
                z,
            )
            bracket = bracket.cut(motor_mount_hole)

    for x in (-BASE_M5_X_SPACING / 2.0, BASE_M5_X_SPACING / 2.0):
        for y in (
            BASE_M5_Y_CENTER - BASE_M5_Y_SPACING / 2.0,
            BASE_M5_Y_CENTER + BASE_M5_Y_SPACING / 2.0,
        ):
            base_mount_hole = make_z_axis_cylinder(
                BASE_M5_CLEAR_D,
                BASE_T + 4.0,
                x,
                y,
                BASE_T / 2.0,
            )
            bracket = bracket.cut(base_mount_hole)

    return bracket.clean()


def make_m3_motor_mount_screw(x: float, z: float) -> cq.Workplane:
    shaft = make_y_axis_cylinder(
        M3_SCREW_D,
        M3_SCREW_LENGTH,
        x,
        FACE_Y - FACE_T / 2.0 - 2.0,
        z,
    )

    head = make_y_axis_cylinder(
        M3_SCREW_HEAD_D,
        M3_SCREW_HEAD_T,
        x,
        FACE_Y + FACE_T / 2.0,
        z,
    )

    return shaft.union(head).clean()


def build_assembly() -> cq.Assembly:
    bracket = make_motor_mount_bracket()

    assembly = cq.Assembly(name=COMPONENT_NAME)
    assembly.add(
        bracket,
        name="rigid_l_bracket_with_outboard_gussets",
        loc=cq.Location(cq.Vector(0.0, 0.0, 0.0)),
    )

    screw_index = 1
    for x in (-NEMA17_BOLT_PATTERN / 2.0, NEMA17_BOLT_PATTERN / 2.0):
        for z in (
            MOTOR_CENTER_Z - NEMA17_BOLT_PATTERN / 2.0,
            MOTOR_CENTER_Z + NEMA17_BOLT_PATTERN / 2.0,
        ):
            screw = make_m3_motor_mount_screw(x, z)
            assembly.add(
                screw,
                name=f"m3_motor_mount_screw_{screw_index}",
                loc=cq.Location(cq.Vector(0.0, 0.0, 0.0)),
            )
            screw_index += 1

    return assembly


if __name__ == "__main__":
    assembly = build_assembly()
    assembly.save(f"{COMPONENT_NAME}.step")
```
