from __future__ import annotations

import logging

from cadpilotv3.agents.geometry_planner_agent import GeometryPlannerAgent
from cadpilotv3.config.settings import AppSettings

# Keep these imports exactly from your existing schema module paths.
from cadpilotv3.schemas.intent_spec import IntentSpec
from cadpilotv3.schemas.geometry_plan import GeometryPlan
from cadpilotv3.schemas.critic import CriticReport

logger = logging.getLogger(__name__)


class GeometryPlannerService:
    def __init__(self, settings: AppSettings) -> None:
        self.agent = GeometryPlannerAgent(settings)

    def execute(
        self,
        spec: IntentSpec,
        critique: CriticReport | None = None,
    ) -> GeometryPlan:
        logger.info("Running geometry_planner_agent")

        geometry_plan = self.agent.run(spec=spec, critique=critique)

        logger.info(
            "Geometry plan created",
            extra={
                "parts_count": len(geometry_plan.parts),
                "joint_definitions_count": len(geometry_plan.joint_definitions),
                "failure_risks_count": len(geometry_plan.failure_risks),
                "is_replan": critique is not None,
            },
        )

        return geometry_plan