## Critic - Checkpoint A Few-Shots

### Example 1 - Static Plan Pass

INPUT:
```json
{
  "spec_summary": "static single-piece FDM servo L-bracket, no joints, four M2 holes, two M5 holes, outboard gussets",
  "plan_summary": "plan defines matching-width plates, four M2 through holes on vertical face, two M5 through holes on base, outboard gussets, joint_definitions empty"
}
```

OUTPUT:
```json
{
  "checkpoint": "A",
  "verdict": "pass",
  "overall_fidelity_score": 0.96,
  "dimension_scores": {
    "dof_fidelity": 1.0,
    "part_completeness": 1.0,
    "constraint_coverage": 0.95,
    "scale_plausibility": 0.95,
    "style_alignment": 0.95,
    "coordinate_sanity": 0.9
  },
  "issues": [],
  "routing": "proceed",
  "replan_instructions": null
}
```

### Example 2 - Static Plan Fail Due to Invented Motion

INPUT:
```json
{
  "spec_summary": "static two-part enclosure assembly with no moving joints",
  "plan_summary": "plan includes a hinge joint between base and lid, hinge barrels, and lid rotation range of 0-110 degrees"
}
```

OUTPUT:
```json
{
  "checkpoint": "A",
  "verdict": "fail",
  "overall_fidelity_score": 0.62,
  "dimension_scores": {
    "dof_fidelity": 0.0,
    "part_completeness": 0.75,
    "constraint_coverage": 0.75,
    "scale_plausibility": 0.9,
    "style_alignment": 0.8,
    "coordinate_sanity": 0.75
  },
  "issues": [
    {
      "dimension": "dof_fidelity",
      "severity": "critical",
      "score": 0.0,
      "description": "The plan invents a hinged lid even though the specification requires a static screw-together enclosure with no moving joints.",
      "plan_citation": "joint_definitions includes hinge joint and range_of_motion 0-110 degrees",
      "correction": "Remove all hinge geometry and joint definitions; model the base and lid as separate fixed components assembled in the closed position."
    }
  ],
  "routing": "replan",
  "replan_instructions": "Replan the enclosure as a fixed two-part assembly. Use joint_definitions: [] and place the lid closed on the base with screw holes aligned to internal standoffs. Do not include hinge barrels, hinge pins, or any lid rotation range."
}
```

### Example 3 - Static Plan Fail Due to Interference

INPUT:
```json
{
  "spec_summary": "static NEMA 17 mount with outboard gussets clear of M3 bolt pattern",
  "plan_summary": "gussets are placed at x=+/-15mm, directly through the NEMA 17 M3 holes at x=+/-15.5mm"
}
```

OUTPUT:
```json
{
  "checkpoint": "A",
  "verdict": "fail",
  "overall_fidelity_score": 0.72,
  "dimension_scores": {
    "dof_fidelity": 1.0,
    "part_completeness": 0.85,
    "constraint_coverage": 0.55,
    "scale_plausibility": 0.9,
    "style_alignment": 0.85,
    "coordinate_sanity": 0.55
  },
  "issues": [
    {
      "dimension": "coordinate_sanity",
      "severity": "major",
      "score": 0.55,
      "description": "The side gussets intersect the NEMA 17 M3 clearance holes, making the motor face unusable.",
      "plan_citation": "triangular_side_gussets at x=+/-15mm; NEMA17 holes at x=+/-15.5mm",
      "correction": "Move gussets outboard near the left and right face plate edges, outside the 31mm square bolt pattern and away from the centered shaft clearance hole."
    }
  ],
  "routing": "replan",
  "replan_instructions": "Keep the static L-bracket architecture but widen the face plate and move the triangular gussets outboard. Preserve the centered shaft hole and four M3 holes on the 31mm NEMA 17 pattern without obstruction."
}
```