from pydantic import BaseModel, Field


class IntentSpec(BaseModel):
    artifact_type: str = "single_part"
    component: str | None = None
    category: str | None = None
    complexity: str = "simple"

    dof: int | None = Field(default=None, ge=0)
    dof_config: list[str] = Field(default_factory=list)

    parts: list[str] = Field(default_factory=list)
    subassemblies: list[str] = Field(default_factory=list)

    output_format: str | None = None
    units: str | None = None
    style: str | None = None
    material_hint: str | None = None
    manufacturing_process: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    performance_targets: list[str] = Field(default_factory=list)

    clarifications_needed: list[str] = Field(default_factory=list)