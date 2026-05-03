from __future__ import annotations

from cadpilotv3.config.settings import AppSettings
from cadpilotv3.llm import AgentName, get_llm_factory
from cadpilotv3.shared import invoke_pydantic, load_prompt_text

# Keep these imports exactly from your existing schema module paths.
from cadpilotv3.schemas.intent_spec import IntentSpec
from cadpilotv3.schemas.geometry_plan import GeometryPlan
from cadpilotv3.schemas.critic import CriticReport


class GeometryPlannerAgent:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.llm_factory = get_llm_factory(settings)

    def run(
        self,
        spec: IntentSpec,
        critique: CriticReport | None = None,
    ) -> GeometryPlan:
        llm = self.llm_factory.get_for_agent(AgentName.GEOMETRY_PLANNER)

        system_prompt = load_prompt_text(self.settings, "geometry_planner_agent.md")
        few_shot_prompt = load_prompt_text(
            self.settings,
            "geometry_planner_examples.md",
        )

        prompt_sections = [
            system_prompt.strip(),
            few_shot_prompt.strip(),
            "Structured spec:",
            spec.model_dump_json(indent=2),
        ]

        if critique is not None:
            prompt_sections.extend(
                [
                    "Critic Checkpoint A critique:",
                    critique.model_dump_json(indent=2),
                    "This is a replan. Address every flagged issue explicitly.",
                ]
            )

        prompt = "\n\n".join(prompt_sections)

        return invoke_pydantic(llm, prompt, GeometryPlan)