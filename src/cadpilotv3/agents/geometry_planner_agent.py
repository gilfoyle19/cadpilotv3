from __future__ import annotations

from cadpilotv3.config.settings import AppSettings
from cadpilotv3.llm import AgentName, get_llm_factory
from cadpilotv3.schemas.critic import CriticReport
from cadpilotv3.schemas.geometry_plan import GeometryPlan
from cadpilotv3.schemas.intent_spec import IntentSpec
from cadpilotv3.shared import ainvoke_pydantic, invoke_pydantic, load_prompt_text


class GeometryPlannerAgent:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.llm_factory = get_llm_factory()

    def run(
        self,
        spec: IntentSpec,
        critique: CriticReport | None = None,
        critic_b_replan_instructions: str | None = None,
        repair_replan_instructions: str | None = None,
    ) -> GeometryPlan:
        llm = self.llm_factory.get_for_agent(AgentName.GEOMETRY_PLANNER)
        prompt = self._build_prompt(
            spec=spec,
            critique=critique,
            critic_b_replan_instructions=critic_b_replan_instructions,
            repair_replan_instructions=repair_replan_instructions,
        )

        return invoke_pydantic(
            llm,
            prompt,
            GeometryPlan,
            agent_name=AgentName.GEOMETRY_PLANNER.value,
        )

    async def arun(
        self,
        spec: IntentSpec,
        critique: CriticReport | None = None,
        critic_b_replan_instructions: str | None = None,
        repair_replan_instructions: str | None = None,
    ) -> GeometryPlan:
        llm = self.llm_factory.get_for_agent(AgentName.GEOMETRY_PLANNER)
        prompt = self._build_prompt(
            spec=spec,
            critique=critique,
            critic_b_replan_instructions=critic_b_replan_instructions,
            repair_replan_instructions=repair_replan_instructions,
        )

        return await ainvoke_pydantic(
            llm,
            prompt,
            GeometryPlan,
            agent_name=AgentName.GEOMETRY_PLANNER.value,
        )

    def _build_prompt(
        self,
        *,
        spec: IntentSpec,
        critique: CriticReport | None,
        critic_b_replan_instructions: str | None,
        repair_replan_instructions: str | None,
    ) -> str:
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

        if critic_b_replan_instructions:
            prompt_sections.extend(
                [
                    "Critic Checkpoint B replan instructions:",
                    critic_b_replan_instructions.strip(),
                    (
                        "This is a final-output replan. Address these semantic "
                        "fidelity issues explicitly in replan_changes."
                    ),
                ]
            )

        if repair_replan_instructions:
            prompt_sections.extend(
                [
                    "Repair agent replan instructions:",
                    repair_replan_instructions.strip(),
                    (
                        "This replan follows an execution or geometry validation "
                        "failure. Address the repair root cause explicitly and "
                        "avoid recreating the same implementation failure."
                    ),
                ]
            )

        return "\n\n".join(prompt_sections)
