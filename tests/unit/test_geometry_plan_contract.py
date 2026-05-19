from pathlib import Path

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
    assert "Static Camera Mount Face-Axis Assembly Plan" in planner_examples
    assert "left_m4_spacer_stack" in planner_examples
