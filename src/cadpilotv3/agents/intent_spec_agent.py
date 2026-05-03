from __future__ import annotations

from cadpilotv3.config.settings import AppSettings
from cadpilotv3.llm import AgentName, get_llm_factory
from cadpilotv3.schemas.intent_spec import IntentSpec
from cadpilotv3.shared import invoke_pydantic, load_prompt_text


class IntentSpecAgent:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.llm_factory = get_llm_factory(settings)

    def run(self, user_prompt: str) -> IntentSpec:
        llm = self.llm_factory.get_for_agent(AgentName.INTENT_SPEC)

        system_prompt = load_prompt_text(self.settings, "intent_spec_agent.md")
        few_shot_prompt = load_prompt_text(self.settings, "intent_spec_examples.md")

        prompt = "\n\n".join(
            [
                system_prompt.strip(),
                few_shot_prompt.strip(),
                f"User request:\n{user_prompt.strip()}",
            ]
        )

        return invoke_pydantic(llm, prompt, IntentSpec)