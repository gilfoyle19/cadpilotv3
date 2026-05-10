from types import SimpleNamespace

from cadpilotv3.agents.intent_spec_agent import IntentSpecAgent
from cadpilotv3.services.web_research_service import WebResearchContext, WebResearchService


class FakeLLM:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def invoke(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return """
{
  "component": "iphone_desk_dock",
  "component_type": "single_part",
  "dof_count": 0,
  "dof_config": null,
  "joint_types": null,
  "parts": ["dock_body", "phone_slot", "charger_clearance_cutout"],
  "output_format": "STEP",
  "units": "mm",
  "approximate_scale": "small",
  "style": "minimal_printable",
  "manufacturing_process": "FDM",
  "constraints": ["min_wall_2mm", "flat_base_required"],
  "explicit_dimensions": [],
  "explicit_constraints": [],
  "researched_dimensions": [
    "iphone 15: 147.6mm x 71.6mm x 7.8mm, source Apple technical specifications"
  ],
  "research_sources": ["https://www.apple.com/iphone-15/specs/"],
  "clarifications_needed": []
}
"""


class FakeLLMFactory:
    def __init__(self, llm: FakeLLM) -> None:
        self.llm = llm

    def get_for_agent(self, _agent_name):
        return self.llm


class FakeResearchService:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def research_if_needed(self, user_prompt: str) -> WebResearchContext:
        self.prompts.append(user_prompt)
        return WebResearchContext(
            queries=["iphone 15 dimensions official"],
            researched_dimensions=[
                "iphone 15: 147.6mm x 71.6mm x 7.8mm, source Apple technical specifications"
            ],
            sources=["https://www.apple.com/iphone-15/specs/"],
        )


def test_intent_spec_agent_injects_web_research_context(monkeypatch) -> None:
    monkeypatch.setattr(
        "cadpilotv3.agents.intent_spec_agent.load_prompt_text",
        lambda _settings, name: f"{name} prompt",
    )

    llm = FakeLLM()
    research = FakeResearchService()
    agent = IntentSpecAgent(settings=SimpleNamespace())
    agent.llm_factory = FakeLLMFactory(llm)
    agent.web_research_service = research

    spec = agent.run("Create a desk dock that fits an iPhone 15 and charger.")

    assert spec.researched_dimensions == [
        "iphone 15: 147.6mm x 71.6mm x 7.8mm, source Apple technical specifications"
    ]
    assert research.prompts == ["Create a desk dock that fits an iPhone 15 and charger."]
    assert "Web research context for real-world product interfaces:" in llm.prompts[0]
    assert "iphone 15: 147.6mm x 71.6mm x 7.8mm" in llm.prompts[0]


def test_web_research_trigger_detects_product_interfaces() -> None:
    service = WebResearchService(settings=SimpleNamespace())

    assert service.needs_research("Make a wall mount for a Raspberry Pi PCB.")
    assert service.needs_research("Create a phone stand with a USB-C charger cutout.")
    assert not service.needs_research("Make a generic 80mm by 40mm shelf bracket.")
    assert not service.needs_research(
        "Make a phone stand without web research; use placeholder dimensions."
    )
