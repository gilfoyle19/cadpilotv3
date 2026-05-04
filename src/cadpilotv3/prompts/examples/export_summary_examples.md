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
  "export_files": [
    {
      "format": "STEP",
      "filename": "micro_servo_extrusion_mount.step",
      "filepath": "output/micro_servo_extrusion_mount.step",
      "size_kb": 42.0,
      "contents": "Single-piece servo extrusion mount"
    }
  ],
  "warnings": []
}
```

OUTPUT:
```json
{
  "export_files": [
    {
      "format": "STEP",
      "filename": "micro_servo_extrusion_mount.step",
      "filepath": "output/micro_servo_extrusion_mount.step",
      "size_kb": 42.0,
      "contents": "Single-piece servo extrusion mount"
    }
  ],
  "assembly_report_markdown": "# Micro Servo Extrusion Mount\n*Generated: 2026-05-02T00:00:00Z*\n*CadQuery 2.x | Units: mm*\n\n---\n\n## Overview\nThis is a single-piece fixed L-bracket for mounting a micro servo to a 20x20 aluminum extrusion. It has a horizontal base plate, a vertical servo face plate, and two outboard gussets for stiffness. The part has no moving joints.\n\n---\n\n## Part List\n\n| Part | Description | Volume (mm^3) | Bounding Box (mm) | Qty |\n|------|-------------|--------------|-------------------|-----|\n| micro_servo_extrusion_mount | One-piece FDM servo bracket with base, face plate, gussets, and mounting holes | 18500.0 | 58.0 x 42.0 x 51.0 | 1 |\n\n**Total Assembly Volume:** 18500.0 mm^3\n**Assembly Bounding Box:** 58.0 x 42.0 x 51.0 mm\n\n---\n\n## Key Dimensions\n\n| Parameter | Value |\n|-----------|-------|\n| BASE_L | 58.0 mm |\n| PLATE_W | 42.0 mm |\n| BASE_T | 5.0 mm |\n| SERVO_PLATE_H | 46.0 mm |\n| M2_CLEAR_D | 2.4 mm |\n| M5_CLEAR_D | 5.5 mm |\n| EXTRUSION_SLOT_PATTERN_SPACING | 20.0 mm |\n\n### Derived Values\n\n| Parameter | Value |\n|-----------|-------|\n| BASE_W | PLATE_W |\n\n---\n\n## Assembly Instructions\n\n1. Place the bracket on the extrusion with the flat base against the 20x20 extrusion face.\n2. Align the two M5 base holes with the extrusion slot pattern.\n3. Fasten the bracket to the extrusion using two M5 fasteners.\n4. Align the micro servo with the four M2 holes on the vertical face plate.\n5. Fasten the servo to the face plate with four M2 screws until seated flush.\n\n---\n\n## Manufacturing Recommendations\n\n### Print Orientation (FDM)\nPrint the part with the horizontal base plate on the build plate. This keeps the base flat and makes the gussets self-supporting.\n\n### Support Structures\nNo supports should be required if the gusset slopes are kept within printable overhang limits.\n\n### Material Recommendations\nUse PETG or ASA for better creep resistance than PLA near screw-loaded holes.\n\n### Critical Tolerances\nM2 servo holes: 2.4mm clearance. M5 extrusion holes: 5.5mm clearance. Ream holes after printing if screw fit is tight.\n\n### Post-Processing\nDeburr or lightly drill the M2 and M5 holes if needed.\n\n---\n\n## Export Files\n\n| Format | Filename | Size | Contents |\n|--------|----------|------|----------|\n| STEP | micro_servo_extrusion_mount.step | 42.0 KB | Single-piece servo extrusion mount |",
  "user_facing_warnings": []
}
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
  "export_files": [
    {
      "format": "STEP",
      "filename": "two_part_electronics_enclosure_assembly.step",
      "filepath": "output/two_part_electronics_enclosure_assembly.step",
      "size_kb": 88.0,
      "contents": "Base and lid assembly"
    }
  ],
  "warnings": []
}
```

OUTPUT:
```json
{
  "export_files": [
    {
      "format": "STEP",
      "filename": "two_part_electronics_enclosure_assembly.step",
      "filepath": "output/two_part_electronics_enclosure_assembly.step",
      "size_kb": 88.0,
      "contents": "Base and lid assembly"
    }
  ],
  "assembly_report_markdown": "# Two Part Electronics Enclosure\n*Generated: 2026-05-02T00:00:00Z*\n*CadQuery 2.x | Units: mm*\n\n---\n\n## Overview\nThis is a fixed screw-together electronics enclosure with a separate base and removable lid. The base contains internal PCB standoffs and the lid closes over the base with a shallow internal lip. The assembly has no moving joints.\n\n---\n\n## Part List\n\n| Part | Description | Volume (mm^3) | Bounding Box (mm) | Qty |\n|------|-------------|--------------|-------------------|-----|\n| base | Open-top thin-wall base shell with standoffs and cable opening | 42000.0 | 100.0 x 60.0 x 30.0 | 1 |\n| removable_lid | Screw-on lid with internal lip and M3 countersunk holes | 42000.0 | 100.0 x 60.0 x 9.0 | 1 |\n\n**Total Assembly Volume:** 42000.0 mm^3\n**Assembly Bounding Box:** 100.0 x 60.0 x 35.0 mm\n\n---\n\n## Key Dimensions\n\n| Parameter | Value |\n|-----------|-------|\n| OUTER_L | 100.0 mm |\n| OUTER_W | 60.0 mm |\n| OVERALL_H | 35.0 mm |\n| WALL_T | 2.0 mm |\n| LID_TOP_T | 5.0 mm |\n| M3_CLEAR_D | 3.4 mm |\n| STANDOFF_OD | 8.0 mm |\n\n### Derived Values\n\n| Parameter | Value |\n|-----------|-------|\n| OVERALL_H | BASE_H + LID_TOP_T |\n\n---\n\n## Assembly Instructions\n\n1. Place the base on a flat surface with the open side facing upward.\n2. Insert the PCB into the base and align it with the four internal standoffs.\n3. Lower the lid onto the base so the internal lip fits inside the base walls.\n4. Align the four lid holes with the base standoffs.\n5. Fasten the lid using four M3 screws until the lid is seated evenly.\n\n---\n\n## Manufacturing Recommendations\n\n### Print Orientation (FDM)\nPrint the base with the flat bottom on the build plate. Print the lid with the top face on the build plate or lip upward depending on surface finish requirements.\n\n### Support Structures\nThe cable opening should not require supports if printed with the base bottom down. The lid lip generally requires no support.\n\n### Material Recommendations\nUse PETG for general electronics use. Use ASA if higher temperature resistance is required.\n\n### Critical Tolerances\nLid lip clearance: 0.4mm total. M3 clearance holes: 3.4mm. Standoff pilot holes may require drilling or tapping depending on screw type.\n\n### Post-Processing\nClean the cable opening and test-fit the lid before installing electronics.\n\n---\n\n## Export Files\n\n| Format | Filename | Size | Contents |\n|--------|----------|------|----------|\n| STEP | two_part_electronics_enclosure_assembly.step | 88.0 KB | Base and lid assembly |",
  "user_facing_warnings": []
}
```
