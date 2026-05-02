## Agent 3 - Parameter Agent Few-Shots

### Example 1 - Static Servo Bracket Parameters

INPUT:
```json
{
  "component": "micro_servo_extrusion_mount",
  "plan_summary": "matching-width L-bracket with horizontal base, vertical servo plate, two outboard triangular gussets, four M2 servo holes, and two M5 base holes spaced 20mm"
}
```

OUTPUT:
```json
{
  "PLATE_W": {
    "value": 42.0,
    "unit": "mm",
    "description": "Common width shared by the base plate and vertical servo plate.",
    "min": 30.0,
    "max": 70.0,
    "depends_on": [],
    "constraint": null,
    "is_derived": false,
    "derived_from": null
  },
  "BASE_L": {
    "value": 58.0,
    "unit": "mm",
    "description": "Length of the horizontal extrusion mounting base.",
    "min": 40.0,
    "max": 90.0,
    "depends_on": [],
    "constraint": null,
    "is_derived": false,
    "derived_from": null
  },
  "BASE_T": {
    "value": 5.0,
    "unit": "mm",
    "description": "Thickness of the horizontal base plate.",
    "min": 3.0,
    "max": 10.0,
    "depends_on": [],
    "constraint": "must be >= 2.0mm for FDM strength",
    "is_derived": false,
    "derived_from": null
  },
  "SERVO_PLATE_T": {
    "value": 5.0,
    "unit": "mm",
    "description": "Thickness of the vertical servo face plate.",
    "min": 3.0,
    "max": 10.0,
    "depends_on": [],
    "constraint": "must support M2 holes without cracking",
    "is_derived": false,
    "derived_from": null
  },
  "SERVO_PLATE_H": {
    "value": 46.0,
    "unit": "mm",
    "description": "Height of the vertical servo face plate above the base.",
    "min": 35.0,
    "max": 70.0,
    "depends_on": [],
    "constraint": null,
    "is_derived": false,
    "derived_from": null
  },
  "GUSSET_X_OFFSET": {
    "value": 18.0,
    "unit": "mm",
    "description": "Side offset of the triangular gusset ribs from centerline.",
    "min": 12.0,
    "max": 25.0,
    "depends_on": [
      "SERVO_HOLE_X_SPACING",
      "GUSSET_T"
    ],
    "constraint": "must place gussets outside the M2 servo mounting hole pattern",
    "is_derived": false,
    "derived_from": null
  },
  "M2_CLEAR_D": {
    "value": 2.4,
    "unit": "mm",
    "description": "Clearance diameter for M2 servo mounting screws.",
    "min": 2.2,
    "max": 2.8,
    "depends_on": [],
    "constraint": null,
    "is_derived": false,
    "derived_from": null
  },
  "M5_CLEAR_D": {
    "value": 5.5,
    "unit": "mm",
    "description": "Clearance diameter for M5 extrusion mounting screws.",
    "min": 5.2,
    "max": 6.2,
    "depends_on": [],
    "constraint": null,
    "is_derived": false,
    "derived_from": null
  },
  "EXTRUSION_SLOT_PATTERN_SPACING": {
    "value": 20.0,
    "unit": "mm",
    "description": "Spacing between the two base mounting holes for the 20x20 extrusion slot pattern.",
    "min": 18.0,
    "max": 22.0,
    "depends_on": [],
    "constraint": "must remain close to 20mm",
    "is_derived": false,
    "derived_from": null
  },
  "BASE_W": {
    "value": 42.0,
    "unit": "mm",
    "description": "Width of the horizontal base plate, derived from common plate width.",
    "min": 30.0,
    "max": 70.0,
    "depends_on": [
      "PLATE_W"
    ],
    "constraint": "must match PLATE_W",
    "is_derived": true,
    "derived_from": "PLATE_W"
  }
}
```

### Example 2 - Static Assembly Parameters

INPUT:
```json
{
  "component": "two_part_electronics_enclosure",
  "plan_summary": "open-top 100x60x35 enclosure with separate base and lid, 2mm walls, four standoffs, lid lip, countersunk screw holes, and cable opening"
}
```

OUTPUT:
```json
{
  "OUTER_L": {
    "value": 100.0,
    "unit": "mm",
    "description": "Overall enclosure length.",
    "min": 70.0,
    "max": 160.0,
    "depends_on": [],
    "constraint": null,
    "is_derived": false,
    "derived_from": null
  },
  "OUTER_W": {
    "value": 60.0,
    "unit": "mm",
    "description": "Overall enclosure width.",
    "min": 40.0,
    "max": 120.0,
    "depends_on": [],
    "constraint": null,
    "is_derived": false,
    "derived_from": null
  },
  "BASE_H": {
    "value": 30.0,
    "unit": "mm",
    "description": "Height of the open-top base shell.",
    "min": 18.0,
    "max": 60.0,
    "depends_on": [],
    "constraint": "must leave room for lid top thickness to reach overall height",
    "is_derived": false,
    "derived_from": null
  },
  "LID_TOP_T": {
    "value": 5.0,
    "unit": "mm",
    "description": "Thickness of the screw-on lid top plate.",
    "min": 3.0,
    "max": 8.0,
    "depends_on": [],
    "constraint": "must be thick enough for countersink recesses",
    "is_derived": false,
    "derived_from": null
  },
  "WALL_T": {
    "value": 2.0,
    "unit": "mm",
    "description": "Nominal FDM wall thickness.",
    "min": 1.6,
    "max": 4.0,
    "depends_on": [],
    "constraint": "must satisfy min_wall_2mm unless explicitly changed",
    "is_derived": false,
    "derived_from": null
  },
  "STANDOFF_OD": {
    "value": 8.0,
    "unit": "mm",
    "description": "Outside diameter of internal M3 screw standoffs.",
    "min": 6.0,
    "max": 12.0,
    "depends_on": [],
    "constraint": "must leave enough material around M3 pilot holes",
    "is_derived": false,
    "derived_from": null
  },
  "SCREW_X_SPACING": {
    "value": 78.0,
    "unit": "mm",
    "description": "X spacing between lid screw holes and base standoffs.",
    "min": 50.0,
    "max": 90.0,
    "depends_on": [
      "OUTER_L",
      "WALL_T",
      "STANDOFF_OD"
    ],
    "constraint": "must keep standoffs inside the base walls",
    "is_derived": false,
    "derived_from": null
  },
  "LIP_CLEARANCE": {
    "value": 0.4,
    "unit": "mm",
    "description": "Total clearance allowing the lid lip to fit inside the base opening.",
    "min": 0.2,
    "max": 1.0,
    "depends_on": [],
    "constraint": "typical FDM clearance for a non-force-fit lid",
    "is_derived": false,
    "derived_from": null
  },
  "OVERALL_H": {
    "value": 35.0,
    "unit": "mm",
    "description": "Overall assembled enclosure height.",
    "min": 25.0,
    "max": 70.0,
    "depends_on": [
      "BASE_H",
      "LID_TOP_T"
    ],
    "constraint": "must equal BASE_H + LID_TOP_T",
    "is_derived": true,
    "derived_from": "BASE_H + LID_TOP_T"
  }
}
```