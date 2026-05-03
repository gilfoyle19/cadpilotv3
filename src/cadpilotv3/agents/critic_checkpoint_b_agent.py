from __future__ import annotations

from cadpilotv3.config.settings import AppSettings
from cadpilotv3.llm import AgentName, get_llm_factory
from cadpilotv3.shared import invoke_pydantic, load_prompt_text


from cadpilotv3.schemas.intent_spec import IntentSpec
from cadpilotv3.schemas.critic import CriticReport
from cadpilotv3.schemas.validation import ValidationReport
from cadpilotv3.schemas.critic import CriticBReport



class CriticCheckpointBAgent:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.llm_factory = get_llm_factory()

    def run(
        self,
        user_prompt: str,
        spec: IntentSpec,
        validation: ValidationReport,
        critic_a_report: CriticReport,
        repair_count: int,
    ) -> CriticBReport:
        llm = self.llm_factory.get_for_agent(AgentName.CRITIC_B)

        system_prompt = load_prompt_text(self.settings, "critic_checkpoint_b.md")
        few_shot_prompt = load_prompt_text(
            self.settings,
            "critic_b_examples.md",
        )

        prompt = "\n\n".join(
            [
                system_prompt.strip(),
                few_shot_prompt.strip(),
                "Original user prompt:",
                user_prompt.strip(),
                "Structured spec:",
                spec.model_dump_json(indent=2),
                "Validation report:",
                validation.model_dump_json(indent=2),
                "Checkpoint A report:",
                critic_a_report.model_dump_json(indent=2),
                f"Repair history count: {repair_count}",
            ]
        )

        return invoke_pydantic(llm, prompt, CriticBReport)