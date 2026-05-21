from __future__ import annotations

import json

from pydantic import ValidationError

from cadpilotv3.config.settings import AppSettings
from cadpilotv3.llm import AgentName, get_llm_factory
from cadpilotv3.schemas.critic import CriticBReport
from cadpilotv3.schemas.export import (
    ExportedFile,
    ExportSummary,
)
from cadpilotv3.schemas.intent_spec import IntentSpec
from cadpilotv3.schemas.parameters import ParameterSchema
from cadpilotv3.schemas.validation import ValidationReport
from cadpilotv3.shared import (
    JSONExtractionError,
    ainvoke_text_with_metadata,
    invoke_text_with_metadata,
    load_prompt_text,
    parse_json,
    strip_code_fences,
)
from cadpilotv3.shared.llm_trace import update_llm_trace
from cadpilotv3.shared.prompt_context import select_relevant_few_shot_examples


class ExportSummaryAgent:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.llm_factory = get_llm_factory()

    def run(
        self,
        user_prompt: str,
        spec: IntentSpec,
        parameters: ParameterSchema,
        validation: ValidationReport,
        critic_b_report: CriticBReport,
        export_files: list[ExportedFile],
    ) -> ExportSummary:
        llm = self.llm_factory.get_for_agent(AgentName.EXPORT_SUMMARY)
        prompt = self._build_prompt(
            user_prompt=user_prompt,
            spec=spec,
            parameters=parameters,
            validation=validation,
            critic_b_report=critic_b_report,
            export_files=export_files,
        )

        result = invoke_text_with_metadata(
            llm,
            prompt,
            agent_name=AgentName.EXPORT_SUMMARY.value,
        )
        return self._parse_result(
            result_text=result.text,
            trace_dir=result.trace_dir,
            export_files=export_files,
            critic_b_report=critic_b_report,
        )

    async def arun(
        self,
        user_prompt: str,
        spec: IntentSpec,
        parameters: ParameterSchema,
        validation: ValidationReport,
        critic_b_report: CriticBReport,
        export_files: list[ExportedFile],
    ) -> ExportSummary:
        llm = self.llm_factory.get_for_agent(AgentName.EXPORT_SUMMARY)
        prompt = self._build_prompt(
            user_prompt=user_prompt,
            spec=spec,
            parameters=parameters,
            validation=validation,
            critic_b_report=critic_b_report,
            export_files=export_files,
        )

        result = await ainvoke_text_with_metadata(
            llm,
            prompt,
            agent_name=AgentName.EXPORT_SUMMARY.value,
        )
        return self._parse_result(
            result_text=result.text,
            trace_dir=result.trace_dir,
            export_files=export_files,
            critic_b_report=critic_b_report,
        )

    def _build_prompt(
        self,
        *,
        user_prompt: str,
        spec: IntentSpec,
        parameters: ParameterSchema,
        validation: ValidationReport,
        critic_b_report: CriticBReport,
        export_files: list[ExportedFile],
    ) -> str:
        system_prompt = load_prompt_text(self.settings, "export_summary_agent.md")
        few_shot_prompt = load_prompt_text(
            self.settings,
            "export_summary_examples.md",
        )
        selected_examples = self._select_relevant_examples(
            few_shot_prompt=few_shot_prompt,
            user_prompt=user_prompt,
            spec=spec,
            parameters=parameters,
            validation=validation,
            critic_b_report=critic_b_report,
            export_files=export_files,
        )

        export_files_json = [
            export_file.model_dump()
            for export_file in export_files
        ]

        prompt = "\n\n".join(
            [
                system_prompt.strip(),
                selected_examples.strip(),
                "Original user prompt:",
                user_prompt.strip(),
                "Structured spec:",
                spec.model_dump_json(indent=2),
                "Parameter schema:",
                parameters.model_dump_json(indent=2),
                "Validation report:",
                validation.model_dump_json(indent=2),
                "Critic B report:",
                critic_b_report.model_dump_json(indent=2),
                "Exported files:",
                json.dumps(export_files_json, indent=2),
            ]
        )
        return prompt

    def _select_relevant_examples(
        self,
        *,
        few_shot_prompt: str,
        user_prompt: str,
        spec: IntentSpec,
        parameters: ParameterSchema,
        validation: ValidationReport,
        critic_b_report: CriticBReport,
        export_files: list[ExportedFile],
        max_examples: int = 1,
    ) -> str:
        query_values: list[object] = [
            user_prompt,
            getattr(spec, "component", "") or "",
            getattr(spec, "component_type", "") or "",
            getattr(spec, "style", "") or "",
            getattr(spec, "manufacturing_process", "") or "",
            getattr(spec, "parts", []) or [],
            getattr(spec, "constraints", []) or [],
            getattr(validation, "status", "") or "",
            getattr(validation, "error_class", "") or "",
            getattr(critic_b_report, "routing", "") or "",
            getattr(critic_b_report, "user_facing_warnings", []) or [],
        ]

        geometry_report = getattr(validation, "geometry_report", None)
        query_values.extend(
            [
                getattr(geometry_report, "part_count", "") or "",
                getattr(geometry_report, "bounding_box_mm", "") or "",
            ]
        )
        for child in getattr(geometry_report, "child_metadata", []) or []:
            query_values.extend(
                [
                    getattr(child, "name", "") or "",
                    getattr(child, "bounding_box_mm", "") or "",
                    getattr(child, "volume_mm3", "") or "",
                ]
            )

        for name, parameter in (getattr(parameters, "parameters", {}) or {}).items():
            query_values.extend(
                [
                    name,
                    getattr(parameter, "name", "") or "",
                    getattr(parameter, "description", "") or "",
                    getattr(parameter, "constraint", "") or "",
                    getattr(parameter, "derived_from", "") or "",
                ]
            )

        for export_file in export_files:
            query_values.extend(
                [
                    getattr(export_file, "format", "") or "",
                    getattr(export_file, "filename", "") or "",
                    getattr(export_file, "contents", "") or "",
                ]
            )

        return select_relevant_few_shot_examples(
            few_shot_prompt=few_shot_prompt,
            query_values=query_values,
            heading="## Selected Export Summary Few-Shots",
            max_examples=max_examples,
        )

    def _parse_result(
        self,
        *,
        result_text: str,
        trace_dir: str | None,
        export_files: list[ExportedFile],
        critic_b_report: CriticBReport,
    ) -> ExportSummary:
        try:
            parsed_json = parse_json(result_text)
            summary = ExportSummary.model_validate(parsed_json)
            update_llm_trace(
                trace_dir,
                metadata_updates={
                    "parse_status": "passed",
                    "validation_status": "passed",
                    "schema": ExportSummary.__name__,
                },
                files={
                    "parsed_output.json": json.dumps(parsed_json, indent=2),
                    "validated_output.json": summary.model_dump_json(indent=2),
                },
            )
            return summary
        except JSONExtractionError:
            update_llm_trace(
                trace_dir,
                metadata_updates={
                    "parse_status": "failed",
                    "validation_status": "fallback_markdown",
                    "schema": ExportSummary.__name__,
                },
            )
            markdown_report = strip_code_fences(result_text)
            return ExportSummary(
                export_files=export_files,
                assembly_report_markdown=markdown_report,
                user_facing_warnings=critic_b_report.user_facing_warnings,
            )
        except ValidationError as exc:
            update_llm_trace(
                trace_dir,
                metadata_updates={
                    "parse_status": "passed",
                    "validation_status": "failed",
                    "schema": ExportSummary.__name__,
                    "validation_error": str(exc),
                },
            )
            raise
