from __future__ import annotations

from cadpilotv3.config.settings import AppSettings
from cadpilotv3.llm import AgentName, get_llm_factory
from cadpilotv3.schemas.geometry_plan import GeometryPlan
from cadpilotv3.schemas.parameters import ParameterSchema
from cadpilotv3.schemas.repair import RepairOutput
from cadpilotv3.schemas.validation import ValidationReport
from cadpilotv3.shared import invoke_pydantic, load_prompt_text


class RepairAgent:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.llm_factory = get_llm_factory()

    def run(
        self,
        script: str,
        geometry_plan: GeometryPlan,
        parameters: ParameterSchema,
        validation: ValidationReport,
        repair_attempt_count: int,
    ) -> RepairOutput:
        llm = self.llm_factory.get_for_agent(AgentName.REPAIR)

        system_prompt = load_prompt_text(self.settings, "repair_agent.md")
        few_shot_prompt = load_prompt_text(
            self.settings,
            "repair_agent_examples.md",
        )

        prompt = "\n\n".join(
            [
                system_prompt.strip(),
                few_shot_prompt.strip(),
                "Current script:",
                script.strip(),
                "Geometry plan:",
                geometry_plan.model_dump_json(indent=2),
                "Parameter schema:",
                parameters.model_dump_json(indent=2),
                "Validation report:",
                validation.model_dump_json(indent=2),
                f"Repair attempt count: {repair_attempt_count}",
            ]
        )

        return invoke_pydantic(
            llm,
            prompt,
            RepairOutput,
            agent_name=AgentName.REPAIR.value,
            trace_metadata={"repair_attempt_count": repair_attempt_count},
        )
