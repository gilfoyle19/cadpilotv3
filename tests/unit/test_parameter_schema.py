from pathlib import Path
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from cadpilotv3.agents.parameter_agent import ParameterAgent
from cadpilotv3.graph.nodes import PipelineNodes
from cadpilotv3.schemas.parameters import ParameterSchema

PROMPT_ROOT = Path("src/cadpilotv3/prompts")


def _parameter(value: float, description: str = "Parameter.") -> dict:
    return {
        "value": value,
        "unit": "mm",
        "description": description,
        "min": 1.0,
        "max": 200.0,
        "depends_on": [],
        "constraint": None,
        "is_derived": False,
        "derived_from": None,
    }


def test_parameter_schema_wraps_flat_llm_output() -> None:
    schema = ParameterSchema.model_validate(
        {
            "PLATE_L": _parameter(80.0, "Plate length."),
            "PLATE_W": _parameter(40.0, "Plate width."),
            "PLATE_T": _parameter(4.0, "Plate thickness."),
        }
    )

    assert schema.parameters["PLATE_L"].value == 80.0
    assert schema.parameters["PLATE_W"].value == 40.0
    assert schema.parameters["PLATE_T"].value == 4.0


def test_parameter_schema_rejects_empty_parameters() -> None:
    with pytest.raises(ValidationError, match="must contain at least one parameter"):
        ParameterSchema.model_validate({"parameters": {}})


def test_parameter_schema_rejects_non_screaming_snake_case_names() -> None:
    with pytest.raises(ValidationError, match="SCREAMING_SNAKE_CASE"):
        ParameterSchema.model_validate({"parameters": {"plate_l": _parameter(80.0)}})


def test_parameter_node_passes_prompt_spec_plan_and_critic_to_service() -> None:
    captured = {}
    produced = object()

    class FakeParameterService:
        def execute(self, **kwargs):
            captured.update(kwargs)
            return produced

    nodes = object.__new__(PipelineNodes)
    nodes.parameter_service = FakeParameterService()

    spec = object()
    geometry_plan = object()
    critic_a_report = object()
    state = {
        "user_prompt": "plate 80mm long, 40mm wide, 4mm thick",
        "spec": spec,
        "geometry_plan": geometry_plan,
        "critic_a_report": critic_a_report,
    }

    result = nodes.parameter_agent(state)

    assert captured["user_prompt"] == "plate 80mm long, 40mm wide, 4mm thick"
    assert captured["spec"] is spec
    assert captured["geometry_plan"] is geometry_plan
    assert captured["critic_a_report"] is critic_a_report
    assert result["parameters"] is produced


def test_parameter_agent_prompt_includes_original_prompt_and_spec(monkeypatch) -> None:
    captured = {}

    class FakeLLM:
        def invoke(self, prompt: str) -> str:
            captured["prompt"] = prompt
            return """
{
  "parameters": {
    "PLATE_L": {
      "value": 80.0,
      "unit": "mm",
      "description": "Plate length.",
      "min": 50.0,
      "max": 120.0,
      "depends_on": [],
      "constraint": null,
      "is_derived": false,
      "derived_from": null
    },
    "PLATE_W": {
      "value": 40.0,
      "unit": "mm",
      "description": "Plate width.",
      "min": 20.0,
      "max": 80.0,
      "depends_on": [],
      "constraint": null,
      "is_derived": false,
      "derived_from": null
    },
    "PLATE_T": {
      "value": 4.0,
      "unit": "mm",
      "description": "Plate thickness.",
      "min": 2.0,
      "max": 12.0,
      "depends_on": [],
      "constraint": null,
      "is_derived": false,
      "derived_from": null
    }
  }
}
"""

    class FakeLLMFactory:
        def get_for_agent(self, _agent_name):
            return FakeLLM()

    monkeypatch.setattr(
        "cadpilotv3.agents.parameter_agent.load_prompt_text",
        lambda _settings, name: f"{name} prompt",
    )

    agent = ParameterAgent(settings=SimpleNamespace())
    agent.llm_factory = FakeLLMFactory()

    result = agent.run(
        user_prompt="Design a plate 80mm long, 40mm wide, and 4mm thick.",
        spec=SimpleNamespace(
            model_dump_json=lambda indent=2: (
                '{"explicit_dimensions":["80mm long","40mm wide","4mm thick"]}'
            )
        ),
        geometry_plan=SimpleNamespace(model_dump_json=lambda indent=2: "{}"),
        critic_a_report=None,
    )

    assert result.parameters["PLATE_L"].value == 80.0
    assert "Original user prompt:" in captured["prompt"]
    assert "Numeric facts extracted from original prompt:" in captured["prompt"]
    assert "80mm long, 40mm wide, and 4mm thick" in captured["prompt"]
    assert "Structured spec:" in captured["prompt"]
    assert "explicit_dimensions" in captured["prompt"]


def test_parameter_prompt_emphasizes_literal_json_number_contract() -> None:
    system_prompt = (
        PROMPT_ROOT / "system" / "parameter_agent.md"
    ).read_text(encoding="utf-8")

    assert "CRITICAL JSON NUMBER CONTRACT" in system_prompt
    assert "value, min, and max must be literal JSON numbers only" in system_prompt
    assert "Never put formulas, parentheses, arithmetic expressions" in system_prompt
    assert '"value": "PLATE_L / 2 - EDGE_INSET"' in system_prompt
    assert '"value": 32.0' in system_prompt
