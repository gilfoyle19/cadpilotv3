from pydantic import BaseModel


class RepairOutput(BaseModel):
    action: str
    root_cause: str
    fix_description: str | None = None
    patched_excerpt: str | None = None
    confidence: str | None = None
    replan_instructions: str | None = None
    cannot_patch_reason: str | None = None