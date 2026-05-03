from typing import Any

from pydantic import BaseModel, Field


class BaseArtifact(BaseModel):
    model_config = {
        "extra": "ignore",
    }

    version: int = Field(default=1, ge=1)
    created_by: str | None = None


class Issue(BaseModel):
    model_config = {
        "extra": "ignore",
    }

    dimension: str
    severity: str
    score: float = Field(ge=0.0, le=1.0)
    description: str
    plan_citation: str
    correction: str


class WarningItem(BaseModel):
    model_config = {
        "extra": "ignore",
    }

    message: str


class KeyValueMetadata(BaseModel):
    model_config = {
        "extra": "ignore",
    }

    key: str
    value: Any