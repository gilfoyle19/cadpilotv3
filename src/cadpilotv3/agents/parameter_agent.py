from __future__ import annotations

import re

from cadpilotv3.config.settings import AppSettings
from cadpilotv3.llm import AgentName, get_llm_factory
from cadpilotv3.schemas.critic import CriticReport
from cadpilotv3.schemas.geometry_plan import GeometryPlan
from cadpilotv3.schemas.intent_spec import IntentSpec
from cadpilotv3.schemas.parameters import ParameterSchema
from cadpilotv3.shared import ainvoke_pydantic, invoke_pydantic, load_prompt_text


class ParameterAgent:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.llm_factory = get_llm_factory()

    def run(
        self,
        user_prompt: str,
        spec: IntentSpec,
        geometry_plan: GeometryPlan,
        critic_a_report: CriticReport | None = None,
    ) -> ParameterSchema:
        llm = self.llm_factory.get_for_agent(AgentName.PARAMETER)
        prompt = self._build_prompt(
            user_prompt=user_prompt,
            spec=spec,
            geometry_plan=geometry_plan,
            critic_a_report=critic_a_report,
        )

        return invoke_pydantic(
            llm,
            prompt,
            ParameterSchema,
            agent_name=AgentName.PARAMETER.value,
        )

    async def arun(
        self,
        user_prompt: str,
        spec: IntentSpec,
        geometry_plan: GeometryPlan,
        critic_a_report: CriticReport | None = None,
    ) -> ParameterSchema:
        llm = self.llm_factory.get_for_agent(AgentName.PARAMETER)
        prompt = self._build_prompt(
            user_prompt=user_prompt,
            spec=spec,
            geometry_plan=geometry_plan,
            critic_a_report=critic_a_report,
        )

        return await ainvoke_pydantic(
            llm,
            prompt,
            ParameterSchema,
            agent_name=AgentName.PARAMETER.value,
        )

    def _build_prompt(
        self,
        *,
        user_prompt: str,
        spec: IntentSpec,
        geometry_plan: GeometryPlan,
        critic_a_report: CriticReport | None,
    ) -> str:
        system_prompt = load_prompt_text(self.settings, "parameter_agent.md")
        few_shot_prompt = load_prompt_text(
            self.settings,
            "parameter_agent_examples.md",
        )

        return "\n\n".join(
            [
                system_prompt.strip(),
                few_shot_prompt.strip(),
                "Original user prompt:",
                user_prompt.strip(),
                "Numeric facts extracted from original prompt:",
                "\n".join(self._extract_numeric_fact_sentences(user_prompt)) or "None",
                "Structured spec:",
                spec.model_dump_json(indent=2),
                "Geometry plan:",
                geometry_plan.model_dump_json(indent=2),
                "Critic A report:",
                (
                    critic_a_report.model_dump_json(indent=2)
                    if critic_a_report is not None
                    else "{}"
                ),
            ]
        )

    def _extract_numeric_fact_sentences(self, user_prompt: str) -> list[str]:
        sentences = re.split(r"(?<=[.!?])\s+", user_prompt.strip())
        return [
            sentence.strip()
            for sentence in sentences
            if sentence.strip() and re.search(r"\d", sentence)
        ]
