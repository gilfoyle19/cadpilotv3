from types import SimpleNamespace

from cadpilotv3.agents.parameter_agent import ParameterAgent
from cadpilotv3.schemas.geometry_plan import GeometryPlan
from cadpilotv3.schemas.intent_spec import IntentSpec
from cadpilotv3.schemas.parameters import ParameterSchema
from cadpilotv3.services.parameter_service import ParameterService


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
