from __future__ import annotations

from cadpilotv3.config.settings import AppSettings

from cadpilotv3.services.cadquery_execution_sandbox_service import (
    SandboxExecutionArtifacts,
)
from cadpilotv3.schemas.validation import ValidationReport


class ExecutionValidationAgent:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings

    def run(
        self,
        artifacts: SandboxExecutionArtifacts,
    ) -> ValidationReport:
        if not artifacts.syntax_ok:
            return ValidationReport(
                status="syntax_error",
                error_class=self._map_error_class(artifacts.error_type, artifacts.error_message),
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
            )

        if not artifacts.execution_succeeded:
            error_class = self._map_error_class(artifacts.error_type, artifacts.error_message)
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
                error_summary="The script ran without an exception but did not produce any inspectable geometry.",
                execution_time_s=artifacts.execution_time_s,
                geometry_valid=False,
                repair_needed=True,
                repair_complexity="replan",
                geometry_report=None,
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
                error_summary="The script produced at least one degenerate solid with zero or near-zero volume.",
                execution_time_s=artifacts.execution_time_s,
                geometry_valid=False,
                repair_needed=True,
                repair_complexity="replan",
                geometry_report={
                    "part_count": geometry.part_count,
                    "bounding_box_mm": geometry.bounding_box_mm,
                    "volume_mm3": geometry.volume_mm3,
                    "is_manifold": geometry.is_manifold,
                    "face_count": geometry.face_count,
                    "has_zero_volume_parts": geometry.has_zero_volume_parts,
                    "assembly_valid": geometry.assembly_valid,
                },
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
                error_summary="The script produced geometry that is not watertight or topologically valid.",
                execution_time_s=artifacts.execution_time_s,
                geometry_valid=False,
                repair_needed=True,
                repair_complexity="replan",
                geometry_report={
                    "part_count": geometry.part_count,
                    "bounding_box_mm": geometry.bounding_box_mm,
                    "volume_mm3": geometry.volume_mm3,
                    "is_manifold": geometry.is_manifold,
                    "face_count": geometry.face_count,
                    "has_zero_volume_parts": geometry.has_zero_volume_parts,
                    "assembly_valid": geometry.assembly_valid,
                },
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
                error_summary="The script produced parts, but the final assembly is not spatially valid.",
                execution_time_s=artifacts.execution_time_s,
                geometry_valid=False,
                repair_needed=True,
                repair_complexity="replan",
                geometry_report={
                    "part_count": geometry.part_count,
                    "bounding_box_mm": geometry.bounding_box_mm,
                    "volume_mm3": geometry.volume_mm3,
                    "is_manifold": geometry.is_manifold,
                    "face_count": geometry.face_count,
                    "has_zero_volume_parts": geometry.has_zero_volume_parts,
                    "assembly_valid": geometry.assembly_valid,
                },
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
            geometry_report={
                "part_count": geometry.part_count,
                "bounding_box_mm": geometry.bounding_box_mm,
                "volume_mm3": geometry.volume_mm3,
                "is_manifold": geometry.is_manifold,
                "face_count": geometry.face_count,
                "has_zero_volume_parts": geometry.has_zero_volume_parts,
                "assembly_valid": geometry.assembly_valid,
            },
        )

    def _map_error_class(self, error_type: str | None, error_message: str | None) -> str:
        error_type = (error_type or "").lower()
        error_message_l = (error_message or "").lower()

        if error_type == "syntaxerror":
            return "syntax_error"
        if error_type == "indentationerror":
            return "indent_error"
        if error_type == "nameerror":
            return "name_error"
        if error_type == "attributeerror":
            return "api_misuse"
        if error_type == "typeerror":
            return "type_error"
        if error_type == "importerror" or error_type == "modulenotfounderror":
            return "import_error"
        if "fillet" in error_message_l and ("radius" in error_message_l or "notdone" in error_message_l):
            return "fillet_radius_overflow"
        if error_type == "valueerror":
            return "parameter_overflow"
        if "topology" in error_message_l or "brep" in error_message_l:
            return "topology_error"
        if "export" in error_message_l or "path" in error_message_l:
            return "export_format_error"
        if "selector" in error_message_l or "no faces" in error_message_l or "no edges" in error_message_l:
            return "empty_selection"

        return "api_misuse"

    def _map_repair_complexity(self, error_class: str) -> str:
        if error_class in {
            "syntax_error",
            "indent_error",
            "name_error",
            "api_misuse",
            "type_error",
            "parameter_overflow",
            "fillet_radius_overflow",
            "export_format_error",
            "import_error",
        }:
            return "patch"

        return "replan"

    def _build_error_summary(self, artifacts: SandboxExecutionArtifacts) -> str:
        error_class = self._map_error_class(artifacts.error_type, artifacts.error_message)

        if error_class == "syntax_error":
            return "The script could not be parsed because it contains a Python syntax error."
        if error_class == "indent_error":
            return "The script structure is invalid because one or more code blocks are indented incorrectly."
        if error_class == "name_error":
            return "The script references a parameter or variable that was never defined."
        if error_class == "api_misuse":
            return "The geometry generation failed because the script called CadQuery with an invalid method or object usage."
        if error_class == "type_error":
            return "The geometry generation failed because a CadQuery operation received an argument of the wrong type."
        if error_class == "parameter_overflow":
            return "The geometry generation failed because one or more dimensions violate valid geometric limits."
        if error_class == "fillet_radius_overflow":
            return "The fillet operation failed because the requested fillet radius exceeds the available wall thickness."
        if error_class == "import_error":
            return "The script could not run because a required module or import path is unavailable."
        if error_class == "topology_error":
            return "A Boolean or topological modeling operation failed during solid construction."
        if error_class == "empty_selection":
            return "The script attempted a face or edge operation on geometry that did not match the selector assumption."

        return "The generated script failed during execution before valid geometry could be produced."