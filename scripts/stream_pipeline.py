from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from uuid import uuid4

from cadpilotv3.config.settings import get_settings
from cadpilotv3.graph import PipelineStreamEvent, astream_pipeline_with_code_events
from cadpilotv3.graph.pipeline_state import PipelineState
from cadpilotv3.logging import log_error, setup_logging
from cadpilotv3.services import configure_langsmith
from cadpilotv3.shared import clear_llm_trace, configure_llm_trace

logger = logging.getLogger(__name__)

DEFAULT_PROMPT = (
    "Create a compact FDM-printable wall bracket in CadQuery using millimeters "
    "and export STEP. Include two M5 mounting holes, light chamfers, and a flat "
    "print orientation."
)


def build_initial_state(user_prompt: str) -> PipelineState:
    return {
        "user_prompt": user_prompt,
        "spec": {},
        "geometry_plan": {},
        "parameters": {},
        "script": "",
        "validation": {},
        "contract_validation": {},
        "critic_a_report": {},
        "critic_b_report": {},
        "repair_decision": None,
        "repair_count": 0,
        "critic_a_attempts": 0,
        "critic_b_attempts": 0,
        "final_geometry": None,
        "export_files": [],
        "user_facing_warnings": [],
        "assembly_report_markdown": "",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the async CadPilot pipeline and stream progress events.",
    )
    parser.add_argument(
        "--prompt",
        default=DEFAULT_PROMPT,
        help="CAD request to stream through the pipeline.",
    )
    parser.add_argument(
        "--mode",
        choices=["jsonl", "readable", "code"],
        default="jsonl",
        help=(
            "jsonl emits machine-readable events, readable emits concise progress, "
            "and code streams generated CadQuery chunks to stdout."
        ),
    )
    return parser.parse_args()


async def run_stream(prompt: str, *, mode: str) -> None:
    setup_logging()
    settings = get_settings()

    if not settings.cad_enable_async:
        raise RuntimeError("CAD async execution is disabled by cad_enable_async=false")
    if not settings.cad_enable_streaming:
        raise RuntimeError("CAD streaming is disabled by cad_enable_streaming=false")

    configure_langsmith()
    run_id = str(uuid4())
    configure_llm_trace(run_id)

    logger.info(
        "Starting streaming CAD pipeline",
        extra={"run_id": run_id, "status": "starting"},
    )

    try:
        async for event in astream_pipeline_with_code_events(
            settings,
            build_initial_state(prompt),
            run_id=run_id,
            user_prompt=prompt,
        ):
            emit_event(event, mode=mode)
    except Exception as exc:
        log_error(
            logger,
            "Streaming CAD pipeline failed",
            run_id=run_id,
            error_class=type(exc).__name__,
            exc_info=True,
        )
        raise
    finally:
        clear_llm_trace()


def emit_event(event: PipelineStreamEvent, *, mode: str) -> None:
    if mode == "jsonl":
        print(json.dumps(event.to_dict()), flush=True)
        return

    if mode == "code":
        if event.event_type == "code_chunk":
            print(event.payload.get("text", ""), end="", flush=True)
        elif event.event_type != "code_generation_complete":
            print(_format_readable_event(event), file=sys.stderr, flush=True)
        return

    print(_format_readable_event(event), flush=True)


def _format_readable_event(event: PipelineStreamEvent) -> str:
    prefix = f"[{event.sequence}] {event.event_type}"
    if event.node_name:
        prefix = f"{prefix} {event.node_name}"

    if event.event_type == "code_chunk":
        text = event.payload.get("text", "")
        return f"{prefix}: {len(text)} chars"

    if event.event_type in {"pipeline_error", "code_generation_error"}:
        return f"{prefix}: {event.payload.get('error_class')} {event.payload.get('error_message')}"

    if event.event_type == "code_generation_retry":
        return f"{prefix}: retrying because {event.payload.get('reason')}"

    summary = event.payload.get("summary") or {}
    status = summary.get("validation_status")
    script_length = summary.get("script_length_chars")
    export_count = summary.get("export_count")
    details = []
    if status:
        details.append(f"validation={status}")
    if script_length:
        details.append(f"script={script_length} chars")
    if export_count:
        details.append(f"exports={export_count}")
    return f"{prefix}: {', '.join(details) if details else 'ok'}"


def main() -> None:
    args = parse_args()
    asyncio.run(run_stream(args.prompt, mode=args.mode))


if __name__ == "__main__":
    main()
