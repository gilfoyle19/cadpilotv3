import json
from types import SimpleNamespace

from pydantic import BaseModel

from cadpilotv3.shared.llm_trace import clear_llm_trace, configure_llm_trace
from cadpilotv3.shared.llm_utils import (
    ainvoke_pydantic,
    astream_text_with_metadata,
    invoke_pydantic,
)


class SimpleOutput(BaseModel):
    action: str


class FakeLLM:
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.prompts: list[str] = []

    def invoke(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.responses.pop(0)


class AsyncFakeLLM:
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.prompts: list[str] = []

    async def ainvoke(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.responses.pop(0)


class StreamingFakeLLM:
    def __init__(self, chunks: list[str]) -> None:
        self.chunks = chunks
        self.prompts: list[str] = []

    async def astream(self, prompt: str):
        self.prompts.append(prompt)
        for chunk in self.chunks:
            yield chunk


def test_invoke_pydantic_retries_malformed_json() -> None:
    llm = FakeLLM(
        [
            '{"action": "patch',
            '{"action": "patch"}',
        ]
    )

    result = invoke_pydantic(llm, "Return JSON.", SimpleOutput)

    assert result.action == "patch"
    assert len(llm.prompts) == 2
    assert "The previous response was not valid structured output." in llm.prompts[1]


async def test_ainvoke_pydantic_retries_malformed_json() -> None:
    llm = AsyncFakeLLM(
        [
            '{"action": "patch',
            '{"action": "patch"}',
        ]
    )

    result = await ainvoke_pydantic(llm, "Return JSON.", SimpleOutput)

    assert result.action == "patch"
    assert len(llm.prompts) == 2
    assert "The previous response was not valid structured output." in llm.prompts[1]


def test_invoke_pydantic_persists_llm_trace(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "cadpilotv3.shared.llm_trace.get_settings",
        lambda: SimpleNamespace(
            cad_artifacts_dir=str(tmp_path),
            llm_trace_outputs=True,
        ),
    )
    configure_llm_trace("run-123")
    llm = FakeLLM(['{"action": "patch"}'])

    try:
        result = invoke_pydantic(
            llm,
            "Return JSON.",
            SimpleOutput,
            agent_name="repair_agent",
        )
    finally:
        clear_llm_trace()

    assert result.action == "patch"
    trace_dir = tmp_path / "llm_runs" / "run-123" / "001_repair_agent"
    assert (trace_dir / "prompt.txt").read_text(encoding="utf-8") == "Return JSON."
    assert (trace_dir / "raw_response.txt").read_text(encoding="utf-8") == (
        '{"action": "patch"}'
    )
    assert json.loads((trace_dir / "parsed_output.json").read_text(encoding="utf-8")) == {
        "action": "patch"
    }

    metadata = json.loads((trace_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["run_id"] == "run-123"
    assert metadata["agent_name"] == "repair_agent"
    assert metadata["schema"] == "SimpleOutput"
    assert metadata["validation_status"] == "passed"


async def test_ainvoke_pydantic_persists_llm_trace(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        "cadpilotv3.shared.llm_trace.get_settings",
        lambda: SimpleNamespace(
            cad_artifacts_dir=str(tmp_path),
            llm_trace_outputs=True,
        ),
    )
    configure_llm_trace("async-run-123")
    llm = AsyncFakeLLM(['{"action": "patch"}'])

    try:
        result = await ainvoke_pydantic(
            llm,
            "Return JSON.",
            SimpleOutput,
            agent_name="repair_agent",
        )
    finally:
        clear_llm_trace()

    assert result.action == "patch"
    trace_dir = tmp_path / "llm_runs" / "async-run-123" / "001_repair_agent"
    assert (trace_dir / "prompt.txt").read_text(encoding="utf-8") == "Return JSON."
    assert (trace_dir / "raw_response.txt").read_text(encoding="utf-8") == (
        '{"action": "patch"}'
    )
    assert json.loads((trace_dir / "parsed_output.json").read_text(encoding="utf-8")) == {
        "action": "patch"
    }

    metadata = json.loads((trace_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["run_id"] == "async-run-123"
    assert metadata["agent_name"] == "repair_agent"
    assert metadata["schema"] == "SimpleOutput"
    assert metadata["validation_status"] == "passed"


async def test_astream_text_with_metadata_yields_chunks_and_final_trace(
    tmp_path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "cadpilotv3.shared.llm_trace.get_settings",
        lambda: SimpleNamespace(
            cad_artifacts_dir=str(tmp_path),
            llm_trace_outputs=True,
        ),
    )
    configure_llm_trace("stream-run-123")
    llm = StreamingFakeLLM(["hello", " ", "world"])

    try:
        chunks = [
            chunk
            async for chunk in astream_text_with_metadata(
                llm,
                "Say hello.",
                agent_name="code_generation_agent",
            )
        ]
    finally:
        clear_llm_trace()

    assert [chunk.text for chunk in chunks if not chunk.is_final] == [
        "hello",
        " ",
        "world",
    ]
    assert chunks[-1].is_final
    assert chunks[-1].result is not None
    assert chunks[-1].result.text == "hello world"

    trace_dir = tmp_path / "llm_runs" / "stream-run-123" / "001_code_generation_agent"
    assert (trace_dir / "raw_response.txt").read_text(encoding="utf-8") == "hello world"
    metadata = json.loads((trace_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["streaming"] is True
    assert metadata["stream_chunk_count"] == 3
