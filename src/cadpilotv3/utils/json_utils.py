from __future__ import annotations

import json
import re
from typing import Any


class JSONExtractionError(ValueError):
    """Raised when valid JSON cannot be extracted from model output."""


def strip_code_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z0-9_-]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return text.strip()


def extract_json_block(text: str) -> str:
    cleaned = strip_code_fences(text)

    if cleaned.startswith("{") and cleaned.endswith("}"):
        return cleaned

    if cleaned.startswith("[") and cleaned.endswith("]"):
        return cleaned

    match = re.search(r"(\{.*\}|\[.*\])", cleaned, flags=re.DOTALL)
    if not match:
        raise JSONExtractionError("No JSON object or array found in model output.")
    return match.group(1).strip()


def parse_json(text: str) -> Any:
    json_block = extract_json_block(text)
    try:
        return json.loads(json_block)
    except json.JSONDecodeError as exc:
        raise JSONExtractionError(f"Failed to parse JSON: {exc}") from exc