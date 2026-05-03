from pydantic import BaseModel, Field


class ExportedFile(BaseModel):
    format: str
    filename: str
    filepath: str
    size_kb: float
    contents: str


class AssemblyReport(BaseModel):
    markdown: str


class ExportSummary(BaseModel):
    fexport_files: list[ExportedFile] = Field(default_factory=list)
    assembly_report_markdown: str
    user_facing_warnings: list[str] = Field(default_factory=list)