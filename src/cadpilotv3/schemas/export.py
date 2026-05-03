from pydantic import BaseModel, Field


class ExportedFile(BaseModel):
    model_config = {
        "extra": "ignore",
    }

    format: str
    filename: str
    filepath: str
    size_kb: float
    contents: str


class AssemblyReport(BaseModel):
    model_config = {
        "extra": "ignore",
    }

    markdown: str


class ExportSummary(BaseModel):
    model_config = {
        "extra": "ignore",
    }

    export_files: list[ExportedFile] = Field(default_factory=list)
    assembly_report_markdown: str
    user_facing_warnings: list[str] = Field(default_factory=list)