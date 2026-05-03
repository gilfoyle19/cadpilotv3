from __future__ import annotations

import logging

from cadpilotv3.agents.intent_spec_agent import IntentSpecAgent
from cadpilotv3.config.settings import AppSettings

logger = logging.getLogger(__name__)


class IntentSpecService:
    def __init__(self, settings: AppSettings) -> None:
        self.agent = IntentSpecAgent(settings)

    def execute(self, user_prompt: str):
        logger.info("Running intent_spec_agent")

        spec = self.agent.run(user_prompt)

        logger.info(
            "Intent specification created",
            extra={
                "component": spec.component,
                "component_type": spec.component_type,
                "dof_count": spec.dof_count,
                "parts_count": len(spec.parts),
                "clarifications_needed_count": len(spec.clarifications_needed),
            },
        )

        return spec