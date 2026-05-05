from pydantic import BaseModel, Field
from typing import Literal


class CoordinateConvention(BaseModel):
    model_config = {
        "extra": "ignore",
    }

    x_direction: str
    y_direction: str
    z_direction: str
    world_origin: str | None = None
    zero_config: str | None = None


class StrategyCandidate(BaseModel):
    model_config = {
        "extra": "ignore",
    }

    strategy: str
    advantage: str
    disadvantage: str


class StrategySelection(BaseModel):
    model_config = {
        "extra": "ignore",
    }

    candidates: list[StrategyCandidate] = Field(default_factory=list)
    winner: str
    rationale: str


class KeyFeature(BaseModel):
    model_config = {
        "extra": "ignore",
    }

    feature: str
    description: str


class PlannedPart(BaseModel):
    model_config = {
        "extra": "ignore",
    }

    name: str
    geometric_role: str | None = None
    local_origin: str | None = None
    modeling_strategy: str
    strategy_selection: StrategySelection
    key_features: list[KeyFeature] = Field(default_factory=list)
    body_type: str = "solid"


class TransformChain(BaseModel):
    model_config = {
        "extra": "ignore",
    }

    part: str
    transforms: list[str] = Field(default_factory=list)
    zero_config_position: str | None = None


class JointDefinition(BaseModel):
    model_config = {
        "extra": "ignore",
    }

    name: str
    type: str
    axis_world: str | None = None
    origin_world: str | None = None
    range_of_motion: str | None = None
    connects: list[str] = Field(default_factory=list)


class InterfaceDefinition(BaseModel):
    model_config = {
        "extra": "ignore",
    }

    name: str
    interface_type: str
    owner: str
    target: str | None = None
    description: str


class FailureRisk(BaseModel):
    model_config = {
        "extra": "ignore",
    }

    risk_name: str
    affected: str | None = None
    description: str
    mitigation: str


class GeometryPlan(BaseModel):
    model_config = {
        "extra": "ignore",
    }

    artifact_type: Literal["single_part", "assembly"]
    coordinate_convention: CoordinateConvention | None = None

    parts: list[PlannedPart] = Field(default_factory=list)
    subassemblies: list[str] = Field(default_factory=list)
    assembly_transform_chain: list[TransformChain] = Field(default_factory=list)
    joint_definitions: list[JointDefinition] = Field(default_factory=list)
    interfaces: list[InterfaceDefinition] = Field(default_factory=list)
    failure_risks: list[FailureRisk] = Field(default_factory=list)