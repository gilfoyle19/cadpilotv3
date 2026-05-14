from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

from cadpilotv3.config.settings import AppSettings
from cadpilotv3.graph.nodes import PipelineNodes
from cadpilotv3.graph.routing import (
    route_critic_a,
    route_critic_b,
    route_repair,
    route_validation,
)

PipelineStreamEventType = Literal[
    "pipeline_start",
    "node_start",
    "node_complete",
    "code_generation_start",
    "code_chunk",
    "code_generation_retry",
    "code_generation_complete",
    "code_generation_error",
    "pipeline_complete",
    "pipeline_error",
]


@dataclass(frozen=True)
class PipelineStreamEvent:
    event_type: PipelineStreamEventType
    sequence: int
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    run_id: str | None = None
    node_name: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "sequence": self.sequence,
            "timestamp": self.timestamp,
            "run_id": self.run_id,
            "node_name": self.node_name,
            "payload": _to_jsonable(self.payload),
        }


async def astream_pipeline_events(
    pipeline: Any,
    initial_state: Mapping[str, Any],
    *,
    run_id: str | None = None,
    user_prompt: str | None = None,
) -> AsyncIterator[PipelineStreamEvent]:
    sequence = 1
    yield PipelineStreamEvent(
        event_type="pipeline_start",
        sequence=sequence,
        run_id=run_id,
        payload={
            "user_prompt_preview": (user_prompt or initial_state.get("user_prompt") or "")[:200],
            "initial_state_keys": sorted(str(key) for key in initial_state.keys()),
        },
    )

    final_state: Mapping[str, Any] | None = None

    try:
        async for update in pipeline.astream(dict(initial_state), stream_mode="updates"):
            for node_name, node_state in _iter_node_updates(update):
                sequence += 1
                if isinstance(node_state, Mapping):
                    final_state = node_state
                yield PipelineStreamEvent(
                    event_type="node_complete",
                    sequence=sequence,
                    run_id=run_id,
                    node_name=node_name,
                    payload=_summarize_node_state(node_state),
                )

        sequence += 1
        yield PipelineStreamEvent(
            event_type="pipeline_complete",
            sequence=sequence,
            run_id=run_id,
            payload=_summarize_final_state(final_state),
        )
    except Exception as exc:
        sequence += 1
        yield PipelineStreamEvent(
            event_type="pipeline_error",
            sequence=sequence,
            run_id=run_id,
            payload={
                "error_class": type(exc).__name__,
                "error_message": str(exc),
            },
        )
        raise


async def astream_pipeline_with_code_events(
    settings: AppSettings,
    initial_state: Mapping[str, Any],
    *,
    run_id: str | None = None,
    user_prompt: str | None = None,
) -> AsyncIterator[PipelineStreamEvent]:
    nodes = PipelineNodes(settings)
    state = dict(initial_state)
    sequence = 1

    yield PipelineStreamEvent(
        event_type="pipeline_start",
        sequence=sequence,
        run_id=run_id,
        payload={
            "user_prompt_preview": (user_prompt or state.get("user_prompt") or "")[:200],
            "initial_state_keys": sorted(str(key) for key in state.keys()),
            "streaming_mode": "orchestrated",
        },
    )

    try:
        async for event in _run_async_node(
            nodes.aintent_spec_agent,
            state,
            node_name="intent_spec_agent",
            run_id=run_id,
            sequence=sequence,
        ):
            sequence = event.sequence
            yield event

        next_node = "geometry_planner_agent"
        while True:
            if next_node == "geometry_planner_agent":
                async for event in _run_async_node(
                    nodes.ageometry_planner_agent,
                    state,
                    node_name="geometry_planner_agent",
                    run_id=run_id,
                    sequence=sequence,
                ):
                    sequence = event.sequence
                    yield event
                next_node = "critic_checkpoint_a"
                continue

            if next_node == "critic_checkpoint_a":
                async for event in _run_async_node(
                    nodes.acritic_checkpoint_a,
                    state,
                    node_name="critic_checkpoint_a",
                    run_id=run_id,
                    sequence=sequence,
                ):
                    sequence = event.sequence
                    yield event
                next_node = route_critic_a(state)
                continue

            if next_node == "parameter_agent":
                async for event in _run_async_node(
                    nodes.aparameter_agent,
                    state,
                    node_name="parameter_agent",
                    run_id=run_id,
                    sequence=sequence,
                ):
                    sequence = event.sequence
                    yield event
                next_node = "code_generation_infill_agent"
                continue

            if next_node == "code_generation_infill_agent":
                async for event in _stream_codegen_node(
                    nodes,
                    state,
                    run_id=run_id,
                    sequence=sequence,
                ):
                    sequence = event.sequence
                    yield event
                next_node = "execution_validation_node"
                continue

            if next_node == "execution_validation_node":
                async for event in _run_async_node(
                    nodes.aexecution_validation_node,
                    state,
                    node_name="execution_validation_node",
                    run_id=run_id,
                    sequence=sequence,
                ):
                    sequence = event.sequence
                    yield event
                next_node = route_validation(state)
                continue

            if next_node == "repair_agent":
                async for event in _run_async_node(
                    nodes.arepair_agent,
                    state,
                    node_name="repair_agent",
                    run_id=run_id,
                    sequence=sequence,
                ):
                    sequence = event.sequence
                    yield event
                next_node = route_repair(state)
                continue

            if next_node == "critic_checkpoint_b":
                async for event in _run_async_node(
                    nodes.acritic_checkpoint_b,
                    state,
                    node_name="critic_checkpoint_b",
                    run_id=run_id,
                    sequence=sequence,
                ):
                    sequence = event.sequence
                    yield event
                next_node = route_critic_b(state)
                continue

            if next_node == "export_summary_agent":
                async for event in _run_async_node(
                    nodes.aexport_summary_agent,
                    state,
                    node_name="export_summary_agent",
                    run_id=run_id,
                    sequence=sequence,
                ):
                    sequence = event.sequence
                    yield event
                break

            raise RuntimeError(f"Unsupported streaming pipeline node '{next_node}'")

        sequence += 1
        yield PipelineStreamEvent(
            event_type="pipeline_complete",
            sequence=sequence,
            run_id=run_id,
            payload=_summarize_final_state(state),
        )
    except Exception as exc:
        sequence += 1
        yield PipelineStreamEvent(
            event_type="pipeline_error",
            sequence=sequence,
            run_id=run_id,
            payload={
                "error_class": type(exc).__name__,
                "error_message": str(exc),
            },
        )
        raise


async def _run_async_node(
    node_callable: Any,
    state: dict[str, Any],
    *,
    node_name: str,
    run_id: str | None,
    sequence: int,
) -> AsyncIterator[PipelineStreamEvent]:
    sequence += 1
    yield PipelineStreamEvent(
        event_type="node_start",
        sequence=sequence,
        run_id=run_id,
        node_name=node_name,
        payload={"summary": _summarize_state(state)},
    )

    updated_state = await node_callable(state)
    state.update(updated_state)

    sequence += 1
    yield PipelineStreamEvent(
        event_type="node_complete",
        sequence=sequence,
        run_id=run_id,
        node_name=node_name,
        payload=_summarize_node_state(state),
    )


async def _stream_codegen_node(
    nodes: PipelineNodes,
    state: dict[str, Any],
    *,
    run_id: str | None,
    sequence: int,
) -> AsyncIterator[PipelineStreamEvent]:
    node_name = "code_generation_infill_agent"
    sequence += 1
    yield PipelineStreamEvent(
        event_type="node_start",
        sequence=sequence,
        run_id=run_id,
        node_name=node_name,
        payload={"summary": _summarize_state(state)},
    )

    critic_feedback = None
    critic_b_report = state.get("critic_b_report")
    if (
        critic_b_report
        and getattr(critic_b_report, "routing", None) == "patch"
        and getattr(critic_b_report, "patch_instructions", None)
    ):
        critic_feedback = critic_b_report.patch_instructions

    async for code_event in nodes.code_generation_infill_service.astream_script(
        spec=state["spec"],
        geometry_plan=state["geometry_plan"],
        parameters=state["parameters"],
        repair_context=state["repair_decision"],
        critic_feedback=critic_feedback,
        current_script=state.get("script")
        if critic_feedback or state.get("repair_decision")
        else None,
    ):
        sequence += 1
        payload = {
            **code_event.payload,
            "attempt_number": code_event.attempt_number,
        }
        yield PipelineStreamEvent(
            event_type=code_event.event_type,
            sequence=sequence,
            run_id=run_id,
            node_name=node_name,
            payload=payload,
        )

        if code_event.event_type == "code_generation_complete":
            state["script"] = code_event.payload["script"]

    sequence += 1
    yield PipelineStreamEvent(
        event_type="node_complete",
        sequence=sequence,
        run_id=run_id,
        node_name=node_name,
        payload=_summarize_node_state(state),
    )


def _iter_node_updates(update: Any) -> list[tuple[str, Any]]:
    if not isinstance(update, Mapping):
        return [("pipeline", update)]

    node_updates: list[tuple[str, Any]] = []
    for key, value in update.items():
        node_updates.append((str(key), value))
    return node_updates


def _summarize_node_state(node_state: Any) -> dict[str, Any]:
    if not isinstance(node_state, Mapping):
        return {"value": _short_repr(node_state)}

    return {
        "state_keys": sorted(str(key) for key in node_state.keys()),
        "summary": _summarize_state(node_state),
    }


def _summarize_final_state(state: Mapping[str, Any] | None) -> dict[str, Any]:
    if state is None:
        return {"state_keys": [], "summary": {}, "result": {}}

    return {
        "state_keys": sorted(str(key) for key in state.keys()),
        "summary": _summarize_state(state),
        "result": {
            "export_files": state.get("export_files", []),
            "user_facing_warnings": state.get("user_facing_warnings", []),
            "validation": state.get("validation", {}),
            "assembly_report_markdown": state.get("assembly_report_markdown", ""),
        },
    }


def _summarize_state(state: Mapping[str, Any]) -> dict[str, Any]:
    validation = state.get("validation")
    critic_a_report = state.get("critic_a_report")
    critic_b_report = state.get("critic_b_report")

    return {
        "has_spec": bool(state.get("spec")),
        "has_geometry_plan": bool(state.get("geometry_plan")),
        "has_parameters": bool(state.get("parameters")),
        "script_length_chars": len(state.get("script") or ""),
        "validation_status": getattr(validation, "status", None),
        "repair_needed": getattr(validation, "repair_needed", None),
        "critic_a_routing": getattr(critic_a_report, "routing", None),
        "critic_b_routing": getattr(critic_b_report, "routing", None),
        "repair_count": state.get("repair_count"),
        "critic_a_attempts": state.get("critic_a_attempts"),
        "critic_b_attempts": state.get("critic_b_attempts"),
        "export_count": len(state.get("export_files") or []),
        "warning_count": len(state.get("user_facing_warnings") or []),
        "assembly_report_length_chars": len(state.get("assembly_report_markdown") or ""),
    }


def _to_jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, Mapping):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_to_jsonable(item) for item in value]
    try:
        import json

        json.dumps(value)
    except TypeError:
        return _short_repr(value)
    return value


def _short_repr(value: Any, max_length: int = 500) -> str:
    text = repr(value)
    if len(text) <= max_length:
        return text
    return f"{text[:max_length]}..."
