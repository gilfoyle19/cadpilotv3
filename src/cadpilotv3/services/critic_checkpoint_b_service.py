from __future__ import annotations

import logging

from cadpilotv3.agents.critic_checkpoint_b_agent import CriticCheckpointBAgent
from cadpilotv3.config.settings import AppSettings


from cadpilotv3.schemas.intent_spec import IntentSpec
from cadpilotv3.schemas.critic import CriticReport
from cadpilotv3.schemas.validation import ValidationReport
from cadpilotv3.schemas.critic import CriticBReport

logger = logging.getLogger(__name__)


class CriticCheckpointBService:
    def __init__(self, settings: AppSettings) -> None:
        self.agent = CriticCheckpointBAgent(settings)

    def execute(
        self,
        user_prompt: str,
        spec: IntentSpec,
        validation: ValidationReport,
        critic_a_report: CriticReport,
        repair_count: int,
    ) -> CriticBReport:
        logger.info(
            "Running critic_checkpoint_b",
            extra={"repair_count": repair_count},
        )

        report = self.agent.run(
            user_prompt=user_prompt,
            spec=spec,
            validation=validation,
            critic_a_report=critic_a_report,
            repair_count=repair_count,
        )

        logger.info(
            "Critic Checkpoint B completed",
            extra={
                "routing": report.routing,
                "score": getattr(report, "overall_fidelity_score", None),
            },
        )

        return report