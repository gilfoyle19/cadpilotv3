import os
from typing import Any

from langsmith import Client, traceable

from cadpilotv3.config import get_settings


def configure_langsmith() -> None:
    settings = get_settings()

    os.environ["LANGSMITH_TRACING"] = str(settings.langsmith_tracing).lower()
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
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


@traceable(run_type="chain", name="cadpilotv3_pipeline")
def traced_pipeline_call(payload: dict[str, Any]) -> dict[str, Any]:
    return payload