from __future__ import annotations

from cadpilotv3.config.settings import AppSettings
from cadpilotv3.llm import AgentName, get_llm_factory
from cadpilotv3.schemas.intent_spec import IntentSpec
from cadpilotv3.services.web_research_service import WebResearchContext, WebResearchService
from cadpilotv3.shared import ainvoke_pydantic, invoke_pydantic, load_prompt_text


class IntentSpecAgent:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.llm_factory = get_llm_factory()
        self.web_research_service = WebResearchService(settings)

    def run(self, user_prompt: str) -> IntentSpec:
        llm = self.llm_factory.get_for_agent(AgentName.INTENT_SPEC)
        prompt = self._build_prompt(
            user_prompt=user_prompt,
            research_context=self.web_research_service.research_if_needed(user_prompt),
        )

        return invoke_pydantic(
            llm,
            prompt,
            IntentSpec,
            agent_name=AgentName.INTENT_SPEC.value,
        )

    async def arun(self, user_prompt: str) -> IntentSpec:
        llm = self.llm_factory.get_for_agent(AgentName.INTENT_SPEC)
        prompt = self._build_prompt(
            user_prompt=user_prompt,
            research_context=await self.web_research_service.aresearch_if_needed(user_prompt),
        )

        return await ainvoke_pydantic(
            llm,
            prompt,
            IntentSpec,
            agent_name=AgentName.INTENT_SPEC.value,
        )

    def _build_prompt(
        self,
        *,
        user_prompt: str,
        research_context: WebResearchContext,
    ) -> str:
        system_prompt = load_prompt_text(self.settings, "intent_spec_agent.md")
        few_shot_prompt = load_prompt_text(self.settings, "intent_spec_examples.md")

        return "\n\n".join(
            [
                system_prompt.strip(),
                few_shot_prompt.strip(),
                research_context.to_prompt_block(),
                f"User request:\n{user_prompt.strip()}",
            ]
        )
