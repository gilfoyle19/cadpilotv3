from __future__ import annotations

import asyncio
import logging
import shutil
from pathlib import Path
from typing import Any

from cadpilotv3.agents.export_summary_agent import ExportSummaryAgent
from cadpilotv3.config.settings import AppSettings
from cadpilotv3.schemas.critic import CriticBReport
from cadpilotv3.schemas.export import (
    ExportedFile,
    ExportSummary,
)
from cadpilotv3.schemas.intent_spec import IntentSpec
from cadpilotv3.schemas.parameters import ParameterSchema
from cadpilotv3.schemas.validation import ValidationReport
from cadpilotv3.services.geometry_export_service import GeometryExportService

logger = logging.getLogger(__name__)


class ExportSummaryService:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.exporter = GeometryExportService(output_dir="output")
        self.agent = ExportSummaryAgent(settings)

    def execute(
        self,
        geometry_object: Any,
        user_prompt: str,
        spec: IntentSpec,
        parameters: ParameterSchema,
        validation: ValidationReport,
        critic_b_report: CriticBReport,
    ) -> ExportSummary:
        logger.info(
            "Running geometry export before export summary",
            extra={
                "component": spec.component,
                "output_format": spec.output_format,
            },
        )

        export_files = self._prepare_export_files(
            geometry_object,
            spec.component,
            spec.output_format,
        )

        logger.info(
            "Geometry export completed",
            extra={"export_file_count": len(export_files)},
        )

        result = self._build_summary(
            user_prompt=user_prompt,
            spec=spec,
            parameters=parameters,
            validation=validation,
            critic_b_report=critic_b_report,
            export_files=export_files,
        )
        self._fill_summary_defaults(
            result=result,
            export_files=export_files,
            critic_b_report=critic_b_report,
        )

        self._log_summary_completed(result)

        return result

    async def aexecute(
        self,
        geometry_object: Any,
        user_prompt: str,
        spec: IntentSpec,
        parameters: ParameterSchema,
        validation: ValidationReport,
        critic_b_report: CriticBReport,
    ) -> ExportSummary:
        logger.info(
            "Running geometry export before export summary",
            extra={
                "component": spec.component,
                "output_format": spec.output_format,
            },
        )

        export_files = await asyncio.to_thread(
            self._prepare_export_files,
            geometry_object,
            spec.component,
            spec.output_format,
        )

        logger.info(
            "Geometry export completed",
            extra={"export_file_count": len(export_files)},
        )

        result = await self._abuild_summary(
            user_prompt=user_prompt,
            spec=spec,
            parameters=parameters,
            validation=validation,
            critic_b_report=critic_b_report,
            export_files=export_files,
        )
        self._fill_summary_defaults(
            result=result,
            export_files=export_files,
            critic_b_report=critic_b_report,
        )

        self._log_summary_completed(result)

        return result

    def _prepare_export_files(
        self,
        geometry_object: Any,
        component_name: str,
        output_format: str,
    ) -> list[ExportedFile]:
        export_files = self._collect_sandbox_exports(
            geometry_object=geometry_object,
            output_format=output_format,
        )

        if export_files:
            return export_files

        export_artifacts = self.exporter.export(
            geometry_object=geometry_object,
            component_name=component_name,
            output_format=output_format,
        )

        return [
            ExportedFile(
                format=artifact.format,
                filename=artifact.filename,
                filepath=artifact.filepath,
                size_kb=artifact.size_kb,
                contents=artifact.contents,
            )
            for artifact in export_artifacts
        ]

    def _build_summary(
        self,
        *,
        user_prompt: str,
        spec: IntentSpec,
        parameters: ParameterSchema,
        validation: ValidationReport,
        critic_b_report: CriticBReport,
        export_files: list[ExportedFile],
    ) -> ExportSummary:
        if self.settings.cad_enable_llm_export_summary:
            return self.agent.run(
                user_prompt=user_prompt,
                spec=spec,
                parameters=parameters,
                validation=validation,
                critic_b_report=critic_b_report,
                export_files=export_files,
            )

        return self._build_deterministic_summary(
            user_prompt=user_prompt,
            spec=spec,
            parameters=parameters,
            validation=validation,
            critic_b_report=critic_b_report,
            export_files=export_files,
        )

    async def _abuild_summary(
        self,
        *,
        user_prompt: str,
        spec: IntentSpec,
        parameters: ParameterSchema,
        validation: ValidationReport,
        critic_b_report: CriticBReport,
        export_files: list[ExportedFile],
    ) -> ExportSummary:
        if self.settings.cad_enable_llm_export_summary:
            return await self.agent.arun(
                user_prompt=user_prompt,
                spec=spec,
                parameters=parameters,
                validation=validation,
                critic_b_report=critic_b_report,
                export_files=export_files,
            )

        return self._build_deterministic_summary(
            user_prompt=user_prompt,
            spec=spec,
            parameters=parameters,
            validation=validation,
            critic_b_report=critic_b_report,
            export_files=export_files,
        )

    def _fill_summary_defaults(
        self,
        *,
        result: ExportSummary,
        export_files: list[ExportedFile],
        critic_b_report: CriticBReport,
    ) -> None:
        if not result.export_files:
            result.export_files = export_files

        if not result.user_facing_warnings:
            result.user_facing_warnings = critic_b_report.user_facing_warnings

    def _log_summary_completed(self, result: ExportSummary) -> None:
        logger.info(
            "Export summary completed",
            extra={
                "report_length": len(result.assembly_report_markdown),
                "export_file_count": len(result.export_files),
            },
        )

    def _build_deterministic_summary(
        self,
        *,
        user_prompt: str,
        spec: IntentSpec,
        parameters: ParameterSchema,
        validation: ValidationReport,
        critic_b_report: CriticBReport,
        export_files: list[ExportedFile],
    ) -> ExportSummary:
        component = spec.component or "Generated CAD Model"
        warnings = list(getattr(critic_b_report, "user_facing_warnings", []) or [])
        geometry = validation.geometry_report

        lines = [
            f"# {_markdown_escape(component)}",
            "",
            "## Overview",
            "",
            f"- Request: {_markdown_escape(user_prompt.strip())}",
            f"- Component type: {_format_optional(spec.component_type)}",
            f"- Manufacturing process: {_format_optional(spec.manufacturing_process)}",
            f"- Units: {_format_optional(spec.units)}",
            f"- Output format: {_format_optional(spec.output_format)}",
            "",
            "## Validation",
            "",
            f"- Status: {_format_optional(validation.status)}",
            f"- Geometry valid: {_format_bool(validation.geometry_valid)}",
            f"- Repair needed: {_format_bool(validation.repair_needed)}",
            f"- Summary: {_format_optional(validation.error_summary)}",
        ]

        if geometry is not None:
            lines.extend(
                [
                    "",
                    "## Geometry",
                    "",
                    f"- Artifact type: {_format_optional(geometry.artifact_type)}",
                    f"- Part count: {_format_optional(geometry.part_count)}",
                    f"- Bounding box: {_format_vector(geometry.bounding_box_mm)}",
                    f"- Volume: {_format_number(geometry.volume_mm3, 'mm^3')}",
                    f"- Face count: {_format_optional(geometry.face_count)}",
                    f"- Manifold: {_format_bool(geometry.is_manifold)}",
                    f"- Assembly valid: {_format_bool(geometry.assembly_valid)}",
                ]
            )
            if geometry.child_metadata:
                lines.extend(
                    [
                        "",
                        "### Parts",
                        "",
                        "| Part | Bounding Box | Center | Volume |",
                        "| --- | --- | --- | --- |",
                    ]
                )
                for child in geometry.child_metadata:
                    lines.append(
                        "| "
                        f"{_format_optional(child.name)} | "
                        f"{_format_vector(child.bounding_box_mm)} | "
                        f"{_format_vector(child.center_mm)} | "
                        f"{_format_number(child.volume_mm3, 'mm^3')} |"
                    )

        lines.extend(self._parameter_summary_lines(parameters))
        lines.extend(self._export_file_summary_lines(export_files))

        if warnings:
            lines.extend(["", "## Warnings", ""])
            lines.extend(f"- {_markdown_escape(warning)}" for warning in warnings)

        return ExportSummary(
            export_files=export_files,
            assembly_report_markdown="\n".join(lines).strip() + "\n",
            user_facing_warnings=warnings,
        )

    def _parameter_summary_lines(self, parameters: ParameterSchema) -> list[str]:
        parameter_items = sorted((parameters.parameters or {}).items())
        if not parameter_items:
            return []

        lines = [
            "",
            "## Key Parameters",
            "",
            "| Name | Value | Unit | Description |",
            "| --- | --- | --- | --- |",
        ]
        for name, parameter in parameter_items[:24]:
            lines.append(
                "| "
                f"{_markdown_escape(name)} | "
                f"{_markdown_escape(str(parameter.value))} | "
                f"{_markdown_escape(parameter.unit)} | "
                f"{_markdown_escape(parameter.description)} |"
            )
        if len(parameter_items) > 24:
            lines.append(
                f"| ... | {len(parameter_items) - 24} additional parameters omitted | | |"
            )
        return lines

    def _export_file_summary_lines(self, export_files: list[ExportedFile]) -> list[str]:
        lines = [
            "",
            "## Export Files",
            "",
            "| Format | Filename | Size KB | Path |",
            "| --- | --- | --- | --- |",
        ]
        if not export_files:
            lines.append("| None | No exported files were reported | 0 | |")
            return lines

        for export_file in export_files:
            lines.append(
                "| "
                f"{_markdown_escape(export_file.format)} | "
                f"{_markdown_escape(export_file.filename)} | "
                f"{_format_optional(export_file.size_kb)} | "
                f"{_markdown_escape(export_file.filepath)} |"
            )
        return lines

    def _collect_sandbox_exports(
        self,
        geometry_object: Any,
        output_format: str,
    ) -> list[ExportedFile]:
        if not isinstance(geometry_object, dict):
            return []

        workspace_dir = geometry_object.get("workspace_dir")
        if not workspace_dir:
            return []

        workspace_path = Path(workspace_dir)
        if not workspace_path.exists():
            return []

        extensions = self._extensions_for_format(output_format)
        exported_paths = [
            path
            for path in workspace_path.rglob("*")
            if path.is_file() and path.suffix.lower() in extensions
        ]

        export_files: list[ExportedFile] = []
        for source_path in sorted(exported_paths):
            target_path = self.exporter.output_dir / source_path.name
            shutil.copy2(source_path, target_path)
            export_files.append(
                ExportedFile(
                    format=output_format.upper(),
                    filename=target_path.name,
                    filepath=str(target_path),
                    size_kb=round(target_path.stat().st_size / 1024, 2),
                    contents="Generated by CadQuery script in execution sandbox",
                )
            )

        return export_files

    def _extensions_for_format(self, output_format: str) -> set[str]:
        fmt = output_format.upper()
        if fmt == "STEP":
            return {".step", ".stp"}
        if fmt == "STL":
            return {".stl"}
        if fmt == "DXF":
            return {".dxf"}
        if fmt == "IGES":
            return {".iges", ".igs"}
        return {f".{output_format.lower()}"}


def _format_bool(value: bool | None) -> str:
    if value is None:
        return "not reported"
    return "yes" if value else "no"


def _format_number(value: float | int | None, unit: str) -> str:
    if value is None:
        return "not reported"
    return f"{value:g} {unit}"


def _format_optional(value: Any) -> str:
    if value is None or value == "":
        return "not reported"
    return _markdown_escape(str(value))


def _format_vector(values: list[float] | None) -> str:
    if not values:
        return "not reported"
    return _markdown_escape(" x ".join(f"{value:g}" for value in values) + " mm")


def _markdown_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()
