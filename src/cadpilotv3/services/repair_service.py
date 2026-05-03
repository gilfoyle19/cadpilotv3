from __future__ import annotations

import logging

from cadpilotv3.agents.repair_agent import RepairAgent
from cadpilotv3.config.settings import AppSettings

from cadpilotv3.schemas.geometry_plan import GeometryPlan
from cadpilotv3.schemas.parameters import ParameterSchema
from cadpilotv3.schemas.validation import ValidationReport
from cadpilotv3.schemas.repair import RepairOutput

logger = logging.getLogger(__name__)


class RepairService:
    def __init__(self, settings: AppSettings) -> None:
        self.agent = RepairAgent(settings)

    def execute(
        self,
        script: str,
        geometry_plan: GeometryPlan,
        parameters: ParameterSchema,
        validation: ValidationReport,
        repair_attempt_count: int,
    ) -> RepairOutput:
        logger.info(
            "Running repair_agent",
            extra={
                "error_class": validation.error_class,
                "repair_attempt_count": repair_attempt_count,
            },
        )

        decision = self.agent.run(
            script=script,
            geometry_plan=geometry_plan,
            parameters=parameters,
            validation=validation,
            repair_attempt_count=repair_attempt_count,
        )

        logger.info(
            "Repair decision completed",
            extra={
                "action": decision.action,
                "error_class": getattr(decision, "error_class", None),
            },
        )

        return decision