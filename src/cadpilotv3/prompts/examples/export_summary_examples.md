## Agent 7 - Export & Summary Few-Shots

### Example 1 - Static Single-Part Report

INPUT:
```json
{
  "component": "micro_servo_extrusion_mount",
  "spec": "single-piece FDM servo bracket",
  "geometry_report": {
    "part_count": 1,
    "bounding_box_mm": [58.0, 42.0, 51.0],
    "volume_mm3": 18500.0
  },
  "warnings": []
}
```

OUTPUT:
```markdown
# Micro Servo Extrusion Mount
*Generated: 2026-05-02T00:00:00Z*
*CadQuery 2.x | Units: mm*

---

## Overview
This is a single-piece fixed L-bracket for mounting a micro servo to a 20x20 aluminum extrusion. It has a horizontal base plate, a vertical servo face plate, and two outboard gussets for stiffness. The part has no moving joints.

---

## Part List

| Part | Description | Volume (mm^3) | Bounding Box (mm) | Qty |
|------|-------------|--------------|-------------------|-----|
| micro_servo_extrusion_mount | One-piece FDM servo bracket with base, face plate, gussets, and mounting holes | 18500.0 | 58.0 x 42.0 x 51.0 | 1 |

**Total Assembly Volume:** 18500.0 mm^3
**Assembly Bounding Box:** 58.0 x 42.0 x 51.0 mm

---

## Key Dimensions

| Parameter | Value |
|-----------|-------|
| BASE_L | 58.0 mm |
| PLATE_W | 42.0 mm |
| BASE_T | 5.0 mm |
| SERVO_PLATE_H | 46.0 mm |
| M2_CLEAR_D | 2.4 mm |
| M5_CLEAR_D | 5.5 mm |
| EXTRUSION_SLOT_PATTERN_SPACING | 20.0 mm |

### Derived Values

| Parameter | Value |
|-----------|-------|
| BASE_W | PLATE_W |

---

## Assembly Instructions

1. Place the bracket on the extrusion with the flat base against the 20x20 extrusion face.
2. Align the two M5 base holes with the extrusion slot pattern.
3. Fasten the bracket to the extrusion using two M5 fasteners.
4. Align the micro servo with the four M2 holes on the vertical face plate.
5. Fasten the servo to the face plate with four M2 screws until seated flush.

---

## Manufacturing Recommendations

### Print Orientation (FDM)
Print the part with the horizontal base plate on the build plate. This keeps the base flat and makes the gussets self-supporting.

### Support Structures
No supports should be required if the gusset slopes are kept within printable overhang limits.

### Material Recommendations
Use PETG or ASA for better creep resistance than PLA near screw-loaded holes.

### Critical Tolerances
M2 servo holes: 2.4mm clearance. M5 extrusion holes: 5.5mm clearance. Ream holes after printing if screw fit is tight.

### Post-Processing
Deburr or lightly drill the M2 and M5 holes if needed.

---

## Export Files

| Format | Filename | Size | Contents |
|--------|----------|------|----------|
| STEP | micro_servo_extrusion_mount.step | [size_kb] KB | Single-piece servo extrusion mount |
```

### Example 2 - Static Assembly Report

INPUT:
```json
{
  "component": "two_part_electronics_enclosure",
  "spec": "static base and lid assembly",
  "geometry_report": {
    "part_count": 2,
    "bounding_box_mm": [100.0, 60.0, 35.0],
    "volume_mm3": 42000.0
  },
  "warnings": []
}
```

OUTPUT:
```markdown
# Two Part Electronics Enclosure
*Generated: 2026-05-02T00:00:00Z*
*CadQuery 2.x | Units: mm*

---

## Overview
This is a fixed screw-together electronics enclosure with a separate base and removable lid. The base contains internal PCB standoffs and the lid closes over the base with a shallow internal lip. The assembly has no moving joints.

---

## Part List

| Part | Description | Volume (mm^3) | Bounding Box (mm) | Qty |
|------|-------------|--------------|-------------------|-----|
| base | Open-top thin-wall base shell with standoffs and cable opening | [value] | 100.0 x 60.0 x 30.0 | 1 |
| removable_lid | Screw-on lid with internal lip and M3 countersunk holes | [value] | 100.0 x 60.0 x 9.0 | 1 |

**Total Assembly Volume:** 42000.0 mm^3
**Assembly Bounding Box:** 100.0 x 60.0 x 35.0 mm

---

## Key Dimensions

| Parameter | Value |
|-----------|-------|
| OUTER_L | 100.0 mm |
| OUTER_W | 60.0 mm |
| OVERALL_H | 35.0 mm |
| WALL_T | 2.0 mm |
| LID_TOP_T | 5.0 mm |
| M3_CLEAR_D | 3.4 mm |
| STANDOFF_OD | 8.0 mm |

### Derived Values

| Parameter | Value |
|-----------|-------|
| OVERALL_H | BASE_H + LID_TOP_T |

---

## Assembly Instructions

1. Place the base on a flat surface with the open side facing upward.
2. Insert the PCB into the base and align it with the four internal standoffs.
3. Lower the lid onto the base so the internal lip fits inside the base walls.
4. Align the four lid holes with the base standoffs.
5. Fasten the lid using four M3 screws until the lid is seated evenly.

---

## Manufacturing Recommendations

### Print Orientation (FDM)
Print the base with the flat bottom on the build plate. Print the lid with the top face on the build plate or lip upward depending on surface finish requirements.

### Support Structures
The cable opening should not require supports if printed with the base bottom down. The lid lip generally requires no support.

### Material Recommendations
Use PETG for general electronics use. Use ASA if higher temperature resistance is required.

### Critical Tolerances
Lid lip clearance: 0.4mm total. M3 clearance holes: 3.4mm. Standoff pilot holes may require drilling or tapping depending on screw type.

### Post-Processing
Clean the cable opening and test-fit the lid before installing electronics.

---

## Export Files

| Format | Filename | Size | Contents |
|--------|----------|------|----------|
| STEP | two_part_electronics_enclosure_assembly.step | [size_kb] KB | Base and lid assembly |
```