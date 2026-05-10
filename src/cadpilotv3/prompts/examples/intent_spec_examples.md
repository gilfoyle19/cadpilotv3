## Agent 1 - Intent & Specification Agent Few-Shots

### Example 1 - Static Single-Part FDM Bracket

INPUT:
```text
Create a single-piece FDM-printable micro servo bracket for mounting a standard micro servo to a 20x20 aluminum extrusion. Use mm units and export as STEP. The part should be a rigid fixed L-bracket with matching-width horizontal and vertical plates. Include a horizontal base plate with two M5 through holes spaced 20mm apart for the extrusion slot pattern. Include a vertical servo face plate with four M2 through holes in a rectangular servo mounting pattern. Add two triangular side gusset ribs between the base and face plate for stiffness, placed near the outer edges so they do not interfere with any mounting holes. Keep the design lightweight but structurally stiff, with minimum 2mm walls, a flat print base, and no moving joints.
```

OUTPUT:
```json
{
  "component": "micro_servo_extrusion_mount",
  "component_type": "single_part",
  "dof_count": 0,
  "dof_config": null,
  "joint_types": null,
  "parts": [
    "l_bracket_body",
    "horizontal_base_plate",
    "vertical_servo_face_plate",
    "triangular_side_gusset_left",
    "triangular_side_gusset_right",
    "m2_servo_mounting_holes",
    "m5_extrusion_mounting_holes"
  ],
  "output_format": "STEP",
  "units": "mm",
  "approximate_scale": "small",
  "style": "lightweight_structural",
  "manufacturing_process": "FDM",
  "constraints": [
    "min_wall_2mm",
    "flat_base_required",
    "no_floating_geometry",
    "bolt_pattern_required"
  ],
  "explicit_dimensions": [
    "20x20 aluminum extrusion",
    "two M5 through holes spaced 20mm apart",
    "four M2 through holes",
    "minimum 2mm walls"
  ],
  "explicit_constraints": [],
  "researched_dimensions": [],
  "research_sources": [],
  "clarifications_needed": []
}
```

### Example 2 - Static Single-Part CNC Bearing Block

INPUT:
```text
Design a single-piece bearing pillow block for a 608 bearing. Use mm units and export as STEP. The part will be CNC machined from aluminum. Include a rectangular base with two M6 through holes, a raised central bearing boss, and a circular bearing seat sized for a press-fit 608 bearing. Avoid internal undercuts, keep all holes through-drilled from accessible faces, and include small chamfers on external edges. The design should be a solid structural block, approximately 80mm long, 35mm wide, and 35mm tall.
```

OUTPUT:
```json
{
  "component": "bearing_pillow_block_608",
  "component_type": "single_part",
  "dof_count": 0,
  "dof_config": null,
  "joint_types": null,
  "parts": [
    "rectangular_base",
    "raised_pedestal",
    "central_bearing_boss",
    "press_fit_bearing_seat",
    "shaft_clearance_bore",
    "m6_base_mounting_holes"
  ],
  "output_format": "STEP",
  "units": "mm",
  "approximate_scale": "small",
  "style": "solid_block",
  "manufacturing_process": "CNC",
  "constraints": [
    "no_internal_undercuts",
    "through_holes_only",
    "min_feature_3mm",
    "no_stress_concentrations"
  ],
  "explicit_dimensions": [
    "608 bearing",
    "two M6 through holes",
    "approximately 80mm long",
    "35mm wide",
    "35mm tall"
  ],
  "explicit_constraints": [],
  "researched_dimensions": [],
  "research_sources": [],
  "clarifications_needed": []
}
```

### Example 3 - Static Two-Part Assembly

INPUT:
```text
Create a static two-part FDM-printable electronics enclosure assembly with a base and a removable screw-on lid. Use mm units and export as STEP. The enclosure should be about 100mm x 60mm x 35mm overall, with no moving joints. The base should be an open-top thin-wall box with a flat bottom, 2mm walls, and four internal cylindrical standoffs for M3 screws. Add a cable opening on one short side of the base. The lid should sit on top of the base, overlap it with a shallow internal lip, and include four M3 countersunk through holes aligned with the base standoffs. Assemble the base and lid in the closed position as separate components in a CadQuery assembly.
```

OUTPUT:
```json
{
  "component": "two_part_electronics_enclosure",
  "component_type": "assembly",
  "dof_count": 0,
  "dof_config": null,
  "joint_types": null,
  "parts": [
    "base_shell",
    "removable_lid",
    "internal_pcb_standoffs",
    "m3_lid_screw_holes",
    "countersink_recesses",
    "lid_alignment_lip",
    "cable_opening"
  ],
  "output_format": "STEP",
  "units": "mm",
  "approximate_scale": "medium",
  "style": "thin_wall_shell",
  "manufacturing_process": "FDM",
  "constraints": [
    "min_wall_2mm",
    "flat_base_required",
    "no_floating_geometry",
    "bolt_pattern_required",
    "alignment_pins"
  ],
  "explicit_dimensions": [
    "100mm x 60mm x 35mm overall",
    "2mm walls",
    "four internal cylindrical standoffs for M3 screws",
    "four M3 countersunk through holes"
  ],
  "explicit_constraints": [],
  "researched_dimensions": [],
  "research_sources": [],
  "clarifications_needed": []
}
```

### Example 4 - Static Motor Mount Assembly

INPUT:
```text
Create a static FDM-printable NEMA 17 stepper motor mounting assembly. Use mm units and export as STEP. The assembly should include one rigid L-bracket body and four M3 motor mounting screws represented as simple cylinders. The bracket should have a horizontal base plate, a vertical motor face plate, and two triangular side gussets for stiffness. This is a fixed assembly with no joints or motion degrees of freedom. Make the motor face plate large enough for a NEMA 17 mounting pattern. Include a centered shaft clearance hole on the motor face and four M3 clearance holes on the standard 31mm square NEMA 17 bolt pattern. Place the triangular gussets outboard near the left and right edges of the face plate so they do not interfere with the shaft hole or M3 mounting holes. Make the base plate broad and rigid, with four M5 vertical mounting holes positioned clear of the gussets. Keep the design structurally stiff, FDM printable, and assembled in the final mounted position.
```

OUTPUT:
```json
{
  "component": "static_nema17_motor_mount_assembly",
  "component_type": "assembly",
  "dof_count": 0,
  "dof_config": null,
  "joint_types": null,
  "parts": [
    "rigid_l_bracket_body",
    "horizontal_base_plate",
    "vertical_motor_face_plate",
    "triangular_side_gusset_left",
    "triangular_side_gusset_right",
    "m3_motor_mount_screw_1",
    "m3_motor_mount_screw_2",
    "m3_motor_mount_screw_3",
    "m3_motor_mount_screw_4",
    "m5_base_mounting_holes",
    "shaft_clearance_hole",
    "nema17_bolt_pattern_holes"
  ],
  "output_format": "STEP",
  "units": "mm",
  "approximate_scale": "medium",
  "style": "lightweight_structural",
  "manufacturing_process": "FDM",
  "constraints": [
    "min_wall_2mm",
    "flat_base_required",
    "symmetric_load_path",
    "bolt_pattern_required",
    "no_floating_geometry"
  ],
  "explicit_dimensions": [
    "NEMA 17 mounting pattern",
    "four M3 motor mounting screws",
    "31mm square NEMA 17 bolt pattern",
    "four M5 vertical mounting holes"
  ],
  "explicit_constraints": [
    "triangular gussets outboard so they do not interfere with the shaft hole or M3 mounting holes"
  ],
  "researched_dimensions": [],
  "research_sources": [],
  "clarifications_needed": []
}
```
