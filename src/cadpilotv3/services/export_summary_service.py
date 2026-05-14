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
            "Running geometry export before export_summary_agent",
            extra={
                "component": spec.component,
                "output_format": spec.output_format,
            },
        )

        export_files = self._collect_sandbox_exports(
            geometry_object=geometry_object,
            output_format=spec.output_format,
        )

        if not export_files:
            export_artifacts = self.exporter.export(
                geometry_object=geometry_object,
                component_name=spec.component,
                output_format=spec.output_format,
            )

            export_files = [
                ExportedFile(
                    format=artifact.format,
                    filename=artifact.filename,
                    filepath=artifact.filepath,
                    size_kb=artifact.size_kb,
                    contents=artifact.contents,
                )
                for artifact in export_artifacts
            ]

        logger.info(
            "Geometry export completed",
            extra={"export_file_count": len(export_files)},
        )

        result = self.agent.run(
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
            "Running geometry export before export_summary_agent",
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

        result = await self.agent.arun(
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
