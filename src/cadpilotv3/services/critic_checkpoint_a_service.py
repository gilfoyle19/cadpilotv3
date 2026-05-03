from __future__ import annotations

import logging

from cadpilotv3.agents.critic_checkpoint_a_agent import CriticCheckpointAAgent
from cadpilotv3.config.settings import AppSettings

# Keep these imports exactly from your existing schema module paths.
from cadpilotv3.schemas.intent_spec import IntentSpec
from cadpilotv3.schemas.geometry_plan import GeometryPlan
from cadpilotv3.schemas.critic import CriticReport

logger = logging.getLogger(__name__)


class CriticCheckpointAService:
    def __init__(self, settings: AppSettings) -> None:
        self.agent = CriticCheckpointAAgent(settings)

    def execute(
        self,
        user_prompt: str,
        spec: IntentSpec,
        geometry_plan: GeometryPlan,
    ) -> CriticReport:
        logger.info("Running critic_checkpoint_a")

        report = self.agent.run(
            user_prompt=user_prompt,
            spec=spec,
            geometry_plan=geometry_plan,
        )

        logger.info(
            "Critic Checkpoint A completed",
            extra={
                "verdict": report.verdict,
                "routing": report.routing,
                "fidelity_score": report.fidelity_score,
                "issues_count": len(report.issues),
            },
        )

        return report