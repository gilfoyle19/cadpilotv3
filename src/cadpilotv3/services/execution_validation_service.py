from __future__ import annotations

import logging

from cadpilotv3.agents.execution_validation_agent import ExecutionValidationAgent
from cadpilotv3.config.settings import AppSettings
from cadpilotv3.schemas.validation import ValidationReport
from cadpilotv3.services.cadquery_execution_sandbox_service import (
    CadQueryExecutionSandboxService,
)

logger = logging.getLogger(__name__)


class ExecutionValidationService:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.sandbox = CadQueryExecutionSandboxService()
        self.agent = ExecutionValidationAgent(settings)

    def execute(self, script: str) -> ValidationReport:
        logger.info("Running CadQuery execution sandbox")
        artifacts = self.sandbox.execute(script)
        self._log_sandbox_finished(artifacts)

        report = self.agent.run(artifacts)
        self._log_validation_normalized(report)

        return report

    async def aexecute(self, script: str) -> ValidationReport:
        logger.info("Running CadQuery execution sandbox")
        artifacts = await self.sandbox.aexecute(script)
        self._log_sandbox_finished(artifacts)

        report = await self.agent.arun(artifacts)
        self._log_validation_normalized(report)

        return report

    def _log_sandbox_finished(self, artifacts) -> None:
        logger.info(
            "Sandbox execution finished",
            extra={
                "syntax_ok": artifacts.syntax_ok,
                "execution_succeeded": artifacts.execution_succeeded,
                "execution_time_s": artifacts.execution_time_s,
                "error_type": artifacts.error_type,
            },
        )

    def _log_validation_normalized(self, report: ValidationReport) -> None:
        logger.info(
            "Execution validation normalized",
            extra={
                "status": report.status,
                "error_class": report.error_class,
                "geometry_valid": report.geometry_valid,
                "repair_needed": report.repair_needed,
                "repair_complexity": report.repair_complexity,
            },
        )
