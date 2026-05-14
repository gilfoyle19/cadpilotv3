from __future__ import annotations

import logging

from cadpilotv3.agents.geometry_planner_agent import GeometryPlannerAgent
from cadpilotv3.config.settings import AppSettings
from cadpilotv3.schemas.critic import CriticReport
from cadpilotv3.schemas.geometry_plan import GeometryPlan
from cadpilotv3.schemas.intent_spec import IntentSpec

logger = logging.getLogger(__name__)


class GeometryPlannerService:
    def __init__(self, settings: AppSettings) -> None:
        self.agent = GeometryPlannerAgent(settings)

    def execute(
        self,
        spec: IntentSpec,
        critique: CriticReport | None = None,
        critic_b_replan_instructions: str | None = None,
        repair_replan_instructions: str | None = None,
    ) -> GeometryPlan:
        logger.info("Running geometry_planner_agent")

        geometry_plan = self.agent.run(
            spec=spec,
            critique=critique,
            critic_b_replan_instructions=critic_b_replan_instructions,
            repair_replan_instructions=repair_replan_instructions,
        )
        self._log_geometry_plan_created(
            geometry_plan=geometry_plan,
            critique=critique,
            critic_b_replan_instructions=critic_b_replan_instructions,
            repair_replan_instructions=repair_replan_instructions,
        )

        return geometry_plan

    async def aexecute(
        self,
        spec: IntentSpec,
        critique: CriticReport | None = None,
        critic_b_replan_instructions: str | None = None,
        repair_replan_instructions: str | None = None,
    ) -> GeometryPlan:
        logger.info("Running geometry_planner_agent")

        geometry_plan = await self.agent.arun(
            spec=spec,
            critique=critique,
            critic_b_replan_instructions=critic_b_replan_instructions,
            repair_replan_instructions=repair_replan_instructions,
        )
        self._log_geometry_plan_created(
            geometry_plan=geometry_plan,
            critique=critique,
            critic_b_replan_instructions=critic_b_replan_instructions,
            repair_replan_instructions=repair_replan_instructions,
        )

        return geometry_plan

    def _log_geometry_plan_created(
        self,
        *,
        geometry_plan: GeometryPlan,
        critique: CriticReport | None,
        critic_b_replan_instructions: str | None,
        repair_replan_instructions: str | None,
    ) -> None:
        logger.info(
            "Geometry plan created",
            extra={
                "parts_count": len(geometry_plan.parts),
                "joint_definitions_count": len(geometry_plan.joint_definitions),
                "failure_risks_count": len(geometry_plan.failure_risks),
                "is_replan": (
                    critique is not None
                    or critic_b_replan_instructions is not None
                    or repair_replan_instructions is not None
                ),
            },
        )
