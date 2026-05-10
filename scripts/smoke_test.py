import os

from cadpilotv3.config import get_settings
from cadpilotv3.services import (
    build_run_metadata,
    configure_langsmith,
    invoke_traced_pipeline,
    is_tracing_enabled,
)


class SmokePipeline:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def invoke(self, _initial_state: dict) -> dict:
        return self.payload


def main() -> None:
    settings = get_settings()

    print("loaded langsmith key:", bool(settings.langsmith_api_key))
    configure_langsmith()

    print("env LANGSMITH_API_KEY:", bool(os.getenv("LANGSMITH_API_KEY")))
    print("env LANGCHAIN_API_KEY:", bool(os.getenv("LANGCHAIN_API_KEY")))
    print("env LANGSMITH_PROJECT:", os.getenv("LANGSMITH_PROJECT"))
    print("env LANGSMITH_ENDPOINT:", os.getenv("LANGSMITH_ENDPOINT"))
    print("tracing enabled:", is_tracing_enabled())

    user_prompt = "Build a 2 DOF robotic arm in CadQuery and export as STEP"
    payload = {
        "app_name": settings.app_name,
        "project": settings.langsmith_project,
        "tracing_enabled": is_tracing_enabled(),
        "export_files": ["smoke_test.step"],
        "user_facing_warnings": [],
        "validation": {"status": "smoke_test"},
        "repair_count": 0,
        "critic_a_attempts": 0,
        "critic_b_attempts": 0,
        "assembly_report_markdown": "LangSmith smoke test completed.",
        "metadata": build_run_metadata(
            node_name="smoke_test",
            attempt=1,
            user_prompt=user_prompt,
            extra={"stage": "step_3"},
        ),
    }

    result = invoke_traced_pipeline(
        SmokePipeline(payload),
        {"user_prompt": user_prompt},
        run_id="smoke-test",
        user_prompt=user_prompt,
    )
    print(result)


if __name__ == "__main__":
    main()
