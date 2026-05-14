from types import SimpleNamespace

import pytest

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
            event_type="code_chunk",
            attempt_number=1,
            payload={"text": "def build_part():\n    return None\n"},
        )
        yield CodeGenerationStreamEvent(
            event_type="code_generation_complete",
            attempt_number=1,
            payload={
                "script": "import cadquery as cq\ndef build_part():\n    return None\n",
                "script_length_chars": 54,
            },
        )


class FakePipelineNodes:
    def __init__(self, settings) -> None:
        self.code_generation_infill_service = FakeCodeGenerationService()

    async def aintent_spec_agent(self, state):
        state["spec"] = SimpleNamespace(component="bracket")
        return state

    async def ageometry_planner_agent(self, state):
        state["geometry_plan"] = SimpleNamespace(parts=[])
        return state

    async def acritic_checkpoint_a(self, state):
        state["critic_a_report"] = SimpleNamespace(
            verdict="pass",
            routing="proceed",
        )
        return state

    async def aparameter_agent(self, state):
        state["parameters"] = SimpleNamespace(parameters={})
        return state

    async def aexecution_validation_node(self, state):
        state["validation"] = SimpleNamespace(
            status="success",
            repair_needed=False,
        )
        state["final_geometry"] = {
            "workspace_dir": ".sandbox_runs/fake",
            "result_object_name": "model",
        }
        return state

    async def arepair_agent(self, state):
        return state

    async def acritic_checkpoint_b(self, state):
        state["critic_b_report"] = SimpleNamespace(
            routing="export",
            user_facing_warnings=[],
        )
        return state

    async def aexport_summary_agent(self, state):
        state["export_files"] = ["part.step"]
        state["assembly_report_markdown"] = "done"
        state["user_facing_warnings"] = []
        return state


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
        "cadpilotv3.graph.streaming.PipelineNodes",
        FakePipelineNodes,
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
