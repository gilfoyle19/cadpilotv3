from __future__ import annotations

from cadpilotv3.config.settings import AppSettings
from cadpilotv3.llm import AgentName, get_llm_factory
from cadpilotv3.shared import invoke_pydantic, load_prompt_text

# Keep these imports exactly from your existing schema module paths.
from cadpilotv3.schemas.geometry_plan import GeometryPlan
from cadpilotv3.schemas.parameters import ParameterSchema


class ParameterAgent:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.llm_factory = get_llm_factory(settings)

    def run(self, geometry_plan: GeometryPlan) -> ParameterSchema:
        llm = self.llm_factory.get_for_agent(AgentName.PARAMETER)

        system_prompt = load_prompt_text(self.settings, "parameter_agent.md")
        few_shot_prompt = load_prompt_text(
            self.settings,
            "parameter_agent_examples.md",
        )

        prompt = "\n\n".join(
            [
                system_prompt.strip(),
                few_shot_prompt.strip(),
                "Geometry plan:",
                geometry_plan.model_dump_json(indent=2),
            ]
        )

        return invoke_pydantic(llm, prompt, ParameterSchema)