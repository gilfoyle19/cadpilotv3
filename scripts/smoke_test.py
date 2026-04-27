import os

from cadpilotv3.config import get_settings
from cadpilotv3.services import (
    build_run_metadata,
    configure_langsmith,
    is_tracing_enabled,
    traced_pipeline_call,
)


def main() -> None:
    settings = get_settings()

    print("loaded langsmith key:", bool(settings.langsmith_api_key))
    configure_langsmith()

    print("env LANGSMITH_API_KEY:", bool(os.getenv("LANGSMITH_API_KEY")))
    print("env LANGCHAIN_API_KEY:", bool(os.getenv("LANGCHAIN_API_KEY")))
    print("env LANGSMITH_PROJECT:", os.getenv("LANGSMITH_PROJECT"))
    print("env LANGSMITH_ENDPOINT:", os.getenv("LANGSMITH_ENDPOINT"))
    print("tracing enabled:", is_tracing_enabled())

    payload = {
        "app_name": settings.app_name,
        "project": settings.langsmith_project,
        "tracing_enabled": is_tracing_enabled(),
        "metadata": build_run_metadata(
            node_name="smoke_test",
            attempt=1,
            user_prompt="Build a 2 DOF robotic arm in CadQuery and export as STEP",
            extra={"stage": "step_3"},
        ),
    }

    result = traced_pipeline_call(payload)
    print(result)


if __name__ == "__main__":
    main()