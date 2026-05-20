from __future__ import annotations

import logging

from cadpilotv3.agents.critic_checkpoint_b_agent import CriticCheckpointBAgent
from cadpilotv3.config.settings import AppSettings
from cadpilotv3.schemas.contract_validation import ContractValidationReport
from cadpilotv3.schemas.critic import CriticBReport, CriticReport
from cadpilotv3.schemas.geometry_plan import GeometryPlan
from cadpilotv3.schemas.intent_spec import IntentSpec
from cadpilotv3.schemas.parameters import ParameterSchema
from cadpilotv3.schemas.validation import ValidationReport

logger = logging.getLogger(__name__)


class CriticCheckpointBService:
    def __init__(self, settings: AppSettings) -> None:
        self.agent = CriticCheckpointBAgent(settings)

    def execute(
        self,
        user_prompt: str,
        spec: IntentSpec,
        geometry_plan: GeometryPlan,
        parameters: ParameterSchema,
        validation: ValidationReport,
        contract_validation: ContractValidationReport | None,
        critic_a_report: CriticReport,
        repair_count: int,
    ) -> CriticBReport:
        logger.info(
            "Running critic_checkpoint_b",
            extra={
                "repair_count": repair_count,
                "contract_validation_status": getattr(
                    contract_validation,
                    "status",
                    None,
                ),
            },
        )

        report = self.agent.run(
            user_prompt=user_prompt,
            spec=spec,
            geometry_plan=geometry_plan,
            parameters=parameters,
            validation=validation,
            contract_validation=contract_validation,
            critic_a_report=critic_a_report,
            repair_count=repair_count,
        )
        self._log_report_completed(report)

        return report

    async def aexecute(
        self,
        user_prompt: str,
        spec: IntentSpec,
        geometry_plan: GeometryPlan,
        parameters: ParameterSchema,
        validation: ValidationReport,
        contract_validation: ContractValidationReport | None,
        critic_a_report: CriticReport,
        repair_count: int,
    ) -> CriticBReport:
        logger.info(
            "Running critic_checkpoint_b",
            extra={
                "repair_count": repair_count,
                "contract_validation_status": getattr(
                    contract_validation,
                    "status",
                    None,
                ),
            },
        )

        report = await self.agent.arun(
            user_prompt=user_prompt,
            spec=spec,
            geometry_plan=geometry_plan,
            parameters=parameters,
            validation=validation,
            contract_validation=contract_validation,
            critic_a_report=critic_a_report,
            repair_count=repair_count,
        )
        self._log_report_completed(report)

        return report

    def _log_report_completed(self, report: CriticBReport) -> None:
        logger.info(
            "Critic Checkpoint B completed",
            extra={
                "routing": report.routing,
                "score": getattr(report, "overall_fidelity_score", None),
            },
        )
