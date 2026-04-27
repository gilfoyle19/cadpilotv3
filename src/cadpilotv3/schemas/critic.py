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