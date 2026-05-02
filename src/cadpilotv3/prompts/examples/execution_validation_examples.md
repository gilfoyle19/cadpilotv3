## Agent 5 - Execution & Validation Few-Shots

### Example 1 - Successful Static Assembly

INPUT:
```json
{
  "script_result": "assembly.save completed successfully",
  "expected_parts": 2,
  "component": "two_part_electronics_enclosure"
}
```

OUTPUT:
```json
{
  "status": "success",
  "error_class": null,
  "error_location": {
    "line": null,
    "function": null,
    "code_line": null
  },
  "error_message": null,
  "error_summary": "The base and lid were generated as separate valid parts and exported as a static STEP assembly.",
  "execution_time_s": 1.42,
  "geometry_valid": true,
  "repair_needed": false,
  "repair_complexity": null,
  "geometry_report": {
    "part_count": 2,
    "bounding_box_mm": [
      100.0,
      60.0,
      35.0
    ],
    "volume_mm3": 42000.0,
    "is_manifold": true,
    "face_count": 126,
    "has_zero_volume_parts": false,
    "assembly_valid": true
  }
}
```

### Example 2 - Assembly Export API Misuse

INPUT:
```text
Traceback: multimethod.DispatchError when calling exporters.export(asm, "assembly.step") on a cq.Assembly.
```

OUTPUT:
```json
{
  "status": "runtime_error",
  "error_class": "api_misuse",
  "error_location": {
    "line": 196,
    "function": "__main__",
    "code_line": "exporters.export(asm, f\"{COMPONENT_NAME}_assembly.step\")"
  },
  "error_message": "multimethod.DispatchError: ('compound: 0 methods found', (<class 'tuple'>, <class 'tuple'>), set())",
  "error_summary": "The assembly export failed because a cq.Assembly was sent through the solid/workplane exporter instead of using the assembly save method.",
  "execution_time_s": 0.37,
  "geometry_valid": false,
  "repair_needed": true,
  "repair_complexity": "patch",
  "geometry_report": null
}
```

### Example 3 - Semantic Silent Geometry Issue

INPUT:
```json
{
  "script_result": "runs and exports",
  "observed_issue": "servo bracket contains only two visible M2 holes and gussets overlap hole pattern"
}
```

OUTPUT:
```json
{
  "status": "success_with_semantic_issue",
  "error_class": "silent_wrong_part_count",
  "error_location": {
    "line": null,
    "function": "make_micro_servo_extrusion_mount",
    "code_line": null
  },
  "error_message": "Expected four M2 servo holes and non-interfering gussets, but visual/metadata review indicates the hole pattern is incomplete or obstructed.",
  "error_summary": "The bracket exported but does not contain the required unobstructed four-hole servo mounting pattern.",
  "execution_time_s": 0.84,
  "geometry_valid": false,
  "repair_needed": true,
  "repair_complexity": "replan",
  "geometry_report": {
    "part_count": 1,
    "bounding_box_mm": [
      58.0,
      42.0,
      51.0
    ],
    "volume_mm3": 18500.0,
    "is_manifold": true,
    "face_count": 88,
    "has_zero_volume_parts": false,
    "assembly_valid": true
  }
}
```