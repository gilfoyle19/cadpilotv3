from __future__ import annotations

import logging

from cadpilotv3.agents.critic_checkpoint_a_agent import CriticCheckpointAAgent
from cadpilotv3.config.settings import AppSettings
from cadpilotv3.schemas.critic import CriticReport
from cadpilotv3.schemas.geometry_plan import GeometryPlan

# Keep these imports exactly from your existing schema module paths.
from cadpilotv3.schemas.intent_spec import IntentSpec

logger = logging.getLogger(__name__)


class CriticCheckpointAService:
    def __init__(self, settings: AppSettings) -> None:
        self.agent = CriticCheckpointAAgent(settings)

    def execute(
        self,
        user_prompt: str,
        spec: IntentSpec,
        geometry_plan: GeometryPlan,
        critic_attempt_count: int | None = None,
    ) -> CriticReport:
        logger.info("Running critic_checkpoint_a")

        report = self.agent.run(
            user_prompt=user_prompt,
            spec=spec,
            geometry_plan=geometry_plan,
            critic_attempt_count=critic_attempt_count,
        )
        self._log_report_completed(report)

        return report

    async def aexecute(
        self,
        user_prompt: str,
        spec: IntentSpec,
        geometry_plan: GeometryPlan,
        critic_attempt_count: int | None = None,
    ) -> CriticReport:
        logger.info("Running critic_checkpoint_a")

        report = await self.agent.arun(
            user_prompt=user_prompt,
            spec=spec,
            geometry_plan=geometry_plan,
            critic_attempt_count=critic_attempt_count,
        )
        self._log_report_completed(report)

        return report

    def _log_report_completed(self, report: CriticReport) -> None:
        logger.info(
            "Critic Checkpoint A completed",
            extra={
                "verdict": report.verdict,
                "routing": report.routing,
                "overall_fidelity_score": report.overall_fidelity_score,
                "issues_count": len(report.issues),
            },
        )
