from types import SimpleNamespace

from cadpilotv3.agents.design_synthesis_agent import DesignSynthesisAgent
from cadpilotv3.agents.parameter_agent import ParameterAgent
from cadpilotv3.schemas.design_synthesis import DesignSynthesis
from cadpilotv3.schemas.geometry_plan import GeometryPlan
from cadpilotv3.schemas.intent_spec import IntentSpec
from cadpilotv3.schemas.parameters import ParameterSchema
from cadpilotv3.services.design_synthesis_service import DesignSynthesisService
from cadpilotv3.services.parameter_service import ParameterService
from cadpilotv3.services.web_research_service import WebResearchContext


class AsyncFakeLLM:
    def __init__(self, response: str) -> None:
        self.response = response
        self.prompts: list[str] = []

    async def ainvoke(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.response


class FakeLLMFactory:
    def __init__(self, llm: AsyncFakeLLM) -> None:
        self.llm = llm

    def get_for_agent(self, agent_name):
        return self.llm


class FakeParameterAgent:
    def __init__(self, result: ParameterSchema) -> None:
        self.result = result
        self.calls: list[dict] = []

    async def arun(self, **kwargs) -> ParameterSchema:
        self.calls.append(kwargs)
        return self.result


class FakeDesignSynthesisAgent:
    def __init__(self, result: DesignSynthesis) -> None:
        self.result = result
        self.calls: list[dict] = []

    async def arun(self, user_prompt: str) -> DesignSynthesis:
        self.calls.append({"user_prompt": user_prompt})
        return self.result


def _minimal_intent_spec() -> IntentSpec:
    return IntentSpec(
        component="test bracket",
        component_type="bracket",
        output_format="STEP",
        units="mm",
    )


def _minimal_geometry_plan() -> GeometryPlan:
    return GeometryPlan(artifact_type="single_part")


def _minimal_parameters() -> ParameterSchema:
    return ParameterSchema.model_validate(
        {
            "parameters": {
                "WIDTH": {
                    "value": 10,
                    "unit": "mm",
                    "description": "Overall width",
                }
            }
        }
    )


def _minimal_design_synthesis() -> DesignSynthesis:
    return DesignSynthesis.model_validate(
        {
            "spec": _minimal_intent_spec().model_dump(),
            "geometry_plan": _minimal_geometry_plan().model_dump(),
            "parameters": _minimal_parameters().model_dump(),
            "critic_a_report": {
                "verdict": "pass",
                "overall_fidelity_score": 0.95,
                "dimension_scores": {
                    "dof_fidelity": 1.0,
                    "part_completeness": 0.9,
                    "constraint_coverage": 0.9,
                    "scale_plausibility": 0.9,
                    "style_alignment": 0.9,
                    "coordinate_sanity": 0.9,
                },
                "issues": [],
                "routing": "proceed",
                "replan_instructions": None,
                "user_facing_warnings": [],
            },
        }
    )


async def test_parameter_agent_arun_uses_async_llm(monkeypatch) -> None:
    llm = AsyncFakeLLM(
        """
        {
          "parameters": {
            "WIDTH": {
              "value": 10,
              "unit": "mm",
              "description": "Overall width"
            }
          }
        }
        """
    )
    monkeypatch.setattr(
        "cadpilotv3.agents.parameter_agent.get_llm_factory",
        lambda: FakeLLMFactory(llm),
    )
    monkeypatch.setattr(
        "cadpilotv3.agents.parameter_agent.load_prompt_text",
        lambda settings, name: f"prompt:{name}",
    )

    agent = ParameterAgent(SimpleNamespace())
    result = await agent.arun(
        user_prompt="Make it 10 mm wide.",
        spec=_minimal_intent_spec(),
        geometry_plan=_minimal_geometry_plan(),
    )

    assert result.parameters["WIDTH"].value == 10
    assert len(llm.prompts) == 1
    assert "Make it 10 mm wide." in llm.prompts[0]


async def test_parameter_service_aexecute_delegates_to_async_agent() -> None:
    expected = _minimal_parameters()
    service = ParameterService(SimpleNamespace())
    fake_agent = FakeParameterAgent(expected)
    service.agent = fake_agent

    result = await service.aexecute(
        user_prompt="Make it 10 mm wide.",
        spec=_minimal_intent_spec(),
        geometry_plan=_minimal_geometry_plan(),
    )

    assert result is expected
    assert fake_agent.calls[0]["user_prompt"] == "Make it 10 mm wide."


async def test_design_synthesis_agent_arun_uses_async_llm(monkeypatch) -> None:
    llm = AsyncFakeLLM(
        """
        {
          "spec": {
            "component": "test bracket",
            "component_type": "bracket",
            "parts": ["bracket_body"],
            "constraints": [],
            "explicit_dimensions": [],
            "explicit_constraints": [],
            "researched_dimensions": [],
            "research_sources": [],
            "clarifications_needed": []
          },
          "geometry_plan": {
            "artifact_type": "single_part"
          },
          "parameters": {
            "WIDTH": {
              "value": 10,
              "unit": "mm",
              "description": "Overall width"
            }
          },
          "critic_a_report": {
            "verdict": "pass",
            "overall_fidelity_score": 0.9,
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
    )
    monkeypatch.setattr(
        "cadpilotv3.agents.design_synthesis_agent.get_llm_factory",
        lambda: FakeLLMFactory(llm),
    )
    monkeypatch.setattr(
        "cadpilotv3.agents.design_synthesis_agent.load_prompt_text",
        lambda settings, name: f"prompt:{name}",
    )

    async def fake_aresearch_if_needed(_user_prompt: str) -> WebResearchContext:
        return WebResearchContext()

    agent = DesignSynthesisAgent(SimpleNamespace())
    agent.web_research_service = SimpleNamespace(
        aresearch_if_needed=fake_aresearch_if_needed
    )
    result = await agent.arun("Make a 10 mm bracket.")

    assert result.parameters.parameters["WIDTH"].value == 10
    assert len(llm.prompts) == 1
    assert "Make a 10 mm bracket." in llm.prompts[0]


async def test_design_synthesis_service_aexecute_delegates_to_async_agent() -> None:
    expected = _minimal_design_synthesis()
    service = DesignSynthesisService(SimpleNamespace())
    fake_agent = FakeDesignSynthesisAgent(expected)
    service.agent = fake_agent

    result = await service.aexecute("Make a 10 mm bracket.")

    assert result is expected
    assert fake_agent.calls[0]["user_prompt"] == "Make a 10 mm bracket."
