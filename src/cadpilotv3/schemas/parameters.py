import re
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class ParameterDefinition(BaseModel):
    model_config = {
        "extra": "forbid",
    }

    value: float | int | str | bool
    unit: str
    description: str
    min: float | int | None = None
    max: float | int | None = None
    depends_on: list[str] = Field(default_factory=list)
    constraint: str | None = None
    is_derived: bool = False
    derived_from: str | None = None

    @field_validator("depends_on", mode="before")
    @classmethod
    def _normalize_depends_on(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return value

    @model_validator(mode="after")
    def _validate_derived_contract(self) -> "ParameterDefinition":
        if self.is_derived and not self.derived_from:
            raise ValueError("Derived parameters must include derived_from")
        if not self.is_derived and self.derived_from is not None:
            raise ValueError("Non-derived parameters must use derived_from: null")
        return self


class ParameterSchema(BaseModel):
    model_config = {
        "extra": "forbid",
    }

    parameters: dict[str, ParameterDefinition] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _wrap_flat_parameter_dict(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        if "parameters" in data:
            return data

        if data and all(isinstance(value, dict) for value in data.values()):
            return {"parameters": data}

        return data

    @model_validator(mode="after")
    def _reject_empty_or_invalid_parameters(self) -> "ParameterSchema":
        if not self.parameters:
            raise ValueError("Parameter schema must contain at least one parameter")

        invalid_names = [
            name
            for name in self.parameters
            if not re.fullmatch(r"[A-Z][A-Z0-9_]*", name)
        ]
        if invalid_names:
            joined = ", ".join(invalid_names)
            raise ValueError(f"Parameter names must be SCREAMING_SNAKE_CASE: {joined}")

        return self
