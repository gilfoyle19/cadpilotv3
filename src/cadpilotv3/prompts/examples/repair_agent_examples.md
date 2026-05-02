## Agent 6 - Repair Agent Few-Shots

### Example 1 - Patch Assembly Export

INPUT:
```json
{
  "error_class": "api_misuse",
  "code_line": "exporters.export(asm, f\"{COMPONENT_NAME}_assembly.step\")",
  "repair_attempt_count": 1
}
```

OUTPUT:
```json
{
  "action": "patch",
  "error_class": "api_misuse",
  "root_cause": "The script is treating a multi-part CadQuery assembly like a single solid, so the exporter cannot build a compound from the assembly object.",
  "fix_description": "Replace the solid exporter call with the CadQuery assembly save method so the base and lid remain separate STEP assembly components.",
  "patch_type": "api",
  "affected_function": "__main__",
  "patched_code": "if __name__ == \"__main__\":\n    assembly = build_assembly()\n    assembly.save(f\"{COMPONENT_NAME}_assembly.step\")",
  "confidence": "high",
  "confidence_note": null
}
```

### Example 2 - Replan Hole/Gusset Interference

INPUT:
```json
{
  "error_class": "silent_wrong_part_count",
  "observed_issue": "NEMA 17 M3 holes are blocked by triangular gussets",
  "repair_attempt_count": 1
}
```

OUTPUT:
```json
{
  "action": "replan",
  "error_class": "silent_wrong_part_count",
  "root_cause": "The gussets occupy the same area as the motor mounting pattern, so the motor face cannot accept the NEMA 17 screws even though the script runs.",
  "cannot_patch_reason": "A local code patch cannot safely fix this because the face plate width, gusset offsets, and base hole positions must be coordinated as a layout change.",
  "replan_instructions": "Replan the NEMA 17 mount with a wider motor face plate and move the triangular gussets outboard near the left and right edges. Preserve the centered shaft clearance hole and four M3 clearance holes on the 31mm square NEMA 17 pattern. Place base M5 holes clear of the gusset footprints.",
  "affected_part": "rigid_l_bracket_body",
  "repair_attempt_count": 1
}
```

### Example 3 - Replan Bad Sheet-Metal Prompt

INPUT:
```json
{
  "error_class": "silent_scale_error",
  "observed_issue": "sheet-metal bend area is messy and the adjustment slot is missing",
  "repair_attempt_count": 2
}
```

OUTPUT:
```json
{
  "action": "replan",
  "error_class": "silent_scale_error",
  "root_cause": "The original prompt does not sufficiently constrain the sheet-metal bend representation, so the model becomes a blocky L bracket rather than a manufacturable constant-thickness formed part.",
  "cannot_patch_reason": "The bend, reliefs, and adjustment slot must be planned together from sheet-metal design intent rather than patched after construction.",
  "replan_instructions": "Refine the prompt before regeneration: specify a single-piece formed 90-degree sheet-metal L bracket with constant 3mm thickness, a clean 4mm inside bend radius, two 50mm-wide flanges, two M4 frame holes away from the bend, one horizontal slotted M4 adjustment hole on the sensor flange, and rectangular bend reliefs at the side edges.",
  "affected_part": "sheet_metal_l_bracket_body",
  "repair_attempt_count": 2
}
```