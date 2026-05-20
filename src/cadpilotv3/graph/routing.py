from __future__ import annotations

from typing import Literal

from cadpilotv3.config.settings import get_settings
from cadpilotv3.graph.pipeline_state import PipelineState


def route_critic_a(
    state: PipelineState,
) -> Literal["parameter_agent", "geometry_planner_agent"]:
    report = state["critic_a_report"]
    max_attempts = get_settings().cad_max_critic_a_attempts

    if report.verdict == "pass" or report.routing == "proceed":
        return "parameter_agent"

    if state["critic_a_attempts"] > max_attempts:
        state["user_facing_warnings"].extend(
            [issue.description for issue in getattr(report, "issues", [])]
        )
        return "parameter_agent"

    return "geometry_planner_agent"


def route_validation(
    state: PipelineState,
) -> Literal["repair_agent", "contract_validation_node"]:
    if state["validation"].repair_needed:
        return "repair_agent"
    return "contract_validation_node"


def route_repair(
    state: PipelineState,
) -> Literal[
    "execution_validation_node",
    "code_generation_infill_agent",
    "geometry_planner_agent",
    "contract_validation_node",
]:
    decision = state["repair_decision"]
    max_attempts = get_settings().cad_max_repair_attempts

    if state["repair_count"] >= max_attempts:
        return "contract_validation_node"

    if decision.action == "patch":
        return "execution_validation_node"

    if decision.action == "regenerate":
        return "code_generation_infill_agent"

    if decision.action == "replan":
        return "geometry_planner_agent"

    return "contract_validation_node"


def route_critic_b(
    state: PipelineState,
) -> Literal[
    "export_summary_agent",
    "code_generation_infill_agent",
    "geometry_planner_agent",
]:
    report = state["critic_b_report"]
    max_attempts = get_settings().cad_max_critic_b_attempts

    if report.routing == "export":
        return "export_summary_agent"

    if state["critic_b_attempts"] > max_attempts:
        state["user_facing_warnings"].extend(
            [issue.description for issue in getattr(report, "issues", [])]
        )
        return "export_summary_agent"

    if report.routing == "patch":
        return "code_generation_infill_agent"
    if report.routing == "replan":
        return "geometry_planner_agent"

    return "export_summary_agent"
