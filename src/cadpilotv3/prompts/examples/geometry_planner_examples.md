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

### Example 3 - Static Camera Mount Face-Axis Assembly Plan

INPUT:
```json
{
  "component": "machine_vision_camera_mount",
  "component_type": "assembly",
  "parts": [
    "rear_mounting_plate",
    "front_camera_plate",
    "left_spacer_post",
    "right_spacer_post",
    "left_m4_screw",
    "right_m4_screw"
  ],
  "units": "mm",
  "manufacturing_process": "FDM",
  "constraints": [
    "exactly_six_separate_fixed_components",
    "front_plate_parallel_to_rear_plate",
    "spacers_between_plates",
    "m4_screws_coaxial_with_spacers"
  ]
}
```

OUTPUT:
```json
{
  "artifact_type": "assembly",
  "coordinate_convention": {
    "x_direction": "left-right across the plate width",
    "y_direction": "rear-to-front separation axis normal to both plate faces",
    "z_direction": "vertical plate height",
    "world_origin": "center of the rear mounting plate mid-plane",
    "zero_config": "static assembled camera mount with front plate parallel to rear plate"
  },
  "parts": [
    {
      "name": "rear_mounting_plate",
      "geometric_role": "larger flat frame-side plate carrying M6 frame holes and two M4 spacer axes",
      "local_origin": "center of rear plate mid-plane",
      "modeling_strategy": "primitive_csg",
      "strategy_selection": {
        "candidates": [
          {
            "strategy": "primitive_csg",
            "advantage": "flat box plate and explicit cylindrical through-cuts are robust",
            "disadvantage": "requires careful axis naming for face-normal holes"
          }
        ],
        "winner": "primitive_csg",
        "rationale": "simple plate with through holes should be modeled from a box and explicit cutters"
      },
      "key_features": [
        {
          "feature": "four_m6_frame_holes",
          "description": "four M6 clearance holes near the corners pass normal to the rear plate"
        },
        {
          "feature": "two_m4_spacer_holes",
          "description": "two centered M4 clearance holes share the spacer and screw axes"
        }
      ]
    },
    {
      "name": "front_camera_plate",
      "geometric_role": "smaller parallel camera plate with camera M3 pattern and matching M4 spacer holes",
      "local_origin": "center of front plate mid-plane",
      "modeling_strategy": "primitive_csg",
      "strategy_selection": {
        "candidates": [
          {
            "strategy": "primitive_csg",
            "advantage": "rectangular plate and hole arrays are simple and stable",
            "disadvantage": "visual quality depends on obeying the assembly transform contract"
          }
        ],
        "winner": "primitive_csg",
        "rationale": "the front plate is a flat prismatic part with explicit through-holes"
      },
      "key_features": [
        {
          "feature": "four_m3_camera_holes",
          "description": "four M3 clearance holes on a rectangular industrial camera pattern"
        },
        {
          "feature": "two_m4_spacer_holes",
          "description": "two M4 clearance holes coaxial with the rear plate holes, spacers, and screws"
        }
      ]
    },
    {
      "name": "left_spacer_post",
      "geometric_role": "left cylindrical spacer keeping plates parallel at the required separation",
      "local_origin": "center of spacer cylinder",
      "modeling_strategy": "revolve",
      "strategy_selection": {
        "candidates": [
          {
            "strategy": "revolve",
            "advantage": "axisymmetric cylinder is exact and simple",
            "disadvantage": "must be placed on the declared Y axis"
          }
        ],
        "winner": "revolve",
        "rationale": "a spacer post is a simple cylinder aligned along the plate-normal axis"
      },
      "key_features": [
        {
          "feature": "m4_clearance_bore",
          "description": "central bore coaxial with the left M4 screw representation"
        }
      ]
    },
    {
      "name": "right_spacer_post",
      "geometric_role": "right cylindrical spacer keeping plates parallel at the required separation",
      "local_origin": "center of spacer cylinder",
      "modeling_strategy": "revolve",
      "strategy_selection": {
        "candidates": [
          {
            "strategy": "revolve",
            "advantage": "axisymmetric cylinder is exact and simple",
            "disadvantage": "must mirror the left spacer on the declared Y axis"
          }
        ],
        "winner": "revolve",
        "rationale": "identical spacer body mirrored across X=0"
      },
      "key_features": [
        {
          "feature": "m4_clearance_bore",
          "description": "central bore coaxial with the right M4 screw representation"
        }
      ]
    },
    {
      "name": "left_m4_screw",
      "geometric_role": "simple non-threaded screw representation passing through the left coaxial spacer stack",
      "local_origin": "center of screw shaft",
      "modeling_strategy": "primitive_csg",
      "strategy_selection": {
        "candidates": [
          {
            "strategy": "primitive_csg",
            "advantage": "shaft cylinder plus simple head cylinder is robust",
            "disadvantage": "not a real threaded fastener"
          }
        ],
        "winner": "primitive_csg",
        "rationale": "prompt asks for simple screw representation with no threads"
      },
      "key_features": [
        {
          "feature": "plain_cylindrical_shaft",
          "description": "shaft axis is coaxial with the left spacer and M4 holes"
        }
      ]
    },
    {
      "name": "right_m4_screw",
      "geometric_role": "simple non-threaded screw representation passing through the right coaxial spacer stack",
      "local_origin": "center of screw shaft",
      "modeling_strategy": "primitive_csg",
      "strategy_selection": {
        "candidates": [
          {
            "strategy": "primitive_csg",
            "advantage": "shaft cylinder plus simple head cylinder is robust",
            "disadvantage": "not a real threaded fastener"
          }
        ],
        "winner": "primitive_csg",
        "rationale": "prompt asks for simple screw representation with no threads"
      },
      "key_features": [
        {
          "feature": "plain_cylindrical_shaft",
          "description": "shaft axis is coaxial with the right spacer and M4 holes"
        }
      ]
    }
  ],
  "required_features": [
    "rear_plate_m6_hole_pattern",
    "rear_left_m4_spacer_hole",
    "rear_right_m4_spacer_hole",
    "front_camera_m3_hole_pattern",
    "front_left_m4_spacer_hole",
    "front_right_m4_spacer_hole",
    "left_spacer_bore",
    "right_spacer_bore",
    "left_screw_shaft",
    "right_screw_shaft"
  ],
  "feature_contracts": [
    {
      "id": "rear_plate_m6_hole_pattern",
      "host_part": "rear_mounting_plate",
      "type": "through_hole_pattern",
      "operation": "cut",
      "axis": "Y",
      "center": "four corner centers on rear mounting plate XZ face",
      "dimensions": {"count": 4, "diameter": "M6_CLEARANCE_D"},
      "count_group": "rear_plate_m6_frame_pattern",
      "required": true,
      "description": "four M6 clearance holes pass normal to the rear plate near its corners"
    },
    {
      "id": "rear_left_m4_spacer_hole",
      "host_part": "rear_mounting_plate",
      "type": "through_hole",
      "operation": "cut",
      "axis": "Y",
      "center": ["-SPACER_X_OFFSET", 0, 0],
      "dimensions": {"diameter": "M4_CLEARANCE_D", "depth": "REAR_PLATE_T"},
      "count_group": "left_m4_spacer_stack",
      "required": true,
      "description": "rear plate hole sharing the left spacer and screw axis"
    },
    {
      "id": "rear_right_m4_spacer_hole",
      "host_part": "rear_mounting_plate",
      "type": "through_hole",
      "operation": "cut",
      "axis": "Y",
      "center": ["SPACER_X_OFFSET", 0, 0],
      "dimensions": {"diameter": "M4_CLEARANCE_D", "depth": "REAR_PLATE_T"},
      "count_group": "right_m4_spacer_stack",
      "required": true,
      "description": "rear plate hole sharing the right spacer and screw axis"
    },
    {
      "id": "front_camera_m3_hole_pattern",
      "host_part": "front_camera_plate",
      "type": "through_hole_pattern",
      "operation": "cut",
      "axis": "Y",
      "center": "four camera pattern centers on front plate XZ face",
      "dimensions": {"count": 4, "diameter": "M3_CLEARANCE_D"},
      "count_group": "front_camera_m3_pattern",
      "required": true,
      "description": "four M3 camera mounting holes pass normal to the front plate"
    },
    {
      "id": "front_left_m4_spacer_hole",
      "host_part": "front_camera_plate",
      "type": "through_hole",
      "operation": "cut",
      "axis": "Y",
      "center": ["-SPACER_X_OFFSET", "FRONT_PLATE_CENTER_Y", 0],
      "dimensions": {"diameter": "M4_CLEARANCE_D", "depth": "FRONT_PLATE_T"},
      "count_group": "left_m4_spacer_stack",
      "required": true,
      "description": "front plate hole sharing the left spacer and screw axis"
    },
    {
      "id": "front_right_m4_spacer_hole",
      "host_part": "front_camera_plate",
      "type": "through_hole",
      "operation": "cut",
      "axis": "Y",
      "center": ["SPACER_X_OFFSET", "FRONT_PLATE_CENTER_Y", 0],
      "dimensions": {"diameter": "M4_CLEARANCE_D", "depth": "FRONT_PLATE_T"},
      "count_group": "right_m4_spacer_stack",
      "required": true,
      "description": "front plate hole sharing the right spacer and screw axis"
    },
    {
      "id": "left_spacer_bore",
      "host_part": "left_spacer_post",
      "type": "through_hole",
      "operation": "cut",
      "axis": "Y",
      "center": ["-SPACER_X_OFFSET", "SPACER_CENTER_Y", 0],
      "dimensions": {"diameter": "M4_CLEARANCE_D", "depth": "SPACER_LENGTH"},
      "count_group": "left_m4_spacer_stack",
      "required": true,
      "description": "central bore through the left spacer"
    },
    {
      "id": "right_spacer_bore",
      "host_part": "right_spacer_post",
      "type": "through_hole",
      "operation": "cut",
      "axis": "Y",
      "center": ["SPACER_X_OFFSET", "SPACER_CENTER_Y", 0],
      "dimensions": {"diameter": "M4_CLEARANCE_D", "depth": "SPACER_LENGTH"},
      "count_group": "right_m4_spacer_stack",
      "required": true,
      "description": "central bore through the right spacer"
    },
    {
      "id": "left_screw_shaft",
      "host_part": "left_m4_screw",
      "type": "fastener",
      "operation": "add",
      "axis": "Y",
      "center": ["-SPACER_X_OFFSET", "SPACER_CENTER_Y", 0],
      "dimensions": {"diameter": "M4_SHAFT_D", "length": "SCREW_LENGTH"},
      "count_group": "left_m4_spacer_stack",
      "required": true,
      "description": "plain screw shaft running through the left coaxial stack"
    },
    {
      "id": "right_screw_shaft",
      "host_part": "right_m4_screw",
      "type": "fastener",
      "operation": "add",
      "axis": "Y",
      "center": ["SPACER_X_OFFSET", "SPACER_CENTER_Y", 0],
      "dimensions": {"diameter": "M4_SHAFT_D", "length": "SCREW_LENGTH"},
      "count_group": "right_m4_spacer_stack",
      "required": true,
      "description": "plain screw shaft running through the right coaxial stack"
    }
  ],
  "assembly_axes": {
    "x_axis": "left-right across plate width",
    "y_axis": "rear-to-front plate separation and spacer/screw axis",
    "z_axis": "vertical plate height",
    "primary_separation_axis": "Y",
    "description": "plates are parallel XZ slabs separated along Y; spacers and screws run along Y"
  },
  "part_frames": [
    {
      "part": "rear_mounting_plate",
      "local_origin": "center of plate mid-plane",
      "world_center": "[0, 0, 0]",
      "approximate_bounding_box_mm": [70, 5, 50],
      "functional_faces": [
        {
          "name": "front_spacer_face",
          "normal_axis": "+Y",
          "role": "face contacted by spacer rear ends",
          "mates_with": "left_spacer_post.rear_face and right_spacer_post.rear_face"
        }
      ]
    },
    {
      "part": "front_camera_plate",
      "local_origin": "center of plate mid-plane",
      "world_center": "[0, 30, 0]",
      "approximate_bounding_box_mm": [50, 4, 40],
      "functional_faces": [
        {
          "name": "rear_spacer_face",
          "normal_axis": "-Y",
          "role": "face contacted by spacer front ends",
          "mates_with": "left_spacer_post.front_face and right_spacer_post.front_face"
        }
      ]
    },
    {
      "part": "left_spacer_post",
      "local_origin": "center of spacer cylinder",
      "world_center": "[-18, 15, 0]",
      "approximate_bounding_box_mm": [10, 25, 10],
      "functional_faces": [
        {
          "name": "rear_face",
          "normal_axis": "-Y",
          "role": "contacts rear plate front face",
          "mates_with": "rear_mounting_plate.front_spacer_face"
        },
        {
          "name": "front_face",
          "normal_axis": "+Y",
          "role": "contacts front plate rear face",
          "mates_with": "front_camera_plate.rear_spacer_face"
        }
      ]
    },
    {
      "part": "right_spacer_post",
      "local_origin": "center of spacer cylinder",
      "world_center": "[18, 15, 0]",
      "approximate_bounding_box_mm": [10, 25, 10],
      "functional_faces": [
        {
          "name": "rear_face",
          "normal_axis": "-Y",
          "role": "contacts rear plate front face",
          "mates_with": "rear_mounting_plate.front_spacer_face"
        },
        {
          "name": "front_face",
          "normal_axis": "+Y",
          "role": "contacts front plate rear face",
          "mates_with": "front_camera_plate.rear_spacer_face"
        }
      ]
    }
  ],
  "assembly_placement_constraints": [
    {
      "name": "plates_parallel_and_centered",
      "constraint_type": "parallel_faces",
      "parts": ["rear_mounting_plate", "front_camera_plate"],
      "description": "rear and front plates are parallel XZ plates with matching X/Z center and 25mm clear separation along Y"
    }
  ],
  "assembly_contracts": [
    {
      "id": "plates_centered_xz",
      "type": "centered",
      "parts": ["rear_mounting_plate", "front_camera_plate"],
      "axes": ["X", "Z"],
      "feature_refs": [],
      "target": "front and rear plate centers share X=0 and Z=0",
      "tolerance_mm": 0.25,
      "description": "front plate remains centered over the rear plate in the two in-plane axes"
    },
    {
      "id": "plates_parallel_y_faces",
      "type": "parallel_faces",
      "parts": ["rear_mounting_plate", "front_camera_plate"],
      "axes": ["Y"],
      "feature_refs": ["rear_mounting_plate.front_spacer_face", "front_camera_plate.rear_spacer_face"],
      "target": "opposing faces normal to Y",
      "tolerance_mm": 0.25,
      "description": "plate mating faces are parallel XZ planes separated along Y"
    },
    {
      "id": "left_m4_stack_coaxial",
      "type": "coaxial",
      "parts": ["rear_mounting_plate", "front_camera_plate", "left_spacer_post", "left_m4_screw"],
      "axes": ["Y"],
      "feature_refs": ["rear_left_m4_spacer_hole", "front_left_m4_spacer_hole", "left_spacer_bore", "left_screw_shaft"],
      "target": "shared center x=-SPACER_X_OFFSET, z=0",
      "tolerance_mm": 0.25,
      "description": "left rear hole, spacer bore, front hole, and screw shaft share one Y axis"
    },
    {
      "id": "right_m4_stack_coaxial",
      "type": "coaxial",
      "parts": ["rear_mounting_plate", "front_camera_plate", "right_spacer_post", "right_m4_screw"],
      "axes": ["Y"],
      "feature_refs": ["rear_right_m4_spacer_hole", "front_right_m4_spacer_hole", "right_spacer_bore", "right_screw_shaft"],
      "target": "shared center x=SPACER_X_OFFSET, z=0",
      "tolerance_mm": 0.25,
      "description": "right rear hole, spacer bore, front hole, and screw shaft share one Y axis"
    },
    {
      "id": "spacers_between_plates",
      "type": "between",
      "parts": ["rear_mounting_plate", "front_camera_plate", "left_spacer_post", "right_spacer_post"],
      "axes": ["Y"],
      "feature_refs": ["left_spacer_bore", "right_spacer_bore"],
      "target": "spacer centers lie between rear and front plate centers on Y",
      "tolerance_mm": 0.25,
      "description": "spacer posts sit between the plates and contact the opposing plate faces"
    }
  ],
  "alignment_groups": [
    {
      "name": "left_m4_spacer_stack",
      "axis": "Y",
      "center_reference": "x=-18mm, z=0mm",
      "members": ["rear left M4 hole", "left_spacer_post", "front left M4 hole", "left_m4_screw"],
      "tolerance_mm": 0.25,
      "description": "all left stack members are coaxial along the plate separation axis"
    },
    {
      "name": "right_m4_spacer_stack",
      "axis": "Y",
      "center_reference": "x=18mm, z=0mm",
      "members": ["rear right M4 hole", "right_spacer_post", "front right M4 hole", "right_m4_screw"],
      "tolerance_mm": 0.25,
      "description": "all right stack members are coaxial along the plate separation axis"
    }
  ],
  "forbidden_layouts": [
    "do not stack plates vertically on Z",
    "do not place plates side-by-side along X",
    "do not orient spacers or M4 screws along X or Z",
    "do not place screws beside the spacers"
  ],
  "assembly_transform_chain": [
    {
      "part": "rear_mounting_plate",
      "transforms": ["center at [0,0,0] with plate thickness along Y"],
      "zero_config_position": "rear plate center at world origin"
    },
    {
      "part": "front_camera_plate",
      "transforms": ["center at [0,30,0] with plate thickness along Y"],
      "zero_config_position": "front plate parallel to rear plate with 25mm clear gap"
    },
    {
      "part": "left_spacer_post",
      "transforms": ["rotate cylinder axis to Y", "center at [-18,15,0]"],
      "zero_config_position": "between the plates on the left M4 axis"
    },
    {
      "part": "right_spacer_post",
      "transforms": ["rotate cylinder axis to Y", "center at [18,15,0]"],
      "zero_config_position": "between the plates on the right M4 axis"
    },
    {
      "part": "left_m4_screw",
      "transforms": ["rotate screw shaft axis to Y", "center at [-18,15,0]"],
      "zero_config_position": "passing through rear plate, left spacer, and front plate"
    },
    {
      "part": "right_m4_screw",
      "transforms": ["rotate screw shaft axis to Y", "center at [18,15,0]"],
      "zero_config_position": "passing through rear plate, right spacer, and front plate"
    }
  ],
  "joint_definitions": [],
  "failure_risks": [
    {
      "risk_name": "axis_swap",
      "affected": "assembly_transform_chain",
      "description": "code generation may accidentally separate plates along Z or orient spacers along X",
      "mitigation": "treat Y as the only plate separation, spacer, and screw axis"
    }
  ],
  "replan_changes": []
}
```

OUTPUT:
```json
{
  "artifact_type": "single_part",
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
  "required_features": [
    "matching_width_plates",
    "servo_m2_hole_pattern",
    "extrusion_m5_hole_pattern",
    "left_outboard_gusset",
    "right_outboard_gusset"
  ],
  "feature_contracts": [
    {
      "id": "matching_width_plates",
      "host_part": "l_bracket_body",
      "type": "reference",
      "operation": "reference",
      "axis": "X",
      "center": "base and vertical plate share the same X centerline",
      "dimensions": {"width": "BRACKET_W"},
      "count_group": null,
      "required": true,
      "description": "base and vertical plate widths match so the body is one coherent L bracket"
    },
    {
      "id": "servo_m2_hole_pattern",
      "host_part": "l_bracket_body",
      "type": "through_hole_pattern",
      "operation": "cut",
      "axis": "Y",
      "center": "four centers on vertical servo face",
      "dimensions": {"count": 4, "diameter": "M2_CLEARANCE_D", "x_spacing": "SERVO_HOLE_X_SPACING", "z_spacing": "SERVO_HOLE_Z_SPACING"},
      "count_group": "servo_m2_pattern",
      "required": true,
      "description": "four M2 holes pass through the vertical plate on the servo mounting pattern"
    },
    {
      "id": "extrusion_m5_hole_pattern",
      "host_part": "l_bracket_body",
      "type": "through_hole_pattern",
      "operation": "cut",
      "axis": "Z",
      "center": "two centers on the horizontal base plate",
      "dimensions": {"count": 2, "diameter": "M5_CLEARANCE_D", "spacing": "EXTRUSION_HOLE_SPACING"},
      "count_group": "extrusion_m5_pattern",
      "required": true,
      "description": "two M5 vertical through holes mount the bracket to the extrusion"
    },
    {
      "id": "left_outboard_gusset",
      "host_part": "l_bracket_body",
      "type": "rib",
      "operation": "add",
      "axis": "X",
      "center": "-GUSSET_X_OFFSET",
      "dimensions": {"thickness": "GUSSET_T", "height": "GUSSET_H", "depth": "GUSSET_D"},
      "count_group": "outboard_gussets",
      "required": true,
      "description": "left triangular gusset reinforces the L corner without blocking hole paths"
    },
    {
      "id": "right_outboard_gusset",
      "host_part": "l_bracket_body",
      "type": "rib",
      "operation": "add",
      "axis": "X",
      "center": "GUSSET_X_OFFSET",
      "dimensions": {"thickness": "GUSSET_T", "height": "GUSSET_H", "depth": "GUSSET_D"},
      "count_group": "outboard_gussets",
      "required": true,
      "description": "right triangular gusset mirrors the left gusset outside the hole paths"
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
      "dimensions": {"length": "OUTER_L", "width": "OUTER_W", "thickness": "BASE_BOTTOM_T"},
      "count_group": null,
      "required": true,
      "description": "flat rectangular bottom plate supports FDM printing and PCB standoffs"
    },
    {
      "id": "base_side_wall_set",
      "host_part": "base_shell",
      "type": "wall_set",
      "operation": "add",
      "axis": "Z",
      "center": "four walls around the base perimeter",
      "dimensions": {"count": 4, "wall_thickness": "WALL_T", "height": "BASE_WALL_H"},
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
      "center": "four PCB/lid screw centers inset from the corners",
      "dimensions": {"count": 4, "diameter": "STANDOFF_D", "height": "STANDOFF_H", "bore_diameter": "M3_PILOT_D"},
      "count_group": "m3_lid_fastener_pattern",
      "required": true,
      "description": "four standoffs support the PCB and align with the lid screw holes"
    },
    {
      "id": "base_cable_opening",
      "host_part": "base_shell",
      "type": "cutout",
      "operation": "cut",
      "axis": "Y",
      "center": [0, "-OUTER_W / 2", "CABLE_OPENING_CENTER_Z"],
      "dimensions": {"width": "CABLE_OPENING_W", "height": "CABLE_OPENING_H"},
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
      "center": [0, 0, "ENCLOSURE_H - LID_T / 2"],
      "dimensions": {"length": "OUTER_L", "width": "OUTER_W", "thickness": "LID_T"},
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
      "dimensions": {"count": 4, "wall_thickness": "LIP_T", "depth": "LIP_DEPTH", "clearance": "LIP_CLEARANCE"},
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
      "dimensions": {"count": 4, "through_diameter": "M3_CLEARANCE_D", "countersink_diameter": "M3_HEAD_D"},
      "count_group": "m3_lid_fastener_pattern",
      "required": true,
      "description": "four lid holes and recesses align with the base standoffs"
    }
  ],
  "assembly_axes": {
    "x_axis": "enclosure length",
    "y_axis": "enclosure width",
    "z_axis": "lid/base stacking and enclosure height",
    "primary_separation_axis": "Z",
    "description": "base sits below the removable lid; screw and standoff axes run vertically along Z"
  },
  "part_frames": [
    {
      "part": "base_shell",
      "local_origin": "center of base bottom face",
      "world_center": "[0, 0, BASE_TOTAL_H / 2]",
      "approximate_bounding_box_mm": [100, 70, 30],
      "functional_faces": [
        {
          "name": "top_lid_seat",
          "normal_axis": "+Z",
          "role": "supports lid underside in the closed state",
          "mates_with": "removable_lid.underside"
        }
      ]
    },
    {
      "part": "removable_lid",
      "local_origin": "center of lid top plate",
      "world_center": "[0, 0, ENCLOSURE_H - LID_T / 2]",
      "approximate_bounding_box_mm": [100, 70, 5],
      "functional_faces": [
        {
          "name": "underside",
          "normal_axis": "-Z",
          "role": "sits on the top of the base shell with lip extending downward",
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
      "description": "lid is not side-by-side with the base and remains centered in plan view"
    },
    {
      "id": "lid_closed_above_base",
      "type": "above",
      "parts": ["base_shell", "removable_lid"],
      "axes": ["Z"],
      "feature_refs": ["base_side_wall_set", "lid_top_plate", "lid_alignment_lip"],
      "target": "lid top plate spans z=30mm to z=35mm with lip descending into base",
      "tolerance_mm": 0.25,
      "description": "lid sits above the base along Z in the closed position"
    },
    {
      "id": "lid_lip_inside_base_clearance",
      "type": "inside_clearance",
      "parts": ["base_shell", "removable_lid"],
      "axes": ["X", "Y", "Z"],
      "feature_refs": ["base_side_wall_set", "lid_alignment_lip"],
      "target": "lip outside dimensions equal base opening minus 2 * LIP_CLEARANCE",
      "tolerance_mm": 0.25,
      "description": "alignment lip nests inside the base walls without intersecting them"
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
      "members": ["base_pcb_standoff_pattern", "lid_m3_countersunk_hole_pattern"],
      "tolerance_mm": 0.25,
      "description": "all lid fastener holes are coaxial with their base standoffs"
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
