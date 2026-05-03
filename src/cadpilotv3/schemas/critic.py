from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from cadpilotv3.schemas.common import Issue


class CriticReport(BaseModel):
    checkpoint: str
    verdict: str
    fidelity_score: float = Field(ge=0.0, le=1.0)
    drift_detected: bool | None = None
    issues: list[Issue] = Field(default_factory=list)
    routing: str
    user_facing_warnings: list[str] = Field(default_factory=list)

class CriticCheckpointBIssue(BaseModel):
    dimension: str
    severity: Literal["critical", "major", "minor"]
    score: float = Field(ge=0.0, le=1.0)
    description: str
    evidence: str
    suggested_routing: Literal["replan", "patch", "warn_only"]
    correction: str


class CriticCheckpointBDimensionScores(BaseModel):
    dof_count_verification: float = Field(ge=0.0, le=1.0)
    scale_consistency: float = Field(ge=0.0, le=1.0)
    constraint_satisfaction: float = Field(ge=0.0, le=1.0)
    completeness: float = Field(ge=0.0, le=1.0)
    checkpoint_a_resolution: float = Field(ge=0.0, le=1.0)
    regression_detection: float = Field(ge=0.0, le=1.0)


class CriticBReport(BaseModel):
    checkpoint: Literal["B"] = "B"
    verdict: Literal["pass", "conditional_pass", "fail"]
    overall_fidelity_score: float = Field(ge=0.0, le=1.0)
    dimension_scores: CriticCheckpointBDimensionScores
    issues: list[CriticCheckpointBIssue]
    routing: Literal["export", "patch", "replan"]
    patch_instructions: str | None = None
    replan_instructions: str | None = None
    user_facing_warnings: list[str] = Field(default_factory=list)