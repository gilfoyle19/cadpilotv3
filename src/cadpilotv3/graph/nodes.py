from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from langgraph.config import get_stream_writer

from cadpilotv3.agents.execution_validation_agent import ExecutionValidationAgent
from cadpilotv3.config.settings import AppSettings
from cadpilotv3.graph.pipeline_state import PipelineState
from cadpilotv3.schemas.repair import RepairOutput
from cadpilotv3.services.cadquery_execution_sandbox_service import CadQueryExecutionSandboxService
from cadpilotv3.services.code_generation_infill_service import (
    CodeGenerationInfillService,
    CodePatchApplicationError,
)
from cadpilotv3.services.critic_checkpoint_a_service import CriticCheckpointAService
from cadpilotv3.services.critic_checkpoint_b_service import CriticCheckpointBService
from cadpilotv3.services.export_summary_service import ExportSummaryService
from cadpilotv3.services.geometry_planner_service import GeometryPlannerService
from cadpilotv3.services.intent_spec_service import IntentSpecService
from cadpilotv3.services.parameter_service import ParameterService
from cadpilotv3.services.repair_service import RepairService

logger = logging.getLogger(__name__)
CODEGEN_NODE_NAME = "code_generation_infill_agent"


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

    async def aintent_spec_agent(self, state: PipelineState) -> PipelineState:
        state["spec"] = await self.intent_spec_service.aexecute(state["user_prompt"])
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

        repair_replan_instructions = None
        repair_decision = state.get("repair_decision")
        if (
            repair_decision
            and getattr(repair_decision, "action", None) == "replan"
            and getattr(repair_decision, "replan_instructions", None)
        ):
            repair_replan_instructions = repair_decision.replan_instructions

        state["geometry_plan"] = self.geometry_planner_service.execute(
            spec=state["spec"],
            critique=critique,
            critic_b_replan_instructions=critic_b_replan_instructions,
            repair_replan_instructions=repair_replan_instructions,
        )

        if repair_replan_instructions is not None:
            state["repair_decision"] = None

        return state

    async def ageometry_planner_agent(self, state: PipelineState) -> PipelineState:
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

        repair_replan_instructions = None
        repair_decision = state.get("repair_decision")
        if (
            repair_decision
            and getattr(repair_decision, "action", None) == "replan"
            and getattr(repair_decision, "replan_instructions", None)
        ):
            repair_replan_instructions = repair_decision.replan_instructions

        state["geometry_plan"] = await self.geometry_planner_service.aexecute(
            spec=state["spec"],
            critique=critique,
            critic_b_replan_instructions=critic_b_replan_instructions,
            repair_replan_instructions=repair_replan_instructions,
        )

        if repair_replan_instructions is not None:
            state["repair_decision"] = None

        return state

    def critic_checkpoint_a(self, state: PipelineState) -> PipelineState:
        state["critic_a_report"] = self.critic_checkpoint_a_service.execute(
            user_prompt=state["user_prompt"],
            spec=state["spec"],
            geometry_plan=state["geometry_plan"],
            critic_attempt_count=state["critic_a_attempts"],
        )

        report = state["critic_a_report"]
        if (
            getattr(report, "verdict", None) != "pass"
            and getattr(report, "routing", None) == "replan"
        ):
            state["critic_a_attempts"] += 1

        return state

    async def acritic_checkpoint_a(self, state: PipelineState) -> PipelineState:
        state["critic_a_report"] = await self.critic_checkpoint_a_service.aexecute(
            user_prompt=state["user_prompt"],
            spec=state["spec"],
            geometry_plan=state["geometry_plan"],
            critic_attempt_count=state["critic_a_attempts"],
        )

        report = state["critic_a_report"]
        if (
            getattr(report, "verdict", None) != "pass"
            and getattr(report, "routing", None) == "replan"
        ):
            state["critic_a_attempts"] += 1

        return state

    def parameter_agent(self, state: PipelineState) -> PipelineState:
        state["parameters"] = self.parameter_service.execute(
            user_prompt=state["user_prompt"],
            spec=state["spec"],
            geometry_plan=state["geometry_plan"],
            critic_a_report=state.get("critic_a_report"),
        )
        return state

    async def aparameter_agent(self, state: PipelineState) -> PipelineState:
        state["parameters"] = await self.parameter_service.aexecute(
            user_prompt=state["user_prompt"],
            spec=state["spec"],
            geometry_plan=state["geometry_plan"],
            critic_a_report=state.get("critic_a_report"),
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
            current_script=state.get("script")
            if critic_feedback or state.get("repair_decision")
            else None,
        )

        state["script"] = implemented_script

        return state

    async def acode_generation_infill_agent(self, state: PipelineState) -> PipelineState:
        critic_feedback = None
        critic_b_report = state.get("critic_b_report")
        if (
            critic_b_report
            and getattr(critic_b_report, "routing", None) == "patch"
            and getattr(critic_b_report, "patch_instructions", None)
        ):
            critic_feedback = critic_b_report.patch_instructions

        writer = _get_optional_stream_writer()
        async for code_event in self.code_generation_infill_service.astream_script(
            spec=state["spec"],
            geometry_plan=state["geometry_plan"],
            parameters=state["parameters"],
            repair_context=state["repair_decision"],
            critic_feedback=critic_feedback,
            current_script=state.get("script")
            if critic_feedback or state.get("repair_decision")
            else None,
        ):
            if writer is not None:
                writer(
                    {
                        "node_name": CODEGEN_NODE_NAME,
                        "event_type": code_event.event_type,
                        "attempt_number": code_event.attempt_number,
                        "payload": code_event.payload,
                    }
                )

            if code_event.event_type == "code_generation_complete":
                state["script"] = code_event.payload["script"]

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

    async def aexecution_validation_node(self, state: PipelineState) -> PipelineState:
        artifacts = await self.sandbox_service.aexecute(state["script"])
        state["validation"] = await self.execution_validation_llm_agent.arun(artifacts)

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
            repair_history=state.get("repair_history", []),
        )

        state["repair_decision"] = decision

        patch_application_error = None
        if decision.action == "patch":
            try:
                state["script"] = self.code_generation_infill_service.apply_patch(
                    current_script=state["script"],
                    affected_function=decision.affected_function,
                    patched_code=decision.patched_code,
                )
            except CodePatchApplicationError as exc:
                state["repair_decision"] = RepairOutput(
                    action="regenerate",
                    root_cause=str(exc),
                    fix_description=(
                        "Patch replacement failed, so regenerate the complete "
                        "script using the current script and validation error."
                    ),
                    confidence="medium",
                )
                patch_application_error = str(exc)

        self._append_repair_history(
            state,
            decision=state["repair_decision"],
            patch_application_error=patch_application_error,
        )
        state["repair_count"] += 1

        return state

    async def arepair_agent(self, state: PipelineState) -> PipelineState:
        decision = await self.repair_service.aexecute(
            script=state["script"],
            geometry_plan=state["geometry_plan"],
            parameters=state["parameters"],
            validation=state["validation"],
            repair_attempt_count=state["repair_count"],
            repair_history=state.get("repair_history", []),
        )

        state["repair_decision"] = decision

        patch_application_error = None
        if decision.action == "patch":
            try:
                state["script"] = self.code_generation_infill_service.apply_patch(
                    current_script=state["script"],
                    affected_function=decision.affected_function,
                    patched_code=decision.patched_code,
                )
            except CodePatchApplicationError as exc:
                state["repair_decision"] = RepairOutput(
                    action="regenerate",
                    root_cause=str(exc),
                    fix_description=(
                        "Patch replacement failed, so regenerate the complete "
                        "script using the current script and validation error."
                    ),
                    confidence="medium",
                )
                patch_application_error = str(exc)

        self._append_repair_history(
            state,
            decision=state["repair_decision"],
            patch_application_error=patch_application_error,
        )
        state["repair_count"] += 1

        return state

    def _append_repair_history(
        self,
        state: PipelineState,
        *,
        decision: RepairOutput,
        patch_application_error: str | None = None,
    ) -> None:
        validation = state["validation"]
        history = list(state.get("repair_history", []) or [])
        entry = {
            "attempt_index": state["repair_count"],
            "validation_error_class": getattr(validation, "error_class", None),
            "validation_error_summary": getattr(validation, "error_summary", None),
            "action": decision.action,
            "root_cause": decision.root_cause,
            "fix_description": decision.fix_description,
            "affected_function": decision.affected_function,
            "cannot_patch_reason": decision.cannot_patch_reason,
            "replan_instructions": decision.replan_instructions,
            "patch_application_error": patch_application_error,
        }
        state["repair_history"] = [
            {key: value for key, value in item.items() if _has_repair_history_value(value)}
            for item in [*history, entry]
        ]

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

        if getattr(state["critic_b_report"], "routing", None) in {"patch", "replan"}:
            state["critic_b_attempts"] += 1

        return state

    async def acritic_checkpoint_b(self, state: PipelineState) -> PipelineState:
        state["critic_b_report"] = await self.critic_checkpoint_b_service.aexecute(
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

        if getattr(state["critic_b_report"], "routing", None) in {"patch", "replan"}:
            state["critic_b_attempts"] += 1

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

    async def aexport_summary_agent(self, state: PipelineState) -> PipelineState:
        result = await self.export_summary_service.aexecute(
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


def _get_optional_stream_writer() -> Callable[[Any], None] | None:
    try:
        return get_stream_writer()
    except RuntimeError:
        return None


def _has_repair_history_value(value: Any) -> bool:
    return value is not None and value != "" and value != []
