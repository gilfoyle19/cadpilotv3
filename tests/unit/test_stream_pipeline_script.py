import importlib.util
from pathlib import Path

from cadpilotv3.graph.streaming import PipelineStreamEvent

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "stream_pipeline.py"
SCRIPT_SPEC = importlib.util.spec_from_file_location("stream_pipeline_script", SCRIPT_PATH)
assert SCRIPT_SPEC is not None
assert SCRIPT_SPEC.loader is not None
stream_pipeline = importlib.util.module_from_spec(SCRIPT_SPEC)
SCRIPT_SPEC.loader.exec_module(stream_pipeline)


def test_format_readable_event_includes_code_chunk_size() -> None:
    event = PipelineStreamEvent(
        event_type="code_chunk",
        sequence=3,
        node_name="code_generation_infill_agent",
        payload={"text": "import cadquery as cq\n"},
    )

    formatted = stream_pipeline._format_readable_event(event)

    assert "code_chunk" in formatted
    assert "22 chars" in formatted


def test_format_readable_event_includes_validation_summary() -> None:
    event = PipelineStreamEvent(
        event_type="node_complete",
        sequence=7,
        node_name="execution_validation_node",
        payload={
            "summary": {
                "validation_status": "success",
                "script_length_chars": 100,
                "export_count": 1,
            }
        },
    )

    formatted = stream_pipeline._format_readable_event(event)

    assert "validation=success" in formatted
    assert "script=100 chars" in formatted
    assert "exports=1" in formatted
