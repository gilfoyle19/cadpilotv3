from __future__ import annotations

from typing import Literal

from cadpilotv3.config.settings import get_settings
from cadpilotv3.graph.pipeline_state import PipelineState


def route_critic_a(
    state: PipelineState,
) -> Literal["parameter_agent", "geometry_planner_agent"]:
    report = state["critic_a_report"]
    max_attempts = get_settings().cad_max_critic_a_attempts

    if state["critic_a_attempts"] >= max_attempts:
        state["user_facing_warnings"].extend(
            [issue.description for issue in getattr(report, "issues", [])]
        )
        return "parameter_agent"

    if report.verdict == "pass":
        return "parameter_agent"

    state["critic_a_attempts"] += 1
    return "geometry_planner_agent"


def route_validation(
    state: PipelineState,
) -> Literal["repair_agent", "critic_checkpoint_b"]:
    if state["validation"].repair_needed:
        return "repair_agent"
    return "critic_checkpoint_b"


def route_repair(
    state: PipelineState,
) -> Literal[
    "execution_validation_node",
    "geometry_planner_agent",
    "critic_checkpoint_b",
]:
    decision = state["repair_decision"]
    max_attempts = get_settings().cad_max_repair_attempts

    if state["repair_count"] >= max_attempts:
        return "critic_checkpoint_b"

    if decision.action == "patch":
        return "execution_validation_node"

    if decision.action == "replan":
        return "geometry_planner_agent"

    return "critic_checkpoint_b"


def route_critic_b(
    state: PipelineState,
) -> Literal[
    "export_summary_agent",
    "code_generation_infill_agent",
    "geometry_planner_agent",
]:
    report = state["critic_b_report"]
    max_attempts = get_settings().cad_max_critic_b_attempts

    if state["critic_b_attempts"] >= max_attempts:
        state["user_facing_warnings"].extend(
            [issue.description for issue in getattr(report, "issues", [])]
        )
        return "export_summary_agent"

    if report.routing == "export":
        return "export_summary_agent"
    if report.routing == "patch":
        state["critic_b_attempts"] += 1
        return "code_generation_infill_agent"
    if report.routing == "replan":
        state["critic_b_attempts"] += 1
        return "geometry_planner_agent"

    return "export_summary_agent"
