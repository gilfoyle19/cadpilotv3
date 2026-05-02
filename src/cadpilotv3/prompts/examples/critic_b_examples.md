## Critic - Checkpoint B Few-Shots

### Example 1 - Final Static Assembly Pass

INPUT:
```json
{
  "spec": "static two-part electronics enclosure, no moving joints",
  "geometry_report": {
    "part_count": 2,
    "bounding_box_mm": [100.0, 60.0, 35.0],
    "is_manifold": true,
    "has_zero_volume_parts": false,
    "assembly_valid": true
  },
  "checkpoint_a": "pass"
}
```

OUTPUT:
```json
{
  "checkpoint": "B",
  "verdict": "pass",
  "overall_fidelity_score": 0.97,
  "dimension_scores": {
    "dof_count_verification": 1.0,
    "scale_consistency": 1.0,
    "constraint_satisfaction": 0.9,
    "completeness": 1.0,
    "checkpoint_a_resolution": 1.0,
    "regression_detection": 1.0
  },
  "issues": [],
  "routing": "export",
  "patch_instructions": null,
  "replan_instructions": null,
  "user_facing_warnings": []
}
```

### Example 2 - Final Output Replan Due to Interference

INPUT:
```json
{
  "spec": "static motor mount with centered shaft hole and unobstructed M3 pattern",
  "geometry_report": {
    "part_count": 5,
    "bounding_box_mm": [86.0, 72.0, 80.0],
    "is_manifold": true,
    "has_zero_volume_parts": false,
    "assembly_valid": true
  },
  "observed_issue": "triangular gussets intersect the M3 motor mounting holes"
}
```

OUTPUT:
```json
{
  "checkpoint": "B",
  "verdict": "fail",
  "overall_fidelity_score": 0.74,
  "dimension_scores": {
    "dof_count_verification": 1.0,
    "scale_consistency": 0.9,
    "constraint_satisfaction": 0.45,
    "completeness": 0.75,
    "checkpoint_a_resolution": 0.7,
    "regression_detection": 0.7
  },
  "issues": [
    {
      "dimension": "constraint_satisfaction",
      "severity": "major",
      "score": 0.45,
      "description": "The gussets obstruct the NEMA 17 M3 mounting holes, violating the bolt pattern requirement.",
      "evidence": "M3 hole positions are on the 31mm pattern while gusset footprints cross the same x/z region.",
      "suggested_routing": "replan",
      "correction": "Move gussets outboard near the face plate edges and keep all gusset geometry clear of the centered shaft hole and four M3 holes."
    }
  ],
  "routing": "replan",
  "patch_instructions": null,
  "replan_instructions": "Replan the motor mount with wider face plate geometry and outboard gusset offsets. Preserve the static assembly and no-DOF interpretation.",
  "user_facing_warnings": []
}
```