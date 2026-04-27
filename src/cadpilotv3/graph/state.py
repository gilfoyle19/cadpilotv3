from typing import Any

from pydantic import BaseModel, Field

from cadpilotv3.schemas import (
    CriticReport,
    ExportSummary,
    GeometryPlan,
    IntentSpec,
    ParameterSchema,
    RepairOutput,
    ValidationReport,
)


class PipelineState(BaseModel):
    user_prompt: str

    spec: IntentSpec | None = None
    geometry_plan: GeometryPlan | None = None
    parameters: ParameterSchema | None = None
    script: str = ""

    validation: ValidationReport | None = None
    repair_output: RepairOutput | None = None
    critic_a_report: CriticReport | None = None
    critic_b_report: CriticReport | None = None

    spec_history: list[dict[str, Any]] = Field(default_factory=list)
    geometry_plan_history: list[dict[str, Any]] = Field(default_factory=list)
    script_history: list[str] = Field(default_factory=list)

    repair_count: int = 0
    critic_a_attempts: int = 0
    critic_b_attempts: int = 0

    final_geometry: dict[str, Any] | None = None
    export_summary: ExportSummary | None = None
    export_files: list[str] = Field(default_factory=list)
    user_facing_warnings: list[str] = Field(default_factory=list)


def build_initial_state(user_prompt: str) -> PipelineState:
    return PipelineState(user_prompt=user_prompt)