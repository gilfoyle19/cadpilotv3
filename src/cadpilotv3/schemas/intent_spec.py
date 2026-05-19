from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field, field_validator


class IntentSpec(BaseModel):
    model_config = {
        "extra": "ignore",
    }

    component: str | None = None
    component_type: str | None = None
    dof_count: int | None = Field(default=None, ge=0)
    dof_config: list[str] | None = None
    joint_types: list[str] | None = None

    parts: list[str] = Field(default_factory=list)

    output_format: str | None = None
    units: str | None = None
    approximate_scale: str | None = None
    style: str | None = None
    manufacturing_process: str | None = None
    constraints: list[str] = Field(default_factory=list)
    explicit_dimensions: list[str] = Field(default_factory=list)
    explicit_constraints: list[str] = Field(default_factory=list)
    researched_dimensions: list[str] = Field(default_factory=list)
    research_sources: list[str] = Field(default_factory=list)

    clarifications_needed: list[str] = Field(default_factory=list)

    @field_validator("dof_config", "joint_types", mode="before")
    @classmethod
    def _normalize_optional_list_fields(cls, value):
        if value is None:
            return None
        if isinstance(value, str):
            return [value]
        return value

    @field_validator(
        "parts",
        "constraints",
        "explicit_dimensions",
        "explicit_constraints",
        "clarifications_needed",
        mode="before",
    )
    @classmethod
    def _normalize_list_fields(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return value

    @field_validator("researched_dimensions", "research_sources", mode="before")
    @classmethod
    def _normalize_research_string_lists(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        if isinstance(value, dict):
            return [cls._stringify_research_item(value)]
        if isinstance(value, list):
            normalized = [cls._stringify_research_item(item) for item in value]
            return [item for item in normalized if item]
        return [str(value)]

    @staticmethod
    def _stringify_research_item(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if not isinstance(value, dict):
            return str(value)

        item = _first_present(
            value,
            "item",
            "name",
            "dimension",
            "feature",
            "component",
            "title",
        )
        measured_value = _first_present(
            value,
            "value",
            "size",
            "measurement",
            "dimension_value",
        )
        unit = _first_present(value, "unit", "units")
        source = _first_present(
            value,
            "source",
            "source_note",
            "source_url",
            "url",
        )

        parts: list[str] = []
        if item is not None and measured_value is not None:
            measurement = str(measured_value)
            if unit is not None and str(unit) not in measurement:
                measurement = f"{measurement} {unit}"
            parts.append(f"{item}: {measurement}")
        elif item is not None:
            parts.append(str(item))
        elif measured_value is not None:
            measurement = str(measured_value)
            if unit is not None and str(unit) not in measurement:
                measurement = f"{measurement} {unit}"
            parts.append(measurement)

        if source is not None:
            parts.append(f"source {source}")

        if parts:
            return ", ".join(parts)

        return json.dumps(value, sort_keys=True)


def _first_present(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return value
    return None
