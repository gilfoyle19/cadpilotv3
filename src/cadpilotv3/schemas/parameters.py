from pydantic import BaseModel, Field


class ParameterDefinition(BaseModel):
    model_config = {
        "extra": "ignore",
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


class ParameterSchema(BaseModel):
    model_config = {
        "extra": "ignore",
    }

    parameters: dict[str, ParameterDefinition] = Field(default_factory=dict)