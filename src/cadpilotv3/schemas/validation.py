from pydantic import BaseModel, Field


class ErrorLocation(BaseModel):
    model_config = {
        "extra": "ignore",
    }

    line: int | None = None
    function: str | None = None
    code_line: str | None = None


class GeometryReport(BaseModel):
    model_config = {
        "extra": "ignore",
    }

    artifact_type: str | None = None
    part_count: int | None = None
    bounding_box_mm: list[float] | None = None
    volume_mm3: float | None = None
    is_manifold: bool | None = None
    face_count: int | None = None
    has_zero_volume_parts: bool | None = None
    assembly_valid: bool | None = None


class ValidationReport(BaseModel):
    model_config = {
        "extra": "ignore",
    }

    status: str
    error_class: str | None = None
    error_location: ErrorLocation | None = None
    error_message: str | None = None
    error_summary: str | None = None
    execution_time_s: float | None = None
    geometry_valid: bool = False
    repair_needed: bool = False
    repair_complexity: str | None = None
    geometry_report: GeometryReport | None = None