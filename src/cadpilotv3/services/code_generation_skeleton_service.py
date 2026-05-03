from __future__ import annotations

import logging

from cadpilotv3.agents.code_generation_skeleton_agent import (
    CodeGenerationSkeletonAgent,
)
from cadpilotv3.config.settings import AppSettings


from cadpilotv3.schemas.geometry_plan import GeometryPlan
from cadpilotv3.schemas.parameters import ParameterSchema

logger = logging.getLogger(__name__)


class CodeGenerationSkeletonService:
    def __init__(self, settings: AppSettings) -> None:
        self.agent = CodeGenerationSkeletonAgent(settings)

    def execute(
        self,
        geometry_plan: GeometryPlan,
        parameters: ParameterSchema,
    ) -> str:
        logger.info("Running code_generation_agent_stage_a")

        skeleton_script = self.agent.run(
            geometry_plan=geometry_plan,
            parameters=parameters,
        )

        logger.info(
            "CadQuery skeleton script created",
            extra={
                "script_length_chars": len(skeleton_script),
            },
        )

        return skeleton_script