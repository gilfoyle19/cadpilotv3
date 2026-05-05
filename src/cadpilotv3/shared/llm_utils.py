from __future__ import annotations

import json
import logging
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from cadpilotv3.shared.json_utils import JSONExtractionError, parse_json

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


def invoke_pydantic(llm: Any, prompt: str, schema: type[T]) -> T:
    last_error: Exception | None = None
    active_prompt = prompt

    for attempt_number in range(1, 3):
        text = invoke_text(llm, active_prompt)
        try:
            data = parse_json(text)
            return schema.model_validate(data)
        except (JSONExtractionError, ValidationError) as exc:
            last_error = exc
            if attempt_number == 2:
                break

            logger.warning(
                "LLM response failed structured validation; retrying",
                extra={
                    "schema": schema.__name__,
                    "attempt_number": attempt_number,
                    "reason": str(exc),
                },
            )
            active_prompt = _build_structured_retry_prompt(
                prompt=prompt,
                schema=schema,
                error=exc,
                invalid_response=text,
            )

    logger.error(
        "LLM response failed schema validation",
        extra={"schema": schema.__name__, "reason": str(last_error)},
    )
    raise LLMResponseValidationError(str(last_error)) from last_error


def _build_structured_retry_prompt(
    *,
    prompt: str,
    schema: type[BaseModel],
    error: Exception,
    invalid_response: str,
) -> str:
    schema_json = json.dumps(schema.model_json_schema(), indent=2)
    return "\n\n".join(
        [
            prompt,
            "The previous response was not valid structured output.",
            f"Validation error: {error}",
            "Previous response excerpt:",
            invalid_response[:2000],
            "Return ONLY valid JSON matching this schema. Do not include prose or markdown fences.",
            schema_json[:6000],
        ]
    )
