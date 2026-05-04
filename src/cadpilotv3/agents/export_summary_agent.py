from __future__ import annotations

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
    invoke_text,
    load_prompt_text,
    parse_json,
    strip_code_fences,
)


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

        system_prompt = load_prompt_text(self.settings, "export_summary_agent.md")
        few_shot_prompt = load_prompt_text(
            self.settings,
            "export_summary_examples.md",
        )

        export_files_json = [
            export_file.model_dump()
            for export_file in export_files
        ]

        prompt = "\n\n".join(
            [
                system_prompt.strip(),
                few_shot_prompt.strip(),
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
                __import__("json").dumps(export_files_json, indent=2),
            ]
        )

        response_text = invoke_text(llm, prompt)
        try:
            return ExportSummary.model_validate(parse_json(response_text))
        except JSONExtractionError:
            markdown_report = strip_code_fences(response_text)
            return ExportSummary(
                export_files=export_files,
                assembly_report_markdown=markdown_report,
                user_facing_warnings=critic_b_report.user_facing_warnings,
            )
