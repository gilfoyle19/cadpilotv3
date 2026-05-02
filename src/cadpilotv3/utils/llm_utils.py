from __future__ import annotations

import logging
from typing import Any, Type, TypeVar

from pydantic import BaseModel, ValidationError

from cadpilotv3.shared.json_utils import parse_json

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMResponseValidationError(ValueError):
    """Raised when model output cannot be validated against a schema."""


def get_message_text(response: Any) -> str:
    content = getattr(response, "content", response)

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                parts.append(str(item["text"]))
        return "\n".join(parts).strip()

    return str(content)


def invoke_text(llm: Any, prompt: str) -> str:
    response = llm.invoke(prompt)
    return get_message_text(response)


def invoke_json(llm: Any, prompt: str) -> dict[str, Any] | list[Any]:
    text = invoke_text(llm, prompt)
    return parse_json(text)


def invoke_pydantic(llm: Any, prompt: str, schema: Type[T]) -> T:
    data = invoke_json(llm, prompt)
    try:
        return schema.model_validate(data)
    except ValidationError as exc:
        logger.exception("LLM response failed schema validation")
        raise LLMResponseValidationError(str(exc)) from exc