from pydantic import BaseModel, Field


class ParameterDefinition(BaseModel):
    value: float | int | str | bool
    unit: str
    description: str
    min: float | int | None = None
    max: float | int | None = None
    depends_on: list[str] = Field(default_factory=list)
    derived: bool = False
    group: str | None = None


class ParameterSchema(BaseModel):
    parameters: dict[str, ParameterDefinition] = Field(default_factory=dict)