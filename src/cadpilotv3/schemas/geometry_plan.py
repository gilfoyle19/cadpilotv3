from typing import Literal

from pydantic import BaseModel, Field, model_validator


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


class FeatureContract(BaseModel):
    model_config = {
        "extra": "ignore",
    }

    id: str
    host_part: str
    type: str
    operation: str | None = None
    axis: str | None = None
    center: list[str | float | int] | str | None = None
    dimensions: dict[str, str | float | int | None] = Field(default_factory=dict)
    count_group: str | None = None
    required: bool = True
    description: str | None = None


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


class AssemblyAxisContract(BaseModel):
    model_config = {
        "extra": "ignore",
    }

    x_axis: str
    y_axis: str
    z_axis: str
    primary_separation_axis: str | None = None
    description: str | None = None


class FunctionalFace(BaseModel):
    model_config = {
        "extra": "ignore",
    }

    name: str
    normal_axis: str
    role: str
    mates_with: str | None = None


class PartFrame(BaseModel):
    model_config = {
        "extra": "ignore",
    }

    part: str
    local_origin: str
    world_center: str | None = None
    approximate_bounding_box_mm: list[float] | None = None
    functional_faces: list[FunctionalFace] = Field(default_factory=list)


class AssemblyPlacementConstraint(BaseModel):
    model_config = {
        "extra": "ignore",
    }

    name: str
    constraint_type: str
    parts: list[str] = Field(default_factory=list)
    description: str


class AssemblyContract(BaseModel):
    model_config = {
        "extra": "ignore",
    }

    id: str
    type: str
    parts: list[str] = Field(default_factory=list)
    axes: list[str] = Field(default_factory=list)
    feature_refs: list[str] = Field(default_factory=list)
    target: str | float | int | None = None
    tolerance_mm: float | None = None
    description: str


class AlignmentGroup(BaseModel):
    model_config = {
        "extra": "ignore",
    }

    name: str
    axis: str
    center_reference: str
    members: list[str] = Field(default_factory=list)
    tolerance_mm: float | None = None
    description: str | None = None


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
    required_features: list[str] = Field(default_factory=list)
    feature_contracts: list[FeatureContract] = Field(default_factory=list)
    subassemblies: list[str] = Field(default_factory=list)
    assembly_axes: AssemblyAxisContract | None = None
    part_frames: list[PartFrame] = Field(default_factory=list)
    assembly_placement_constraints: list[AssemblyPlacementConstraint] = Field(
        default_factory=list
    )
    assembly_contracts: list[AssemblyContract] = Field(default_factory=list)
    alignment_groups: list[AlignmentGroup] = Field(default_factory=list)
    forbidden_layouts: list[str] = Field(default_factory=list)
    assembly_transform_chain: list[TransformChain] = Field(default_factory=list)
    joint_definitions: list[JointDefinition] = Field(default_factory=list)
    interfaces: list[InterfaceDefinition] = Field(default_factory=list)
    failure_risks: list[FailureRisk] = Field(default_factory=list)

    @model_validator(mode="after")
    def populate_required_features(self) -> "GeometryPlan":
        if not self.required_features and self.feature_contracts:
            self.required_features = [
                contract.id for contract in self.feature_contracts if contract.required
            ]
        return self
