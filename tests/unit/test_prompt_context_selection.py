from types import SimpleNamespace

from cadpilotv3.agents.critic_checkpoint_b_agent import CriticCheckpointBAgent
from cadpilotv3.schemas.validation import ChildGeometryReport, GeometryReport, ValidationReport


def test_critic_b_selects_spatial_fidelity_few_shot() -> None:
    agent = object.__new__(CriticCheckpointBAgent)
    few_shots = """
### Example 1 - Final Static Assembly Pass
INPUT: enclosure pass
OUTPUT: export

### Example 2 - Final Output Replan Due to Interference
INPUT: motor mount gussets intersect holes
OUTPUT: replan

### Example 3 - Replan Due to Side-by-Side Parts That Should Be Stacked
INPUT: lid is beside base instead of on top
OUTPUT: replan stacked assembly
"""

    selected = agent._select_relevant_examples(
        few_shot_prompt=few_shots,
        user_prompt="Create a static two-part enclosure with the lid closed on top.",
        spec=SimpleNamespace(
            component="two_part_enclosure",
            component_type="static_assembly",
            style="box",
            parts=["base", "lid"],
            constraints=["lid closed on top"],
        ),
        geometry_plan=SimpleNamespace(
            artifact_type="static_assembly",
            parts=[
                SimpleNamespace(name="base", geometric_role="lower base", key_features=[]),
                SimpleNamespace(name="lid", geometric_role="upper lid", key_features=[]),
            ],
        ),
        validation=ValidationReport(
            status="success",
            geometry_valid=True,
            geometry_report=GeometryReport(
                part_count=2,
                child_metadata=[
                    ChildGeometryReport(name="base", center_mm=[0, 0, 15]),
                    ChildGeometryReport(name="lid", center_mm=[100, 0, 2]),
                ],
            ),
        ),
        max_examples=1,
    )

    assert "Side-by-Side Parts That Should Be Stacked" in selected
    assert "Final Output Replan Due to Interference" not in selected
