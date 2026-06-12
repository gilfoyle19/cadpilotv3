from __future__ import annotations

import logging

from cadpilotv3.agents.design_synthesis_agent import DesignSynthesisAgent
from cadpilotv3.config.settings import AppSettings
from cadpilotv3.schemas.design_synthesis import DesignSynthesis

logger = logging.getLogger(__name__)


class DesignSynthesisService:
    def __init__(self, settings: AppSettings) -> None:
        self.agent = DesignSynthesisAgent(settings)

    def execute(self, user_prompt: str) -> DesignSynthesis:
        logger.info("Running design_synthesis_agent")

        synthesis = self.agent.run(user_prompt)
        self._log_design_synthesis_created(synthesis)

        return synthesis

    async def aexecute(self, user_prompt: str) -> DesignSynthesis:
        logger.info("Running design_synthesis_agent")

        synthesis = await self.agent.arun(user_prompt)
        self._log_design_synthesis_created(synthesis)

        return synthesis

    def _log_design_synthesis_created(self, synthesis: DesignSynthesis) -> None:
        logger.info(
            "Design synthesis created",
            extra={
                "component": synthesis.spec.component,
                "artifact_type": synthesis.geometry_plan.artifact_type,
                "parts_count": len(synthesis.geometry_plan.parts),
                "parameter_count": len(synthesis.parameters.parameters),
                "critic_verdict": synthesis.critic_a_report.verdict,
                "critic_routing": synthesis.critic_a_report.routing,
            },
        )
