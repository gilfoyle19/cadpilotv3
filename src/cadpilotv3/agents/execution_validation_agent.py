from __future__ import annotations

from cadpilotv3.config.settings import AppSettings
from cadpilotv3.schemas.validation import ValidationReport
from cadpilotv3.services.cadquery_execution_sandbox_service import (
    SandboxExecutionArtifacts,
)

PATCHABLE_ERROR_CLASSES = frozenset(
    {
        "syntax_error",
        "indent_error",
        "name_error",
        "api_misuse",
        "type_error",
        "parameter_overflow",
        "fillet_radius_overflow",
        "export_format_error",
        "import_error",
    }
)


class ExecutionValidationAgent:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings

    def run(
        self,
        artifacts: SandboxExecutionArtifacts,
    ) -> ValidationReport:
        if not artifacts.syntax_ok:
            error_class = self._map_error_class(
                artifacts.error_type,
                artifacts.error_message,
                artifacts.traceback_text,
                artifacts.error_location.code_line,
            )
            return ValidationReport(
                status="syntax_error",
                error_class=error_class,
                error_location={
                    "line": artifacts.error_location.line,
                    "function": artifacts.error_location.function,
                    "code_line": artifacts.error_location.code_line,
                },
                error_message=artifacts.error_message,
                error_summary=self._build_error_summary(artifacts),
                execution_time_s=artifacts.execution_time_s,
                geometry_valid=False,
                repair_needed=True,
                repair_complexity="patch",
                geometry_report=None,
                **self._artifact_validation_payload(artifacts),
            )

        if not artifacts.execution_succeeded:
            error_class = self._map_error_class(
                artifacts.error_type,
                artifacts.error_message,
                artifacts.traceback_text,
                artifacts.error_location.code_line,
            )
            repair_complexity = self._map_repair_complexity(error_class)

            return ValidationReport(
                status="runtime_error",
                error_class=error_class,
                error_location={
                    "line": artifacts.error_location.line,
                    "function": artifacts.error_location.function,
                    "code_line": artifacts.error_location.code_line,
                },
                error_message=artifacts.error_message,
                error_summary=self._build_error_summary(artifacts),
                execution_time_s=artifacts.execution_time_s,
                geometry_valid=False,
                repair_needed=True,
                repair_complexity=repair_complexity,
                geometry_report=None,
                **self._artifact_validation_payload(artifacts),
            )

        if artifacts.geometry_report is None:
            return ValidationReport(
                status="runtime_error",
                error_class="silent_empty_result",
                error_location={
                    "line": None,
                    "function": "build_assembly",
                    "code_line": None,
                },
                error_message=None,
                error_summary=(
                    "The script ran without an exception but did not produce "
                    "any inspectable geometry."
                ),
                execution_time_s=artifacts.execution_time_s,
                geometry_valid=False,
                repair_needed=True,
                repair_complexity="replan",
                geometry_report=None,
                **self._artifact_validation_payload(artifacts),
            )

        geometry = artifacts.geometry_report

        if geometry.has_zero_volume_parts:
            return ValidationReport(
                status="geometry_invalid",
                error_class="zero_volume_solid",
                error_location={
                    "line": None,
                    "function": "build_assembly",
                    "code_line": None,
                },
                error_message=None,
                error_summary=(
                    "The script produced at least one degenerate solid with "
                    "zero or near-zero volume."
                ),
                execution_time_s=artifacts.execution_time_s,
                geometry_valid=False,
                repair_needed=True,
                repair_complexity="replan",
                geometry_report=self._geometry_report_payload(geometry),
                **self._artifact_validation_payload(artifacts),
            )

        if not geometry.is_manifold:
            return ValidationReport(
                status="geometry_invalid",
                error_class="non_manifold_geometry",
                error_location={
                    "line": None,
                    "function": "build_assembly",
                    "code_line": None,
                },
                error_message=None,
                error_summary=(
                    "The script produced geometry that is not watertight or "
                    "topologically valid."
                ),
                execution_time_s=artifacts.execution_time_s,
                geometry_valid=False,
                repair_needed=True,
                repair_complexity="replan",
                geometry_report=self._geometry_report_payload(geometry),
                **self._artifact_validation_payload(artifacts),
            )

        if not geometry.assembly_valid:
            return ValidationReport(
                status="geometry_invalid",
                error_class="assembly_misalignment",
                error_location={
                    "line": None,
                    "function": "build_assembly",
                    "code_line": None,
                },
                error_message=None,
                error_summary=(
                    "The script produced parts, but the final assembly is not "
                    "spatially valid."
                ),
                execution_time_s=artifacts.execution_time_s,
                geometry_valid=False,
                repair_needed=True,
                repair_complexity="replan",
                geometry_report=self._geometry_report_payload(geometry),
                **self._artifact_validation_payload(artifacts),
            )

        return ValidationReport(
            status="success",
            error_class=None,
            error_location={
                "line": None,
                "function": None,
                "code_line": None,
            },
            error_message=None,
            error_summary="The script executed successfully and produced valid geometry.",
            execution_time_s=artifacts.execution_time_s,
            geometry_valid=True,
            repair_needed=False,
            repair_complexity=None,
            geometry_report=self._geometry_report_payload(geometry),
            **self._artifact_validation_payload(artifacts),
        )

    async def arun(
        self,
        artifacts: SandboxExecutionArtifacts,
    ) -> ValidationReport:
        return self.run(artifacts)

    def _geometry_report_payload(self, geometry) -> dict:
        return {
            "part_count": geometry.part_count,
            "bounding_box_mm": geometry.bounding_box_mm,
            "volume_mm3": geometry.volume_mm3,
            "is_manifold": geometry.is_manifold,
            "face_count": geometry.face_count,
            "has_zero_volume_parts": geometry.has_zero_volume_parts,
            "assembly_valid": geometry.assembly_valid,
            "child_metadata": [
                {
                    "name": child.name,
                    "bounding_box_mm": child.bounding_box_mm,
                    "center_mm": child.center_mm,
                    "volume_mm3": child.volume_mm3,
                }
                for child in (geometry.child_metadata or [])
            ],
        }

    def _artifact_validation_payload(self, artifacts: SandboxExecutionArtifacts) -> dict:
        return {
            "build_manifest": artifacts.build_manifest,
            "generated_validation": artifacts.generated_validation,
        }

    def _map_error_class(
        self,
        error_type: str | None,
        error_message: str | None,
        traceback_text: str | None = None,
        code_line: str | None = None,
    ) -> str:
        error_type_l = (error_type or "").lower()
        diagnostic_text = " ".join(
            part
            for part in (
                error_type or "",
                error_message or "",
                traceback_text or "",
                code_line or "",
            )
            if part
        ).lower()

        if error_type_l == "syntaxerror":
            return "syntax_error"
        if error_type_l in {"indentationerror", "taberror"}:
            return "indent_error"
        if error_type_l in {"nameerror", "unboundlocalerror"}:
            return "name_error"
        if error_type_l in {"importerror", "modulenotfounderror"}:
            return "import_error"

        if self._looks_like_export_failure(diagnostic_text):
            return "export_format_error"
        if self._looks_like_empty_selection(diagnostic_text):
            return "empty_selection"
        if self._looks_like_fillet_radius_failure(diagnostic_text):
            return "fillet_radius_overflow"
        if self._looks_like_degenerate_sketch(diagnostic_text):
            return "degenerate_sketch"
        if self._looks_like_topology_failure(diagnostic_text):
            return "topology_error"

        if error_type_l in {"attributeerror", "dispatcherror", "notimplementederror"}:
            return "api_misuse"
        if error_type_l == "typeerror":
            return "type_error"
        if error_type_l == "valueerror":
            return "parameter_overflow"
        if "multimethod" in diagnostic_text or "no method found" in diagnostic_text:
            return "api_misuse"
        if self._looks_like_parameter_overflow(diagnostic_text):
            return "parameter_overflow"

        return "api_misuse"

    def _looks_like_export_failure(self, diagnostic_text: str) -> bool:
        export_terms = (
            "export",
            "exporters.",
            ".step",
            ".stp",
            ".stl",
            ".brep",
            "unsupported format",
            "file extension",
            "permission denied",
            "no such file or directory",
        )
        return any(term in diagnostic_text for term in export_terms)

    def _looks_like_empty_selection(self, diagnostic_text: str) -> bool:
        explicit_empty_selection_terms = (
            "empty selection",
            "nothing selected",
            "no faces",
            "no face",
            "no edges",
            "no edge",
            "selector",
            "selected no objects",
            "did not match",
        )
        if any(term in diagnostic_text for term in explicit_empty_selection_terms):
            return True

        selector_code_terms = (
            ".faces",
            ".edges",
            "faces(",
            "edges(",
            "vertices(",
            ".vertices",
        )
        selection_failure_terms = (
            "list index out of range",
            "not enough values",
            "no values",
            "empty list",
        )
        return any(term in diagnostic_text for term in selector_code_terms) and any(
            term in diagnostic_text for term in selection_failure_terms
        )

    def _looks_like_fillet_radius_failure(self, diagnostic_text: str) -> bool:
        has_fillet_or_chamfer = "fillet" in diagnostic_text or "chamfer" in diagnostic_text
        failure_terms = (
            "radius",
            "notdone",
            "stdfail",
            "brepfillet",
            "failed",
            "unable",
        )
        return has_fillet_or_chamfer and any(term in diagnostic_text for term in failure_terms)

    def _looks_like_topology_failure(self, diagnostic_text: str) -> bool:
        topology_terms = (
            "topology",
            "topological",
            "brep",
            "brep_api",
            "brepalgo",
            "topods",
            "standard_failure",
            "stdfail_notdone",
            "boolean",
            "bopalgo",
            "cut failed",
            "fuse failed",
            "operation failed",
            "non-manifold",
            "non manifold",
        )
        return any(term in diagnostic_text for term in topology_terms)

    def _looks_like_degenerate_sketch(self, diagnostic_text: str) -> bool:
        sketch_terms = (
            "degenerate sketch",
            "self-intersect",
            "self intersect",
            "wire is not closed",
            "wire not closed",
            "cannot build face",
            "invalid wire",
        )
        return any(term in diagnostic_text for term in sketch_terms)

    def _looks_like_parameter_overflow(self, diagnostic_text: str) -> bool:
        dimension_terms = (
            "negative",
            "must be positive",
            "greater than zero",
            "less than or equal",
            "out of bounds",
            "invalid dimension",
            "too large",
            "wall thickness",
        )
        return any(term in diagnostic_text for term in dimension_terms)

    def _map_repair_complexity(self, error_class: str) -> str:
        if error_class in PATCHABLE_ERROR_CLASSES:
            return "patch"

        return "replan"

    def _build_error_summary(self, artifacts: SandboxExecutionArtifacts) -> str:
        error_class = self._map_error_class(
            artifacts.error_type,
            artifacts.error_message,
            artifacts.traceback_text,
            artifacts.error_location.code_line,
        )

        if error_class == "syntax_error":
            return "The script could not be parsed because it contains a Python syntax error."
        if error_class == "indent_error":
            return (
                "The script structure is invalid because one or more code "
                "blocks are indented incorrectly."
            )
        if error_class == "name_error":
            return "The script references a parameter or variable that was never defined."
        if error_class == "api_misuse":
            return (
                "The geometry generation failed because the script called "
                "CadQuery with an invalid method or object usage."
            )
        if error_class == "type_error":
            return (
                "The geometry generation failed because a CadQuery operation "
                "received an argument of the wrong type."
            )
        if error_class == "parameter_overflow":
            return (
                "The geometry generation failed because one or more dimensions "
                "violate valid geometric limits."
            )
        if error_class == "fillet_radius_overflow":
            return (
                "The fillet operation failed because the requested fillet "
                "radius exceeds the available wall thickness."
            )
        if error_class == "import_error":
            return (
                "The script could not run because a required module or import "
                "path is unavailable."
            )
        if error_class == "export_format_error":
            return (
                "The geometry may have been built, but the script failed while "
                "writing the requested CAD export."
            )
        if error_class == "topology_error":
            return "A Boolean or topological modeling operation failed during solid construction."
        if error_class == "degenerate_sketch":
            return (
                "A 2D profile could not form a valid closed sketch for solid "
                "construction."
            )
        if error_class == "empty_selection":
            return (
                "The script attempted a face or edge operation on geometry "
                "that did not match the selector assumption."
            )

        return (
            "The generated script failed during execution before valid geometry "
            "could be produced."
        )
