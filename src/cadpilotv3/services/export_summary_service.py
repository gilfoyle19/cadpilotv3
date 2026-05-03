from __future__ import annotations

import logging
from typing import Any

from cadpilotv3.agents.export_summary_agent import ExportSummaryAgent
from cadpilotv3.config.settings import AppSettings
from cadpilotv3.services.geometry_export_service import GeometryExportService

from cadpilotv3.schemas.intent_spec import IntentSpec
from cadpilotv3.schemas.parameters import ParameterSchema
from cadpilotv3.schemas.validation import ValidationReport
from cadpilotv3.schemas.critic import CriticBReport
from cadpilotv3.schemas.export import (
    ExportedFile,
    ExportSummary,
)

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

        if not result.export_files:
            result.export_files = export_files

        if not result.user_facing_warnings:
            result.user_facing_warnings = critic_b_report.user_facing_warnings

        logger.info(
            "Export summary completed",
            extra={
                "report_length": len(result.assembly_report_markdown),
                "export_file_count": len(result.export_files),
            },
        )

        return result