from types import SimpleNamespace

import pytest

from cadpilotv3.graph.nodes import PipelineNodes
from cadpilotv3.services.code_generation_infill_service import (
    CodeGenerationInfillService,
    CodeGenerationOutputError,
)


def test_codegen_node_passes_critic_b_patch_instructions() -> None:
    captured = {}

    class FakeCodeGenerationService:
        def execute_script(self, **kwargs):
            captured.update(kwargs)
            return "import cadquery as cq\n"

    nodes = object.__new__(PipelineNodes)
    nodes.code_generation_infill_service = FakeCodeGenerationService()

    state = {
        "spec": object(),
        "geometry_plan": object(),
        "parameters": object(),
        "script": "import cadquery as cq\nold_model = cq.Workplane('XY').box(1, 1, 1)\n",
        "repair_decision": None,
        "critic_b_report": SimpleNamespace(
            routing="patch",
            patch_instructions="Move the gussets outboard and preserve the hole pattern.",
        ),
    }

    result = nodes.code_generation_infill_agent(state)

    assert captured["critic_feedback"] == (
        "Move the gussets outboard and preserve the hole pattern."
    )
    assert captured["current_script"] == (
        "import cadquery as cq\nold_model = cq.Workplane('XY').box(1, 1, 1)\n"
    )
    assert result["script"] == "import cadquery as cq\n"


def test_geometry_planner_node_passes_critic_b_replan_instructions() -> None:
    captured = {}
    planned = object()

    class FakeGeometryPlannerService:
        def execute(self, **kwargs):
            captured.update(kwargs)
            return planned

    nodes = object.__new__(PipelineNodes)
    nodes.geometry_planner_service = FakeGeometryPlannerService()

    state = {
        "spec": object(),
        "critic_a_report": {},
        "critic_b_report": SimpleNamespace(
            routing="replan",
            replan_instructions="Use an outboard gusset strategy with clear M3 holes.",
        ),
    }

    result = nodes.geometry_planner_agent(state)

    assert captured["critic_b_replan_instructions"] == (
        "Use an outboard gusset strategy with clear M3 holes."
    )
    assert result["geometry_plan"] is planned


def test_critic_b_node_passes_geometry_plan_and_parameters() -> None:
    captured = {}

    class FakeCriticBService:
        def execute(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(user_facing_warnings=[])

    nodes = object.__new__(PipelineNodes)
    nodes.critic_checkpoint_b_service = FakeCriticBService()

    geometry_plan = object()
    parameters = object()
    state = {
        "user_prompt": "make a bracket",
        "spec": object(),
        "geometry_plan": geometry_plan,
        "parameters": parameters,
        "validation": object(),
        "critic_a_report": object(),
        "repair_count": 0,
    }

    nodes.critic_checkpoint_b(state)

    assert captured["geometry_plan"] is geometry_plan
    assert captured["parameters"] is parameters


def test_codegen_output_guard_rejects_empty_script() -> None:
    service = object.__new__(CodeGenerationInfillService)

    with pytest.raises(CodeGenerationOutputError):
        service._validate_generated_code("\n")


def test_codegen_output_guard_rejects_non_cadquery_text() -> None:
    service = object.__new__(CodeGenerationInfillService)

    with pytest.raises(CodeGenerationOutputError):
        service._validate_generated_code("print('not a cad script')\n")


def test_execute_script_retries_after_empty_generation() -> None:
    class FakeAgent:
        def __init__(self) -> None:
            self.calls = []

        def run(self, **kwargs):
            self.calls.append(kwargs)
            if len(self.calls) == 1:
                return "```python\n\n```"
            return "import cadquery as cq\nmodel = cq.Workplane('XY').box(1, 1, 1)\n"

    service = object.__new__(CodeGenerationInfillService)
    service.agent = FakeAgent()

    script = service.execute_script(
        spec=SimpleNamespace(component="test_part"),
        geometry_plan=object(),
        parameters=object(),
    )

    assert "import cadquery as cq" in script
    assert len(service.agent.calls) == 2
    assert service.agent.calls[0]["generation_feedback"] is None
    assert service.agent.calls[1]["generation_feedback"] == (
        "Code generation returned an empty script"
    )
