from __future__ import annotations

import ast
import json
import logging
import re
import uuid
from pathlib import Path

from cadpilotv3.agents.code_generation_infill_agent import (
    CodeGenerationInfillAgent,
)
from cadpilotv3.config.settings import AppSettings
from cadpilotv3.schemas.geometry_plan import GeometryPlan
from cadpilotv3.schemas.intent_spec import IntentSpec
from cadpilotv3.schemas.parameters import ParameterSchema
from cadpilotv3.schemas.repair import RepairOutput
from cadpilotv3.shared import LLMTextResult, coerce_llm_text_result
from cadpilotv3.shared.llm_trace import update_llm_trace

logger = logging.getLogger(__name__)


class CodeGenerationOutputError(ValueError):
    """Raised when the code generation model returns unusable script text."""


class CodePatchApplicationError(ValueError):
    """Raised when a repair patch cannot be applied without corrupting the script."""


class CodeGenerationInfillService:
    max_generation_attempts = 3

    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
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
        compact_retry = False

        for attempt_number in range(1, self.max_generation_attempts + 1):
            llm_result = coerce_llm_text_result(
                self.agent.run(
                    spec=spec,
                    geometry_plan=geometry_plan,
                    parameters=parameters,
                    repair_context=repair_context,
                    critic_feedback=critic_feedback,
                    current_script=current_script,
                    generation_feedback=generation_feedback,
                    compact_retry=compact_retry,
                )
            )
            implemented_script = self._extract_generated_code(llm_result.text)
            update_llm_trace(
                llm_result.trace_dir,
                metadata_updates={
                    "extracted_script_length_chars": len(implemented_script),
                },
                files={"extracted_script.py": implemented_script},
            )

            try:
                self._validate_generated_code(implemented_script)
            except CodeGenerationOutputError as exc:
                last_error = exc
                generation_feedback = str(exc)
                compact_retry = self._should_use_compact_retry(exc)
                update_llm_trace(
                    llm_result.trace_dir,
                    metadata_updates={
                        "validation_status": "failed",
                        "validation_error": str(exc),
                        "compact_retry_next": compact_retry,
                    },
                )
                artifact_path = self._write_failed_attempt(
                    llm_result=llm_result,
                    implemented_script=implemented_script,
                    attempt_number=attempt_number,
                    reason=str(exc),
                    compact_retry=compact_retry,
                )
                logger.warning(
                    (
                        "Code generation returned unusable output; retrying "
                        f"reason={exc}"
                    ),
                    extra={
                        "attempt_number": attempt_number,
                        "max_attempts": self.max_generation_attempts,
                        "reason": str(exc),
                        "artifact_path": str(artifact_path) if artifact_path else None,
                        "raw_response_length_chars": len(llm_result.text),
                        "extracted_script_length_chars": len(implemented_script),
                        "compact_retry_next": compact_retry,
                    },
                )
                continue

            update_llm_trace(
                llm_result.trace_dir,
                metadata_updates={"validation_status": "passed"},
            )
            logger.info(
                "Implemented complete CadQuery script",
                extra={
                    "output_length_chars": len(implemented_script),
                    "attempt_number": attempt_number,
                },
            )

            return implemented_script

        raise last_error or CodeGenerationOutputError("Code generation failed validation")

    async def aexecute_script(
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
        compact_retry = False

        for attempt_number in range(1, self.max_generation_attempts + 1):
            llm_result = coerce_llm_text_result(
                await self.agent.arun(
                    spec=spec,
                    geometry_plan=geometry_plan,
                    parameters=parameters,
                    repair_context=repair_context,
                    critic_feedback=critic_feedback,
                    current_script=current_script,
                    generation_feedback=generation_feedback,
                    compact_retry=compact_retry,
                )
            )
            implemented_script = self._extract_generated_code(llm_result.text)
            update_llm_trace(
                llm_result.trace_dir,
                metadata_updates={
                    "extracted_script_length_chars": len(implemented_script),
                },
                files={"extracted_script.py": implemented_script},
            )

            try:
                self._validate_generated_code(implemented_script)
            except CodeGenerationOutputError as exc:
                last_error = exc
                generation_feedback = str(exc)
                compact_retry = self._should_use_compact_retry(exc)
                update_llm_trace(
                    llm_result.trace_dir,
                    metadata_updates={
                        "validation_status": "failed",
                        "validation_error": str(exc),
                        "compact_retry_next": compact_retry,
                    },
                )
                artifact_path = self._write_failed_attempt(
                    llm_result=llm_result,
                    implemented_script=implemented_script,
                    attempt_number=attempt_number,
                    reason=str(exc),
                    compact_retry=compact_retry,
                )
                logger.warning(
                    (
                        "Code generation returned unusable output; retrying "
                        f"reason={exc}"
                    ),
                    extra={
                        "attempt_number": attempt_number,
                        "max_attempts": self.max_generation_attempts,
                        "reason": str(exc),
                        "artifact_path": str(artifact_path) if artifact_path else None,
                        "raw_response_length_chars": len(llm_result.text),
                        "extracted_script_length_chars": len(implemented_script),
                        "compact_retry_next": compact_retry,
                    },
                )
                continue

            update_llm_trace(
                llm_result.trace_dir,
                metadata_updates={"validation_status": "passed"},
            )
            logger.info(
                "Implemented complete CadQuery script",
                extra={
                    "output_length_chars": len(implemented_script),
                    "attempt_number": attempt_number,
                },
            )

            return implemented_script

        raise last_error or CodeGenerationOutputError("Code generation failed validation")

    def _should_use_compact_retry(self, error: CodeGenerationOutputError) -> bool:
        return "empty script" in str(error).lower()

    def _write_failed_attempt(
        self,
        *,
        llm_result: LLMTextResult,
        implemented_script: str,
        attempt_number: int,
        reason: str,
        compact_retry: bool,
    ) -> Path | None:
        try:
            settings = getattr(self, "settings", None)
            artifacts_dir = getattr(settings, "cad_artifacts_dir", "artifacts")
            run_dir = (
                Path(artifacts_dir)
                / "codegen_failed_attempts"
                / f"attempt_{uuid.uuid4().hex}"
            )
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "raw_response.txt").write_text(
                llm_result.text,
                encoding="utf-8",
            )
            (run_dir / "generated_script.py").write_text(
                implemented_script,
                encoding="utf-8",
            )
            (run_dir / "metadata.json").write_text(
                json.dumps(
                    {
                        "attempt_number": attempt_number,
                        "max_attempts": self.max_generation_attempts,
                        "reason": reason,
                        "raw_response_length_chars": len(llm_result.text),
                        "extracted_script_length_chars": len(implemented_script),
                        "response_metadata": llm_result.response_metadata,
                        "usage_metadata": llm_result.usage_metadata,
                        "response_id": llm_result.response_id,
                        "compact_retry_next": compact_retry,
                        "raw_response_repr": llm_result.raw_response_repr[:4000],
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            return run_dir
        except OSError:
            logger.exception("Failed to persist rejected codegen attempt")
            return None

    def _validate_generated_code(self, implemented_script: str) -> None:
        if not implemented_script.strip():
            raise CodeGenerationOutputError("Code generation returned an empty script")

        if "cadquery" not in implemented_script:
            raise CodeGenerationOutputError(
                "Code generation returned text that does not appear to import CadQuery"
            )

        self._preflight_generated_code(implemented_script)

    def _preflight_generated_code(self, implemented_script: str) -> None:
        try:
            tree = ast.parse(implemented_script)
        except SyntaxError as exc:
            raise CodeGenerationOutputError(f"Generated script has a syntax error: {exc}") from exc

        function_names = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }

        if not ({"build_part", "build_assembly"} & function_names):
            raise CodeGenerationOutputError(
                "Generated script must define build_part() or build_assembly()"
            )
        if "validate_geometry" not in function_names:
            raise CodeGenerationOutputError("Generated script must define validate_geometry()")
        if "export_all" not in function_names:
            raise CodeGenerationOutputError("Generated script must define export_all()")

        if any(isinstance(node, ast.Global) for node in ast.walk(tree)):
            raise CodeGenerationOutputError(
                "Generated script must not use global statements; use constants directly"
            )

        if any(self._is_disallowed_hole_call(node) for node in ast.walk(tree)):
            raise CodeGenerationOutputError(
                "Generated script must avoid Workplane.hole(); use explicit cutter solids"
            )

        if any(self._is_disallowed_volume_reasonable_key(node) for node in ast.walk(tree)):
            raise CodeGenerationOutputError(
                "Generated script must not include heuristic volume_reasonable checks; "
                "use positive-volume and bounding-box checks only"
            )

        if not any(self._is_main_guard(node) for node in ast.walk(tree)):
            raise CodeGenerationOutputError("Generated script must include a __main__ export block")

    def _is_disallowed_hole_call(self, node: ast.AST) -> bool:
        return (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "hole"
        )

    def _is_main_guard(self, node: ast.AST) -> bool:
        if not isinstance(node, ast.If):
            return False

        test = node.test
        if not isinstance(test, ast.Compare):
            return False
        if not isinstance(test.left, ast.Name) or test.left.id != "__name__":
            return False
        if len(test.ops) != 1 or not isinstance(test.ops[0], ast.Eq):
            return False
        if len(test.comparators) != 1:
            return False

        comparator = test.comparators[0]
        return isinstance(comparator, ast.Constant) and comparator.value == "__main__"

    def _is_disallowed_volume_reasonable_key(self, node: ast.AST) -> bool:
        disallowed_names = {
            "volume_reasonable",
            "volume_reduced_by_holes",
            "expected_volume",
            "expected_plate_volume",
            "expected_final_volume_upper_bound",
        }

        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value in disallowed_names

        return isinstance(node, ast.Name) and node.id in disallowed_names

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

        opening_fence = re.compile(
            r"^\s*```(?:python|py)?\s*\r?\n(?P<code>.*)$",
            re.IGNORECASE | re.DOTALL,
        )
        match = opening_fence.match(text)
        if match:
            return match.group("code").strip() + "\n"

        apostrophe_fence = re.compile(
            r"^\s*'''(?:python|py)?\s*\r?\n(?P<code>.*?)\r?\n'''\s*$",
            re.IGNORECASE | re.DOTALL,
        )
        match = apostrophe_fence.match(text)
        if match:
            return match.group("code").strip() + "\n"

        quoted_language_prefix = re.compile(
            r"^\s*['\"]{0,3}(?:python|py)['\"]{0,3}\s*\r?\n(?P<code>.*)$",
            re.IGNORECASE | re.DOTALL,
        )
        match = quoted_language_prefix.match(text)
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
            raise CodePatchApplicationError(
                f"Could not replace function implementation for '{function_name}'"
            )

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
            raise CodePatchApplicationError(
                f"Could not apply patch to function '{affected_function}'"
            )

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
