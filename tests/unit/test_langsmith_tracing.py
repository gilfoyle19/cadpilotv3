import importlib.util
import os
from pathlib import Path
from types import SimpleNamespace

from cadpilotv3.services.langsmith import (
    ainvoke_traced_pipeline,
    configure_langsmith,
    invoke_traced_pipeline,
)

MAIN_PATH = Path(__file__).resolve().parents[2] / "main.py"
MAIN_SPEC = importlib.util.spec_from_file_location("cadpilotv3_main", MAIN_PATH)
assert MAIN_SPEC is not None
assert MAIN_SPEC.loader is not None
main_module = importlib.util.module_from_spec(MAIN_SPEC)
MAIN_SPEC.loader.exec_module(main_module)


class FakePipeline:
    def __init__(self, result: dict) -> None:
        self.result = result
        self.invoked_with: dict | None = None

    def invoke(self, initial_state: dict) -> dict:
        self.invoked_with = initial_state
        return self.result


class FakeAsyncPipeline:
    def __init__(self, result: dict) -> None:
        self.result = result
        self.ainvoked_with: dict | None = None

    async def ainvoke(self, initial_state: dict) -> dict:
        self.ainvoked_with = initial_state
        return self.result


def test_configure_langsmith_exports_langsmith_and_langchain_env(monkeypatch) -> None:
    for name in [
        "LANGSMITH_TRACING",
        "LANGSMITH_TRACING_V2",
        "LANGCHAIN_TRACING_V2",
        "LANGSMITH_PROJECT",
        "LANGCHAIN_PROJECT",
        "LANGSMITH_ENDPOINT",
        "LANGSMITH_API_KEY",
        "LANGCHAIN_API_KEY",
    ]:
        monkeypatch.delenv(name, raising=False)

    monkeypatch.setattr(
        "cadpilotv3.services.langsmith.get_settings",
        lambda: SimpleNamespace(
            langsmith_tracing=True,
            langsmith_project="cadpilotv3-test",
            langsmith_endpoint="https://api.smith.langchain.com",
            langsmith_api_key="test-key",
        ),
    )

    configure_langsmith()

    assert os.environ["LANGSMITH_TRACING"] == "true"
    assert os.environ["LANGSMITH_TRACING_V2"] == "true"
    assert os.environ["LANGCHAIN_TRACING_V2"] == "true"
    assert os.environ["LANGSMITH_PROJECT"] == "cadpilotv3-test"
    assert os.environ["LANGCHAIN_PROJECT"] == "cadpilotv3-test"
    assert os.environ["LANGSMITH_ENDPOINT"] == "https://api.smith.langchain.com"
    assert os.environ["LANGSMITH_API_KEY"] == "test-key"
    assert os.environ["LANGCHAIN_API_KEY"] == "test-key"


def test_invoke_traced_pipeline_invokes_pipeline_without_serializing_pipeline_input(
    monkeypatch,
) -> None:
    monkeypatch.setenv("LANGSMITH_TRACING", "false")
    monkeypatch.setenv("LANGSMITH_TRACING_V2", "false")
    pipeline = FakePipeline(
        {
            "export_files": ["part.step"],
            "user_facing_warnings": [],
            "validation": {"status": "passed"},
            "repair_count": 0,
            "critic_a_attempts": 1,
            "critic_b_attempts": 1,
            "assembly_report_markdown": "done",
        }
    )
    initial_state = {"user_prompt": "Make a bracket.", "script": ""}

    result = invoke_traced_pipeline(
        pipeline,
        initial_state,
        run_id="run-123",
        user_prompt="Make a bracket.",
    )

    assert result["export_files"] == ["part.step"]
    assert pipeline.invoked_with == initial_state


async def test_ainvoke_traced_pipeline_invokes_pipeline_ainvoke(monkeypatch) -> None:
    monkeypatch.setenv("LANGSMITH_TRACING", "false")
    monkeypatch.setenv("LANGSMITH_TRACING_V2", "false")
    pipeline = FakeAsyncPipeline(
        {
            "export_files": ["part.step"],
            "user_facing_warnings": [],
            "validation": {"status": "passed"},
            "repair_count": 0,
            "critic_a_attempts": 1,
            "critic_b_attempts": 1,
            "assembly_report_markdown": "done",
        }
    )
    initial_state = {"user_prompt": "Make a bracket.", "script": ""}

    result = await ainvoke_traced_pipeline(
        pipeline,
        initial_state,
        run_id="run-123",
        user_prompt="Make a bracket.",
    )

    assert result["export_files"] == ["part.step"]
    assert pipeline.ainvoked_with == initial_state


def test_main_configures_langsmith_before_building_pipeline(monkeypatch, capsys) -> None:
    calls: list[str] = []

    monkeypatch.setattr(main_module, "setup_logging", lambda: None)
    monkeypatch.setattr(main_module, "get_settings", lambda: SimpleNamespace())
    monkeypatch.setattr(main_module, "configure_llm_trace", lambda _run_id: None)
    monkeypatch.setattr(main_module, "clear_llm_trace", lambda: None)
    monkeypatch.setattr(main_module, "configure_langsmith", lambda: calls.append("configure"))

    def fake_build_pipeline(_settings):
        calls.append("build")
        return FakePipeline({})

    def fake_invoke_traced_pipeline(_pipeline, _initial_state, *, run_id, user_prompt):
        calls.append("invoke")
        assert run_id
        assert user_prompt
        return {
            "export_files": [],
            "user_facing_warnings": [],
            "validation": {},
            "repair_count": 0,
            "critic_a_attempts": 0,
            "critic_b_attempts": 0,
            "assembly_report_markdown": "",
        }

    monkeypatch.setattr(main_module, "build_pipeline", fake_build_pipeline)
    monkeypatch.setattr(main_module, "invoke_traced_pipeline", fake_invoke_traced_pipeline)

    main_module.main()

    assert calls == ["configure", "build", "invoke"]
    capsys.readouterr()


def test_main_stream_flag_dispatches_to_streaming_runner(monkeypatch) -> None:
    calls: list[tuple[str, str]] = []

    async def fake_run_streaming_pipeline(user_prompt: str, *, mode: str) -> None:
        calls.append((user_prompt, mode))

    monkeypatch.setattr(main_module, "run_streaming_pipeline", fake_run_streaming_pipeline)

    main_module.main(
        [
            "--stream",
            "--stream-mode",
            "readable",
            "--prompt",
            "Make a bracket.",
        ]
    )

    assert calls == [("Make a bracket.", "readable")]


def test_print_streaming_final_result_outputs_exports_and_report(capsys) -> None:
    event = main_module.PipelineStreamEvent(
        event_type="pipeline_complete",
        sequence=10,
        payload={
            "result": {
                "export_files": ["part.step"],
                "user_facing_warnings": ["Check hole spacing."],
                "validation": {"status": "success"},
                "assembly_report_markdown": "# Report\nDone.",
            }
        },
    )

    main_module.print_streaming_final_result(event)

    output = capsys.readouterr().out
    assert "STREAMING PIPELINE COMPLETED" in output
    assert "part.step" in output
    assert "Check hole spacing." in output
    assert "# Report" in output
    assert '"status": "success"' in output
