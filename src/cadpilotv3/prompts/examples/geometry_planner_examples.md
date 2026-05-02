### Example 1 - Static Single-Part Geometry Plan

INPUT:
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
  "clarifications_needed": []
}
```

OUTPUT:
```json
{
  "coordinate_convention": {
    "x_direction": "left-right across the bracket width",
    "y_direction": "front-back from the vertical face toward the extrusion mounting flange",
    "z_direction": "upward from the print bed",
    "world_origin": "center of the horizontal base plate on the bottom face",
    "zero_config": "static fixed bracket; no moving configuration"
  },
  "parts": [
    {
      "name": "l_bracket_body",
      "geometric_role": "single fused structural body containing the base, vertical face, and gussets",
      "local_origin": "center of the base bottom face",
      "modeling_strategy": "primitive_csg",
      "strategy_selection": {
        "candidates": [
          {
            "strategy": "primitive_csg",
            "advantage": "boxes and triangular prisms are robust in CadQuery and keep the bracket manufacturable",
            "disadvantage": "less organic than a fully filleted molded bracket"
          },
          {
            "strategy": "single_profile_extrude",
            "advantage": "could create the L shape from one profile",
            "disadvantage": "hole axes and gusset placement are clearer as separate primitives"
          }
        ],
        "winner": "primitive_csg",
        "rationale": "the validated geometry uses simple boxes, triangular gusset prisms, and explicit cylindrical cuts to avoid fragile final fillets"
      },
      "key_features": [
        {
          "feature": "matching_width_plates",
          "description": "horizontal and vertical plates use the same width so the bracket reads as a deliberate L-bracket"
        },
        {
          "feature": "servo_hole_pattern",
          "description": "four M2 through holes cut through the vertical plate on a rectangular servo mounting pattern"
        },
        {
          "feature": "extrusion_hole_pattern",
          "description": "two M5 vertical through holes in the base plate spaced 20mm apart"
        },
        {
          "feature": "outboard_gussets",
          "description": "two triangular ribs are placed near the outer edges, outside all M2 and M5 hole paths"
        }
      ]
    }
  ],
  "assembly_transform_chain": [
    {
      "part": "l_bracket_body",
      "transforms": [
        "base plate centered on origin with bottom at z=0",
        "vertical plate placed at negative y edge of base",
        "gussets mirrored about X=0 and attached between base top and vertical plate front face"
      ],
      "zero_config_position": "static single part with base bottom centered at (0,0,0)"
    }
  ],
  "joint_definitions": [],
  "failure_risks": [
    {
      "risk_name": "hole_gusset_interference",
      "affected": "triangular_side_gussets",
      "description": "gussets can obscure or intersect the M2 servo hole pattern if placed too close to the center",
      "mitigation": "place gussets outboard near the side edges and keep their rise below the upper servo hole row when necessary"
    },
    {
      "risk_name": "fragile_global_chamfer",
      "affected": "l_bracket_body",
      "description": "filleting or chamfering all edges after unions and cuts can fail in CadQuery",
      "mitigation": "avoid broad final fillets or apply only to simple primitives before cuts"
    }
  ],
  "replan_changes": []
}
```

### Example 2 - Static Assembly Geometry Plan

INPUT:
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
  "clarifications_needed": []
}
```

OUTPUT:
```json
{
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
            "strategy": "shell",
            "advantage": "compact representation of thin-wall enclosure",
            "disadvantage": "shell operations can fail or create hard-to-control wall openings"
          },
          {
            "strategy": "primitive_csg",
            "advantage": "bottom, walls, standoffs, and openings are explicit and robust",
            "disadvantage": "slightly more verbose code"
          }
        ],
        "winner": "primitive_csg",
        "rationale": "explicit wall boxes and standoff cylinders are robust and keep all FDM features controllable"
      },
      "key_features": [
        {
          "feature": "flat_bottom",
          "description": "rectangular bottom plate provides the print base"
        },
        {
          "feature": "thin_side_walls",
          "description": "four 2mm walls form an open-top box"
        },
        {
          "feature": "pcb_standoffs",
          "description": "four cylindrical standoffs align with lid screw holes"
        },
        {
          "feature": "cable_opening",
          "description": "one rectangular through opening is cut into a short side wall"
        }
      ]
    },
    {
      "name": "removable_lid",
      "geometric_role": "separate top cover with shallow internal lip and countersunk screw holes",
      "local_origin": "same world origin as the base when assembled closed",
      "modeling_strategy": "primitive_csg",
      "strategy_selection": {
        "candidates": [
          {
            "strategy": "primitive_csg",
            "advantage": "top slab, lip strips, and countersink recesses are clear and reliable",
            "disadvantage": "countersinks are simplified as cylindrical recesses unless cone features are added"
          }
        ],
        "winner": "primitive_csg",
        "rationale": "a real assembly requires a separate lid body, not a union with the base"
      },
      "key_features": [
        {
          "feature": "top_plate",
          "description": "top plate completes the 35mm enclosure height"
        },
        {
          "feature": "internal_lip",
          "description": "four shallow lip strips overlap inside the base walls with clearance"
        },
        {
          "feature": "m3_countersunk_holes",
          "description": "four through holes and top recesses align to the standoffs"
        }
      ]
    }
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
        "place lid directly above base with top plate spanning z=30mm to z=35mm",
        "place internal lip down into the base opening"
      ],
      "zero_config_position": "lid closed on base with screw holes aligned to standoffs"
    }
  ],
  "joint_definitions": [],
  "failure_risks": [
    {
      "risk_name": "assembly_export_misuse",
      "affected": "export",
      "description": "using exporters.export on cq.Assembly can fail in some CadQuery versions",
      "mitigation": "use assembly.save('name.step') for STEP assembly export"
    },
    {
      "risk_name": "base_lid_union_error",
      "affected": "assembly_transform_chain",
      "description": "unioning base and lid destroys the required two-part assembly semantics",
      "mitigation": "keep base and lid as separate Workplane objects added to cq.Assembly"
    }
  ],
  "replan_changes": []
}
```