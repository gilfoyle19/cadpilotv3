from __future__ import annotations

import logging

from cadpilotv3.agents.code_generation_infill_agent import (
    CodeGenerationInfillAgent,
)
from cadpilotv3.config.settings import AppSettings


from cadpilotv3.schemas.geometry_plan import GeometryPlan
from cadpilotv3.schemas.parameters import ParameterSchema
from cadpilotv3.schemas.repair import RepairOutput

logger = logging.getLogger(__name__)


class CodeGenerationInfillService:
    def __init__(self, settings: AppSettings) -> None:
        self.agent = CodeGenerationInfillAgent(settings)

    def execute(
        self,
        skeleton_script: str,
        geometry_plan: GeometryPlan,
        parameters: ParameterSchema,
        function_name: str,
        repair_context: RepairOutput | None = None,
    ) -> str:
        logger.info(
            "Running code_generation_agent_stage_b",
            extra={"function_name": function_name},
        )

        implemented_function = self.agent.run(
            skeleton_script=skeleton_script,
            geometry_plan=geometry_plan,
            parameters=parameters,
            function_name=function_name,
            repair_context=repair_context,
        )

        logger.info(
            "Implemented CadQuery function",
            extra={
                "function_name": function_name,
                "output_length_chars": len(implemented_function),
            },
        )

        return implemented_function