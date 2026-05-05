from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from cadpilotv3.shared.json_utils import JSONExtractionError, parse_json
from cadpilotv3.shared.llm_trace import record_llm_call, update_llm_trace

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
    trace_dir: str | None = None


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


def invoke_text(
    llm: Any,
    prompt: str,
    *,
    agent_name: str | None = None,
    trace_metadata: dict[str, Any] | None = None,
) -> str:
    return invoke_text_with_metadata(
        llm,
        prompt,
        agent_name=agent_name,
        trace_metadata=trace_metadata,
    ).text


def invoke_text_with_metadata(
    llm: Any,
    prompt: str,
    *,
    agent_name: str | None = None,
    trace_metadata: dict[str, Any] | None = None,
) -> LLMTextResult:
    response = llm.invoke(prompt)
    response_metadata = getattr(response, "response_metadata", None)
    usage_metadata = getattr(response, "usage_metadata", None)
    response_id = getattr(response, "id", None)

    if response_metadata is not None and not isinstance(response_metadata, dict):
        response_metadata = {"value": str(response_metadata)}
    if usage_metadata is not None and not isinstance(usage_metadata, dict):
        usage_metadata = {"value": str(usage_metadata)}

    response_text = get_message_text(response)
    raw_response_repr = repr(response)
    trace_dir = record_llm_call(
        prompt=prompt,
        response_text=response_text,
        agent_name=agent_name,
        response_metadata=response_metadata or {},
        usage_metadata=usage_metadata,
        response_id=str(response_id) if response_id is not None else None,
        raw_response_repr=raw_response_repr,
        extra_metadata=trace_metadata,
    )

    return LLMTextResult(
        text=response_text,
        response_metadata=response_metadata or {},
        usage_metadata=usage_metadata,
        response_id=str(response_id) if response_id is not None else None,
        raw_response_repr=raw_response_repr,
        trace_dir=str(trace_dir) if trace_dir is not None else None,
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
            trace_dir=str(getattr(response, "trace_dir", "")) or None,
        )

    return LLMTextResult(
        text=str(response),
        response_metadata={},
        usage_metadata=None,
        response_id=None,
        raw_response_repr=repr(response),
        trace_dir=None,
    )


def invoke_json(
    llm: Any,
    prompt: str,
    *,
    agent_name: str | None = None,
    trace_metadata: dict[str, Any] | None = None,
) -> dict[str, Any] | list[Any]:
    result = invoke_text_with_metadata(
        llm,
        prompt,
        agent_name=agent_name,
        trace_metadata=trace_metadata,
    )
    try:
        data = parse_json(result.text)
    except JSONExtractionError as exc:
        update_llm_trace(
            result.trace_dir,
            metadata_updates={
                "parse_status": "failed",
                "parse_error": str(exc),
            },
        )
        raise

    update_llm_trace(
        result.trace_dir,
        metadata_updates={"parse_status": "passed"},
        files={"parsed_output.json": json.dumps(data, indent=2)},
    )
    return data


def invoke_pydantic(
    llm: Any,
    prompt: str,
    schema: type[T],
    *,
    agent_name: str | None = None,
    trace_metadata: dict[str, Any] | None = None,
) -> T:
    last_error: Exception | None = None
    active_prompt = prompt

    for attempt_number in range(1, 3):
        result = invoke_text_with_metadata(
            llm,
            active_prompt,
            agent_name=agent_name,
            trace_metadata={
                **(trace_metadata or {}),
                "schema": schema.__name__,
                "structured_attempt_number": attempt_number,
            },
        )
        text = result.text
        try:
            data = parse_json(text)
            parsed = schema.model_validate(data)
            update_llm_trace(
                result.trace_dir,
                metadata_updates={
                    "parse_status": "passed",
                    "validation_status": "passed",
                    "schema": schema.__name__,
                },
                files={
                    "parsed_output.json": json.dumps(data, indent=2),
                    "validated_output.json": parsed.model_dump_json(indent=2),
                },
            )
            return parsed
        except (JSONExtractionError, ValidationError) as exc:
            last_error = exc
            update_llm_trace(
                result.trace_dir,
                metadata_updates={
                    "parse_status": "failed"
                    if isinstance(exc, JSONExtractionError)
                    else "passed",
                    "validation_status": "failed",
                    "schema": schema.__name__,
                    "validation_error": str(exc),
                },
            )
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
