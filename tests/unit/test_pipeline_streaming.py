from types import SimpleNamespace

import pytest

from cadpilotv3.graph.streaming import PipelineStreamEvent, astream_pipeline_events


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
    assert pipeline.seen_initial_state == {"user_prompt": "Make a bracket."}


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
