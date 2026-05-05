from __future__ import annotations

import logging
import re

from cadpilotv3.agents.code_generation_infill_agent import (
    CodeGenerationInfillAgent,
)
from cadpilotv3.config.settings import AppSettings
from cadpilotv3.schemas.geometry_plan import GeometryPlan
from cadpilotv3.schemas.intent_spec import IntentSpec
from cadpilotv3.schemas.parameters import ParameterSchema
from cadpilotv3.schemas.repair import RepairOutput

logger = logging.getLogger(__name__)


class CodeGenerationOutputError(ValueError):
    """Raised when the code generation model returns unusable script text."""


class CodeGenerationInfillService:
    max_generation_attempts = 3

    def __init__(self, settings: AppSettings) -> None:
        self.agent = CodeGenerationInfillAgent(settings)

    def execute_script(
        self,
        spec: IntentSpec,
        geometry_plan: GeometryPlan,
        parameters: ParameterSchema,
        repair_context: RepairOutput | None = None,
        critic_feedback: str | None = None,
        current_script: str | None = None,
    ) -> str:
        logger.info(
            "Running code_generation_agent for complete script",
            extra={"component": getattr(spec, "component", None)},
        )

        generation_feedback = None
        last_error: CodeGenerationOutputError | None = None

        for attempt_number in range(1, self.max_generation_attempts + 1):
            implemented_script = self.agent.run(
                spec=spec,
                geometry_plan=geometry_plan,
                parameters=parameters,
                repair_context=repair_context,
                critic_feedback=critic_feedback,
                current_script=current_script,
                generation_feedback=generation_feedback,
            )
            implemented_script = self._extract_generated_code(implemented_script)

            try:
                self._validate_generated_code(implemented_script)
            except CodeGenerationOutputError as exc:
                last_error = exc
                generation_feedback = str(exc)
                logger.warning(
                    "Code generation returned unusable output; retrying",
                    extra={
                        "attempt_number": attempt_number,
                        "max_attempts": self.max_generation_attempts,
                        "reason": str(exc),
                    },
                )
                continue

            logger.info(
                "Implemented complete CadQuery script",
                extra={
                    "output_length_chars": len(implemented_script),
                    "attempt_number": attempt_number,
                },
            )

            return implemented_script

        raise last_error or CodeGenerationOutputError("Code generation failed validation")

    def _validate_generated_code(self, implemented_script: str) -> None:
        if not implemented_script.strip():
            raise CodeGenerationOutputError("Code generation returned an empty script")

        if "cadquery" not in implemented_script:
            raise CodeGenerationOutputError(
                "Code generation returned text that does not appear to import CadQuery"
            )

    def _extract_generated_code(self, generated_text: str) -> str:
        text = generated_text.strip()
        full_fence = re.compile(
            r"^\s*```(?:python|py)?\s*\r?\n(?P<code>.*?)\r?\n```\s*$",
            re.IGNORECASE | re.DOTALL,
        )
        match = full_fence.match(text)
        if match:
            return match.group("code").strip() + "\n"

        python_fence = re.compile(
            r"```(?:python|py)\s*\r?\n(?P<code>.*?)\r?\n```",
            re.IGNORECASE | re.DOTALL,
        )
        match = python_fence.search(text)
        if match:
            return match.group("code").strip() + "\n"

        return text + "\n"

    def apply_function_implementation(
        self,
        current_script: str,
        function_name: str,
        implemented_function_code: str,
    ) -> str:
        updated_script = self._replace_function_definition(
            current_script=current_script,
            function_name=function_name,
            replacement_code=implemented_function_code,
        )

        if updated_script == current_script:
            logger.warning(
                "Could not replace function implementation; appending implemented code",
                extra={"function_name": function_name},
            )
            updated_script = f"{current_script.rstrip()}\n\n{implemented_function_code.strip()}\n"

        return updated_script

    def apply_patch(
        self,
        current_script: str,
        affected_function: str,
        patched_code: str,
    ) -> str:
        if affected_function == "__main__":
            updated_script = self._replace_main_block(
                current_script=current_script,
                replacement_code=patched_code,
            )
        else:
            updated_script = self._replace_function_definition(
                current_script=current_script,
                function_name=affected_function,
                replacement_code=patched_code,
            )

        if updated_script == current_script:
            logger.warning(
                "Could not apply patch to function; appending patched code",
                extra={"affected_function": affected_function},
            )
            updated_script = f"{current_script.rstrip()}\n\n{patched_code.strip()}\n"

        return updated_script

    def _replace_function_definition(
        self,
        current_script: str,
        function_name: str,
        replacement_code: str,
    ) -> str:
        lines = current_script.splitlines(keepends=True)
        pattern = re.compile(rf"^\s*def\s+{re.escape(function_name)}\s*\(", re.MULTILINE)
        start_index = next(
            (
                idx
                for idx, line in enumerate(lines)
                if pattern.match(line)
            ),
            None,
        )

        if start_index is None:
            return current_script

        indent = len(lines[start_index]) - len(lines[start_index].lstrip(" \t"))
        end_index = start_index + 1
        while end_index < len(lines):
            line = lines[end_index]
            if line.strip() == "":
                end_index += 1
                continue
            current_indent = len(line) - len(line.lstrip(" \t"))
            if current_indent <= indent:
                break
            end_index += 1

        replacement = replacement_code.rstrip() + "\n"
        return "".join(lines[:start_index] + [replacement] + lines[end_index:])

    def _replace_main_block(
        self,
        current_script: str,
        replacement_code: str,
    ) -> str:
        lines = current_script.splitlines(keepends=True)
        pattern = re.compile(r"""^if\s+__name__\s*==\s*["']__main__["']\s*:""")
        start_index = next(
            (
                idx
                for idx, line in enumerate(lines)
                if pattern.match(line)
            ),
            None,
        )

        if start_index is None:
            return current_script

        end_index = start_index + 1
        while end_index < len(lines):
            line = lines[end_index]
            if line.strip() == "":
                end_index += 1
                continue
            current_indent = len(line) - len(line.lstrip(" \t"))
            if current_indent == 0:
                break
            end_index += 1

        replacement = replacement_code.rstrip() + "\n"
        return "".join(lines[:start_index] + [replacement] + lines[end_index:])
