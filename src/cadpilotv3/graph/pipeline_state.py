from __future__ import annotations

from typing import Any, TypedDict

from cadpilotv3.schemas.intent_spec import IntentSpec
from cadpilotv3.schemas.geometry_plan import GeometryPlan
from cadpilotv3.schemas.parameters import ParameterSchema
from cadpilotv3.schemas.validation import ValidationReport
from cadpilotv3.schemas.repair import RepairOutput
from cadpilotv3.schemas.critic import (
    CriticReport,
    CriticBReport,
)
from cadpilotv3.schemas.export import ExportedFile


class PipelineState(TypedDict):
    user_prompt: str

    spec: IntentSpec | dict
    geometry_plan: GeometryPlan | dict
    parameters: ParameterSchema | dict
    script_skeleton: str
    script: str
    pending_infill_functions: list[str]
    completed_infill_functions: list[str]
    validation: ValidationReport | dict

    critic_a_report: CriticReport | dict
    critic_b_report: CriticBReport | dict

    repair_decision: RepairOutput | None
    repair_count: int
    critic_a_attempts: int
    critic_b_attempts: int

    final_geometry: Any | None
    export_files: list[ExportedFile]
    user_facing_warnings: list[str]
    assembly_report_markdown: str
