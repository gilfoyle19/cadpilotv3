from __future__ import annotations

from typing import Self

from pydantic import AliasChoices, BaseModel, Field, model_validator


class RepairOutput(BaseModel):
    model_config = {
        "extra": "ignore",
    }

    action: str
    root_cause: str
    fix_description: str | None = None
    affected_function: str | None = None
    patched_code: str | None = Field(
        default=None,
        validation_alias=AliasChoices("patched_code", "patched_excerpt"),
    )
    confidence: str | None = None
    replan_instructions: str | None = None
    cannot_patch_reason: str | None = None

    @model_validator(mode="after")
    def validate_patch_payload(self) -> Self:
        self.action = self.action.strip().lower()
        if self.affected_function is not None:
            self.affected_function = self.affected_function.strip()

        if self.action != "patch":
            return self

        if not self.affected_function:
            raise ValueError("patch repair output requires affected_function")

        if not self.patched_code or not self.patched_code.strip():
            raise ValueError("patch repair output requires patched_code")

        return self
