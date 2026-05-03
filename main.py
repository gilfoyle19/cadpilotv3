from __future__ import annotations

import json
import logging
from uuid import uuid4

from cadpilotv3.config.settings import get_settings
from cadpilotv3.graph.pipeline import build_pipeline
from cadpilotv3.graph.pipeline_state import PipelineState
from cadpilotv3.logging import log_error, log_with_context, setup_logging


logger = logging.getLogger(__name__)


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

        "script_skeleton": "",
        "script": "",
        "pending_infill_functions": [],
        "completed_infill_functions": [],

        "validation": {},
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


def main() -> None:
    setup_logging()

    settings = get_settings()
    run_id = str(uuid4())

    logger.info(
        "Starting CAD pipeline",
        extra={
            "run_id": run_id,
            "status": "starting",
        },
    )

    user_prompt = "L-bracket for mounting a servo motor to 20x20 aluminum extrusion, M3 bolts, needs to be rigid, export as STEP"

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

        result = pipeline.invoke(initial_state)
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


if __name__ == "__main__":
    main()
