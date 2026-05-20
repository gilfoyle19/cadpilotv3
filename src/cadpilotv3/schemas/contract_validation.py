from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

ContractCheckStatus = Literal["pass", "fail", "warn", "skip"]
ContractCheckSeverity = Literal["critical", "major", "minor", "info"]


class ContractCheck(BaseModel):
    model_config = {
        "extra": "ignore",
    }

    id: str
    category: str
    status: ContractCheckStatus
    severity: ContractCheckSeverity = "info"
    message: str
    evidence: dict[str, Any] = Field(default_factory=dict)


class ContractValidationReport(BaseModel):
    model_config = {
        "extra": "ignore",
    }

    status: Literal["pass", "fail", "warn", "skip"]
    passed: bool
    summary: str
    checks: list[ContractCheck] = Field(default_factory=list)
    failure_count: int = 0
    warning_count: int = 0
    skipped_count: int = 0
    compact_evidence: list[str] = Field(default_factory=list)
