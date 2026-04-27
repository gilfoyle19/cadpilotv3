from typing import Any

from pydantic import BaseModel, Field


class BaseArtifact(BaseModel):
    version: int = Field(default=1, ge=1)
    created_by: str | None = None


class Issue(BaseModel):
    dimension: str
    severity: str
    description: str
    suggested_routing: str | None = None


class WarningItem(BaseModel):
    message: str


class KeyValueMetadata(BaseModel):
    key: str
    value: Any