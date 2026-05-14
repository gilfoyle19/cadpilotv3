from __future__ import annotations

from cadpilotv3.config.settings import AppSettings
from cadpilotv3.llm import AgentName, get_llm_factory
from cadpilotv3.schemas.critic import CriticReport
from cadpilotv3.schemas.geometry_plan import GeometryPlan
from cadpilotv3.schemas.intent_spec import IntentSpec
from cadpilotv3.shared import ainvoke_pydantic, invoke_pydantic, load_prompt_text


class CriticCheckpointAAgent:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.llm_factory = get_llm_factory()

    def run(
        self,
        user_prompt: str,
        spec: IntentSpec,
        geometry_plan: GeometryPlan,
        critic_attempt_count: int | None = None,
    ) -> CriticReport:
        llm = self.llm_factory.get_for_agent(AgentName.CRITIC_A)
        prompt = self._build_prompt(
            user_prompt=user_prompt,
            spec=spec,
            geometry_plan=geometry_plan,
            critic_attempt_count=critic_attempt_count,
        )

        return invoke_pydantic(
            llm,
            prompt,
            CriticReport,
            agent_name=AgentName.CRITIC_A.value,
            trace_metadata={"critic_attempt_count": critic_attempt_count},
        )

    async def arun(
        self,
        user_prompt: str,
        spec: IntentSpec,
        geometry_plan: GeometryPlan,
        critic_attempt_count: int | None = None,
    ) -> CriticReport:
        llm = self.llm_factory.get_for_agent(AgentName.CRITIC_A)
        prompt = self._build_prompt(
            user_prompt=user_prompt,
            spec=spec,
            geometry_plan=geometry_plan,
            critic_attempt_count=critic_attempt_count,
        )

        return await ainvoke_pydantic(
            llm,
            prompt,
            CriticReport,
            agent_name=AgentName.CRITIC_A.value,
            trace_metadata={"critic_attempt_count": critic_attempt_count},
        )

    def _build_prompt(
        self,
        *,
        user_prompt: str,
        spec: IntentSpec,
        geometry_plan: GeometryPlan,
        critic_attempt_count: int | None,
    ) -> str:
        system_prompt = load_prompt_text(self.settings, "critic_checkpoint_a.md")
        few_shot_prompt = load_prompt_text(
            self.settings,
            "critic_a_examples.md",
        )

        prompt_parts = [
            system_prompt.strip(),
            few_shot_prompt.strip(),
            "Original user prompt:",
            user_prompt.strip(),
            "Structured spec:",
            spec.model_dump_json(indent=2),
            "Geometry plan:",
            geometry_plan.model_dump_json(indent=2),
        ]

        if critic_attempt_count is not None:
            prompt_parts.extend(
                [
                    "Critic attempt count:",
                    str(critic_attempt_count),
                ]
            )

        return "\n\n".join(prompt_parts)
