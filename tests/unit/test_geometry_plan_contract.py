from pathlib import Path
from types import SimpleNamespace

from cadpilotv3.agents.geometry_planner_agent import GeometryPlannerAgent
from cadpilotv3.schemas.geometry_plan import GeometryPlan

PROMPT_ROOT = Path("src/cadpilotv3/prompts")


def test_geometry_plan_schema_accepts_face_axis_assembly_contract() -> None:
    plan = GeometryPlan.model_validate(
        {
            "artifact_type": "assembly",
            "assembly_axes": {
                "x_axis": "left-right across plate width",
                "y_axis": "rear-to-front separation axis",
                "z_axis": "vertical plate height",
                "primary_separation_axis": "Y",
                "description": "plates are parallel XZ slabs separated along Y",
            },
            "part_frames": [
                {
                    "part": "rear_mounting_plate",
                    "local_origin": "center of rear plate",
                    "world_center": "[0, 0, 0]",
                    "approximate_bounding_box_mm": [70.0, 5.0, 50.0],
                    "functional_faces": [
                        {
                            "name": "front_spacer_face",
                            "normal_axis": "+Y",
                            "role": "contacts spacer rear ends",
                            "mates_with": "left_spacer_post.rear_face",
                        }
                    ],
                }
            ],
            "assembly_placement_constraints": [
                {
                    "name": "plates_parallel",
                    "constraint_type": "parallel_faces",
                    "parts": ["rear_mounting_plate", "front_camera_plate"],
                    "description": "plates remain parallel and centered in X/Z",
                }
            ],
            "alignment_groups": [
                {
                    "name": "left_m4_spacer_stack",
                    "axis": "Y",
                    "center_reference": "x=-18mm, z=0mm",
                    "members": [
                        "rear left M4 hole",
                        "left_spacer_post",
                        "front left M4 hole",
                        "left_m4_screw",
                    ],
                    "tolerance_mm": 0.25,
                    "description": "all members share one Y axis",
                }
            ],
            "forbidden_layouts": [
                "do not place plates side-by-side along X",
            ],
        }
    )

    assert plan.assembly_axes is not None
    assert plan.assembly_axes.primary_separation_axis == "Y"
    assert plan.part_frames[0].functional_faces[0].normal_axis == "+Y"
    assert plan.alignment_groups[0].members[-1] == "left_m4_screw"
    assert "side-by-side" in plan.forbidden_layouts[0]


def test_geometry_plan_schema_accepts_feature_and_assembly_contracts() -> None:
    plan = GeometryPlan.model_validate(
        {
            "artifact_type": "assembly",
            "parts": [
                {
                    "name": "base_plate",
                    "modeling_strategy": "primitive_csg",
                    "strategy_selection": {
                        "candidates": [
                            {
                                "strategy": "primitive_csg",
                                "advantage": "simple plate",
                                "disadvantage": "requires explicit cutters",
                            }
                        ],
                        "winner": "primitive_csg",
                        "rationale": "stable base plate construction",
                    },
                }
            ],
            "feature_contracts": [
                {
                    "id": "base_m4_hole_1",
                    "host_part": "base_plate",
                    "type": "through_hole",
                    "operation": "cut",
                    "axis": "Z",
                    "center": ["-HOLE_X_OFFSET", "-HOLE_Y_OFFSET", "BASE_T / 2"],
                    "dimensions": {"diameter": "M4_CLEARANCE_D"},
                    "count_group": "base_m4_hole_pattern",
                    "required": True,
                    "description": "first M4 clearance hole in the base pattern",
                }
            ],
            "assembly_contracts": [
                {
                    "id": "lid_centered_on_base",
                    "type": "centered",
                    "parts": ["base_plate", "lid"],
                    "axes": ["X", "Y"],
                    "feature_refs": ["base_m4_hole_1"],
                    "target": "centers share X and Y",
                    "tolerance_mm": 0.25,
                    "description": "lid and base stay centered in plan view",
                }
            ],
        }
    )

    assert plan.required_features == ["base_m4_hole_1"]
    assert plan.feature_contracts[0].type == "through_hole"
    assert plan.feature_contracts[0].dimensions["diameter"] == "M4_CLEARANCE_D"
    assert plan.assembly_contracts[0].tolerance_mm == 0.25


def test_geometry_plan_normalizes_harmless_design_synthesis_shape_slips() -> None:
    plan = GeometryPlan.model_validate(
        {
            "artifact_type": "single_part",
            "assembly_axes": {},
            "part_frames": [
                {
                    "part": "bracket_body",
                    "local_origin": "center of wall plate back face",
                    "world_center": [0, 0, 0],
                    "approximate_bounding_box_mm": [60, 70, 90],
                }
            ],
        }
    )

    assert plan.assembly_axes is None
    assert plan.part_frames[0].world_center == "[0, 0, 0]"


def test_geometry_planner_prompt_requires_face_axis_contract() -> None:
    planner_prompt = (
        PROMPT_ROOT / "system" / "geometry_planner_agent.md"
    ).read_text(encoding="utf-8")
    planner_examples = (
        PROMPT_ROOT / "examples" / "geometry_planner_examples.md"
    ).read_text(encoding="utf-8")

    assert "face-axis assembly contract" in planner_prompt
    assert "assembly_axes" in planner_prompt
    assert "part_frames" in planner_prompt
    assert "alignment_groups" in planner_prompt
    assert "forbidden_layouts" in planner_prompt
    assert "required_features" in planner_prompt
    assert "feature_contracts" in planner_prompt
    assert "assembly_contracts" in planner_prompt
    assert "Static Camera Mount Face-Axis Assembly Plan" in planner_examples
    assert "left_m4_spacer_stack" in planner_examples
    assert "rear_plate_m6_hole_pattern" in planner_examples
    assert "plates_centered_xz" in planner_examples


def test_geometry_planner_selects_camera_mount_example_without_whole_file() -> None:
    agent = object.__new__(GeometryPlannerAgent)
    few_shots = """
### Example 1 - Static Single-Part Geometry Plan
INPUT: servo bracket gussets
OUTPUT: single part bracket plan

### Example 2 - Static Assembly Geometry Plan
INPUT: electronics enclosure base and lid
OUTPUT: two part enclosure plan

### Example 3 - Static Camera Mount Face-Axis Assembly Plan
INPUT: rear plate front camera plate spacer posts and M4 screws
OUTPUT: camera mount face-axis contract
"""

    selected = agent._select_relevant_examples(
        few_shot_prompt=few_shots,
        spec=SimpleNamespace(
            component="machine_vision_camera_mount",
            component_type="assembly",
            style="flat parallel plates with spacers",
            manufacturing_process="FDM",
            approximate_scale="small",
            parts=[
                "rear_mounting_plate",
                "front_camera_plate",
                "left_spacer_post",
                "right_spacer_post",
                "left_m4_screw",
                "right_m4_screw",
            ],
            constraints=[
                "front_plate_parallel_to_rear_plate",
                "m4_screws_coaxial_with_spacers",
            ],
        ),
    )

    assert "Selected Geometry Planner Few-Shots" in selected
    assert "Static Camera Mount Face-Axis Assembly Plan" in selected
    assert "Static Single-Part Geometry Plan" not in selected
    assert "Static Assembly Geometry Plan" not in selected
