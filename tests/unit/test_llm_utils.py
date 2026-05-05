from pydantic import BaseModel

from cadpilotv3.shared.llm_utils import invoke_pydantic


class SimpleOutput(BaseModel):
    action: str


class FakeLLM:
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses
        self.prompts: list[str] = []

    def invoke(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.responses.pop(0)


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
