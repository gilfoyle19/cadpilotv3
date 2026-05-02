## Agent 4 - Stage B Infill Few-Shots

### Example 1 - Robust Axis-Aligned Cutter Helper

INPUT:
```json
{
  "function_name": "make_y_axis_cylinder",
  "intent": "Create a cutter cylinder through a vertical plate along the Y axis."
}
```

OUTPUT:
```python
def make_y_axis_cylinder(diameter: float, length: float, x: float, y: float, z: float) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .cylinder(length, diameter / 2)
        .rotate((0, 0, 0), (1, 0, 0), 90)
        .translate((x, y, z))
    )
```

### Example 2 - Static Assembly Build Function

INPUT:
```json
{
  "function_name": "build_assembly",
  "intent": "Assemble enclosure base and lid as separate components; do not union them."
}
```

OUTPUT:
```python
def build_assembly() -> cq.Assembly:
    base = make_base()
    lid = make_lid()

    assembly = cq.Assembly(name=COMPONENT_NAME)
    assembly.add(base, name="base", loc=cq.Location(cq.Vector(0.0, 0.0, 0.0)))
    assembly.add(lid, name="removable_lid", loc=cq.Location(cq.Vector(0.0, 0.0, 0.0)))
    return assembly
```

### Example 3 - Static Motor Mount Hole/Gusset Non-Interference

INPUT:
```json
{
  "function_name": "make_motor_mount_bracket",
  "intent": "Create a NEMA 17 bracket with centered shaft hole, 31mm M3 pattern, outboard gussets, and base M5 holes clear of gussets."
}
```

OUTPUT:
```python
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
```