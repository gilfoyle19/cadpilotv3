from types import SimpleNamespace

from cadpilotv3.agents.critic_checkpoint_a_agent import CriticCheckpointAAgent
from cadpilotv3.agents.critic_checkpoint_b_agent import CriticCheckpointBAgent
from cadpilotv3.agents.export_summary_agent import ExportSummaryAgent
from cadpilotv3.agents.intent_spec_agent import IntentSpecAgent
from cadpilotv3.schemas.validation import ChildGeometryReport, GeometryReport, ValidationReport
from cadpilotv3.services.web_research_service import WebResearchContext


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


def test_intent_selects_local_few_shot_from_user_prompt(monkeypatch) -> None:
    agent = object.__new__(IntentSpecAgent)
    agent.settings = SimpleNamespace()

    def fake_load_prompt_text(settings, filename):
        if filename == "intent_spec_agent.md":
            return "SYSTEM"
        return """
### Example 1 - FDM Bracket
INPUT: bracket
OUTPUT: bracket spec

### Example 2 - CNC Bearing Block
INPUT: 608 bearing pillow block
OUTPUT: bearing spec

### Example 3 - Electronics Enclosure
INPUT: enclosure
OUTPUT: enclosure spec
"""

    monkeypatch.setattr(
        "cadpilotv3.agents.intent_spec_agent.load_prompt_text",
        fake_load_prompt_text,
    )

    prompt = agent._build_prompt(
        user_prompt="Create a CNC 608 bearing pillow block with mounting holes.",
        research_context=WebResearchContext(),
    )

    assert "CNC Bearing Block" in prompt
    assert "Electronics Enclosure" not in prompt


def test_critic_a_selects_failure_few_shot_for_motion_plan() -> None:
    agent = object.__new__(CriticCheckpointAAgent)
    few_shots = """
### Example 1 - Static Plan Pass
INPUT: valid static bracket
OUTPUT: pass

### Example 2 - Static Plan Fail Due to Invented Motion
INPUT: hinge animation and moving latch
OUTPUT: fail

### Example 3 - Static Plan Fail Due to Interference
INPUT: overlapping ribs
OUTPUT: fail
"""

    selected = agent._select_relevant_examples(
        few_shot_prompt=few_shots,
        user_prompt="Make a static enclosure, but the plan added a hinge animation.",
        spec=SimpleNamespace(
            component="enclosure",
            component_type="static_assembly",
            style="box",
            manufacturing_process="FDM",
            parts=["base", "lid"],
            constraints=["static only", "no moving hinge"],
        ),
        geometry_plan=SimpleNamespace(
            artifact_type="static_assembly",
            parts=[
                SimpleNamespace(
                    name="animated_hinge",
                    geometric_role="moving lid joint",
                    modeling_strategy="jointed motion",
                    key_features=[],
                ),
            ],
        ),
        max_examples=1,
    )

    assert "Invented Motion" in selected
    assert "Interference" not in selected


def test_export_summary_selects_manufacturing_report_few_shot() -> None:
    agent = object.__new__(ExportSummaryAgent)
    few_shots = """
### Example 1 - FDM Static Assembly Manufacturing Report
INPUT: two part enclosure assembly
OUTPUT: fdm report

### Example 2 - CNC Single-Part Manufacturing Report With Warning
INPUT: CNC bearing block with warning
OUTPUT: cnc report
"""

    selected = agent._select_relevant_examples(
        few_shot_prompt=few_shots,
        user_prompt="Export the CNC bearing block and mention the machining warning.",
        spec=SimpleNamespace(
            component="bearing_pillow_block",
            component_type="single_part",
            style="solid_block",
            manufacturing_process="CNC",
            parts=["bearing_block"],
            constraints=["bearing seat"],
        ),
        parameters=SimpleNamespace(
            parameters={
                "BEARING_OD": SimpleNamespace(
                    description="608 bearing outside diameter",
                    constraint="press fit",
                    derived_from=None,
                )
            }
        ),
        validation=ValidationReport(
            status="success",
            geometry_valid=True,
            geometry_report=GeometryReport(
                artifact_type="single_part",
                part_count=1,
                child_metadata=[],
            ),
        ),
        critic_b_report=SimpleNamespace(
            routing="export",
            user_facing_warnings=["CNC internal corner radii require review."],
        ),
        export_files=[
            SimpleNamespace(
                format="STEP",
                filename="bearing_pillow_block.step",
                contents="CNC single part STEP",
            )
        ],
        max_examples=1,
    )

    assert "CNC Single-Part Manufacturing Report" in selected
    assert "FDM Static Assembly" not in selected
