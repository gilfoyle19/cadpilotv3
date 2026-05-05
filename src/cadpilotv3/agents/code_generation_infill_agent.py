from __future__ import annotations

from cadpilotv3.config.settings import AppSettings
from cadpilotv3.llm import AgentName, get_llm_factory
from cadpilotv3.schemas.geometry_plan import GeometryPlan
from cadpilotv3.schemas.intent_spec import IntentSpec
from cadpilotv3.schemas.parameters import ParameterSchema
from cadpilotv3.schemas.repair import RepairOutput
from cadpilotv3.shared import invoke_text, load_prompt_text


class CodeGenerationInfillAgent:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.llm_factory = get_llm_factory()

    def run(
        self,
        spec: IntentSpec,
        geometry_plan: GeometryPlan,
        parameters: ParameterSchema,
        repair_context: RepairOutput | None = None,
        critic_feedback: str | None = None,
        current_script: str | None = None,
        generation_feedback: str | None = None,
    ) -> str:
        llm = self.llm_factory.get_for_agent(AgentName.CODEGEN)

        system_prompt = load_prompt_text(
            self.settings,
            "code_generation_infill.md",
        )
        few_shot_prompt = load_prompt_text(
            self.settings,
            "codegen_infill_examples.md",
        )
        cadquery_cheatsheet = load_prompt_text(self.settings, "cheatsheet.md")

        prompt_parts = [
            system_prompt.strip(),
            few_shot_prompt.strip(),
            "CadQuery 2.x API reference:",
            cadquery_cheatsheet.strip(),
            "Intent spec:",
            spec.model_dump_json(indent=2),
            "Geometry plan:",
            geometry_plan.model_dump_json(indent=2),
            "Parameter schema:",
            parameters.model_dump_json(indent=2),
            (
                "Generation mode: complete script. Generate the final runnable "
                "CadQuery script directly from the inputs."
            ),
        ]

        if repair_context is not None:
            prompt_parts.extend(
                [
                    "Repair context:",
                    repair_context.model_dump_json(indent=2),
                ]
            )

        if critic_feedback:
            prompt_parts.extend(
                [
                    "Critic B semantic patch instructions:",
                    critic_feedback.strip(),
                    "Current script to revise:",
                    (current_script or "").strip(),
                    (
                        "This is a targeted regeneration. Preserve the current "
                        "geometry plan and parameter schema unless these "
                        "instructions explicitly require a local correction."
                    ),
                ]
            )

        if generation_feedback:
            prompt_parts.extend(
                [
                    "Previous generation attempt failed validation:",
                    generation_feedback.strip(),
                    (
                        "Return one complete, non-empty Python CadQuery script. "
                        "Do not return prose, an empty code fence, or a partial excerpt."
                    ),
                ]
            )

        prompt = "\n\n".join(prompt_parts)
        return invoke_text(llm, prompt)
