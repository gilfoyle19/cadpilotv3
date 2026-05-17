from types import SimpleNamespace

import pytest
from langgraph.graph import StateGraph

from cadpilotv3.graph.nodes import PipelineNodes
from cadpilotv3.graph.pipeline_state import PipelineState
from cadpilotv3.graph.streaming import (
    PipelineStreamEvent,
    astream_pipeline_events,
    astream_pipeline_with_code_events,
)
from cadpilotv3.services.code_generation_infill_service import CodeGenerationStreamEvent


class FakeStreamingPipeline:
    def __init__(self, updates: list[dict]) -> None:
        self.updates = updates
        self.seen_initial_state: dict | None = None

    async def astream(self, initial_state: dict, *, stream_mode: str):
        self.seen_initial_state = initial_state
        assert stream_mode == "updates"
        for update in self.updates:
            yield update


class FailingStreamingPipeline:
    async def astream(self, initial_state: dict, *, stream_mode: str):
        raise RuntimeError("stream failed")
        yield {}


class FakeGraphStreamingPipeline:
    async def astream(self, initial_state: dict, *, stream_mode: list[str]):
        assert stream_mode == ["tasks", "updates", "custom"]
        state = dict(initial_state)
        yield (
            "tasks",
            {
                "name": "intent_spec_agent",
                "input": dict(state),
            },
        )
        state["spec"] = SimpleNamespace(component="bracket")
        yield ("updates", {"intent_spec_agent": dict(state)})

        yield (
            "tasks",
            {
                "name": "code_generation_infill_agent",
                "input": dict(state),
            },
        )
        yield (
            "custom",
            {
                "node_name": "code_generation_infill_agent",
                "event_type": "code_generation_start",
                "attempt_number": 1,
                "payload": {},
            },
        )
        yield (
            "custom",
            {
                "node_name": "code_generation_infill_agent",
                "event_type": "code_chunk",
                "attempt_number": 1,
                "payload": {"text": "import cadquery as cq\n"},
            },
        )
        yield (
            "custom",
            {
                "node_name": "code_generation_infill_agent",
                "event_type": "code_chunk",
                "attempt_number": 1,
                "payload": {"text": "def build_part():\n    return None\n"},
            },
        )
        state["script"] = "import cadquery as cq\ndef build_part():\n    return None\n"
        yield (
            "custom",
            {
                "node_name": "code_generation_infill_agent",
                "event_type": "code_generation_complete",
                "attempt_number": 1,
                "payload": {
                    "script": state["script"],
                    "script_length_chars": len(state["script"]),
                },
            },
        )
        yield ("updates", {"code_generation_infill_agent": dict(state)})

        yield (
            "tasks",
            {
                "name": "export_summary_agent",
                "input": dict(state),
            },
        )
        state["export_files"] = ["part.step"]
        state["assembly_report_markdown"] = "done"
        yield ("updates", {"export_summary_agent": dict(state)})


class FakeCodeGenerationService:
    async def astream_script(self, **kwargs):
        yield CodeGenerationStreamEvent(
            event_type="code_generation_start",
            attempt_number=1,
        )
        yield CodeGenerationStreamEvent(
            event_type="code_chunk",
            attempt_number=1,
            payload={"text": "import cadquery as cq\n"},
        )
        yield CodeGenerationStreamEvent(
            event_type="code_generation_complete",
            attempt_number=1,
            payload={
                "script": "import cadquery as cq\n",
                "script_length_chars": 22,
            },
        )


async def test_astream_pipeline_events_yields_progress_and_completion() -> None:
    validation = SimpleNamespace(status="success", repair_needed=False)
    critic_a_report = SimpleNamespace(routing="proceed")
    critic_b_report = SimpleNamespace(routing="export")
    pipeline = FakeStreamingPipeline(
        [
            {
                "intent_spec_agent": {
                    "user_prompt": "Make a bracket.",
                    "spec": SimpleNamespace(component="bracket"),
                    "geometry_plan": {},
                    "parameters": {},
                    "script": "",
                    "validation": {},
                    "critic_a_report": {},
                    "critic_b_report": {},
                    "repair_count": 0,
                    "critic_a_attempts": 0,
                    "critic_b_attempts": 0,
                    "export_files": [],
                    "user_facing_warnings": [],
                    "assembly_report_markdown": "",
                }
            },
            {
                "export_summary_agent": {
                    "user_prompt": "Make a bracket.",
                    "spec": SimpleNamespace(component="bracket"),
                    "geometry_plan": SimpleNamespace(parts=[]),
                    "parameters": SimpleNamespace(parameters={}),
                    "script": "import cadquery as cq\n",
                    "validation": validation,
                    "critic_a_report": critic_a_report,
                    "critic_b_report": critic_b_report,
                    "repair_count": 0,
                    "critic_a_attempts": 0,
                    "critic_b_attempts": 0,
                    "export_files": ["part.step"],
                    "user_facing_warnings": [],
                    "assembly_report_markdown": "done",
                }
            },
        ]
    )

    events = [
        event
        async for event in astream_pipeline_events(
            pipeline,
            {"user_prompt": "Make a bracket."},
            run_id="run-123",
        )
    ]

    assert [event.event_type for event in events] == [
        "pipeline_start",
        "node_complete",
        "node_complete",
        "pipeline_complete",
    ]
    assert [event.sequence for event in events] == [1, 2, 3, 4]
    assert events[1].node_name == "intent_spec_agent"
    assert events[2].payload["summary"]["validation_status"] == "success"
    assert events[2].payload["summary"]["export_count"] == 1
    assert events[3].payload["summary"]["assembly_report_length_chars"] == 4
    assert events[3].payload["result"]["export_files"] == ["part.step"]
    assert events[3].payload["result"]["assembly_report_markdown"] == "done"
    assert pipeline.seen_initial_state == {"user_prompt": "Make a bracket."}


async def test_astream_pipeline_with_code_events_yields_code_chunks(monkeypatch) -> None:
    monkeypatch.setattr(
        "cadpilotv3.graph.streaming.build_async_pipeline",
        lambda _settings: FakeGraphStreamingPipeline(),
    )

    events = [
        event
        async for event in astream_pipeline_with_code_events(
            SimpleNamespace(),
            {
                "user_prompt": "Make a bracket.",
                "spec": {},
                "geometry_plan": {},
                "parameters": {},
                "script": "",
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
            },
            run_id="run-123",
        )
    ]

    event_types = [event.event_type for event in events]
    assert "code_chunk" in event_types
    assert event_types[-1] == "pipeline_complete"
    streamed_code = "".join(
        event.payload["text"]
        for event in events
        if event.event_type == "code_chunk"
    )
    assert streamed_code.startswith("import cadquery as cq")
    codegen_complete = next(
        event
        for event in events
        if event.event_type == "code_generation_complete"
    )
    assert codegen_complete.payload["script"] == streamed_code
    assert events[-1].payload["summary"]["export_count"] == 1
    assert events[-1].payload["result"]["export_files"] == ["part.step"]
    assert events[-1].payload["result"]["assembly_report_markdown"] == "done"


async def test_codegen_node_streams_custom_events_inside_graph() -> None:
    nodes = object.__new__(PipelineNodes)
    nodes.code_generation_infill_service = FakeCodeGenerationService()

    graph = StateGraph(PipelineState)
    graph.add_node("code_generation_infill_agent", nodes.acode_generation_infill_agent)
    graph.set_entry_point("code_generation_infill_agent")
    pipeline = graph.compile()

    stream_parts = [
        part
        async for part in pipeline.astream(
            {
                "spec": object(),
                "geometry_plan": object(),
                "parameters": object(),
                "script": "",
                "repair_decision": None,
                "critic_b_report": {},
            },
            stream_mode=["custom", "updates"],
        )
    ]

    custom_parts = [payload for mode, payload in stream_parts if mode == "custom"]
    assert [part["event_type"] for part in custom_parts] == [
        "code_generation_start",
        "code_chunk",
        "code_generation_complete",
    ]
    assert custom_parts[1]["payload"]["text"] == "import cadquery as cq\n"

    update_payload = next(payload for mode, payload in stream_parts if mode == "updates")
    assert (
        update_payload["code_generation_infill_agent"]["script"]
        == "import cadquery as cq\n"
    )


def test_pipeline_stream_event_to_dict_coerces_payload() -> None:
    event = PipelineStreamEvent(
        event_type="node_complete",
        sequence=1,
        node_name="intent_spec_agent",
        payload={"spec": SimpleNamespace(component="bracket")},
    )

    data = event.to_dict()

    assert data["event_type"] == "node_complete"
    assert data["node_name"] == "intent_spec_agent"
    assert data["payload"]["spec"].startswith("namespace(")


async def test_astream_pipeline_events_yields_error_then_reraises() -> None:
    events = []

    with pytest.raises(RuntimeError, match="stream failed"):
        async for event in astream_pipeline_events(
            FailingStreamingPipeline(),
            {"user_prompt": "Make a bracket."},
            run_id="run-123",
        ):
            events.append(event)

    assert [event.event_type for event in events] == [
        "pipeline_start",
        "pipeline_error",
    ]
    assert events[-1].payload["error_class"] == "RuntimeError"
