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
