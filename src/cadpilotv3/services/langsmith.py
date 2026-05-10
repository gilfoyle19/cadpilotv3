import os
from typing import Any

from langsmith import Client, traceable

from cadpilotv3.config import get_settings


def configure_langsmith() -> None:
    settings = get_settings()

    os.environ["LANGSMITH_TRACING"] = str(settings.langsmith_tracing).lower()
    os.environ["LANGSMITH_TRACING_V2"] = str(settings.langsmith_tracing).lower()
    os.environ["LANGCHAIN_TRACING_V2"] = str(settings.langsmith_tracing).lower()
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
    os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint

    if settings.langsmith_api_key:
        os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
        os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key


def is_tracing_enabled() -> bool:
    settings = get_settings()
    return bool(settings.langsmith_tracing)


def get_langsmith_client() -> Client | None:
    if not is_tracing_enabled():
        return None

    configure_langsmith()
    return Client()


def build_run_metadata(
    *,
    node_name: str | None = None,
    attempt: int | None = None,
    user_prompt: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metadata: dict[str, Any] = {}

    if node_name is not None:
        metadata["node_name"] = node_name
    if attempt is not None:
        metadata["attempt"] = attempt
    if user_prompt is not None:
        metadata["user_prompt_preview"] = user_prompt[:200]

    if extra:
        metadata.update(extra)

    return metadata


def _pipeline_trace_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    initial_state = inputs.get("initial_state") or {}
    return {
        "run_id": inputs.get("run_id"),
        "user_prompt": inputs.get("user_prompt") or initial_state.get("user_prompt"),
        "initial_state_keys": sorted(initial_state.keys()),
    }


def _pipeline_trace_outputs(outputs: dict[str, Any]) -> dict[str, Any]:
    return _to_jsonable(
        {
            "export_files": outputs.get("export_files", []),
            "user_facing_warnings": outputs.get("user_facing_warnings", []),
            "validation": outputs.get("validation", {}),
            "repair_count": outputs.get("repair_count"),
            "critic_a_attempts": outputs.get("critic_a_attempts"),
            "critic_b_attempts": outputs.get("critic_b_attempts"),
            "assembly_report_preview": (outputs.get("assembly_report_markdown") or "")[:1000],
        }
    )


@traceable(
    run_type="chain",
    name="cadpilotv3_pipeline",
    process_inputs=_pipeline_trace_inputs,
    process_outputs=_pipeline_trace_outputs,
)
def invoke_traced_pipeline(
    pipeline: Any,
    initial_state: dict[str, Any],
    *,
    run_id: str,
    user_prompt: str,
) -> dict[str, Any]:
    return pipeline.invoke(initial_state)


@traceable(run_type="chain", name="cadpilotv3_pipeline")
def traced_pipeline_call(payload: dict[str, Any]) -> dict[str, Any]:
    return payload


def _to_jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    return value
