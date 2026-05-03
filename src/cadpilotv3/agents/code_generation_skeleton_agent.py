from __future__ import annotations

from cadpilotv3.config.settings import AppSettings
from cadpilotv3.llm import AgentName, get_llm_factory
from cadpilotv3.shared import invoke_text, load_prompt_text


from cadpilotv3.schemas.geometry_plan import GeometryPlan
from cadpilotv3.schemas.intent_spec import IntentSpec
from cadpilotv3.schemas.parameters import ParameterSchema


class CodeGenerationSkeletonAgent:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.llm_factory = get_llm_factory()

    def run(
        self,
        geometry_plan: GeometryPlan,
        parameters: ParameterSchema,
        spec: IntentSpec | None = None,
    ) -> str:
        llm = self.llm_factory.get_for_agent(AgentName.CODEGEN)

        system_prompt = load_prompt_text(
            self.settings,
            "code_generation_skeleton.md",
        )
        few_shot_prompt = load_prompt_text(
            self.settings,
            "codegen_skeleton_examples.md",
        )

        prompt_parts = [
            system_prompt.strip(),
            few_shot_prompt.strip(),
            "Geometry plan:",
            geometry_plan.model_dump_json(indent=2),
            "Parameter schema:",
            parameters.model_dump_json(indent=2),
        ]

        if spec is not None:
            prompt_parts.extend(
                [
                    "Intent spec:",
                    spec.model_dump_json(indent=2),
                ]
            )

        prompt = "\n\n".join(prompt_parts)

        return invoke_text(llm, prompt)