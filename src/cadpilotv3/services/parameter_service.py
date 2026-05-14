from __future__ import annotations

import logging

from cadpilotv3.agents.parameter_agent import ParameterAgent
from cadpilotv3.config.settings import AppSettings
from cadpilotv3.schemas.critic import CriticReport
from cadpilotv3.schemas.geometry_plan import GeometryPlan
from cadpilotv3.schemas.intent_spec import IntentSpec
from cadpilotv3.schemas.parameters import ParameterSchema

logger = logging.getLogger(__name__)


class ParameterService:
    def __init__(self, settings: AppSettings) -> None:
        self.agent = ParameterAgent(settings)

    def execute(
        self,
        user_prompt: str,
        spec: IntentSpec,
        geometry_plan: GeometryPlan,
        critic_a_report: CriticReport | None = None,
    ) -> ParameterSchema:
        logger.info("Running parameter_agent")

        parameters = self.agent.run(
            user_prompt=user_prompt,
            spec=spec,
            geometry_plan=geometry_plan,
            critic_a_report=critic_a_report,
        )
        self._log_parameters_created(parameters)

        return parameters

    async def aexecute(
        self,
        user_prompt: str,
        spec: IntentSpec,
        geometry_plan: GeometryPlan,
        critic_a_report: CriticReport | None = None,
    ) -> ParameterSchema:
        logger.info("Running parameter_agent")

        parameters = await self.agent.arun(
            user_prompt=user_prompt,
            spec=spec,
            geometry_plan=geometry_plan,
            critic_a_report=critic_a_report,
        )
        self._log_parameters_created(parameters)

        return parameters

    def _log_parameters_created(self, parameters: ParameterSchema) -> None:
        logger.info(
            "Parameter schema created",
            extra={
                "parameter_count": len(parameters.parameters),
            },
        )
