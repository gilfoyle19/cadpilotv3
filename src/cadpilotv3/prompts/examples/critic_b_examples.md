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
    "assembly_valid": true,
    "child_metadata": [
      {
        "name": "base",
        "bounding_box_mm": [100.0, 60.0, 30.0],
        "center_mm": [0.0, 0.0, 15.0],
        "volume_mm3": 10200.0
      },
      {
        "name": "lid",
        "bounding_box_mm": [100.0, 60.0, 3.0],
        "center_mm": [0.0, 0.0, 31.5],
        "volume_mm3": 18000.0
      }
    ]
  },
  "contract_validation_report": {
    "status": "pass",
    "failure_count": 0,
    "warning_count": 0,
    "compact_evidence": []
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

### Example 3 - Replan Due to Side-by-Side Parts That Should Be Stacked

INPUT:
```json
{
  "spec": "static two-part enclosure with lid closed on top of base",
  "geometry_plan": {
    "artifact_type": "static_assembly",
    "parts": ["open_top_base", "flat_lid"]
  },
  "geometry_report": {
    "part_count": 2,
    "bounding_box_mm": [205.0, 62.0, 30.0],
    "is_manifold": true,
    "has_zero_volume_parts": false,
    "assembly_valid": true,
    "child_metadata": [
      {
        "name": "base",
        "bounding_box_mm": [100.0, 60.0, 30.0],
        "center_mm": [0.0, 0.0, 15.0],
        "volume_mm3": 11000.0
      },
      {
        "name": "lid",
        "bounding_box_mm": [100.0, 60.0, 3.0],
        "center_mm": [105.0, 0.0, 1.5],
        "volume_mm3": 18000.0
      }
    ]
  },
  "contract_validation_report": {
    "status": "fail",
    "failure_count": 2,
    "warning_count": 0,
    "compact_evidence": [
      "fail:lid_centered_on_base:Part centers violate centered assembly contract.",
      "fail:lid_above_base:Second part is not above the first on the declared axis."
    ]
  },
  "observed_issue": "The lid is placed next to the base instead of closed on top."
}
```

OUTPUT:
```json
{
  "checkpoint": "B",
  "verdict": "fail",
  "overall_fidelity_score": 0.62,
  "dimension_scores": {
    "dof_count_verification": 1.0,
    "scale_consistency": 0.45,
    "constraint_satisfaction": 0.35,
    "completeness": 0.8,
    "checkpoint_a_resolution": 0.8,
    "regression_detection": 0.4
  },
  "issues": [
    {
      "dimension": "constraint_satisfaction",
      "severity": "critical",
      "score": 0.35,
      "description": "The lid is modeled as a separate component but is not in the closed assembled position on top of the base.",
      "evidence": "contract_validation compact_evidence includes fail:lid_centered_on_base and fail:lid_above_base; child_metadata shows base center [0,0,15] and lid center [105,0,1.5], so the parts are separated in X instead of stacked in Z.",
      "suggested_routing": "replan",
      "correction": "Replan the assembly transforms so the lid shares the base X/Y center and sits above the base in Z."
    }
  ],
  "routing": "replan",
  "patch_instructions": null,
  "replan_instructions": "Place the lid concentrically over the base in the closed position. Preserve two separate assembly components and align matching holes/standoffs by X/Y center.",
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
  "contract_validation_report": {
    "status": "warn",
    "failure_count": 0,
    "warning_count": 1,
    "compact_evidence": [
      "warn:m3_hole_clearance_bbox:Manifest feature bounding box could not confirm cutter clearance."
    ]
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
