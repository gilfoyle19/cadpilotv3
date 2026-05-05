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
