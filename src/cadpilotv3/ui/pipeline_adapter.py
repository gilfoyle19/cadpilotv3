from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any
from uuid import uuid4

from cadpilotv3.config.settings import get_settings
from cadpilotv3.graph import PipelineStreamEvent, astream_pipeline_with_code_events
from cadpilotv3.graph.pipeline_state import PipelineState
from cadpilotv3.logging import setup_logging
from cadpilotv3.services import configure_langsmith
from cadpilotv3.shared import clear_llm_trace, configure_llm_trace

DEFAULT_DEMO_PROMPT = (
    "Create a single-part FDM-printable cable clamp block in CadQuery using "
    "millimeters and exporting STEP. The part should be a rectangular block "
    "about 50 mm long, 24 mm wide, and 12 mm tall, with a centered semicircular "
    "cable channel running along its length for a 10 mm diameter cable. Add two "
    "M4 clearance through-holes, one near each end, so the block can be screwed "
    "down to a surface."
)


def build_initial_state(user_prompt: str) -> PipelineState:
    return {
        "user_prompt": user_prompt,
        "spec": {},
        "geometry_plan": {},
        "parameters": {},
        "script": "",
        "validation": {},
        "critic_a_report": {},
        "critic_b_report": {},
        "repair_decision": None,
        "repair_history": [],
        "repair_count": 0,
        "critic_a_attempts": 0,
        "critic_b_attempts": 0,
        "final_geometry": None,
        "export_files": [],
        "user_facing_warnings": [],
        "assembly_report_markdown": "",
    }


def run_streaming_pipeline_for_ui(
    user_prompt: str,
    *,
    on_event: Callable[[PipelineStreamEvent], None] | None = None,
) -> dict[str, Any]:
    return asyncio.run(_run_streaming_pipeline_for_ui(user_prompt, on_event=on_event))


async def _run_streaming_pipeline_for_ui(
    user_prompt: str,
    *,
    on_event: Callable[[PipelineStreamEvent], None] | None = None,
) -> dict[str, Any]:
    setup_logging()
    settings = get_settings()

    if not settings.cad_enable_async:
        raise RuntimeError("CAD async execution is disabled by cad_enable_async=false")
    if not settings.cad_enable_streaming:
        raise RuntimeError("CAD streaming is disabled by cad_enable_streaming=false")

    configure_langsmith()
    run_id = str(uuid4())
    configure_llm_trace(run_id)

    final_result: dict[str, Any] = {}
    try:
        async for event in astream_pipeline_with_code_events(
            settings,
            build_initial_state(user_prompt),
            run_id=run_id,
            user_prompt=user_prompt,
        ):
            if on_event is not None:
                on_event(event)
            if event.event_type == "pipeline_complete":
                final_result = dict(event.payload.get("result") or {})
    finally:
        clear_llm_trace()

    return final_result


def format_stream_event(event: PipelineStreamEvent) -> str | None:
    if event.event_type == "pipeline_start":
        return "Starting pipeline."

    if event.event_type == "node_start":
        return f"Starting `{event.node_name}`."

    if event.event_type == "node_complete":
        summary = event.payload.get("summary") or {}
        validation = summary.get("validation_status")
        if validation:
            return f"Finished `{event.node_name}` — validation: `{validation}`."
        return f"Finished `{event.node_name}`."

    if event.event_type == "code_generation_start":
        return f"Generating CadQuery script — attempt {event.payload.get('attempt_number')}."

    if event.event_type == "code_generation_retry":
        return f"Retrying code generation: {event.payload.get('reason')}."

    if event.event_type == "code_generation_complete":
        return "CadQuery script generated."

    if event.event_type == "pipeline_complete":
        return "Pipeline complete."

    if event.event_type in {"pipeline_error", "code_generation_error"}:
        return (
            f"{event.payload.get('error_class')}: "
            f"{event.payload.get('error_message')}"
        )

    return None
