from pydantic import BaseModel, Field


class ErrorLocation(BaseModel):
    line: int | None = None
    function: str | None = None


class GeometryReport(BaseModel):
    artifact_type: str | None = None
    volume_mm3: float | None = None
    surface_area_mm2: float | None = None
    bounding_box_mm: list[float] | None = None
    manifold: bool | None = None
    part_count: int | None = None
    body_count: int | None = None
    interface_count: int | None = None
    warnings: list[str] = Field(default_factory=list)


class ValidationReport(BaseModel):
    status: str
    error_class: str | None = None
    error_location: ErrorLocation | None = None
    error_summary: str | None = None
    geometry_valid: bool = False
    repair_needed: bool = False
    repair_complexity: str | None = None
    geometry_report: GeometryReport | None = None