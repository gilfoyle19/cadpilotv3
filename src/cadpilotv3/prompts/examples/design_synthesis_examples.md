## Design Synthesis Few-Shots

### Example 1 - CNC Bearing Block Synthesis

INPUT:
```text
Design a single-piece bearing pillow block for a 608 bearing. Use mm units and
export as STEP. The part will be CNC machined from aluminum. Include a
rectangular base with two M6 through holes, a raised central bearing boss, and a
circular bearing seat sized for a press-fit 608 bearing. Avoid internal
undercuts, keep all holes through-drilled from accessible faces, and include
small chamfers on external edges. The design should be a solid structural block,
approximately 80mm long, 35mm wide, and 35mm tall.
```

OUTPUT:
```json
{
  "spec": {
    "component": "bearing_pillow_block_608",
    "component_type": "single_part",
    "dof_count": 0,
    "dof_config": null,
    "joint_types": null,
    "parts": [
      "bearing_block_body"
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
    "explicit_constraints": [
      "bearing seat sized for a press-fit 608 bearing",
      "all holes through-drilled from accessible faces"
    ],
    "researched_dimensions": [],
    "research_sources": [],
    "clarifications_needed": []
  },
  "geometry_plan": {
    "artifact_type": "single_part",
    "coordinate_convention": {
      "x_direction": "left-right along the 80mm base length",
      "y_direction": "front-back along the 35mm base width",
      "z_direction": "vertical height from the base bottom",
      "world_origin": "center of the base bottom face",
      "zero_config": "static single machined part with no moving configuration"
    },
    "parts": [
      {
        "name": "bearing_block_body",
        "geometric_role": "single machined aluminum pillow block with base, raised boss, bearing seat, shaft bore, and mounting holes",
        "local_origin": "center of the base bottom face",
        "modeling_strategy": "primitive_csg",
        "strategy_selection": {
          "candidates": [
            {
              "strategy": "primitive_csg",
              "advantage": "rectangular base, raised boss, bores, and through holes are robust with explicit solids and cutters",
              "disadvantage": "requires careful ordering so the bearing seat and shaft bore remain coaxial"
            },
            {
              "strategy": "sketch_extrude",
              "advantage": "could capture a side profile with fewer unions",
              "disadvantage": "less direct for drilling axes and boss-seat contracts"
            }
          ],
          "winner": "primitive_csg",
          "rationale": "the requested CNC block is prismatic with axis-aligned accessible through cuts"
        },
        "key_features": [
          {
            "feature": "rectangular_base",
            "description": "80mm by 35mm solid base provides mounting footprint and machining datum"
          },
          {
            "feature": "raised_central_boss",
            "description": "central boss carries the bearing seat and shaft clearance bore"
          },
          {
            "feature": "press_fit_bearing_seat",
            "description": "front-accessible circular pocket sized for a 608 bearing press fit"
          },
          {
            "feature": "m6_mounting_holes",
            "description": "two M6 through holes pass vertically through the base"
          },
          {
            "feature": "small_edge_chamfers",
            "description": "small external chamfers remove sharp machined edges without weakening the block"
          }
        ],
        "body_type": "solid"
      }
    ],
    "required_features": [
      "base_envelope",
      "central_bearing_boss",
      "press_fit_608_bearing_seat",
      "shaft_clearance_bore",
      "m6_base_mounting_hole_pattern",
      "external_chamfers"
    ],
    "feature_contracts": [
      {
        "id": "base_envelope",
        "host_part": "bearing_block_body",
        "type": "reference",
        "operation": "add",
        "axis": "Z",
        "center": [0, 0, "BASE_T / 2"],
        "dimensions": {
          "length": "BASE_L",
          "width": "BASE_W",
          "thickness": "BASE_T"
        },
        "count_group": null,
        "required": true,
        "description": "solid rectangular base preserves the requested 80mm by 35mm footprint"
      },
      {
        "id": "central_bearing_boss",
        "host_part": "bearing_block_body",
        "type": "boss",
        "operation": "add",
        "axis": "Y",
        "center": [0, 0, "BASE_T + BOSS_R"],
        "dimensions": {
          "diameter": "BOSS_D",
          "width": "BASE_W",
          "height": "BOSS_R"
        },
        "count_group": null,
        "required": true,
        "description": "raised central material around the 608 bearing seat"
      },
      {
        "id": "press_fit_608_bearing_seat",
        "host_part": "bearing_block_body",
        "type": "counterbore",
        "operation": "cut",
        "axis": "Y",
        "center": [0, 0, "BEARING_CENTER_Z"],
        "dimensions": {
          "diameter": "BEARING_SEAT_D",
          "depth": "BEARING_SEAT_DEPTH"
        },
        "count_group": "bearing_axis",
        "required": true,
        "description": "front-accessible circular press-fit pocket for the 608 bearing"
      },
      {
        "id": "shaft_clearance_bore",
        "host_part": "bearing_block_body",
        "type": "through_hole",
        "operation": "cut",
        "axis": "Y",
        "center": [0, 0, "BEARING_CENTER_Z"],
        "dimensions": {
          "diameter": "SHAFT_CLEARANCE_D",
          "depth": "BASE_W"
        },
        "count_group": "bearing_axis",
        "required": true,
        "description": "through bore remains coaxial with the bearing seat"
      },
      {
        "id": "m6_base_mounting_hole_pattern",
        "host_part": "bearing_block_body",
        "type": "through_hole_pattern",
        "operation": "cut",
        "axis": "Z",
        "center": "two centers mirrored about X=0 on the base top face",
        "dimensions": {
          "count": 2,
          "diameter": "M6_CLEARANCE_D",
          "spacing": "MOUNT_HOLE_SPACING"
        },
        "count_group": "m6_base_mounting_pattern",
        "required": true,
        "description": "two accessible vertical M6 mounting holes pass through the base"
      },
      {
        "id": "external_chamfers",
        "host_part": "bearing_block_body",
        "type": "chamfer",
        "operation": "reference",
        "axis": null,
        "center": "external block edges only",
        "dimensions": {
          "width": "EDGE_CHAMFER_W"
        },
        "count_group": null,
        "required": true,
        "description": "small chamfers apply only to stable external edges"
      }
    ],
    "subassemblies": [],
    "assembly_placement_constraints": [],
    "assembly_contracts": [],
    "alignment_groups": [],
    "forbidden_layouts": [],
    "assembly_transform_chain": [
      {
        "part": "bearing_block_body",
        "transforms": [
          "base bottom centered on world origin at z=0",
          "bearing boss and bearing axis centered at x=0 and y=0"
        ],
        "zero_config_position": "single static body centered on base datum"
      }
    ],
    "joint_definitions": [],
    "interfaces": [],
    "failure_risks": [
      {
        "risk_name": "oversized_chamfer_failure",
        "affected": "external_chamfers",
        "description": "large blanket chamfers can fail after the bearing seat and mounting holes are cut",
        "mitigation": "keep EDGE_CHAMFER_W small and apply only to simple external edges"
      },
      {
        "risk_name": "bearing_seat_wall_breakout",
        "affected": "press_fit_608_bearing_seat",
        "description": "a bearing seat too close to the base top or side faces can leave insufficient material",
        "mitigation": "derive boss diameter and center height from bearing diameter plus CNC wall allowance"
      }
    ]
  },
  "parameters": {
    "parameters": {
      "BASE_L": {
        "value": 80.0,
        "unit": "mm",
        "description": "Overall base length from the explicit prompt dimension.",
        "min": 70.0,
        "max": 95.0,
        "depends_on": [],
        "constraint": "must preserve the approximately 80mm requested length",
        "is_derived": false,
        "derived_from": null
      },
      "BASE_W": {
        "value": 35.0,
        "unit": "mm",
        "description": "Overall base width from the explicit prompt dimension.",
        "min": 30.0,
        "max": 45.0,
        "depends_on": [],
        "constraint": "must preserve the approximately 35mm requested width",
        "is_derived": false,
        "derived_from": null
      },
      "OVERALL_H": {
        "value": 35.0,
        "unit": "mm",
        "description": "Overall block height from the explicit prompt dimension.",
        "min": 28.0,
        "max": 45.0,
        "depends_on": [],
        "constraint": "must preserve the approximately 35mm requested height",
        "is_derived": false,
        "derived_from": null
      },
      "BASE_T": {
        "value": 12.0,
        "unit": "mm",
        "description": "Thickness of the solid base below the raised bearing boss.",
        "min": 8.0,
        "max": 18.0,
        "depends_on": [],
        "constraint": "must leave enough material for M6 through holes and boss support",
        "is_derived": false,
        "derived_from": null
      },
      "BEARING_OD": {
        "value": 22.0,
        "unit": "mm",
        "description": "Nominal 608 bearing outside diameter used for the press-fit seat.",
        "min": 21.8,
        "max": 22.2,
        "depends_on": [],
        "constraint": "standard 608 bearing outside diameter",
        "is_derived": false,
        "derived_from": null
      },
      "BEARING_SEAT_D": {
        "value": 21.95,
        "unit": "mm",
        "description": "Press-fit bearing seat diameter slightly below nominal bearing outside diameter.",
        "min": 21.8,
        "max": 22.0,
        "depends_on": [
          "BEARING_OD",
          "PRESS_FIT_INTERFERENCE"
        ],
        "constraint": "must equal BEARING_OD - PRESS_FIT_INTERFERENCE",
        "is_derived": true,
        "derived_from": "BEARING_OD - PRESS_FIT_INTERFERENCE"
      },
      "PRESS_FIT_INTERFERENCE": {
        "value": 0.05,
        "unit": "mm",
        "description": "Small CNC aluminum press-fit interference for the 608 bearing seat.",
        "min": 0.02,
        "max": 0.08,
        "depends_on": [],
        "constraint": "must remain small enough to avoid impossible assembly",
        "is_derived": false,
        "derived_from": null
      },
      "BEARING_CENTER_Z": {
        "value": 23.0,
        "unit": "mm",
        "description": "Vertical center of the bearing seat above the base bottom.",
        "min": 20.0,
        "max": 26.0,
        "depends_on": [
          "BASE_T",
          "BEARING_OD"
        ],
        "constraint": "must keep bearing seat above the base with sufficient lower wall",
        "is_derived": false,
        "derived_from": null
      },
      "BOSS_D": {
        "value": 32.0,
        "unit": "mm",
        "description": "Raised boss diameter providing material around the 608 bearing seat.",
        "min": 28.0,
        "max": 34.0,
        "depends_on": [
          "BEARING_OD"
        ],
        "constraint": "must exceed BEARING_OD by at least 6mm",
        "is_derived": false,
        "derived_from": null
      },
      "BOSS_R": {
        "value": 16.0,
        "unit": "mm",
        "description": "Raised boss radius derived from the boss diameter.",
        "min": 14.0,
        "max": 17.0,
        "depends_on": [
          "BOSS_D"
        ],
        "constraint": "must equal BOSS_D / 2",
        "is_derived": true,
        "derived_from": "BOSS_D / 2"
      },
      "SHAFT_CLEARANCE_D": {
        "value": 8.2,
        "unit": "mm",
        "description": "Through bore clearance diameter for a typical 608 bearing shaft.",
        "min": 8.0,
        "max": 9.0,
        "depends_on": [],
        "constraint": "must remain smaller than BEARING_SEAT_D",
        "is_derived": false,
        "derived_from": null
      },
      "M6_CLEARANCE_D": {
        "value": 6.6,
        "unit": "mm",
        "description": "Clearance diameter for M6 mounting bolts.",
        "min": 6.4,
        "max": 7.0,
        "depends_on": [],
        "constraint": null,
        "is_derived": false,
        "derived_from": null
      },
      "MOUNT_HOLE_SPACING": {
        "value": 56.0,
        "unit": "mm",
        "description": "Center spacing between the two M6 base mounting holes.",
        "min": 45.0,
        "max": 65.0,
        "depends_on": [
          "BASE_L"
        ],
        "constraint": "must keep both holes safely inside the 80mm base length",
        "is_derived": false,
        "derived_from": null
      },
      "EDGE_CHAMFER_W": {
        "value": 1.0,
        "unit": "mm",
        "description": "Small external edge chamfer width for CNC deburring.",
        "min": 0.3,
        "max": 2.0,
        "depends_on": [],
        "constraint": "must remain smaller than nearby wall thicknesses and hole edge distances",
        "is_derived": false,
        "derived_from": null
      }
    }
  },
  "critic_a_report": {
    "checkpoint": "A",
    "verdict": "pass",
    "overall_fidelity_score": 0.96,
    "dimension_scores": {
      "dof_fidelity": 1.0,
      "part_completeness": 0.95,
      "constraint_coverage": 0.95,
      "scale_plausibility": 0.95,
      "style_alignment": 1.0,
      "coordinate_sanity": 0.95
    },
    "issues": [],
    "routing": "proceed",
    "replan_instructions": null,
    "user_facing_warnings": []
  }
}
```

### Example 2 - Two-Part Electronics Enclosure Synthesis

INPUT:
```text
Create a static two-part FDM-printable electronics enclosure assembly with a
base and a removable screw-on lid. Use mm units and export as STEP. The enclosure
should be about 100mm x 60mm x 35mm overall, with no moving joints. The base
should be an open-top thin-wall box with a flat bottom, 2mm walls, and four
internal cylindrical standoffs for M3 screws. Add a cable opening on one short
side of the base. The lid should sit on top of the base, overlap it with a
shallow internal lip, and include four M3 countersunk through holes aligned with
the base standoffs. Assemble the base and lid in the closed position as separate
components in a CadQuery assembly.
```

OUTPUT:
```json
{
  "spec": {
    "component": "two_part_electronics_enclosure",
    "component_type": "assembly",
    "dof_count": 0,
    "dof_config": null,
    "joint_types": null,
    "parts": [
      "base_shell",
      "removable_lid"
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
    "explicit_constraints": [
      "lid sits on top of the base",
      "lid overlaps base with a shallow internal lip",
      "lid holes aligned with base standoffs",
      "base and lid assembled closed as separate components"
    ],
    "researched_dimensions": [],
    "research_sources": [],
    "clarifications_needed": []
  },
  "geometry_plan": {
    "artifact_type": "assembly",
    "coordinate_convention": {
      "x_direction": "enclosure length",
      "y_direction": "enclosure width",
      "z_direction": "vertical height from the flat bottom",
      "world_origin": "center of the base bottom face",
      "zero_config": "base and lid assembled in the closed screw-together position"
    },
    "parts": [
      {
        "name": "base_shell",
        "geometric_role": "open-top thin-wall box with flat bottom, side walls, standoffs, and cable opening",
        "local_origin": "center of the base bottom face",
        "modeling_strategy": "primitive_csg",
        "strategy_selection": {
          "candidates": [
            {
              "strategy": "primitive_csg",
              "advantage": "bottom, walls, standoffs, and cable opening are explicit and robust",
              "disadvantage": "requires more feature contracts than a shell operation"
            },
            {
              "strategy": "shell",
              "advantage": "compact way to represent thin walls",
              "disadvantage": "shelling can fail around openings and standoff joins"
            }
          ],
          "winner": "primitive_csg",
          "rationale": "explicit wall boxes and standoff cylinders are robust for FDM enclosure geometry"
        },
        "key_features": [
          {
            "feature": "flat_bottom",
            "description": "rectangular bottom plate creates the print base"
          },
          {
            "feature": "thin_side_walls",
            "description": "four 2mm walls create the open-top box"
          },
          {
            "feature": "standoff_pattern",
            "description": "four M3 standoffs align with lid screw holes"
          },
          {
            "feature": "cable_opening",
            "description": "rectangular opening on one short side wall"
          }
        ],
        "body_type": "solid"
      },
      {
        "name": "removable_lid",
        "geometric_role": "separate top cover with shallow internal lip and countersunk screw holes",
        "local_origin": "center of the lid top plate in the closed assembly position",
        "modeling_strategy": "primitive_csg",
        "strategy_selection": {
          "candidates": [
            {
              "strategy": "primitive_csg",
              "advantage": "top slab, lip strips, through holes, and recesses are stable",
              "disadvantage": "countersinks may be approximated unless conical cutters are added"
            }
          ],
          "winner": "primitive_csg",
          "rationale": "the lid is a separate prismatic body with explicit mating features"
        },
        "key_features": [
          {
            "feature": "top_plate",
            "description": "top slab closes the enclosure at the requested height"
          },
          {
            "feature": "internal_alignment_lip",
            "description": "lip descends inside the base opening with FDM clearance"
          },
          {
            "feature": "m3_countersunk_holes",
            "description": "four through holes and top recesses align to base standoffs"
          }
        ],
        "body_type": "solid"
      }
    ],
    "required_features": [
      "base_flat_bottom",
      "base_side_wall_set",
      "base_pcb_standoff_pattern",
      "base_cable_opening",
      "lid_top_plate",
      "lid_alignment_lip",
      "lid_m3_countersunk_hole_pattern"
    ],
    "feature_contracts": [
      {
        "id": "base_flat_bottom",
        "host_part": "base_shell",
        "type": "plate",
        "operation": "add",
        "axis": "Z",
        "center": [0, 0, "BASE_BOTTOM_T / 2"],
        "dimensions": {
          "length": "OUTER_L",
          "width": "OUTER_W",
          "thickness": "BASE_BOTTOM_T"
        },
        "count_group": null,
        "required": true,
        "description": "flat rectangular bottom plate supports FDM printing"
      },
      {
        "id": "base_side_wall_set",
        "host_part": "base_shell",
        "type": "wall_set",
        "operation": "add",
        "axis": "Z",
        "center": "four walls around the base perimeter",
        "dimensions": {
          "count": 4,
          "wall_thickness": "WALL_T",
          "height": "BASE_WALL_H"
        },
        "count_group": "base_walls",
        "required": true,
        "description": "four side walls create the open-top base shell"
      },
      {
        "id": "base_pcb_standoff_pattern",
        "host_part": "base_shell",
        "type": "standoff_pattern",
        "operation": "add",
        "axis": "Z",
        "center": "four symmetric centers inset from enclosure corners",
        "dimensions": {
          "count": 4,
          "diameter": "STANDOFF_OD",
          "height": "STANDOFF_H",
          "bore_diameter": "M3_PILOT_D"
        },
        "count_group": "m3_lid_fastener_pattern",
        "required": true,
        "description": "four standoffs support screws and align with the lid holes"
      },
      {
        "id": "base_cable_opening",
        "host_part": "base_shell",
        "type": "cutout",
        "operation": "cut",
        "axis": "Y",
        "center": [0, "-OUTER_W / 2", "CABLE_OPENING_CENTER_Z"],
        "dimensions": {
          "width": "CABLE_OPENING_W",
          "height": "CABLE_OPENING_H"
        },
        "count_group": null,
        "required": true,
        "description": "rectangular cable opening cuts through one short side wall"
      },
      {
        "id": "lid_top_plate",
        "host_part": "removable_lid",
        "type": "plate",
        "operation": "add",
        "axis": "Z",
        "center": [0, 0, "OVERALL_H - LID_TOP_T / 2"],
        "dimensions": {
          "length": "OUTER_L",
          "width": "OUTER_W",
          "thickness": "LID_TOP_T"
        },
        "count_group": null,
        "required": true,
        "description": "separate top plate closes the enclosure at the requested height"
      },
      {
        "id": "lid_alignment_lip",
        "host_part": "removable_lid",
        "type": "lip",
        "operation": "add",
        "axis": "Z",
        "center": "four lip strips descending inside the base opening",
        "dimensions": {
          "count": 4,
          "wall_thickness": "LIP_T",
          "depth": "LIP_DEPTH",
          "clearance": "LIP_CLEARANCE"
        },
        "count_group": "lid_lip_set",
        "required": true,
        "description": "internal lip nests inside the base walls with clearance"
      },
      {
        "id": "lid_m3_countersunk_hole_pattern",
        "host_part": "removable_lid",
        "type": "countersunk_hole_pattern",
        "operation": "cut",
        "axis": "Z",
        "center": "four centers matching the base standoff pattern",
        "dimensions": {
          "count": 4,
          "through_diameter": "M3_CLEARANCE_D",
          "countersink_diameter": "M3_HEAD_D"
        },
        "count_group": "m3_lid_fastener_pattern",
        "required": true,
        "description": "four lid holes and recesses align with the base standoffs"
      }
    ],
    "subassemblies": [],
    "assembly_axes": {
      "x_axis": "enclosure length",
      "y_axis": "enclosure width",
      "z_axis": "lid/base stacking and screw axis",
      "primary_separation_axis": "Z",
      "description": "base sits below removable lid; standoffs and screws run vertically along Z"
    },
    "part_frames": [
      {
        "part": "base_shell",
        "local_origin": "center of base bottom face",
        "world_center": "[0, 0, BASE_TOTAL_H / 2]",
        "approximate_bounding_box_mm": [100, 60, 30],
        "functional_faces": [
          {
            "name": "top_lid_seat",
            "normal_axis": "+Z",
            "role": "supports the lid underside in the closed state",
            "mates_with": "removable_lid.underside"
          }
        ]
      },
      {
        "part": "removable_lid",
        "local_origin": "center of lid top plate",
        "world_center": "[0, 0, OVERALL_H - LID_TOP_T / 2]",
        "approximate_bounding_box_mm": [100, 60, 5],
        "functional_faces": [
          {
            "name": "underside",
            "normal_axis": "-Z",
            "role": "sits on top of the base with lip extending downward",
            "mates_with": "base_shell.top_lid_seat"
          }
        ]
      }
    ],
    "assembly_placement_constraints": [
      {
        "name": "lid_centered_over_base",
        "constraint_type": "centered",
        "parts": ["base_shell", "removable_lid"],
        "description": "base and lid share X/Y centerlines in the closed state"
      },
      {
        "name": "standoffs_align_to_lid_holes",
        "constraint_type": "coaxial",
        "parts": ["base_shell", "removable_lid"],
        "description": "lid screw holes and base standoffs share vertical Z axes"
      }
    ],
    "assembly_contracts": [
      {
        "id": "lid_centered_xy",
        "type": "centered",
        "parts": ["base_shell", "removable_lid"],
        "axes": ["X", "Y"],
        "feature_refs": ["base_flat_bottom", "lid_top_plate"],
        "target": "base and lid centers share X=0 and Y=0",
        "tolerance_mm": 0.25,
        "description": "lid remains centered over the base rather than placed beside it"
      },
      {
        "id": "lid_closed_above_base",
        "type": "above",
        "parts": ["base_shell", "removable_lid"],
        "axes": ["Z"],
        "feature_refs": ["base_side_wall_set", "lid_top_plate", "lid_alignment_lip"],
        "target": "lid top plate spans the top of the enclosure with lip descending into base",
        "tolerance_mm": 0.25,
        "description": "lid sits above the base in the closed position"
      },
      {
        "id": "lid_lip_inside_base_clearance",
        "type": "inside_clearance",
        "parts": ["base_shell", "removable_lid"],
        "axes": ["X", "Y", "Z"],
        "feature_refs": ["base_side_wall_set", "lid_alignment_lip"],
        "target": "lip outside dimensions equal base opening minus 2 * LIP_CLEARANCE",
        "tolerance_mm": 0.25,
        "description": "alignment lip nests inside the base walls without intersection"
      },
      {
        "id": "lid_holes_coaxial_with_standoffs",
        "type": "coaxial",
        "parts": ["base_shell", "removable_lid"],
        "axes": ["Z"],
        "feature_refs": ["base_pcb_standoff_pattern", "lid_m3_countersunk_hole_pattern"],
        "target": "four matching fastener centers share vertical Z axes",
        "tolerance_mm": 0.25,
        "description": "each lid screw hole aligns to its corresponding base standoff"
      }
    ],
    "alignment_groups": [
      {
        "name": "m3_lid_fastener_pattern",
        "axis": "Z",
        "center_reference": "four symmetric centers inset from enclosure corners",
        "members": [
          "base_pcb_standoff_pattern",
          "lid_m3_countersunk_hole_pattern"
        ],
        "tolerance_mm": 0.25,
        "description": "all lid fastener holes remain coaxial with their base standoffs"
      }
    ],
    "forbidden_layouts": [
      "do not place lid beside the base along X or Y",
      "do not union base and lid into a single body",
      "do not omit the internal lip or standoff-to-hole alignment"
    ],
    "assembly_transform_chain": [
      {
        "part": "base_shell",
        "transforms": [
          "place base bottom on z=0 centered at world origin"
        ],
        "zero_config_position": "base centered at origin"
      },
      {
        "part": "removable_lid",
        "transforms": [
          "place lid directly above base with top plate spanning the final enclosure height",
          "place internal lip down into the base opening"
        ],
        "zero_config_position": "lid closed on base with screw holes aligned to standoffs"
      }
    ],
    "joint_definitions": [],
    "interfaces": [
      {
        "name": "lid_base_overlap",
        "interface_type": "nested_lip",
        "owner": "removable_lid",
        "target": "base_shell",
        "description": "lid lip nests inside the base opening with clearance"
      }
    ],
    "failure_risks": [
      {
        "risk_name": "assembly_export_misuse",
        "affected": "export",
        "description": "using a single fused solid would destroy the requested two-part assembly semantics",
        "mitigation": "keep base_shell and removable_lid as separate Workplane objects in a CadQuery assembly"
      },
      {
        "risk_name": "lip_wall_interference",
        "affected": "lid_alignment_lip",
        "description": "a lip modeled at the same size as the base opening can intersect the base walls",
        "mitigation": "derive lip outside dimensions from inner opening minus 2 * LIP_CLEARANCE"
      }
    ]
  },
  "parameters": {
    "parameters": {
      "OUTER_L": {
        "value": 100.0,
        "unit": "mm",
        "description": "Overall enclosure length from the explicit 100mm request.",
        "min": 80.0,
        "max": 140.0,
        "depends_on": [],
        "constraint": "must preserve the requested 100mm overall length",
        "is_derived": false,
        "derived_from": null
      },
      "OUTER_W": {
        "value": 60.0,
        "unit": "mm",
        "description": "Overall enclosure width from the explicit 60mm request.",
        "min": 45.0,
        "max": 90.0,
        "depends_on": [],
        "constraint": "must preserve the requested 60mm overall width",
        "is_derived": false,
        "derived_from": null
      },
      "OVERALL_H": {
        "value": 35.0,
        "unit": "mm",
        "description": "Overall assembled enclosure height from the explicit 35mm request.",
        "min": 28.0,
        "max": 60.0,
        "depends_on": [
          "BASE_WALL_H",
          "LID_TOP_T"
        ],
        "constraint": "must equal BASE_WALL_H + LID_TOP_T",
        "is_derived": true,
        "derived_from": "BASE_WALL_H + LID_TOP_T"
      },
      "BASE_WALL_H": {
        "value": 30.0,
        "unit": "mm",
        "description": "Height of the open-top base walls below the lid.",
        "min": 20.0,
        "max": 50.0,
        "depends_on": [],
        "constraint": "must leave room for lid top thickness to reach overall height",
        "is_derived": false,
        "derived_from": null
      },
      "BASE_BOTTOM_T": {
        "value": 3.0,
        "unit": "mm",
        "description": "Flat FDM bottom thickness of the base shell.",
        "min": 2.0,
        "max": 6.0,
        "depends_on": [],
        "constraint": "must satisfy flat_base_required and min_wall_2mm",
        "is_derived": false,
        "derived_from": null
      },
      "LID_TOP_T": {
        "value": 5.0,
        "unit": "mm",
        "description": "Thickness of the removable lid top plate.",
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
        "description": "Nominal FDM wall thickness from the explicit 2mm request.",
        "min": 1.8,
        "max": 4.0,
        "depends_on": [],
        "constraint": "must satisfy min_wall_2mm unless explicitly changed",
        "is_derived": false,
        "derived_from": null
      },
      "INNER_L": {
        "value": 96.0,
        "unit": "mm",
        "description": "Internal base opening length derived from outer length and wall thickness.",
        "min": 70.0,
        "max": 132.0,
        "depends_on": [
          "OUTER_L",
          "WALL_T"
        ],
        "constraint": "must equal OUTER_L - 2 * WALL_T",
        "is_derived": true,
        "derived_from": "OUTER_L - 2 * WALL_T"
      },
      "INNER_W": {
        "value": 56.0,
        "unit": "mm",
        "description": "Internal base opening width derived from outer width and wall thickness.",
        "min": 35.0,
        "max": 82.0,
        "depends_on": [
          "OUTER_W",
          "WALL_T"
        ],
        "constraint": "must equal OUTER_W - 2 * WALL_T",
        "is_derived": true,
        "derived_from": "OUTER_W - 2 * WALL_T"
      },
      "STANDOFF_OD": {
        "value": 8.0,
        "unit": "mm",
        "description": "Outside diameter of internal M3 screw standoffs.",
        "min": 6.0,
        "max": 12.0,
        "depends_on": [],
        "constraint": "must leave material around M3 pilot holes",
        "is_derived": false,
        "derived_from": null
      },
      "M3_PILOT_D": {
        "value": 2.7,
        "unit": "mm",
        "description": "Pilot hole diameter in base standoffs for M3 screws.",
        "min": 2.4,
        "max": 3.0,
        "depends_on": [],
        "constraint": "must remain smaller than STANDOFF_OD",
        "is_derived": false,
        "derived_from": null
      },
      "M3_CLEARANCE_D": {
        "value": 3.4,
        "unit": "mm",
        "description": "Clearance diameter for M3 lid through holes.",
        "min": 3.2,
        "max": 3.8,
        "depends_on": [],
        "constraint": null,
        "is_derived": false,
        "derived_from": null
      },
      "M3_HEAD_D": {
        "value": 6.2,
        "unit": "mm",
        "description": "Simplified countersink or head recess diameter for M3 screws.",
        "min": 5.5,
        "max": 7.0,
        "depends_on": [],
        "constraint": "must fit within lid material near each hole",
        "is_derived": false,
        "derived_from": null
      },
      "FASTENER_X_EDGE_INSET": {
        "value": 12.0,
        "unit": "mm",
        "description": "Inset of standoff and lid screw centers from the left and right enclosure edges.",
        "min": 8.0,
        "max": 20.0,
        "depends_on": [
          "WALL_T",
          "STANDOFF_OD"
        ],
        "constraint": "must keep standoffs inside the base walls",
        "is_derived": false,
        "derived_from": null
      },
      "FASTENER_Y_EDGE_INSET": {
        "value": 10.0,
        "unit": "mm",
        "description": "Inset of standoff and lid screw centers from the front and rear enclosure edges.",
        "min": 8.0,
        "max": 18.0,
        "depends_on": [
          "WALL_T",
          "STANDOFF_OD"
        ],
        "constraint": "must keep standoffs inside the base walls",
        "is_derived": false,
        "derived_from": null
      },
      "SCREW_X_OFFSET": {
        "value": 38.0,
        "unit": "mm",
        "description": "Center-origin X coordinate magnitude for the symmetric standoff and lid hole pattern.",
        "min": 25.0,
        "max": 45.0,
        "depends_on": [
          "OUTER_L",
          "FASTENER_X_EDGE_INSET"
        ],
        "constraint": "must equal OUTER_L / 2 - FASTENER_X_EDGE_INSET",
        "is_derived": true,
        "derived_from": "OUTER_L / 2 - FASTENER_X_EDGE_INSET"
      },
      "SCREW_Y_OFFSET": {
        "value": 20.0,
        "unit": "mm",
        "description": "Center-origin Y coordinate magnitude for the symmetric standoff and lid hole pattern.",
        "min": 12.0,
        "max": 28.0,
        "depends_on": [
          "OUTER_W",
          "FASTENER_Y_EDGE_INSET"
        ],
        "constraint": "must equal OUTER_W / 2 - FASTENER_Y_EDGE_INSET",
        "is_derived": true,
        "derived_from": "OUTER_W / 2 - FASTENER_Y_EDGE_INSET"
      },
      "LIP_CLEARANCE": {
        "value": 0.4,
        "unit": "mm",
        "description": "FDM clearance between the lid lip and base inner walls.",
        "min": 0.2,
        "max": 0.8,
        "depends_on": [],
        "constraint": "must allow the removable lid to fit without force",
        "is_derived": false,
        "derived_from": null
      },
      "LIP_OUTER_L": {
        "value": 95.2,
        "unit": "mm",
        "description": "Outer length of the lid alignment lip derived from the base opening and clearance.",
        "min": 68.0,
        "max": 130.0,
        "depends_on": [
          "INNER_L",
          "LIP_CLEARANCE"
        ],
        "constraint": "must equal INNER_L - 2 * LIP_CLEARANCE",
        "is_derived": true,
        "derived_from": "INNER_L - 2 * LIP_CLEARANCE"
      },
      "LIP_OUTER_W": {
        "value": 55.2,
        "unit": "mm",
        "description": "Outer width of the lid alignment lip derived from the base opening and clearance.",
        "min": 33.0,
        "max": 80.0,
        "depends_on": [
          "INNER_W",
          "LIP_CLEARANCE"
        ],
        "constraint": "must equal INNER_W - 2 * LIP_CLEARANCE",
        "is_derived": true,
        "derived_from": "INNER_W - 2 * LIP_CLEARANCE"
      },
      "LIP_T": {
        "value": 2.0,
        "unit": "mm",
        "description": "Thickness of the internal lid lip strips.",
        "min": 1.6,
        "max": 3.0,
        "depends_on": [],
        "constraint": "must remain printable and fit inside the base walls",
        "is_derived": false,
        "derived_from": null
      },
      "LIP_DEPTH": {
        "value": 4.0,
        "unit": "mm",
        "description": "Vertical depth that the lid lip descends into the base.",
        "min": 2.0,
        "max": 8.0,
        "depends_on": [],
        "constraint": "must overlap base enough for alignment without hitting internal components",
        "is_derived": false,
        "derived_from": null
      },
      "CABLE_OPENING_W": {
        "value": 16.0,
        "unit": "mm",
        "description": "Width of the cable opening on one short side.",
        "min": 8.0,
        "max": 25.0,
        "depends_on": [],
        "constraint": "must fit through one short side wall",
        "is_derived": false,
        "derived_from": null
      },
      "CABLE_OPENING_H": {
        "value": 8.0,
        "unit": "mm",
        "description": "Height of the cable opening on one short side.",
        "min": 4.0,
        "max": 14.0,
        "depends_on": [
          "BASE_WALL_H"
        ],
        "constraint": "must remain below the lid seat and above the bottom plate",
        "is_derived": false,
        "derived_from": null
      },
      "CABLE_OPENING_CENTER_Z": {
        "value": 10.0,
        "unit": "mm",
        "description": "Vertical center of the side cable opening above the base bottom.",
        "min": 6.0,
        "max": 20.0,
        "depends_on": [
          "BASE_BOTTOM_T",
          "CABLE_OPENING_H"
        ],
        "constraint": "must keep the cable opening clear of the bottom and top wall edges",
        "is_derived": false,
        "derived_from": null
      }
    }
  },
  "critic_a_report": {
    "checkpoint": "A",
    "verdict": "pass",
    "overall_fidelity_score": 0.95,
    "dimension_scores": {
      "dof_fidelity": 1.0,
      "part_completeness": 0.95,
      "constraint_coverage": 0.95,
      "scale_plausibility": 0.95,
      "style_alignment": 0.95,
      "coordinate_sanity": 0.95
    },
    "issues": [],
    "routing": "proceed",
    "replan_instructions": null,
    "user_facing_warnings": []
  }
}
```
