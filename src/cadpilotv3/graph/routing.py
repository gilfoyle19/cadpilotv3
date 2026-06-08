from __future__ import annotations

from typing import Any, Literal

from cadpilotv3.config.settings import get_settings
from cadpilotv3.graph.pipeline_state import PipelineState


def route_contract_validation(
    state: PipelineState,
) -> Literal["critic_checkpoint_b", "export_summary_agent"]:
    if should_skip_critic_b(state):
        return "export_summary_agent"
    return "critic_checkpoint_b"


def route_critic_a(
    state: PipelineState,
) -> Literal["parameter_agent", "geometry_planner_agent"]:
    report = state["critic_a_report"]
    max_attempts = get_settings().cad_max_critic_a_attempts

    if report.verdict == "pass" or report.routing == "proceed":
        return "parameter_agent"

    if state["critic_a_attempts"] >= max_attempts:
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

    if state["critic_b_attempts"] >= max_attempts:
        state["user_facing_warnings"].extend(
            [issue.description for issue in getattr(report, "issues", [])]
        )
        return "export_summary_agent"

    if report.routing == "patch":
        return "code_generation_infill_agent"
    if report.routing == "replan":
        return "geometry_planner_agent"

    return "export_summary_agent"


def should_skip_critic_b(state: PipelineState) -> bool:
    settings = get_settings()
    if not getattr(settings, "cad_enable_conditional_critic_b", False):
        return False

    if state.get("repair_count", 0) > 0:
        return False

    if state.get("user_facing_warnings"):
        return False

    validation = state.get("validation")
    if not _validation_passed_cleanly(validation):
        return False

    contract_validation = state.get("contract_validation")
    if not _contract_validation_passed_cleanly(contract_validation):
        return False

    return _is_single_part_output(state)


def _validation_passed_cleanly(validation: Any) -> bool:
    if validation is None:
        return False
    if _get_value(validation, "status") != "success":
        return False
    if _get_value(validation, "repair_needed", False):
        return False
    return bool(_get_value(validation, "geometry_valid", False))


def _contract_validation_passed_cleanly(contract_validation: Any) -> bool:
    if contract_validation is None:
        return False
    if _get_value(contract_validation, "status") != "pass":
        return False
    if _get_value(contract_validation, "passed") is not True:
        return False
    if _get_value(contract_validation, "failure_count", 0) != 0:
        return False
    return _get_value(contract_validation, "warning_count", 0) == 0


def _is_single_part_output(state: PipelineState) -> bool:
    validation = state.get("validation")
    geometry_report = _get_value(validation, "geometry_report")
    geometry_plan = state.get("geometry_plan")

    artifact_type = (
        _get_value(geometry_report, "artifact_type")
        or _get_value(geometry_plan, "artifact_type")
        or ""
    )
    if str(artifact_type).lower() == "assembly":
        return False

    part_count = _get_value(geometry_report, "part_count")
    if part_count is None:
        return True
    return int(part_count) <= 1


def _get_value(value: Any, name: str, default: Any = None) -> Any:
    if value is None:
        return default
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)
