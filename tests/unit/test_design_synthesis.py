from pathlib import Path
from types import SimpleNamespace

from cadpilotv3.agents.design_synthesis_agent import DesignSynthesisAgent
from cadpilotv3.graph.nodes import PipelineNodes
from cadpilotv3.schemas.design_synthesis import DesignSynthesis
from cadpilotv3.services.web_research_service import WebResearchContext

PROMPT_ROOT = Path("src/cadpilotv3/prompts")


class FakeLLM:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def invoke(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return """
{
  "spec": {
    "component": "iphone_desk_dock",
    "component_type": "single_part",
    "dof_count": 0,
    "parts": ["dock_body"],
    "output_format": "STEP",
    "units": "mm",
    "approximate_scale": "small",
    "style": "minimal_printable",
    "manufacturing_process": "FDM",
    "constraints": ["flat_base_required"],
    "explicit_dimensions": [],
    "explicit_constraints": [],
    "researched_dimensions": [
      "iphone 15: 147.6mm x 71.6mm x 7.8mm, source Apple technical specifications"
    ],
    "research_sources": ["https://www.apple.com/iphone-15/specs/"],
    "clarifications_needed": []
  },
  "geometry_plan": {
    "artifact_type": "single_part",
    "parts": [
      {
        "name": "dock_body",
        "geometric_role": "supports the phone",
        "modeling_strategy": "extrude base with angled support",
        "strategy_selection": {
          "candidates": [
            {
              "strategy": "simple extrude",
              "advantage": "easy to print",
              "disadvantage": "less sculpted"
            }
          ],
          "winner": "simple extrude",
          "rationale": "Matches the printable dock request."
        },
        "key_features": [
          {
            "feature": "phone_slot",
            "description": "Supports the phone body with clearance."
          }
        ],
        "body_type": "solid"
      }
    ],
    "feature_contracts": [
      {
        "id": "phone_slot",
        "host_part": "dock_body",
        "type": "slot",
        "dimensions": {
          "width": "PHONE_WIDTH + 2"
        },
        "required": true,
        "description": "Phone support slot."
      }
    ]
  },
  "parameters": {
    "DOCK_WIDTH": {
      "value": 90.0,
      "unit": "mm",
      "description": "Overall dock width.",
      "min": 70.0,
      "max": 120.0,
      "depends_on": [],
      "constraint": null,
      "is_derived": false,
      "derived_from": null
    }
  },
  "critic_a_report": {
    "checkpoint": "A",
    "verdict": "pass",
    "overall_fidelity_score": 0.92,
    "dimension_scores": {
      "dof_fidelity": 1.0,
      "part_completeness": 0.9,
      "constraint_coverage": 0.9,
      "scale_plausibility": 0.9,
      "style_alignment": 0.9,
      "coordinate_sanity": 0.9
    },
    "issues": [],
    "routing": "proceed",
    "replan_instructions": null,
    "user_facing_warnings": []
  }
}
"""


class FakeLLMFactory:
    def __init__(self, llm: FakeLLM) -> None:
        self.llm = llm

    def get_for_agent(self, _agent_name):
        return self.llm


class FakeResearchService:
    def research_if_needed(self, user_prompt: str) -> WebResearchContext:
        return WebResearchContext(
            queries=["iphone 15 dimensions official"],
            researched_dimensions=[
                "iphone 15: 147.6mm x 71.6mm x 7.8mm, source Apple technical specifications"
            ],
            sources=["https://www.apple.com/iphone-15/specs/"],
        )


def test_design_synthesis_schema_validates_nested_outputs() -> None:
    synthesis = DesignSynthesis.model_validate(
        {
            "spec": {
                "component": "test_bracket",
                "component_type": "single_part",
                "parts": ["bracket_body"],
                "constraints": [],
                "explicit_dimensions": [],
                "explicit_constraints": [],
                "researched_dimensions": [],
                "research_sources": [],
                "clarifications_needed": [],
            },
            "geometry_plan": {
                "artifact_type": "single_part",
            },
            "parameters": {
                "WIDTH": {
                    "value": 10,
                    "unit": "mm",
                    "description": "Overall width",
                }
            },
            "critic_a_report": {
                "verdict": "conditional_pass",
                "overall_fidelity_score": 0.8,
                "dimension_scores": {
                    "dof_fidelity": 1.0,
                    "part_completeness": 0.8,
                    "constraint_coverage": 0.8,
                    "scale_plausibility": 0.8,
                    "style_alignment": 0.8,
                    "coordinate_sanity": 0.8,
                },
                "issues": [],
                "routing": "proceed",
                "replan_instructions": None,
                "user_facing_warnings": [],
            },
        }
    )

    assert synthesis.parameters.parameters["WIDTH"].value == 10
    assert synthesis.critic_a_report.checkpoint == "A"
    assert synthesis.geometry_plan.artifact_type == "single_part"


def test_design_synthesis_agent_injects_research_context(monkeypatch) -> None:
    monkeypatch.setattr(
        "cadpilotv3.agents.design_synthesis_agent.load_prompt_text",
        lambda _settings, name: f"{name} prompt",
    )

    llm = FakeLLM()
    agent = DesignSynthesisAgent(settings=SimpleNamespace())
    agent.llm_factory = FakeLLMFactory(llm)
    agent.web_research_service = FakeResearchService()

    synthesis = agent.run("Create a desk dock that fits an iPhone 15.")

    assert synthesis.spec.component == "iphone_desk_dock"
    assert synthesis.parameters.parameters["DOCK_WIDTH"].value == 90.0
    assert "Web research context for real-world product interfaces:" in llm.prompts[0]
    assert "design_synthesis_agent.md prompt" in llm.prompts[0]
    assert "User request:" in llm.prompts[0]


def test_design_synthesis_node_populates_existing_front_half_state() -> None:
    spec = object()
    geometry_plan = object()
    parameters = object()
    critic_a_report = object()

    class FakeDesignSynthesisService:
        def execute(self, user_prompt: str):
            assert user_prompt == "Make a bracket."
            return SimpleNamespace(
                spec=spec,
                geometry_plan=geometry_plan,
                parameters=parameters,
                critic_a_report=critic_a_report,
            )

    nodes = object.__new__(PipelineNodes)
    nodes.design_synthesis_service = FakeDesignSynthesisService()
    state = {
        "user_prompt": "Make a bracket.",
        "spec": {},
        "geometry_plan": {},
        "parameters": {},
        "critic_a_report": {},
    }

    result = nodes.design_synthesis_agent(state)

    assert result["spec"] is spec
    assert result["geometry_plan"] is geometry_plan
    assert result["parameters"] is parameters
    assert result["critic_a_report"] is critic_a_report


def test_design_synthesis_node_counts_failed_self_check() -> None:
    class FakeDesignSynthesisService:
        def execute(self, _user_prompt: str):
            return SimpleNamespace(
                spec=object(),
                geometry_plan=object(),
                parameters=object(),
                critic_a_report=SimpleNamespace(
                    verdict="fail",
                    routing="replan",
                ),
            )

    nodes = object.__new__(PipelineNodes)
    nodes.design_synthesis_service = FakeDesignSynthesisService()
    state = {
        "user_prompt": "Make a bracket.",
        "critic_a_attempts": 0,
    }

    result = nodes.design_synthesis_agent(state)

    assert result["critic_a_attempts"] == 1


def test_design_synthesis_prompt_selects_relevant_few_shot(monkeypatch) -> None:
    agent = object.__new__(DesignSynthesisAgent)
    agent.settings = SimpleNamespace()

    def fake_load_prompt_text(_settings, filename):
        if filename == "design_synthesis_agent.md":
            return "SYSTEM"
        return """
### Example 1 - CNC Bearing Block Synthesis
INPUT: CNC pillow block for a 608 bearing with mounting holes
OUTPUT: bearing block synthesis

### Example 2 - Electronics Enclosure Synthesis
INPUT: two-part enclosure with PCB clearance and cutouts
OUTPUT: enclosure synthesis
"""

    monkeypatch.setattr(
        "cadpilotv3.agents.design_synthesis_agent.load_prompt_text",
        fake_load_prompt_text,
    )

    prompt = agent._build_prompt(
        user_prompt="Create a CNC 608 bearing pillow block with mounting holes.",
        research_context=WebResearchContext(),
    )

    assert "CNC Bearing Block Synthesis" in prompt
    assert "Electronics Enclosure Synthesis" not in prompt


def test_design_synthesis_prompt_declares_combined_output_contract() -> None:
    system_prompt = (
        PROMPT_ROOT / "system" / "design_synthesis_agent.md"
    ).read_text(encoding="utf-8")

    assert '"spec": { ... }' in system_prompt
    assert '"geometry_plan": { ... }' in system_prompt
    assert '"parameters": { ... }' in system_prompt
    assert '"critic_a_report": { ... }' in system_prompt
    assert "GROUNDING PRIORITY" in system_prompt
    assert "CRITICAL JSON NUMBER CONTRACT" in system_prompt
    assert "assembly_contracts" in system_prompt
    assert "Critic A scoring" in system_prompt
    assert "If the audit would fail and the issue is fixable" in system_prompt
    assert 'Do not output\n  `"assembly_axes": {}`' in system_prompt
    assert "`part_frames[].world_center` must be a string" in system_prompt


def test_design_synthesis_examples_are_full_combined_few_shots() -> None:
    examples_prompt = (
        PROMPT_ROOT / "examples" / "design_synthesis_examples.md"
    ).read_text(encoding="utf-8")

    assert "CNC Bearing Block Synthesis" in examples_prompt
    assert "Two-Part Electronics Enclosure Synthesis" in examples_prompt
    assert '"spec": {' in examples_prompt
    assert '"geometry_plan": {' in examples_prompt
    assert '"parameters": {' in examples_prompt
    assert '"critic_a_report": {' in examples_prompt
    assert '"assembly_contracts": [' in examples_prompt
    assert '"derived_from": "OUTER_L / 2 - FASTENER_X_EDGE_INSET"' in examples_prompt
