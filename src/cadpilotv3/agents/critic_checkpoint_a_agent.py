from __future__ import annotations

from cadpilotv3.config.settings import AppSettings
from cadpilotv3.llm import AgentName, get_llm_factory
from cadpilotv3.schemas.critic import CriticReport
from cadpilotv3.schemas.geometry_plan import GeometryPlan
from cadpilotv3.schemas.intent_spec import IntentSpec
from cadpilotv3.shared import ainvoke_pydantic, invoke_pydantic, load_prompt_text
from cadpilotv3.shared.prompt_context import select_relevant_few_shot_examples


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
        selected_examples = self._select_relevant_examples(
            few_shot_prompt=few_shot_prompt,
            user_prompt=user_prompt,
            spec=spec,
            geometry_plan=geometry_plan,
        )

        prompt_parts = [
            system_prompt.strip(),
            selected_examples.strip(),
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

    def _select_relevant_examples(
        self,
        *,
        few_shot_prompt: str,
        user_prompt: str,
        spec: IntentSpec,
        geometry_plan: GeometryPlan,
        max_examples: int = 2,
    ) -> str:
        query_values: list[object] = [
            user_prompt,
            getattr(spec, "component", "") or "",
            getattr(spec, "component_type", "") or "",
            getattr(spec, "style", "") or "",
            getattr(spec, "manufacturing_process", "") or "",
            getattr(spec, "parts", []) or [],
            getattr(spec, "constraints", []) or [],
            getattr(geometry_plan, "artifact_type", "") or "",
        ]

        for part in getattr(geometry_plan, "parts", []) or []:
            query_values.extend(
                [
                    getattr(part, "name", "") or "",
                    getattr(part, "geometric_role", "") or "",
                    getattr(part, "modeling_strategy", "") or "",
                ]
            )
            for feature in getattr(part, "key_features", []) or []:
                query_values.extend(
                    [
                        getattr(feature, "feature", "") or "",
                        getattr(feature, "description", "") or "",
                    ]
                )

        return select_relevant_few_shot_examples(
            few_shot_prompt=few_shot_prompt,
            query_values=query_values,
            heading="## Selected Critic A Few-Shots",
            max_examples=max_examples,
        )
