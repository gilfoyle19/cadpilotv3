from __future__ import annotations

import logging

from cadpilotv3.agents.execution_validation_agent import ExecutionValidationAgent
from cadpilotv3.config.settings import AppSettings
from cadpilotv3.graph.pipeline_state import PipelineState
from cadpilotv3.services.cadquery_execution_sandbox_service import CadQueryExecutionSandboxService
from cadpilotv3.services.code_generation_infill_service import CodeGenerationInfillService
from cadpilotv3.services.critic_checkpoint_a_service import CriticCheckpointAService
from cadpilotv3.services.critic_checkpoint_b_service import CriticCheckpointBService
from cadpilotv3.services.export_summary_service import ExportSummaryService
from cadpilotv3.services.geometry_planner_service import GeometryPlannerService
from cadpilotv3.services.intent_spec_service import IntentSpecService
from cadpilotv3.services.parameter_service import ParameterService
from cadpilotv3.services.repair_service import RepairService

logger = logging.getLogger(__name__)


class PipelineNodes:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings

        self.intent_spec_service = IntentSpecService(settings)
        self.geometry_planner_service = GeometryPlannerService(settings)
        self.critic_checkpoint_a_service = CriticCheckpointAService(settings)
        self.parameter_service = ParameterService(settings)

        self.code_generation_infill_service = CodeGenerationInfillService(settings)

        self.sandbox_service = CadQueryExecutionSandboxService()
        self.execution_validation_llm_agent = ExecutionValidationAgent(settings)

        self.repair_service = RepairService(settings)
        self.critic_checkpoint_b_service = CriticCheckpointBService(settings)
        self.export_summary_service = ExportSummaryService(settings)

    def intent_spec_agent(self, state: PipelineState) -> PipelineState:
        state["spec"] = self.intent_spec_service.execute(state["user_prompt"])
        return state

    def geometry_planner_agent(self, state: PipelineState) -> PipelineState:
        critique = None
        if (
            state.get("critic_a_report")
            and getattr(state["critic_a_report"], "verdict", None) == "fail"
        ):
            critique = state["critic_a_report"]

        critic_b_replan_instructions = None
        critic_b_report = state.get("critic_b_report")
        if (
            critic_b_report
            and getattr(critic_b_report, "routing", None) == "replan"
            and getattr(critic_b_report, "replan_instructions", None)
        ):
            critic_b_replan_instructions = critic_b_report.replan_instructions

        state["geometry_plan"] = self.geometry_planner_service.execute(
            spec=state["spec"],
            critique=critique,
            critic_b_replan_instructions=critic_b_replan_instructions,
        )
        return state

    def critic_checkpoint_a(self, state: PipelineState) -> PipelineState:
        state["critic_a_report"] = self.critic_checkpoint_a_service.execute(
            user_prompt=state["user_prompt"],
            spec=state["spec"],
            geometry_plan=state["geometry_plan"],
            critic_attempt_count=state["critic_a_attempts"],
        )
        return state

    def parameter_agent(self, state: PipelineState) -> PipelineState:
        state["parameters"] = self.parameter_service.execute(
            geometry_plan=state["geometry_plan"],
        )
        return state

    def code_generation_infill_agent(self, state: PipelineState) -> PipelineState:
        critic_feedback = None
        critic_b_report = state.get("critic_b_report")
        if (
            critic_b_report
            and getattr(critic_b_report, "routing", None) == "patch"
            and getattr(critic_b_report, "patch_instructions", None)
        ):
            critic_feedback = critic_b_report.patch_instructions

        implemented_script = self.code_generation_infill_service.execute_script(
            spec=state["spec"],
            geometry_plan=state["geometry_plan"],
            parameters=state["parameters"],
            repair_context=state["repair_decision"],
            critic_feedback=critic_feedback,
            current_script=state.get("script") if critic_feedback else None,
        )

        state["script"] = implemented_script

        return state

    def execution_validation_node(self, state: PipelineState) -> PipelineState:
        artifacts = self.sandbox_service.execute(state["script"])
        state["validation"] = self.execution_validation_llm_agent.run(artifacts)

        if state["validation"].status == "success":
            state["final_geometry"] = {
                "workspace_dir": artifacts.workspace_dir,
                "result_object_name": artifacts.result_object_name,
            }
            state["repair_decision"] = None
        else:
            state["final_geometry"] = None

        return state

    def repair_agent(self, state: PipelineState) -> PipelineState:
        decision = self.repair_service.execute(
            script=state["script"],
            geometry_plan=state["geometry_plan"],
            parameters=state["parameters"],
            validation=state["validation"],
            repair_attempt_count=state["repair_count"],
        )

        state["repair_decision"] = decision

        if decision.action == "patch":
            state["script"] = self.code_generation_infill_service.apply_patch(
                current_script=state["script"],
                affected_function=decision.affected_function,
                patched_code=decision.patched_code,
            )
            state["repair_count"] += 1

        return state

    def critic_checkpoint_b(self, state: PipelineState) -> PipelineState:
        state["critic_b_report"] = self.critic_checkpoint_b_service.execute(
            user_prompt=state["user_prompt"],
            spec=state["spec"],
            geometry_plan=state["geometry_plan"],
            parameters=state["parameters"],
            validation=state["validation"],
            critic_a_report=state["critic_a_report"],
            repair_count=state["repair_count"],
        )
        state["user_facing_warnings"] = list(
            getattr(state["critic_b_report"], "user_facing_warnings", []) or []
        )
        return state

    def export_summary_agent(self, state: PipelineState) -> PipelineState:
        result = self.export_summary_service.execute(
            geometry_object=state["final_geometry"],
            user_prompt=state["user_prompt"],
            spec=state["spec"],
            parameters=state["parameters"],
            validation=state["validation"],
            critic_b_report=state["critic_b_report"],
        )

        state["export_files"] = result.export_files
        state["assembly_report_markdown"] = result.assembly_report_markdown
        state["user_facing_warnings"] = result.user_facing_warnings
        return state
