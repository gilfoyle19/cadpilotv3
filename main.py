from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from uuid import uuid4

from cadpilotv3.config.settings import get_settings
from cadpilotv3.graph import PipelineStreamEvent, astream_pipeline_with_code_events
from cadpilotv3.graph.pipeline import build_pipeline
from cadpilotv3.graph.pipeline_state import PipelineState
from cadpilotv3.logging import log_error, log_with_context, setup_logging
from cadpilotv3.services import configure_langsmith, invoke_traced_pipeline
from cadpilotv3.shared import clear_llm_trace, configure_llm_trace

logger = logging.getLogger(__name__)

DEFAULT_USER_PROMPT = (
    "Create a single-part FDM-printable cable clamp block in CadQuery using "
    "millimeters and exporting STEP. The part should be a rectangular block "
    "about 50 mm long, 24 mm wide, and 12 mm tall, with a centered semicircular "
    "cable channel running along its length for a 10 mm diameter cable. Add two "
    "M4 clearance through-holes, one near each end, so the block can be screwed "
    "down to a surface. Keep it as one solid printable part with no lid, no "
    "assembly, and no moving features."
)


def _to_jsonable(value: object) -> object:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_jsonable(item) for key, item in value.items()}
    return value


def _dump_json(value: object) -> str:
    return json.dumps(_to_jsonable(value), indent=2)


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


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the CadPilot pipeline.",
    )
    parser.add_argument(
        "--prompt",
        default=DEFAULT_USER_PROMPT,
        help="CAD request to run through the pipeline.",
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Run the async streaming pipeline instead of the default sync pipeline.",
    )
    parser.add_argument(
        "--stream-mode",
        choices=["jsonl", "readable", "code"],
        default="jsonl",
        help=(
            "Streaming output mode. jsonl emits machine-readable events, readable "
            "emits concise progress, and code streams generated CadQuery chunks."
        ),
    )
    args, _unknown = parser.parse_known_args(argv)
    return args


def run_sync_pipeline(user_prompt: str) -> None:
    setup_logging()

    settings = get_settings()
    configure_langsmith()
    run_id = str(uuid4())
    configure_llm_trace(run_id)

    logger.info(
        "Starting CAD pipeline",
        extra={
            "run_id": run_id,
            "status": "starting",
        },
    )

    try:
        pipeline = build_pipeline(settings)
        initial_state = build_initial_state(user_prompt)

        log_with_context(
            logger,
            logging.INFO,
            "Invoking pipeline",
            run_id=run_id,
            user_prompt_preview=user_prompt[:200],
        )

        result = invoke_traced_pipeline(
            pipeline,
            initial_state,
            run_id=run_id,
            user_prompt=user_prompt,
        )
        export_files = result.get("export_files", [])
        warnings = result.get("user_facing_warnings", [])
        validation = result.get("validation", {})

        logger.info(
            "CAD pipeline completed",
            extra={
                "run_id": run_id,
                "status": "completed",
                "export_count": len(export_files),
                "warning_count": len(warnings),
                "validation_status": getattr(validation, "status", None),
                "repair_count": result.get("repair_count"),
                "critic_a_attempts": result.get("critic_a_attempts"),
                "critic_b_attempts": result.get("critic_b_attempts"),
            },
        )

        print("\n=== PIPELINE COMPLETED ===\n")
        print("Final warnings:")
        print(_dump_json(warnings))

        print("\nExport files:")
        print(_dump_json(export_files))

        print("\nAssembly report preview:")
        report = result.get("assembly_report_markdown", "")
        print(report[:3000] if report else "[no report generated]")

        print("\nValidation:")
        print(_dump_json(validation))

    except Exception as exc:
        log_error(
            logger,
            "CAD pipeline failed",
            run_id=run_id,
            error_class=type(exc).__name__,
            exc_info=True,
        )
        print("\n=== PIPELINE FAILED ===\n")
        print(f"{type(exc).__name__}: {exc}")
    finally:
        clear_llm_trace()


async def run_streaming_pipeline(user_prompt: str, *, mode: str) -> None:
    setup_logging()

    settings = get_settings()
    if not getattr(settings, "cad_enable_async", True):
        raise RuntimeError("CAD async execution is disabled by cad_enable_async=false")
    if not getattr(settings, "cad_enable_streaming", True):
        raise RuntimeError("CAD streaming is disabled by cad_enable_streaming=false")

    configure_langsmith()
    run_id = str(uuid4())
    configure_llm_trace(run_id)

    logger.info(
        "Starting streaming CAD pipeline",
        extra={
            "run_id": run_id,
            "status": "starting",
        },
    )

    try:
        final_event: PipelineStreamEvent | None = None
        async for event in astream_pipeline_with_code_events(
            settings,
            build_initial_state(user_prompt),
            run_id=run_id,
            user_prompt=user_prompt,
        ):
            emit_stream_event(event, mode=mode)
            if event.event_type == "pipeline_complete":
                final_event = event

        if final_event is not None and mode != "jsonl":
            print_streaming_final_result(final_event)
    except Exception as exc:
        log_error(
            logger,
            "Streaming CAD pipeline failed",
            run_id=run_id,
            error_class=type(exc).__name__,
            exc_info=True,
        )
        print("\n=== STREAMING PIPELINE FAILED ===\n")
        print(f"{type(exc).__name__}: {exc}")
    finally:
        clear_llm_trace()


def emit_stream_event(event: PipelineStreamEvent, *, mode: str) -> None:
    if mode == "jsonl":
        print(json.dumps(event.to_dict()), flush=True)
        return

    if mode == "code":
        if event.event_type == "code_chunk":
            print(event.payload.get("text", ""), end="", flush=True)
        elif event.event_type != "code_generation_complete":
            print(_format_readable_stream_event(event), file=sys.stderr, flush=True)
        return

    print(_format_readable_stream_event(event), flush=True)


def print_streaming_final_result(event: PipelineStreamEvent) -> None:
    result = event.payload.get("result") or {}
    export_files = result.get("export_files", [])
    warnings = result.get("user_facing_warnings", [])
    validation = result.get("validation", {})
    report = result.get("assembly_report_markdown", "")

    print("\n=== STREAMING PIPELINE COMPLETED ===\n")
    print("Final warnings:")
    print(_dump_json(warnings))

    print("\nExport files:")
    print(_dump_json(export_files))

    print("\nAssembly report preview:")
    print(report[:3000] if report else "[no report generated]")

    print("\nValidation:")
    print(_dump_json(validation))


def _format_readable_stream_event(event: PipelineStreamEvent) -> str:
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


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.stream:
        asyncio.run(run_streaming_pipeline(args.prompt, mode=args.stream_mode))
        return

    run_sync_pipeline(args.prompt)


if __name__ == "__main__":
    main()
