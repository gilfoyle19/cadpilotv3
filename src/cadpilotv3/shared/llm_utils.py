from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from cadpilotv3.shared.json_utils import JSONExtractionError, parse_json

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMResponseValidationError(ValueError):
    """Raised when model output cannot be validated against a schema."""


@dataclass(frozen=True)
class LLMTextResult:
    text: str
    response_metadata: dict[str, Any]
    usage_metadata: dict[str, Any] | None
    response_id: str | None
    raw_response_repr: str


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
    return invoke_text_with_metadata(llm, prompt).text


def invoke_text_with_metadata(llm: Any, prompt: str) -> LLMTextResult:
    response = llm.invoke(prompt)
    response_metadata = getattr(response, "response_metadata", None)
    usage_metadata = getattr(response, "usage_metadata", None)
    response_id = getattr(response, "id", None)

    if response_metadata is not None and not isinstance(response_metadata, dict):
        response_metadata = {"value": str(response_metadata)}
    if usage_metadata is not None and not isinstance(usage_metadata, dict):
        usage_metadata = {"value": str(usage_metadata)}

    return LLMTextResult(
        text=get_message_text(response),
        response_metadata=response_metadata or {},
        usage_metadata=usage_metadata,
        response_id=str(response_id) if response_id is not None else None,
        raw_response_repr=repr(response),
    )


def coerce_llm_text_result(response: Any) -> LLMTextResult:
    if isinstance(response, LLMTextResult):
        return response

    if hasattr(response, "text"):
        text_value = response.text
        if callable(text_value):
            text_value = text_value()

        response_metadata = getattr(response, "response_metadata", None)
        usage_metadata = getattr(response, "usage_metadata", None)
        response_id = getattr(response, "response_id", getattr(response, "id", None))
        raw_response_repr = getattr(response, "raw_response_repr", repr(response))

        if response_metadata is not None and not isinstance(response_metadata, dict):
            response_metadata = {"value": str(response_metadata)}
        if usage_metadata is not None and not isinstance(usage_metadata, dict):
            usage_metadata = {"value": str(usage_metadata)}

        return LLMTextResult(
            text=str(text_value),
            response_metadata=response_metadata or {},
            usage_metadata=usage_metadata,
            response_id=str(response_id) if response_id is not None else None,
            raw_response_repr=str(raw_response_repr),
        )

    return LLMTextResult(
        text=str(response),
        response_metadata={},
        usage_metadata=None,
        response_id=None,
        raw_response_repr=repr(response),
    )


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
