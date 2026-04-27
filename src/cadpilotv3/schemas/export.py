from pydantic import BaseModel, Field


class ExportedFile(BaseModel):
    format: str
    path: str
    size_bytes: int | None = None


class AssemblyReport(BaseModel):
    markdown: str


class ExportSummary(BaseModel):
    files: list[ExportedFile] = Field(default_factory=list)
    assembly_report: AssemblyReport | None = None