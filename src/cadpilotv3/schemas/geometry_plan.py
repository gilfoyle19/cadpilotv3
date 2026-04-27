from pydantic import BaseModel, Field


class CoordinateConvention(BaseModel):
    x: str
    y: str
    z: str
    zero_config: str | None = None


class PlannedPart(BaseModel):
    name: str
    role: str | None = None
    modeling_strategy: str
    strategy_rationale: str
    origin: str
    key_features: list[str] = Field(default_factory=list)
    body_type: str = "solid"


class TransformChain(BaseModel):
    target: str
    transform_sequence: list[str] = Field(default_factory=list)


class JointDefinition(BaseModel):
    name: str
    type: str
    axis: str | None = None
    origin: str | None = None
    parent: str | None = None
    child: str | None = None


class InterfaceDefinition(BaseModel):
    name: str
    interface_type: str
    owner: str
    target: str | None = None
    description: str


class FailureRisk(BaseModel):
    risk: str
    mitigation: str


class GeometryPlan(BaseModel):
    artifact_type: str = "single_part"
    coordinate_convention: CoordinateConvention | None = None

    parts: list[PlannedPart] = Field(default_factory=list)
    subassemblies: list[str] = Field(default_factory=list)
    assembly_transform_chain: list[TransformChain] = Field(default_factory=list)
    joint_definitions: list[JointDefinition] = Field(default_factory=list)
    interfaces: list[InterfaceDefinition] = Field(default_factory=list)
    failure_risks: list[FailureRisk] = Field(default_factory=list)